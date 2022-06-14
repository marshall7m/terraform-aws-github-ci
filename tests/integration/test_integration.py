import pytest
from pprint import pformat
import requests
import json
import os
import logging
import sys
import github
import boto3
import uuid
import datetime
import time
import re

from tests.integration.utils import pr, push, get_latest_log_stream_events, wait_for_gh_wh_response, get_wh_ids

log = logging.getLogger(__name__)
stream = logging.StreamHandler(sys.stdout)
log.addHandler(stream)
log.setLevel(logging.DEBUG)

os.environ['AWS_DEFAULT_REGION'] = os.environ['AWS_REGION']
tf_dirs = [f'{os.path.dirname(__file__)}/fixtures']
def pytest_generate_tests(metafunc):
    
    if 'terraform_version' in metafunc.fixturenames:
        tf_versions = [pytest.param('latest')]
        metafunc.parametrize('terraform_version', tf_versions, indirect=True, scope='session', ids=[f'tf_{v.values[0]}' for v in tf_versions])

    if 'tf' in metafunc.fixturenames:
        metafunc.parametrize('tf', tf_dirs, indirect=True, scope='session')


@pytest.fixture
def function_start_time():
    '''Returns timestamp of when the function testing started'''
    start_time = datetime.datetime.now(datetime.timezone.utc)
    return start_time


@pytest.fixture
def repo():
    test_repos = []
    gh = github.Github(os.environ['TF_VAR_testing_github_token']).get_user()
    def _get_or_create(name, private=False):

        try:
            repo = gh.get_repo(name)
        except github.UnknownObjectException:
            log.info(f'Creating repo: {name}')
            repo = gh.create_repo(name, auto_init=True, private=private)
        return repo
    yield _get_or_create

    for name in test_repos:
        log.info(f'Deleting repo: {name}')
        try:
            gh.get_repo(name).delete()
        except github.UnknownObjectException:
            log.info('GitHub repo does not exist')

dummy_repo_params = [(False, 'public'), (True, 'private')]
@pytest.fixture(scope='module', params=dummy_repo_params, ids=[r[1] for r in dummy_repo_params],)
def dummy_repo(tf, request):
    '''Creates a dummy repo for testing'''
    gh = github.Github(os.environ['TF_VAR_testing_github_token']).get_user()
    name = f'{request.param[1]}-mut-terraform-aws-github-webhook-{uuid.uuid4()}'
    log.info(f'Creating repo: {name}')
    repo = gh.create_repo(name, auto_init=True, private=request.param[0])

    tf.env.update({"TF_VAR_includes_private_repo": str(request.param[0]).lower()})
    yield repo
    
    log.info(f'Deleting dummy repo: {name}')
    repo.delete()


@pytest.mark.parametrize('sig,expected_err_msg', [
    pytest.param('sha256=123', 'Header signature and expected signature do not match', id='sha256_signed'),
    pytest.param('sha=123', 'Signature not signed with sha256 (e.g. sha256=123456)', id='sha_signed'),
    pytest.param('123', 'Signature not signed with sha256 (e.g. sha256=123456)', id='not_signed')
])
def test_invalid_sha_sig(tf, sig, expected_err_msg, dummy_repo):
    '''Sends request to the AGW API invoke URL with an invalid signature to the Lambda Function and delivers the right response back to the client.'''
    
    tf_vars = {'includes_private_repo': dummy_repo.private, 'repos': [{'name': dummy_repo.name, 'filter_groups': [[{'type': 'event', 'pattern': 'push'}]]}]}
    with open(f'{tf.tfdir}/terraform.tfvars.json', 'w', encoding='utf-8') as f:
        json.dump(tf_vars, f, ensure_ascii=False, indent=4)

    log.info('Runnning Terraform apply')
    tf.apply(auto_approve=True)

    headers = {
        'content-type': 'application/json',
        'X-Hub-Signature-256': sig, 
        'X-GitHub-Event': 'push'
    }

    tf_output = tf.output()
    response = requests.post(tf_output['invoke_url'], json={'body': {}}, headers=headers).json()
    log.debug(f'Response:\n{response}')

    assert response['type'] == 'ClientException'
    assert response['message'] == expected_err_msg

def test_matched_push_event(tf, function_start_time, dummy_repo):
    '''
    Creates a GitHub push event that meets atleast one of the filter groups' requirements and ensures that the 
    associated API response is valid.
    '''
    tf_vars = {'includes_private_repo': dummy_repo.private, 'repos': [{'name': dummy_repo.name, 'filter_groups': [[{'type': 'event', 'pattern': 'push'}]]}]}
    with open(f'{tf.tfdir}/terraform.tfvars.json', 'w', encoding='utf-8') as f:
        json.dump(tf_vars, f, ensure_ascii=False, indent=4)

    log.info('Runnning Terraform apply')
    tf.apply(auto_approve=True)
    tf_output = tf.output()

    wh_ids = get_wh_ids(tf_output["webhook_urls"][dummy_repo.name])

    log.info('Pushing to repo')
    push(dummy_repo.name, dummy_repo.default_branch, {str(uuid.uuid4()) + '.py': 'dummy'})
    
    log.info("Waiting on GitHub webhook to receive the response")
    response = wait_for_gh_wh_response(tf_output["webhook_urls"][dummy_repo.name], "push", wh_ids)
    log.debug(f"Response:\n{pformat(response)}")
    
    assert json.loads(response['payload']) == {"message": "Payload fulfills atleast one filter group"}


