import pytest
import os
import logging
import sys
import hmac
import hashlib
import json
import re
from unittest.mock import patch, mock_open
from function import lambda_function
from collections import defaultdict


log = logging.getLogger(__name__)
stream = logging.StreamHandler(sys.stdout)
log.addHandler(stream)
log.setLevel(logging.DEBUG)


class dotdict(dict):
    """dot.notation access to dictionary attributes"""

    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__


def create_sha256_sig(value, payload):
    """Returns sha256 value using the provided arguments"""
    return hmac.new(
        bytes(str(value), "utf-8"), bytes(str(payload), "utf-8"), hashlib.sha256
    ).hexdigest()


@patch.dict(os.environ, {"GITHUB_WEBHOOK_SECRET_SSM_KEY": "dummy-ssm-key"})
@patch(
    "function.lambda_function.ssm.get_parameter",
    return_value={"Parameter": {"Value": "bar"}},
)
def test_valid_sig(mock_ssm_get_parameter):
    """Ensure that validate_sig() succeeds when the header signature is valid"""
    payload = "foo"
    lambda_function.validate_sig("sha256=" + create_sha256_sig("bar", payload), payload)


@patch.dict(os.environ, {"GITHUB_WEBHOOK_SECRET_SSM_KEY": "dummy-ssm-key"})
@patch("function.lambda_function.ssm")
@pytest.mark.parametrize(
    "header_sig,payload,github_secret,expected_msg",
    [
        pytest.param(
            "sha256=" + create_sha256_sig("baz", "foo"),
            "foo",
            "bar",
            "Header signature and expected signature do not match",
            id="invalid_sha256",
        ),
        pytest.param(
            "sha=" + create_sha256_sig("bar", "foo"),
            "foo",
            "bar",
            "Signature not signed with sha256 (e.g. sha256=123456)",
            id="invalid_sha_type",
        ),
        pytest.param(
            "bar",
            "foo",
            "bar",
            "Signature not signed with sha256 (e.g. sha256=123456)",
            id="invalid_sig",
        ),
    ],
)
def test_invalid_sig(mock_ssm, header_sig, payload, github_secret, expected_msg):
    """Ensure that validate_sig() raises the expected exception when the header signature is invalid"""
    mock_ssm.get_parameter.return_value = {"Parameter": {"Value": github_secret}}

    with pytest.raises(lambda_function.ClientException, match=re.escape(expected_msg)):
        lambda_function.validate_sig(header_sig, payload)


