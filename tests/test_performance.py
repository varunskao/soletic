import pytest
import time
from soletic.main import SolanaProgramAnalyzer
from click.testing import CliRunner
from soletic.cli import cli


class TestPerformance:
    """Performance-related tests"""

    spa = SolanaProgramAnalyzer(".soletic_logs/soletic.log", verbose=False, debug=False)

    @pytest.mark.requires_api
    def test_first_round_trip(self, mock_context, runner: CliRunner):
        with runner.isolated_filesystem():
            # Clear the cache before testing the run
            runner.invoke(cli, ["clear-cache"])

            valid_and_open_program_address = (
                "JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4"
            )

            start_time = time.time()
            program_deployment_time = self.spa.get_deployment_timestamp(
                program_address=valid_and_open_program_address,
                network=mock_context.get("network"),
            )
            end_time = time.time()
            execution_time = end_time - start_time

            assert execution_time < 2
            assert program_deployment_time == 1688482876

    @pytest.mark.requires_api
    def test_susbequent_round_trips(self, mock_context, runner: CliRunner):
        with runner.isolated_filesystem():
            # Clear the cache before testing the run
            runner.invoke(cli, ["clear-cache"])

            valid_and_open_program_address = (
                "JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4"
            )

            start_time = time.time()
            program_deployment_time_first_attempt = self.spa.get_deployment_timestamp(
                program_address=valid_and_open_program_address,
                network=mock_context.get("network"),
            )
            end_time = time.time()
            first_attempt_execution_time = end_time - start_time

            start_time = time.time()
            program_deployment_time_second_attempt = self.spa.get_deployment_timestamp(
                program_address=valid_and_open_program_address,
                network=mock_context.get("network"),
            )
            end_time = time.time()
            second_attempt_execution_time = end_time - start_time

            assert first_attempt_execution_time < 2
            assert second_attempt_execution_time < 0.05
            assert 1688482876 in [
                program_deployment_time_first_attempt,
                program_deployment_time_second_attempt,
            ]
