import json
import hmac
import hashlib
import logging
import boto3
import github
import os
import re
from typing import List
import sys
from pprint import pformat
from jsonpath_ng import parse


log = logging.getLogger(__name__)
stream = logging.StreamHandler(sys.stdout)
log.addHandler(stream)
log.setLevel(logging.DEBUG)

ssm = boto3.client("ssm")


def lambda_handler(event, context):
    """
    Validates the request's sha256 digest value and checks if the GitHub payload passes atleast one of the filter groups.

    Requirements:
        - Payload body must be mapped to the key `body`
        - Payload headers must be mapped to the key `headers`
        - Filter groups and events must be specified in /opt/filter_groups.json
        - If private repositories are included, a pre-existing SSM Paramter Store value for the Github token mapped to the
            Lambda's env var: `GITHUB_TOKEN_SSM_KEY` is required.
    """

    log.debug(f"Event:\n{pformat(event)}")

    try:
        validate_sig(event["headers"]["X-Hub-Signature-256"], event["body"])
    except Exception as e:
        logging.error(e, exc_info=True)
        api_exception_json = json.dumps(
            {"isError": True, "type": e.__class__.__name__, "message": str(e)}
        )
        raise LambdaException(api_exception_json)

    payload = json.loads(event["body"])
    event_header = event["headers"]["X-GitHub-Event"]
    log.info(f"GitHub Event: {event_header}")

    try:
        repo_name = payload["repository"]["name"]
    except KeyError:
        raise ClientException("Repository name could not be found in payload")
    log.info(f"Triggered Repo: {repo_name}")

    with open(f"{os.path.dirname(__file__)}/filter_groups.json") as f:
        all_repos_filter_groups = json.load(f)
        log.debug(f"All repos filter groups:\n{all_repos_filter_groups}")
        filter_groups = all_repos_filter_groups[repo_name]
    log.info(f"Filter Groups: {filter_groups}")

    if filter_groups is None:
        raise ClientException(f"Filter groups were not defined for repo: {repo_name}")
    else:
        try:
            log.info("Validating payload")
            response = validate_payload(event_header, payload, filter_groups)
        except Exception as e:
            logging.error(e, exc_info=True)
            api_exception_json = json.dumps(
                {"isError": True, "type": e.__class__.__name__, "message": str(e)}
            )
            raise LambdaException(api_exception_json)

    return response


def validate_sig(header_sig: str, payload: str) -> None:
    """
    Validates incoming request's sha256 value

    :param header_sig: Github webhook's `X-Hub-Signature-256` header value
    :param payload: Github webhook payload. Must be in string version in order to accurately generate the expected signature
    """
    try:
        github_secret = ssm.get_parameter(
            Name=os.environ["GITHUB_WEBHOOK_SECRET_SSM_KEY"], WithDecryption=True
        )["Parameter"]["Value"]
    except Exception:
        raise ServerException("Internal server error")
    try:
        sha, sig = header_sig.split("=")
    except ValueError:
        raise ClientException("Signature not signed with sha256 (e.g. sha256=123456)")

    if sha != "sha256":
        raise ClientException("Signature not signed with sha256 (e.g. sha256=123456)")

    # creates sha256 value using the Github secret associated with the repo's webhook  and the request payload
    expected_sig = hmac.new(
        bytes(str(github_secret), "utf-8"), bytes(str(payload), "utf-8"), hashlib.sha256
    ).hexdigest()

    log.debug(f"Expected signature: {expected_sig}")
    log.debug(f"Actual signature: {sig}")

    authorized = hmac.compare_digest(str(sig), str(expected_sig))

    if not authorized:
        raise ClientException("Header signature and expected signature do not match")


