import json
import hmac
import hashlib
import logging
import boto3
from github import Github
import os
import re
from typing import List, Union, Dict, Any
<<<<<<< HEAD
from pprint import pformat
import sys
=======

>>>>>>> parent of e2edad6... replace for_each with count for gh webhook resource to handle case of repo created in parent tf cfg

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
    repo_event = event['headers']['X-GitHub-Event']
    repo_name = payload['repository']['name']
    
    with open('/opt/filter_groups.json') as f:
        filter_groups = json.load(f)[repo_name]

    log.info(f'Triggered Repo: {repo_name}')
    log.info(f'Triggered Event: {repo_event}')

    log.info(f'Valid Events: {repo_event}')
    log.info(f'Filter Groups: {filter_groups}')
    
    if filter_groups is None:
        log.info(f'Filter groups were not defined for repo: {repo_name}')
    else:
        try:
            log.info('Validating payload')
            validate_payload(payload, repo_event, filter_groups)
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

def validate_payload(payload: dict, event: str, filter_groups: List[dict]) -> None:
    """
    Checks if payload body passes atleast one filter group

    :param payload: Github webhook payload
    :param event: Triggered Github event
    :param filter_groups: List of filters to check payload with
    """
    try:
        github_token = ssm.get_parameter(Name=os.environ['GITHUB_TOKEN_SSM_KEY'], WithDecryption=True)['Parameter']['Value']
        gh = Github(github_token)
        repo = gh.get_repo(payload['repository']['full_name'])
    except Exception:
        raise ServerException("Internal server error")
    try:
        if event == 'pull_request':
            log.debug('Running validate_pr()')
            valid = validate_pr(payload, filter_groups, repo)
        elif event == 'push':
            log.debug('Running validate_push()')
            valid = validate_push(payload, filter_groups, repo)
        else:
            raise ClientException(
                {
                    'message': f'Handling for event: {event} has not been created'
                }
            )
    except Exception:
        raise ServerException("Internal server error")

    if valid:
        log.info('Payload fulfills atleast one filter group')
    else:
        raise ClientException(
            {
                'message': 'Payload does not fulfill trigger requirements'
            }
        )

def match_patterns(patterns: List[str], value: Union[List[str], str]) -> bool:
    """
    Returns True if one pattern finds a match within the `value` param

    :param patterns: List of regex patterns
    :param value: string or list of strings to see if a pattern will match with
    """

    if type(value) != list:
        value = [value]
    if patterns:
        for pattern in patterns:
            for v in value:
                if re.search(pattern, v):
                    log.debug('MATCHED')
                    return True

        log.debug('NOT MATCHED')
        log.debug('patterns: %s', patterns)
        log.debug('values: %s', value)
        return False
    else:
        log.debug('No filter pattern is defined')
        return True

def lookup_value(items: List[str], value: str) -> bool:
    """
    Returns True if `value` is within list

    :param items: List to look up value in
    :param value: Value to look up within list
    """

    if value in items:
        log.debug('TRUE')
        return True
    else:
        log.debug('NOT TRUE')
        log.debug(f'valid values: {items}')
        log.debug(f'actual value: {value}')
        return False

def validate_push(payload: Dict[Any, Any], filter_groups: List[Dict[str, Any]], repo: Github.get_repo) -> bool:
    """
    Returns True if payload passes atleast one push related filter group

    :param payload: Github webhook payload
    :param filter_groups: List of filters to check payload with
    :param repo: Triggered repository's PyGithub repository class object
    """

    #gets filenames of files that between head commit and base commit
    diff_paths = [path.filename for path in repo.compare(payload['before'], payload['after']).files]
    
    for i, filter_entry in enumerate(filter_groups):
        log.info(f'filter group: {i+1}/{len(filter_groups)}')
        
        log.debug('filter: events')
        if not lookup_value(filter_entry['events'], 'push'):
            continue

        log.debug('filter: file_paths')
        if not match_patterns(filter_entry['file_paths'], diff_paths):
            continue

        log.debug('filter: commit_messages')
        if not match_patterns(filter_entry['commit_messages'], payload['head_commit']['message']):
            continue

        log.debug('filter: base_refs')
        if not match_patterns(filter_entry['base_refs'], payload['ref']):
            continue

        log.debug('filter: actor_account_ids')
        if not match_patterns(filter_entry['actor_account_ids'], payload['sender']['id']):
            continue
        else:
            log.debug(f'payload passed all filters within group: {filter_entry}')
            if filter_entry['exclude_matched_filter']:
                log.debug('`exclude_matched_filter` is True. Excluding matched filter group')
                return False
            else: 
                return True
    return False
def validate_pr(payload: Dict[Any, Any], filter_groups: List[Dict[str, Any]], repo: Github.get_repo) -> bool:
    """
    Returns True if payload passes atleast one pull-request related filter group

    :param payload: Github webhook payload
    :param filter_groups: List of filters to check payload with
    :param repo: Triggered repository's PyGithub repository class object
    """

    #gets filenames of files that changed between PR head commit and base commit
    diff_paths = [path.filename for path in repo.compare(
        payload['pull_request']['base']['sha'], 
        payload['pull_request']['head']['sha']
    ).files]

    commit_message = repo.get_commit(sha=payload['pull_request']['head']['sha']).commit.message

    for filter_entry in filter_groups:
        
        log.debug('filter: events')
        if not lookup_value(filter_entry['events'], 'pull_request'):
            continue

        log.debug('filter: file_paths')
        if not match_patterns(filter_entry['file_paths'], diff_paths):
            continue

        log.debug('filter: commit_messages')
        if not match_patterns(filter_entry['commit_messages'], commit_message):
            continue

        log.debug('filter: base_refs')
        if not match_patterns(filter_entry['base_refs'], payload['pull_request']['base']['ref']):
            continue

        log.debug('filter: head_refs')
        if not match_patterns(filter_entry['head_refs'], payload['pull_request']['head']['ref']):
            continue

        log.debug('filter: actor_account_ids')
        if not match_patterns(filter_entry['actor_account_ids'], payload['sender']['id']):
            continue
        
        log.debug('filter: pr_actions')
        if not lookup_value(filter_entry['pr_actions'], payload['action']):
            continue
        else:
            log.debug(f'all filters are valid within group: {filter_entry}')
            if filter_entry['exclude_matched_filter']:
                log.debug('`exclude_matched_filter` is True. Excluding matched filter group')
                return False
            else: 
                return True
    return False

class ClientException(Exception):
    """Wraps around client-related errors"""
    pass

class LambdaException(Exception):
    """Wraps around all function errors"""
    pass

class ServerException(Exception):
    """Wraps around all server-related errors"""
    pass