@patch.dict(os.environ, {"TOKEN_SSM_KEYS": json.dumps({"repo": "ssm-key"})})
@patch("github.Github.get_repo")
@pytest.mark.parametrize(
    "event,payload,modified_file_paths,pr_commit_message,filter_groups",
    [
        pytest.param(
            "pull_request",
            {
                "repository": {
                    "full_name": "user/dummy-repo",
                    "name": "dummy-repo",
                    "html_url": "https://github.com/user/dummy-repo.git",
                },
                "action": "closed",
                "merged": True,
                "pull_request": {
                    "base": {"ref": "master", "sha": "base-sha"},
                    "head": {"ref": "feature-1", "sha": "head-sha"},
                    "numbder": 1,
                },
                "ref": "ref/heads/master",
                "sender": {"id": "dummy-sender-id"},
            },
            ["foo.py"],
            None,
            [
                [
                    {
                        "type": "event",
                        "pattern": "pull_request",
                        "exclude_matched_filter": False,
                    }
                ]
            ],
            id="pull_request",
        ),
        pytest.param(
            "push",
            {
                "repository": {
                    "full_name": "user/dummy-repo",
                    "name": "dummy-repo",
                    "html_url": "https://github.com/user/dummy-repo.git",
                },
                "ref": "ref/heads/master",
                "before": "base-sha",
                "after": "head-sha",
                "head_commit": {"message": "dummy-head-commit-message"},
                "sender": {"id": "dummy-sender-id"},
            },
            ["foo.py"],
            None,
            [
                [
                    {
                        "type": "event",
                        "pattern": "push",
                        "exclude_matched_filter": False,
                    },
                    {
                        "type": "file_path",
                        "pattern": ".+\\.py",
                        "exclude_matched_filter": False,
                    },
                    {
                        "type": "commit_message",
                        "pattern": ".+",
                        "exclude_matched_filter": False,
                    },
                    {
                        "type": "base_ref",
                        "pattern": ".+",
                        "exclude_matched_filter": False,
                    },
                    {
                        "type": "actor_account_id",
                        "pattern": ".+",
                        "exclude_matched_filter": False,
                    },
                ]
            ],
            id="push_one_match",
        ),
        pytest.param(
            "push",
            {
                "repository": {
                    "full_name": "user/dummy-repo",
                    "name": "dummy-repo",
                    "html_url": "https://github.com/user/dummy-repo.git",
                },
                "ref": "ref/heads/master",
                "before": "base-sha",
                "after": "head-sha",
                "head_commit": {"message": "dummy-head-commit-message"},
                "sender": {"id": "dummy-sender-id"},
            },
            ["foo.py"],
            None,
            [
                [
                    {
                        "type": "event",
                        "pattern": "push",
                        "exclude_matched_filter": False,
                    },
                    {
                        "type": "file_path",
                        "pattern": ".+\\.py",
                        "exclude_matched_filter": False,
                    },
                ],
                [
                    {
                        "type": "commit_message",
                        "pattern": ".+",
                        "exclude_matched_filter": False,
                    },
                    {
                        "type": "base_ref",
                        "pattern": ".+",
                        "exclude_matched_filter": False,
                    },
                    {
                        "type": "actor_account_id",
                        "pattern": ".+",
                        "exclude_matched_filter": False,
                    },
                ],
            ],
            id="push_multiple_matches",
        ),
        pytest.param(
            "push",
            {
                "repository": {
                    "full_name": "user/dummy-repo",
                    "name": "dummy-repo",
                    "html_url": "https://github.com/user/dummy-repo.git",
                },
                "ref": "ref/heads/master",
                "before": "base-sha",
                "after": "head-sha",
                "head_commit": {"message": "dummy-head-commit-message"},
                "sender": {"id": "dummy-sender-id"},
            },
            ["foo.py"],
            None,
            [
                [
                    {
                        "type": "event",
                        "pattern": "push",
                        "exclude_matched_filter": False,
                    },
                    {
                        "type": "file_path",
                        "pattern": ".+\\.sh",
                        "exclude_matched_filter": False,
                    },
                ],
                [
                    {
                        "type": "commit_message",
                        "pattern": ".+",
                        "exclude_matched_filter": False,
                    },
                    {
                        "type": "base_ref",
                        "pattern": ".+",
                        "exclude_matched_filter": False,
                    },
                    {
                        "type": "actor_account_id",
                        "pattern": ".+",
                        "exclude_matched_filter": False,
                    },
                ],
            ],
            id="push_one_match_one_unmatch",
        ),
        pytest.param(
            "push",
            {
                "repository": {
                    "full_name": "user/dummy-repo",
                    "name": "dummy-repo",
                    "html_url": "https://github.com/user/dummy-repo.git",
                },
                "ref": "ref/heads/master",
                "before": "base-sha",
                "after": "head-sha",
                "head_commit": {"message": "dummy-head-commit-message"},
                "sender": {"id": "dummy-sender-id"},
            },
            ["foo.py"],
            None,
            [
                [
                    {
                        "type": "event",
                        "pattern": "push",
                        "exclude_matched_filter": False,
                    },
                    {
                        "type": "file_path",
                        "pattern": ".+\\.py",
                        "exclude_matched_filter": False,
                    },
                    {
                        "type": "commit_message",
                        "pattern": ".+",
                        "exclude_matched_filter": False,
                    },
                    {
                        "type": "base_ref",
                        "pattern": "ref/heads/master",
                        "exclude_matched_filter": False,
                    },
                    {
                        "type": "base_ref",
                        "pattern": "ref/heads/feature-branch-2",
                        "exclude_matched_filter": True,
                    },
                    {
                        "type": "actor_account_id",
                        "pattern": ".+",
                        "exclude_matched_filter": False,
                    },
                ]
            ],
            id="push_one_match_exclude_base_ref",
        ),
        pytest.param(
            "push",
            {
                "repository": {
                    "full_name": "user/dummy-repo",
                    "name": "dummy-repo",
                    "html_url": "https://github.com/user/dummy-repo.git",
                    "private": "true",
                },
                "ref": "ref/heads/master",
                "before": "base-sha",
                "after": "head-sha",
                "head_commit": {"message": "dummy-head-commit-message"},
                "sender": {"id": "dummy-sender-id"},
            },
            [],
            None,
            [
                [
                    {
                        "type": "repository.private",
                        "pattern": "true",
                        "exclude_matched_filter": False,
                    }
                ]
            ],
            id="push_one_match_json_path",
        ),
    ],
)
def test_matched_filter_group(
    mock_repo, event, payload, modified_file_paths, pr_commit_message, filter_groups
):
    """Ensure that validate_payload() succeeds using payloads that meet atleast one filter group"""
    # use param filepaths for repo.compare() file paths
    mock_repo.return_value.compare.return_value.files = [
        dotdict({"filename": path}) for path in modified_file_paths
    ]
    # needed only with PR events since PR commit message is looked up via repo.get_commit() since it's not in payload
    mock_repo.return_value.get_commit.return_value.commit.message = pr_commit_message

    response = lambda_function.validate_payload(event, payload, filter_groups)

    assert response["message"] == "Payload fulfills atleast one filter group"


