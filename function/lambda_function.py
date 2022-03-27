import json
import hmac
import hashlib
import logging
import boto3
from github import Github
import os
import re
from typing import List
from pprint import pformat
import sys

log = logging.getLogger(__name__)
stream = logging.StreamHandler(sys.stdout)
log.addHandler(stream)
log.setLevel(logging.DEBUG)

ssm = boto3.client('ssm')

def lambda_handler(event, context):
    """
    Validates the request's sha256 digest value and checks if the GitHub payload passes atleast one of the filter groups.

    Requirements:
        - Payload body must be mapped to the key `body`
        - Payload headers must be mapped to the key `headers`
        - Pre-existing SSM Paramter Store value for Github token. Parameter key must be specified under Lambda's env var: `GITHUB_TOKEN_SSM_KEY`
            (used to get filepaths that changed between head and base refs via PyGithub)
        - Filter groups and events must be specified in /opt/filter_groups.json
    """

    log.debug(f'Event:\n{event}')

    try:
        validate_sig(event['headers']['X-Hub-Signature-256'], event['body'])
    except Exception as e:
        api_exception_json = json.dumps(
            {
                "isError": True,
                "type": e.__class__.__name__,
                "message": str(e)
            }
        )
        raise LambdaException(api_exception_json)

    payload = json.loads(event['body'])
    event_header = event['headers']['X-GitHub-Event']
    repo_name = payload['repository']['name']
    
    with open('/opt/filter_groups.json') as f:
        filter_groups = json.load(f)[repo_name]
    
    log.info(f'Triggered Repo: {repo_name}')
    log.info(f'GitHub Event: {event_header}')
    log.info(f'Filter Groups: {filter_groups}')
    
    if filter_groups is None:
        log.info(f'Filter groups were not defined for repo: {repo_name}')
    else:
        try:
            log.info('Validating payload')
            validate_payload(event_header, payload, filter_groups)
        except Exception as e:
            api_exception_json = json.dumps(
                {
                    "isError": True,
                    "type": e.__class__.__name__,
                    "message": str(e)
                }
            )
            raise LambdaException(api_exception_json)

    print("Request was successful")
    return {"message": "Request was successful"}

def validate_sig(header_sig: str, payload: str) -> None:
    """
    Validates incoming request's sha256 value

    :param header_sig: Github webhook's `X-Hub-Signature-256` header value
    :param payload: Github webhook payload. Must be in string version in order to accurately generate the expected signature
    """
    try:
        github_secret = ssm.get_parameter(Name=os.environ['GITHUB_WEBHOOK_SECRET_SSM_KEY'], WithDecryption=True)['Parameter']['Value']
    except Exception:
        raise ServerException("Internal server error")
    try:
        sha, sig = header_sig.split('=')
    except ValueError:
        raise ClientException("Signature not signed with sha256 (e.g. sha256=123456)")

    if sha != 'sha256':
        raise ClientException('Signature not signed with sha256 (e.g. sha256=123456)')

    # creates sha256 value using the Github secret associated with the repo's webhook  and the request payload
    expected_sig = hmac.new(bytes(str(github_secret), 'utf-8'), bytes(str(payload), 'utf-8'), hashlib.sha256).hexdigest()

    log.debug(f'Expected signature: {expected_sig}')
    log.debug(f'Actual signature: {sig}')

    authorized = hmac.compare_digest(str(sig), str(expected_sig))

    if not authorized:
       raise ClientException('Header signature and expected signature do not match')

def validate_payload(event: str, payload: dict, filter_groups: List[dict]) -> None:
    """
    Checks if payload body passes atleast one filter group

    :param payload: Github webhook payload
    :param filter_groups: List of filters to check payload with
    """
    try:
        github_token = ssm.get_parameter(Name=os.environ['GITHUB_TOKEN_SSM_KEY'], WithDecryption=True)['Parameter']['Value']
        gh = Github(github_token)
        repo = gh.get_repo(payload['repository']['full_name'])
    except Exception as e:
        logging.error(e, exc_info=True)
        raise ServerException("Internal server error")
    try:
        if event == 'pull_request':
            payload_mapping = {
                'event': event,
                'file_paths': [path.filename for path in repo.compare(payload['pull_request']['base']['sha'], payload['pull_request']['head']['sha']).files],
                'commit_message': repo.get_commit(sha=payload['pull_request']['head']['sha']).commit.message,
                'base_ref': payload['pull_request']['base']['ref'],
                'head_ref': payload['pull_request']['head']['ref'],
                'actor_account_ids': payload['sender']['id'],
                'pr_actions': payload['action']
            }
        elif event == 'push':
            payload_mapping = {
                'event': event,
                'file_paths': [path.filename for path in repo.compare(payload['before'], payload['after']).files],
                'commit_message': payload['head_commit']['message'],
                'base_ref': payload['ref'],
                'actor_account_ids': payload['sender']['id'],
                'pr_actions': payload['action']
            }

        valid = False
        for group in filter_groups:
            valid_count = 0
            for filter_entry in group:
                log.debug(f'Filter: {filter_entry}')
                target = [payload_mapping[filter_entry['type']]] if isinstance(payload_mapping[filter_entry['type']], str) else payload_mapping[filter_entry['type']]
                for value in target:
                    log.debug(f'Target value:\n{value}')
                    if (re.search(filter_entry['pattern'], value) and not filter_entry['exclude_matched_filter']) or (re.search(filter_entry['pattern'], value) and filter_entry['exclude_matched_filter']):
                        log.debug('Matched')
                        valid_count += 1
                        #only one value out of the target needs to be matched for `file_path` filtering
                        break
                    else:
                        log.debug('Not Matched')
            log.debug(f'{valid_count}/{len(group)} filters succeeded')
            if valid_count == len(group):
                valid = True
                break
    except Exception as e:
        logging.error(e, exc_info=True)
        raise ServerException("Internal server error")

    if valid:
        log.info('Payload fulfills atleast one filter group')
    else:
        raise ClientException(
            {
                'message': 'Payload does not fulfill trigger requirements'
            }
        )

class ClientException(Exception):
    """Wraps around client-related errors"""
    pass

class LambdaException(Exception):
    """Wraps around all function errors"""
    pass

class ServerException(Exception):
    """Wraps around all server-related errors"""
    pass