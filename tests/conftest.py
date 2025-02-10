import os
import json
import pytest
from pathlib import Path
from _pytest.config import Config
from _pytest.fixtures import FixtureRequest
import tempfile
from click.testing import CliRunner


# ---------------- FIXTURES ----------------
@pytest.fixture
def mock_context():
    return {
        "network": "mainnet",
        "cache": True,
        "verbose": False,
        "log_file": ".soletic_logs/soletic.log",
        "debug": False,
    }


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
    if request.node.get_closest_marker("requires_api"):  # Check if test has the marker
        if not os.getenv("HELIUS_API_KEY"):
            pytest.skip("Skipping test that requires HELIUS_API_KEY")


@pytest.fixture
def temp_dir():
    """Create a temporary directory for log files"""
    with tempfile.TemporaryDirectory() as tmpdirname:
        yield tmpdirname


@pytest.fixture
def temp_config():
    # Create a temporary config file
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        json.dump(
            {"network": "mainnet", "cache": True, "verbose": False, "log_file": None}, f
        )
    yield Path(f.name)
    # Cleanup
    Path(f.name).unlink()


@pytest.fixture
def clean_config():
    """Remove the config file before and after tests"""
    config_path = os.path.expanduser("~/.soletic_config.json")

    # Delete before test if exists
    if os.path.exists(config_path):
        os.remove(config_path)

    yield  # Run the test

    # Clean up after test
    if os.path.exists(config_path):
        os.remove(config_path)