@patch.dict(os.environ, {"TOKEN_SSM_KEYS": json.dumps({"repo": "ssm-key"})})
@patch("github.Github.get_repo")
@pytest.mark.parametrize(
    "event,payload,modified_file_paths,pr_commit_message,filter_groups",
    [
        pytest.param(
            "pull_request",
            {
                "repository": {
                    "full_name": "user/dummy-repo",
                    "name": "dummy-repo",
                    "html_url": "https://github.com/user/dummy-repo.git",
                },
                "action": "closed",
                "merged": True,
                "pull_request": {
                    "base": {"ref": "master", "sha": "base-sha"},
                    "head": {"ref": "feature-1", "sha": "head-sha"},
                    "numbder": 1,
                },
                "ref": "ref/heads/master",
                "sender": {"id": "dummy-sender-id"},
            },
            ["foo.py"],
            None,
            [
                [
                    {
                        "type": "event",
                        "pattern": "pull_request",
                        "exclude_matched_filter": False,
                    },
                    {
                        "type": "head_ref",
                        "pattern": "feature-2",
                        "exclude_matched_filter": False,
                    },
                ]
            ],
            id="pull_request_unmatched_head_ref",
        ),
        pytest.param(
            "push",
            {
                "repository": {
                    "full_name": "user/dummy-repo",
                    "name": "dummy-repo",
                    "html_url": "https://github.com/user/dummy-repo.git",
                },
                "ref": "ref/heads/master",
                "before": "base-sha",
                "after": "head-sha",
                "head_commit": {"message": "dummy-head-commit-message"},
                "sender": {"id": "dummy-sender-id"},
            },
            ["foo.sh"],
            None,
            [
                [
                    {
                        "type": "event",
                        "pattern": "push",
                        "exclude_matched_filter": False,
                    },
                    {
                        "type": "file_path",
                        "pattern": ".+\\.py",
                        "exclude_matched_filter": False,
                    },
                    {
                        "type": "commit_message",
                        "pattern": ".+",
                        "exclude_matched_filter": False,
                    },
                    {
                        "type": "base_ref",
                        "pattern": ".+",
                        "exclude_matched_filter": False,
                    },
                    {
                        "type": "actor_account_id",
                        "pattern": ".+",
                        "exclude_matched_filter": False,
                    },
                ]
            ],
            id="push_unmatched_file_path",
        ),
        pytest.param(
            "push",
            {
                "repository": {
                    "full_name": "user/dummy-repo",
                    "name": "dummy-repo",
                    "html_url": "https://github.com/user/dummy-repo.git",
                },
                "ref": "ref/heads/master",
                "before": "base-sha",
                "after": "head-sha",
                "head_commit": {"message": "dummy-head-commit-message"},
                "sender": {"id": "dummy-sender-id"},
            },
            ["foo.py"],
            None,
            [
                [
                    {
                        "type": "event",
                        "pattern": "push",
                        "exclude_matched_filter": False,
                    },
                    {
                        "type": "file_path",
                        "pattern": ".+\\.py",
                        "exclude_matched_filter": True,
                    },
                    {
                        "type": "commit_message",
                        "pattern": ".+",
                        "exclude_matched_filter": False,
                    },
                    {
                        "type": "base_ref",
                        "pattern": ".+",
                        "exclude_matched_filter": False,
                    },
                    {
                        "type": "actor_account_id",
                        "pattern": ".+",
                        "exclude_matched_filter": False,
                    },
                ]
            ],
            id="push_unmatched_exclude_file_path",
        ),
        pytest.param(
            "push",
            {
                "repository": {
                    "full_name": "user/dummy-repo",
                    "name": "dummy-repo",
                    "html_url": "https://github.com/user/dummy-repo.git",
                },
                "ref": "ref/heads/master",
                "before": "base-sha",
                "after": "head-sha",
                "head_commit": {"message": "dummy-head-commit-message"},
                "sender": {"id": "dummy-sender-id"},
            },
            ["foo.sh"],
            None,
            [
                [
                    {
                        "type": "event",
                        "pattern": "push",
                        "exclude_matched_filter": False,
                    },
                    {
                        "type": "file_path",
                        "pattern": ".+\\.py",
                        "exclude_matched_filter": False,
                    },
                ],
                [
                    {
                        "type": "commit_message",
                        "pattern": ".+",
                        "exclude_matched_filter": False,
                    },
                    {
                        "type": "base_ref",
                        "pattern": "ref/heads/feature-branch-1",
                        "exclude_matched_filter": False,
                    },
                    {
                        "type": "actor_account_id",
                        "pattern": ".+",
                        "exclude_matched_filter": False,
                    },
                ],
            ],
            id="push_multiple_unmatch",
        ),
        pytest.param(
            "push",
            {
                "repository": {
                    "full_name": "user/dummy-repo",
                    "name": "dummy-repo",
                    "html_url": "https://github.com/user/dummy-repo.git",
                    "private": "true",
                },
                "ref": "ref/heads/master",
                "before": "base-sha",
                "after": "head-sha",
                "head_commit": {"message": "dummy-head-commit-message"},
                "sender": {"id": "dummy-sender-id"},
            },
            [],
            None,
            [
                [
                    {
                        "type": "repository.private",
                        "pattern": "false",
                        "exclude_matched_filter": False,
                    }
                ]
            ],
            id="push_unmatched_json_path",
        ),
    ],
)
def test_no_matched_filter_group(
    mock_repo, event, payload, modified_file_paths, pr_commit_message, filter_groups
):
    """Ensure that validate_payload() raises the approriate exception when using payloads that don't meet any filter groups"""
    # use param filepaths for repo.compare() file paths
    mock_repo.return_value.compare.return_value.files = [
        dotdict({"filename": path}) for path in modified_file_paths
    ]
    # needed only with PR events since PR commit message is looked up via repo.get_commit() since it's not in payload
    mock_repo.return_value.get_commit.return_value.commit.message = pr_commit_message

    with pytest.raises(
        lambda_function.ClientException,
        match="Payload does not fulfill trigger requirements",
    ):
        lambda_function.validate_payload(event, payload, filter_groups)


