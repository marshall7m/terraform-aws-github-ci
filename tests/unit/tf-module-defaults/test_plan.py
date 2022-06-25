import pytest
import logging
import os

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
