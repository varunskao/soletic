from soletic.main import SolanaProgramAnalyzer
from click.testing import CliRunner
from soletic.cli import cli
import pytest


class TestCoreFunctionality:
    """Tests for core functionality to determine program deployment time"""

    most_active_addresses = {
        "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8": 1616309902, # Raydium Liquidity Pool V4
        "SoLFiHG9TfgtdUXUjWAxi3LtvYuFyDLVhBWxdMZxyCe": 1728334480, # SolFi
        "whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc": 1646818456, # Whirlpools Program
        "LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo": 1699333378, # Meteora DLMM Program
        "CAMMCzo5YL8w4VFF8KVHrK22GGUsp5VTaW7grrKgrWqK": 1660709269, # Radium Concentrated Liquidity
    }
    spa = SolanaProgramAnalyzer(".soletic_logs/soletic.log", verbose=False, debug=False)

    @pytest.mark.requires_api
    def test_valid_but_closed_program_address(self, mock_context, runner: CliRunner):
        runner.invoke(cli, args=["clear-cache"])
        valid_but_closed_program_address = "zzMQL1oYoGeM4q8GbPNvWsPJ8RsCYB2bBxX3zfTxBTH"
        response = self.spa.get_deployment_timestamp(program_address=valid_but_closed_program_address, network=mock_context.get("network"))
        assert response == 1738186488

    @pytest.mark.requires_api
    def test_valid_program_address(self, mock_context, runner: CliRunner):
        runner.invoke(cli, args=["clear-cache"])
        valid_and_open_program_address = "JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4"
        response = self.spa.get_deployment_timestamp(program_address=valid_and_open_program_address, network=mock_context.get("network"))
        assert response == 1688482876

    @pytest.mark.requires_api
    def test_most_active_program_address(self, mock_context, runner: CliRunner):
        """
        Using the Solscan Program Leaderboard (https://solscan.io/leaderboard/program), we can evaluate the tool against 
        highly active addresses.
        # NOTE: Ideally we would programmatically pull these to keep the most active list up to date
        """
        runner.invoke(cli, args=["clear-cache"])
        for address, expected_deployment_time in self.most_active_addresses.items():
            deployment_time = self.spa.get_deployment_timestamp(program_address=address, network=mock_context.get("network"))
            assert deployment_time == expected_deployment_time


@pytest.mark.requires_api
class TestAddressValidation:
    """Tests for validating program address format and existence"""

    spa = SolanaProgramAnalyzer(".soletic_logs/soletic.log", verbose=False, debug=False)

    @pytest.mark.requires_api
    def test_incorrect_program_address_format(self, mock_context):
        valid_address = "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
        invalid_addresses = [
            valid_address[:-1],  # too short
            valid_address + "T", # too long
            valid_address[:-1] + "$", # invalid symbol
        ]
        for invalid_address in invalid_addresses:
            err_msg = self.spa.get_deployment_timestamp(program_address=invalid_address, network=mock_context.get("network"))
            assert f"400 | Program address: {invalid_address}, is invalid because" in err_msg

    @pytest.mark.requires_api
    def test_program_address_non_existent(self, mock_context):
        non_existent_addresses = [
            "TestProgramN684nSsdXS5soBFyWVdM6Lx1jc9YQTWS", # undeployed address
            "9RAUg4mfowhSUaL7NEJa9zVr3BgZsTVmCvhdqJfSGKfe", # closed program data address 
        ]
        for non_existent_address in non_existent_addresses:
            err_msg = self.spa.get_deployment_timestamp(program_address=non_existent_address, network=mock_context.get("network"))
            expected_err_msg = f"400 | '{non_existent_address}' does not exist. Please provide a valid program address."
            assert expected_err_msg == err_msg

    @pytest.mark.requires_api
    def test_program_address_not_executable(self, mock_context):
        wallet_address = "9u9iZBWqGsp5hXBxkVZtBTuLSGNAG9gEQLgpuVw39ASg"
        err_msg = self.spa.get_deployment_timestamp(program_address=wallet_address, network=mock_context.get("network"))
        expected_err_msg = f"400 | '{wallet_address}' is not a program account. Please provide a valid program address."
        assert expected_err_msg == err_msg