@patch("function.lambda_function.validate_sig", return_value=None)
@patch("function.lambda_function.validate_payload", return_value="success")
@patch("json.load", return_value=defaultdict(dict))
@patch("json.loads", return_value=defaultdict(lambda: defaultdict(lambda: "")))
@patch("builtins.open", new_callable=mock_open, read_data="mock_open")
def test_successful_lambda_handler(
    mock_open_file,
    mock_json_load,
    mock_json_loads,
    mock_validate_payload,
    mock_validate_sig,
):
    """Ensure that lambda_handler() returns the expected value when function succeeds"""
    event = defaultdict(lambda: defaultdict(dict))
    response = lambda_function.lambda_handler(event, {})

    assert response == mock_validate_payload()


@patch("json.load", return_value="mock-filter-groups")
@patch("builtins.open", new_callable=mock_open, read_data="mock_open")
@pytest.mark.parametrize(
    "validate_sig,validate_payload",
    [
        pytest.param(lambda_function.ClientException("error"), None),
        pytest.param(None, lambda_function.ClientException("error")),
    ],
)
def test_error_lambda_handler(
    mock_open_file, mock_json_load, validate_sig, validate_payload
):
    """Ensure that lambda_handler() raises the expected exception when function fails"""
    patch("lambda_function.validate_sig", return_value=validate_sig)
    patch("lambda_function.validate_payload", return_value=validate_payload)

    event = defaultdict(lambda: "")

    with pytest.raises(lambda_function.LambdaException):
        lambda_function.lambda_handler(event, {})
