import pytest
import time
from soletic.main import get_deployment_timestamp

# ------------ CODE PERFORMANCE TESTS ------------
class TestPerformance:
    """Performance-related tests"""

    @pytest.mark.requires_api
    @pytest.mark.asyncio
    async def test_round_trip(self, mock_context):
        valid_and_open_program_address = "JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4"

        start_time = time.time()
        program_deployment_time = await get_deployment_timestamp(mock_context, valid_and_open_program_address)
        end_time = time.time()
        
        execution_time = end_time - start_time
        print(f"execution_time: {execution_time}")
        
        assert execution_time < 1
        assert program_deployment_time == 1688482876