def validate_payload(event: str, payload: dict, filter_groups: List[dict]) -> None:
    """
    Checks if payload body passes atleast one filter group

    :param payload: Github webhook payload
    :param filter_groups: List of filters to check payload with
    """

    token_ssm_keys = json.loads(os.environ["TOKEN_SSM_KEYS"])
    log.debug(f"Token SSM Parameter keys:\n{pformat(token_ssm_keys)}")
    repo_ssm_key = token_ssm_keys.get(payload["repository"]["name"], None)
    if repo_ssm_key:
        try:
            github_token = ssm.get_parameter(Name=repo_ssm_key, WithDecryption=True)[
                "Parameter"
            ]["Value"]
            gh = github.Github(github_token)
        except Exception as e:
            log.error(e, exc_info=True)
            raise ServerException("Internal server error")
    else:
        gh = github.Github()

    try:
        repo = gh.get_repo(payload["repository"]["full_name"])
    except github.UnknownObjectException as e:
        log.error(e, exc_info=True)
        raise ClientException(
            """
        Repository was not found -- If the repository is private, add a GitHub token with `repo` permissions
        to the var.repo `github_token_ssm_value` attribute within the associated Terraform module.
        """
        )

    request_mapping = {"event": event}

    if event == "pull_request":
        request_mapping = {
            **{
                "file_path": [
                    path.filename
                    for path in repo.compare(
                        payload["pull_request"]["base"]["sha"],
                        payload["pull_request"]["head"]["sha"],
                    ).files
                ],
                "commit_message": repo.get_commit(
                    sha=payload["pull_request"]["head"]["sha"]
                ).commit.message,
                "base_ref": payload["pull_request"]["base"]["ref"],
                "head_ref": payload["pull_request"]["head"]["ref"],
                "actor_account_id": payload["sender"]["id"],
                "pr_action": payload["action"],
            },
            **request_mapping,
        }
    elif event == "push":
        request_mapping = {
            **{
                "file_path": [
                    path.filename
                    for path in repo.compare(payload["before"], payload["after"]).files
                ],
                "commit_message": payload["head_commit"]["message"],
                "base_ref": payload["ref"],
                "actor_account_id": payload["sender"]["id"],
            },
            **request_mapping,
        }

    log.debug(f"Payload Target Values:\n{request_mapping}")
    valid = False

    try:
        for group in filter_groups:
            valid_count = 0
            for filter_entry in group:
                log.debug(f"Filter: {filter_entry}")

                if filter_entry["type"] not in list(request_mapping.keys()):
                    log.info(
                        "Filter type not found in request mapping -- Using JSON path"
                    )
                    target = [
                        match.value
                        for match in parse(filter_entry["type"]).find(payload)
                    ]
                else:
                    # puts payload value into a list if value is not already a list
                    # so they can be processed with list payload values
                    target = (
                        [request_mapping[filter_entry["type"]]]
                        if not isinstance(request_mapping[filter_entry["type"]], list)
                        else request_mapping[filter_entry["type"]]
                    )
                log.debug(f"Target values:\n{pformat(target)}")

                for value in target:
                    log.debug(f"Target value:\n{value}")
                    if (
                        re.search(filter_entry["pattern"], value)
                        and not filter_entry["exclude_matched_filter"]
                    ) or (
                        not re.search(filter_entry["pattern"], value)
                        and filter_entry["exclude_matched_filter"]
                    ):
                        log.debug("Matched")
                        valid_count += 1
                        # only one value out of the target needs to be matched for `file_path` filtering
                        break
                    else:
                        log.debug("Not Matched")
            log.debug(f"{valid_count}/{len(group)} filters succeeded")
            if valid_count == len(group):
                valid = True
                break
    except Exception as e:
        logging.error(e, exc_info=True)
        raise ServerException("Internal server error")

    if valid:
        return {"message": "Payload fulfills atleast one filter group"}
    else:
        return {"message": "Payload does not fulfill trigger requirements"}


class ClientException(Exception):
    """Wraps around client-related errors"""

    pass


class LambdaException(Exception):
    """Wraps around all function errors"""

    pass


class ServerException(Exception):
    """Wraps around all server-related errors"""

    pass