def test_unmatched_push_event(tf, function_start_time, dummy_repo):
    '''
    Creates a GitHub push event that doesn't meet any of the filter groups' requirements and ensures that the 
    associated API response is valid.
    '''

    tf_vars = {'includes_private_repo': dummy_repo.private, 'repos': [
        {
            'name': dummy_repo.name, 
            'filter_groups': [
                [
                    {
                        'type': 'event',
                        'pattern': 'push'
                    },
                    {
                        'type': 'file_path',
                        'pattern': '.+\\.sh'
                    }
                ]
            ]
        }
    ]}
    with open(f'{tf.tfdir}/terraform.tfvars.json', 'w', encoding='utf-8') as f:
        json.dump(tf_vars, f, ensure_ascii=False, indent=4)

    log.info('Runnning Terraform apply')
    tf.apply(auto_approve=True)
    tf_output = tf.output()

    wh_ids = get_wh_ids(tf_output["webhook_urls"][dummy_repo.name])

    log.info('Pushing to repo')
    push(dummy_repo.name, dummy_repo.default_branch, {str(uuid.uuid4()) + '.py': 'dummy'})
    
    log.info("Waiting on GitHub webhook to receive the response")
    response = wait_for_gh_wh_response(tf_output["webhook_urls"][dummy_repo.name], "push", wh_ids)
    log.debug(f"Response:\n{pformat(response)}")

    assert json.loads(response['payload']) == {"message": "Payload does not fulfill trigger requirements"}

def test_matched_pr_event(tf, function_start_time, dummy_repo):
    '''
    Creates a GitHub pull request event that meets atleast one of the filter groups' requirements and ensures that the 
    associated API response is valid.
    '''
    tf_vars = {'includes_private_repo': dummy_repo.private, 'repos': [
        {
            'name': dummy_repo.name, 
            'filter_groups': [
                [
                    {
                        'type': 'event',
                        'pattern': 'pull_request'
                    },
                    {
                        'type': 'file_path',
                        'pattern': '.+\\.py'
                    }
                ]
            ]
        }
    ]}
    with open(f'{tf.tfdir}/terraform.tfvars.json', 'w', encoding='utf-8') as f:
        json.dump(tf_vars, f, ensure_ascii=False, indent=4)

    log.info('Runnning Terraform apply')
    tf.apply(auto_approve=True)
    tf_output = tf.output()

    wh_ids = get_wh_ids(tf_output["webhook_urls"][dummy_repo.name])

    log.info('Creating PR')
    pr(dummy_repo.name, dummy_repo.default_branch, f'feature-{uuid.uuid4()}', {str(uuid.uuid4()) + '.py': 'dummy'}, title=f'test_matched_pr_event-{uuid.uuid4()}')
    
    log.info("Waiting on GitHub webhook to receive the response")
    response = wait_for_gh_wh_response(tf_output["webhook_urls"][dummy_repo.name], "pull_request", wh_ids)
    log.debug(f"Response:\n{pformat(response)}")

    assert json.loads(response['payload']) == {"message": "Payload fulfills atleast one filter group"}
    

def test_unmatched_pr_event(tf, function_start_time, dummy_repo):
    '''
    Creates a GitHub pull request event that doesn't meet any of the filter groups' requirements and ensures that the 
    associated API response is valid.
    '''
    tf_vars = {'includes_private_repo': dummy_repo.private, 'repos': [
        {
            'name': dummy_repo.name, 
            'filter_groups': [
                [
                    {
                        'type': 'event',
                        'pattern': 'pull_request'
                    },
                    {
                        'type': 'file_path',
                        'pattern': '.+\\.sh'
                    }
                ]
            ]
        }
    ]}
    with open(f'{tf.tfdir}/terraform.tfvars.json', 'w', encoding='utf-8') as f:
        json.dump(tf_vars, f, ensure_ascii=False, indent=4)

    log.info('Runnning Terraform apply')
    tf.apply(auto_approve=True)
    tf_output = tf.output()

    wh_ids = get_wh_ids(tf_output["webhook_urls"][dummy_repo.name])

    log.info('Creating PR')
    pr(dummy_repo.name, dummy_repo.default_branch, f'feature-{uuid.uuid4()}', {str(uuid.uuid4()) + '.py': 'dummy'}, title=f'test_matched_pr_event-{uuid.uuid4()}')
    
    log.info("Waiting on GitHub webhook to receive the response")
    response = wait_for_gh_wh_response(tf_output["webhook_urls"][dummy_repo.name], "pull_request", wh_ids)
    log.debug(f"Response:\n{pformat(response)}")
    
    assert json.loads(response['payload']) == {"message": "Payload does not fulfill trigger requirements"}

def test_unsupported_gh_label_event(tf, function_start_time, dummy_repo):
    '''
    Creates a GitHub pull request event that doesn't meet any of the filter groups' requirements and ensures that the 
    associated API response is valid.
    '''
    tf_vars = {'includes_private_repo': dummy_repo.private, 'repos': [
        {
            'name': dummy_repo.name, 
            'filter_groups': [
                [
                    {
                        'type': 'event',
                        'pattern': 'label'
                    }
                ]
            ]
        }
    ]}
    with open(f'{tf.tfdir}/terraform.tfvars.json', 'w', encoding='utf-8') as f:
        json.dump(tf_vars, f, ensure_ascii=False, indent=4)

    log.info('Runnning Terraform apply')
    tf.apply(auto_approve=True)

    tf_output = tf.output()

    wh_ids = get_wh_ids(tf_output["webhook_urls"][dummy_repo.name])

    log.info('Creating label')
    dummy_repo.create_label('test', 'B60205')    
    
    log.info("Waiting on GitHub webhook to receive the response")
    response = wait_for_gh_wh_response(tf_output["webhook_urls"][dummy_repo.name], "label", wh_ids)
    log.debug(f"Response:\n{pformat(response)}")

    assert json.loads(response['payload'])['message'] == "Github event is not supported: label"
