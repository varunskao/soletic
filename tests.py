import json
import os
import pytest
# import requests
# from unittest import mock
from click.testing import CliRunner
# from soletic import cli, save_config, load_config
from getProgramDeploymentTime import (
    # get_signatures_for_address,
    # get_last_n_signatures,
    # get_transaction,
    # is_deployment_transaction,
    get_deployment_timestamp
)

@pytest.fixture
def mock_context():
    return {"network": "mainnet"}

@pytest.fixture
def runner():
    return CliRunner()

@pytest.fixture
def temp_config_file():
    config = {"network": "mainnet", "cache": True, "verbose": False, "log_file": ""}
    with open(".soletic_config.json", "w") as f:
        json.dump(config, f)
    yield 
    os.remove(".soletic_config.json")

# ------------ PROGRAM ADDRESS TESTS ------------
def test_incorrect_program_address_format(mock_context):
    valid_address = "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
    too_short = valid_address[:-1]
    too_long = valid_address + "T"
    invalid_symbol = too_short + "$"
    invalid_addresses = [too_short, too_long, invalid_symbol]
    for invalid_address in invalid_addresses:
        err_msg = get_deployment_timestamp(mock_context, invalid_address)
        assert f"Program address: {invalid_address} is invalid because" in err_msg

def test_program_address_non_existent(mock_context):
    undeployed_address = "TestProgramN684nSsdXS5soBFyWVdM6Lx1jc9YQTWS"
    err_msg = get_deployment_timestamp(mock_context, undeployed_address)
    expected_err_msg = f"Address: {undeployed_address}, does not exist. Please provide a valid program address."
    assert expected_err_msg == err_msg

def test_program_address_not_executable(mock_context):
    undeployed_address = "TestProgramN684nSsdXS5soBFyWVdM6Lx1jc9YQTWS"
    err_msg = get_deployment_timestamp(mock_context, undeployed_address)
    expected_err_msg = f"Address: {undeployed_address}, has not been deployed. Please provide a valid program address."
    assert expected_err_msg == err_msg

def test_valid_program_address(mock_context):
    token_address = "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
    response = get_deployment_timestamp(mock_context, token_address)
    # TODO: Get the valid response
    assert True

test_program_address = "zzMQL1oYoGeM4q8GbPNvWsPJ8RsCYB2bBxX3zfTxBTH"

# @mock.patch("requests.post")
# def test_get_signatures_for_address(mock_post, mock_context):
#     mock_post.return_value.json.return_value = {"result": [{"signature": "sig1"}]}
#     result = get_signatures_for_address(mock_context, "dummy_address", limit=1)
#     assert result == [{"signature": "sig1"}]

# @mock.patch("requests.post")
# def test_get_last_n_signatures(mock_post, mock_context):
#     mock_post.return_value.json.return_value = {"result": [{"signature": "sig1"}, {"signature": "sig2"}]}
#     result = get_last_n_signatures(mock_context, "dummy_address", n=2)
#     assert result == [{"signature": "sig2"}, {"signature": "sig1"}]  # Should be reversed

# @mock.patch("requests.post")
# def test_get_transaction(mock_post, mock_context):
#     mock_post.return_value.json.return_value = {"result": {"transaction": "data"}}
#     result = get_transaction(mock_context, "sig1")
#     assert result == {"transaction": "data"}

# @mock.patch("requests.post")
# def test_get_deployment_timestamp(mock_post, mock_context):
#     mock_post.return_value.json.return_value = {"result": 1672531200}  # Unix timestamp
#     result = get_deployment_timestamp(mock_context, "dummy_address", num_transactions=1)
#     assert result == 1672531200

# @mock.patch("requests.post")
# def test_is_deployment_transaction(mock_post):
#     transaction = {
#         "transaction": {
#             "message": {
#                 "instructions": [{"program": "BPFLoaderUpgradeab1e11111111111111111111111", "accounts": ["dummy_address"]}]
#             }
#         }
#     }
#     assert is_deployment_transaction(transaction, "dummy_address") is True

# @mock.patch("soletic.load_config", return_value={"network": "mainnet", "verbose": True})
# def test_cli_setup(mock_config, runner):
#     result = runner.invoke(cli, ["setup", "--network", "devnet", "--verbose"])
#     assert "Setup complete." in result.output
    
# @mock.patch("soletic.load_config", return_value={"network": "mainnet", "verbose": True})
# def test_cli_getProgramDeploymentDate(mock_config, runner):
#     result = runner.invoke(cli, ["getProgramDeploymentDate", "dummy_address"])
#     assert "Querying deployment date for program ID" in result.output