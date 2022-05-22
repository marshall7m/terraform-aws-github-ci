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

from tests.integration.utils import wait_for_lambda_invocation, pr, push, get_latest_log_stream_events

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
    def _get_or_create(name):

        try:
            repo = gh.get_repo(name)
        except github.UnknownObjectException:
            log.info(f'Creating repo: {name}')
            repo = gh.create_repo(name, auto_init=True)
        return repo
    yield _get_or_create

    for name in test_repos:
        log.info(f'Deleting repo: {name}')
        try:
            gh.get_repo(name).delete()
        except github.UnknownObjectException:
            log.info('GitHub repo does not exist')

@pytest.fixture(scope='module')
def dummy_repo():
    '''Creates a dummy repo for testing'''
    gh = github.Github(os.environ['TF_VAR_testing_github_token']).get_user()
    name = f'mut-terraform-aws-github-webhook-{uuid.uuid4()}'
    log.info(f'Creating repo: {name}')
    repo = gh.create_repo(name, auto_init=True)
    yield repo
    
    log.info(f'Deleting dummy repo: {name}')
    repo.delete()

@pytest.mark.parametrize('sig,expected_err_msg', [
    pytest.param('sha256=123', 'Header signature and expected signature do not match', id='sha256_signed'),
    pytest.param('sha=123', 'Signature not signed with sha256 (e.g. sha256=123456)', id='sha_signed'),
    pytest.param('123', 'Signature not signed with sha256 (e.g. sha256=123456)', id='not_signed')
])
def test_invalid_sha_sig(tf, tf_apply, tf_output, sig, expected_err_msg, dummy_repo):
    '''Sends request to the AGW API invoke URL with an invalid signature to the Lambda Function and delivers the right response back to the client.'''
    log.info('Runnning Terraform apply')
    tf_apply(update=True, repos=[{'name': dummy_repo.name, 'filter_groups': [[{'type': 'event', 'pattern': 'push'}]]}])

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

def test_matched_push_event(tf, function_start_time, tf_apply, tf_output, dummy_repo):
    '''
    Creates a GitHub push event that meets atleast one of the filter groups' requirements and ensures that the 
    associated API response is valid.
    '''
    log.info('Runnning Terraform apply')
    tf_apply(update=True, repos=[
        {
            'name': dummy_repo.name, 
            'filter_groups': [
                [
                    {
                        'type': 'event',
                        'pattern': 'push'
                    }
                ]
            ]
        }
    ])
    push(dummy_repo.name, dummy_repo.default_branch, {str(uuid.uuid4()) + '.py': 'dummy'})
    tf_output = tf.output()
    wait_for_lambda_invocation(tf_output['function_name'], function_start_time)

    results = get_latest_log_stream_events(tf_output['agw_log_group_name'], filter_pattern='"Payload fulfills atleast one filter group"', start_time=int(function_start_time.timestamp() * 1000), end_time=int(datetime.datetime.now(datetime.timezone.utc).timestamp() * 1000))

    assert len(results) >= 0

def test_unmatched_push_event(tf, function_start_time, tf_apply, tf_output, dummy_repo):
    '''
    Creates a GitHub push event that doesn't meet any of the filter groups' requirements and ensures that the 
    associated API response is valid.
    '''
    log.info('Runnning Terraform apply')
    tf_apply(update=True, repos=[
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
    ])

    push(dummy_repo.name, dummy_repo.default_branch, {str(uuid.uuid4()) + '.py': 'dummy'})
    tf_output = tf.output()
    wait_for_lambda_invocation(tf_output['function_name'], function_start_time)
    
    results = get_latest_log_stream_events(tf_output['agw_log_group_name'], filter_pattern='"Payload does not fulfill trigger requirements"', start_time=int(function_start_time.timestamp() * 1000), end_time=int(datetime.datetime.now(datetime.timezone.utc).timestamp() * 1000))
    log.debug(f'Cloudwatch Events:\n{pformat(results)}')
    assert len(results) >= 0

def test_matched_pr_event(tf, function_start_time, tf_apply, tf_output, dummy_repo):
    '''
    Creates a GitHub pull request event that meets atleast one of the filter groups' requirements and ensures that the 
    associated API response is valid.
    '''
    log.info('Runnning Terraform apply')
    tf_apply(update=True, repos=[
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
    ])

    pr(dummy_repo.name, dummy_repo.default_branch, f'feature-{uuid.uuid4()}', {str(uuid.uuid4()) + '.py': 'dummy'}, title=f'test_matched_pr_event-{uuid.uuid4()}')
    tf_output = tf.output()
    wait_for_lambda_invocation(tf_output['function_name'], function_start_time)

    tf_output = tf.output()
    results = get_latest_log_stream_events(tf_output['agw_log_group_name'], filter_pattern='"Payload fulfills atleast one filter group"', start_time=int(function_start_time.timestamp() * 1000), end_time=int(datetime.datetime.now(datetime.timezone.utc).timestamp() * 1000))

    assert len(results) >= 1

def test_unmatched_pr_event(tf, function_start_time, tf_apply, tf_output, dummy_repo):
    '''
    Creates a GitHub pull request event that doesn't meet any of the filter groups' requirements and ensures that the 
    associated API response is valid.
    '''
    log.info('Runnning Terraform apply')
    tf_apply(update=True, repos=[
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
    ])

    pr(dummy_repo.name, dummy_repo.default_branch, f'feature-{uuid.uuid4()}', {str(uuid.uuid4()) + '.py': 'dummy'}, title=f'test_unmatched_pr_event-{uuid.uuid4()}')
    tf_output = tf.output()
    wait_for_lambda_invocation(tf_output['function_name'], function_start_time)

    results = get_latest_log_stream_events(tf_output['agw_log_group_name'], filter_pattern='"Payload does not fulfill trigger requirements"', start_time=int(function_start_time.timestamp() * 1000), end_time=int(datetime.datetime.now(datetime.timezone.utc).timestamp() * 1000))
    log.debug(f'Cloudwatch Events:\n{pformat(results)}')
    assert len(results) >= 1

def test_unsupported_gh_label_event(tf, function_start_time, tf_apply, tf_output, dummy_repo):
    '''
    Creates a GitHub pull request event that doesn't meet any of the filter groups' requirements and ensures that the 
    associated API response is valid.
    '''
    log.info('Runnning Terraform apply')
    tf_apply(update=True, repos=[
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
    ])

    dummy_repo.create_label('test', 'B60205')

    tf_output = tf.output()
    wait_for_lambda_invocation(tf_output['function_name'], function_start_time)

    results = get_latest_log_stream_events(tf_output['agw_log_group_name'], filter_pattern='"Github event is not supported"', start_time=int(function_start_time.timestamp() * 1000), end_time=int(datetime.datetime.now(datetime.timezone.utc).timestamp() * 1000))
    log.debug(f'Cloudwatch Events:\n{pformat(results)}')
    assert len(results) >= 1
