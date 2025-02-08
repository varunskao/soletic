import os
import json
import pytest
from _pytest.config import Config
from _pytest.fixtures import FixtureRequest
import tempfile
from click.testing import CliRunner 


# ---------------- FIXTURES ----------------
@pytest.fixture
def mock_context():
    return {"network": "mainnet"}

@pytest.fixture
def runner():
    return CliRunner()

# Define the custom marker
def pytest_configure(config: Config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "requires_api: mark test as requiring an API key"
    )

# Create a fixture that checks for tests with this marker
@pytest.fixture(autouse=True)
def check_api_key(request: FixtureRequest):
    """Skip marked tests if API key is not present"""
    if request.node.get_closest_marker('requires_api'):  # Check if test has the marker
        if not os.getenv("HELIUS_API_KEY"):
            pytest.skip("Skipping test that requires HELIUS_API_KEY")

@pytest.fixture
def temp_dir():
    """Create a temporary directory for log files"""
    with tempfile.TemporaryDirectory() as tmpdirname:
        yield tmpdirname