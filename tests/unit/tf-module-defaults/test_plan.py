import pytest
import logging
import os
import boto3
import uuid

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

tf_dirs = [
    f"{os.path.dirname(__file__)}/fixtures/create_api",
    f"{os.path.dirname(__file__)}/fixtures/load_api",
    f"{os.path.dirname(__file__)}/fixtures/disable_api_cw_logs",
]


@pytest.mark.parametrize("tf", tf_dirs, indirect=True)
@pytest.mark.parametrize("terraform_version", ["latest"], indirect=True)
def test_plan(tf, terraform_version):
    log.debug(f"Terraform plan:\n{tf.plan()}")


@pytest.fixture
def dummy_ssm_key():
    """Creates dummy AWS SSM Parameter Store value"""
    ssm = boto3.client("ssm")
    name = f"test-param-{uuid.uuid4()}"

    ssm.put_parameter(Name=name, Value="bar", Type="String")

    yield name

    ssm.delete_parameter(Name=name)


@pytest.mark.parametrize(
    "tf", [f"{os.path.dirname(__file__)}/fixtures/load_gh_ssm_param"], indirect=True
)
@pytest.mark.parametrize("terraform_version", ["latest"], indirect=True)
def test_load_gh_ssm_param_plan(tf, terraform_version, dummy_ssm_key):
    """Test case where pre-existing and to be created AWS SSM parameters are passed"""
    log.debug(f"Terraform plan:\n{tf.plan(tf_vars={'dummy_ssm_key': dummy_ssm_key})}")
