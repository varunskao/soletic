import json
import os
import pytest
import time
from unittest import mock
from click.testing import CliRunner
from cli import cli, save_config, load_config
from soletic.get_program_deployment_time import get_deployment_timestamp, get_n_earliest_signatures
from solders.rpc.responses import RpcConfirmedTransactionStatusWithSignature
from solders.transaction_status import TransactionConfirmationStatus
from solders.signature import Signature
 

# ---------------- TEST LOGIC ----------------
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


# ------------ ADDRESS FORMATTING TESTS ------------
def test_incorrect_program_address_format(mock_context):
    valid_address = "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
    too_short = valid_address[:-1]
    too_long = valid_address + "T"
    invalid_symbol = too_short + "$"
    invalid_addresses = [too_short, too_long, invalid_symbol]
    for invalid_address in invalid_addresses:
        err_msg = get_deployment_timestamp(mock_context, invalid_address)
        assert f"400 | Program address: {invalid_address}, is invalid because" in err_msg

def test_program_address_non_existent(mock_context):
    undeployed_address = "TestProgramN684nSsdXS5soBFyWVdM6Lx1jc9YQTWS"
    closed_program_data_address = "9RAUg4mfowhSUaL7NEJa9zVr3BgZsTVmCvhdqJfSGKfe"
    non_existent_addresses = [undeployed_address, closed_program_data_address]
    for non_existent_address in non_existent_addresses:
        err_msg = get_deployment_timestamp(mock_context, non_existent_address)
        expected_err_code = 400
        expected_err_msg = f"{expected_err_code} | '{non_existent_address}' does not exist. Please provide a valid program address."
        assert expected_err_msg == err_msg

def test_program_address_not_executable(mock_context):
    wallet_address = "9u9iZBWqGsp5hXBxkVZtBTuLSGNAG9gEQLgpuVw39ASg"
    err_msg = get_deployment_timestamp(mock_context, wallet_address)
    expected_err_code = 400
    expected_err_msg = f"{expected_err_code} | '{wallet_address}' is not a program account. Please provide a valid program address."
    assert expected_err_msg == err_msg


# ------------ CODE FUNCTIONALITY TESTS ------------
def test_valid_but_closed_program_address(mock_context):
    valid_but_closed_program_address = "zzMQL1oYoGeM4q8GbPNvWsPJ8RsCYB2bBxX3zfTxBTH"
    response = get_deployment_timestamp(mock_context, valid_but_closed_program_address)
    assert response == 1738186488

def test_valid_program_address(mock_context):
    valid_and_open_program_address = "JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4"
    response = get_deployment_timestamp(mock_context, valid_and_open_program_address)
    assert response == 1688482876

def test_most_active_program_address(mock_context):
    """
    Using the Solscan Program Leaderboard (https://solscan.io/leaderboard/program), we can evaluate the tool against 
    highly active addresses.
    # NOTE: Ideally we would programmatically pull these to keep the most active list up to date
    """
    most_active_addresses = {
        "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8": 1616309902, # Raydium Liquidity Pool V4
        "SoLFiHG9TfgtdUXUjWAxi3LtvYuFyDLVhBWxdMZxyCe": 1728334480, # SolFi
        "whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc": 1646818456, # Whirlpools Program
        "LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo": 1699333378, # Meteora DLMM Program
        "CAMMCzo5YL8w4VFF8KVHrK22GGUsp5VTaW7grrKgrWqK": 1660709269, # Radium Concentrated Liquidity
    }
    for address, expected_deployment_time in most_active_addresses.items():
        deployment_time = get_deployment_timestamp(mock_context, address)
        assert deployment_time == expected_deployment_time


# ------------ CODE PERFORMANCE TESTS ------------
def test_round_trip(mock_context):
    valid_and_open_program_address = "JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4"

    start_time = time.time()
    deployment_time = get_deployment_timestamp(mock_context, valid_and_open_program_address)
    end_time = time.time()
    
    execution_time = end_time - start_time
    print(f"execution_time: {execution_time}")
    
    assert execution_time < 1
    assert deployment_time == 1688482876


# ------------ CLI TESTS ------------
@mock.patch("soletic.load_config", return_value={"network": "mainnet", "verbose": True})
def test_cli_setup(mock_context, runner):
    result = runner.invoke(cli, ["setup", "--network", "mainnet", "--verbose"])
    assert "Setup complete." in result.output
    
@mock.patch("soletic.load_config", return_value={"network": "mainnet", "verbose": True})
def test_cli_getProgramDeploymentDate(mock_context, runner):
    valid_and_open_program_address = "JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4"
    result = runner.invoke(cli, ["getProgramDeploymentDate", valid_and_open_program_address])
    assert 1688482876 in result.output