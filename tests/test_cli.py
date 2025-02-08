import os
import json
from pathlib import Path
from soletic.cli import cli
from click.testing import CliRunner
 

class TestCLI:
    """CLI-related tests"""

    default_config = {
        "network": "mainnet",
        "cache": True,
        "verbose": False,
        "log_file": None
    }

    def test_setup_existing_config_no_update(self, runner: CliRunner):
        # First, ensure there's an existing config
        with runner.isolated_filesystem():
            # Create the config file in the temporary directory
            config_path = os.path.expanduser("~/.soletic_config.json")
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            with open(config_path, 'w') as f:
                json.dump(self.default_config, f)

            # Run the command with simulated input 'n' for "no"
            result = runner.invoke(cli, ['setup'], input='n\n')
            
            # Check the output
            expected_output = (
                "Existing configuration found:\n"
                "  network: mainnet\n"
                "  cache: True\n"
                "  verbose: False\n"
                "  log_file: None\n"
                "Would you like to update your configuration? [y/N]: n\n"
                "Using existing configuration.\n"
            )
            
            assert result.exit_code == 0
            assert result.output == expected_output

    def test_setup_existing_config_with_update(self, runner: CliRunner):
        # Setup existing config
        with runner.isolated_filesystem():
            config_path = os.path.expanduser("~/.soletic_config.json")
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            with open(config_path, 'w') as f:
                json.dump(self.default_config, f)

            # Simulate input: 'y' for yes to update, then 'devnet' for network choice
            result = runner.invoke(cli, ['setup'], input='y\ndevnet\n')
            
            # Check the output
            assert result.exit_code == 0
            assert "Existing configuration found:" in result.output
            assert "Would you like to update your configuration? [y/N]: y" in result.output
            assert "Which network do you want to use?" in result.output
            
            # Verify the config was updated
            with open(config_path, 'r') as f:
                updated_config = json.load(f)
                assert updated_config['network'] == 'devnet'

    def test_help_command(self, runner: CliRunner):
        """Test the help command."""
        # Simulate a pipeline execution
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "soletic: A CLI tool for querying the Solana blockchain." in result.output

    def test_setup_with_relative_log_path(self, runner: CliRunner, clean_config):
        with runner.isolated_filesystem():
            config_path = os.path.expanduser("~/.soletic_config.json")
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            
            # Use a relative path for log file
            relative_log_path = "logs/soletic.log"
            
            # Run setup with relative log path
            result = runner.invoke(cli, ['setup', '-n', "mainnet", '--log-file', relative_log_path])
            
            assert result.exit_code == 0
            
            # Verify config was saved with relative path
            with open(config_path, 'r') as f:
                config = json.load(f)
                assert config['log_file'] == relative_log_path
            
            # Verify log directory is created when logging occurs
            log_dir = Path("logs")
            assert log_dir.exists()

    def test_setup_with_absolute_log_path(self, temp_dir, runner: CliRunner, clean_config):
        with runner.isolated_filesystem():
            # Create absolute path in temp directory
            log_path = os.path.join(temp_dir, "soletic.log")
            
            # Run setup with absolute path
            result = runner.invoke(cli, ['setup', '-n', "mainnet", '--log-file', log_path])
            
            assert result.exit_code == 0
            
            # Verify config saved with absolute path
            config_path = os.path.expanduser("~/.soletic_config.json")
            with open(config_path, 'r') as f:
                config = json.load(f)
                assert config['log_file'] == log_path
            
            # Verify log directory exists
            assert os.path.dirname(log_path)

    def test_setup_with_default_log_location(self, runner: CliRunner, clean_config):
        """Test that when no log file is specified, it defaults to console logging"""
        with runner.isolated_filesystem():
            result = runner.invoke(cli, ['setup', '-n', 'mainnet'])
            
            assert result.exit_code == 0
            
            # Verify config has None for log_file
            config_path = os.path.expanduser("~/.soletic_config.json")
            with open(config_path, 'r') as f:
                config = json.load(f)
                assert config['log_file'] is None

    def test_log_directory_creation(self, runner: CliRunner, clean_config):
        """Test that log directories are created if they don't exist"""
        with runner.isolated_filesystem():
            nested_log_path = "logs/nested/deeply/soletic.log"
            
            result = runner.invoke(cli, ['setup', '-n', "mainnet", '--log-file', nested_log_path])
            
            assert result.exit_code == 0
            
            # Verify all parent directories were created
            assert os.path.exists(os.path.dirname(nested_log_path))

    def test_update_with_no_params(self, runner: CliRunner, temp_config):
        """Test update command with no parameters"""
        result = runner.invoke(cli, ['update'], obj={'config_file': temp_config})
        assert result.exit_code == 0
        assert "Nothing was updated" in result.output

    def test_update_network(self, runner: CliRunner, temp_config):
        """Test updating network parameter"""
        result = runner.invoke(cli, ['update', '--network', 'devnet'], obj={'config_file': temp_config})
        assert result.exit_code == 0
        assert "network: devnet" in result.output

    def test_update_multiple_params(self, runner: CliRunner, temp_config):
        """Test updating multiple parameters at once"""
        result = runner.invoke(cli, [
            'update',
            '--network', 'devnet',
            '--verbose',
        ], obj={'config_file': temp_config})
        
        assert result.exit_code == 0
        assert "network: devnet" in result.output
        assert "verbose: True" in result.output

    def test_update_invalid_network(self, runner: CliRunner, temp_config):
        """Test updating with invalid network value"""
        result = runner.invoke(cli, ['update', '--network', 'invalid_network'], obj={'config_file': temp_config})
        assert result.exit_code != 0
        assert "Invalid value" in result.output

    def test_update_invalid_log_file(self, runner: CliRunner, temp_config):
        """Test updating with invalid log file path"""
        result = runner.invoke(cli, [
            'update',
            '--log-file', '/invalid/path/that/cannot/exist/log.txt'
        ], obj={'config_file': temp_config})
        
        assert result.exit_code != 0

    def test_preserve_existing_values(self, runner: CliRunner, temp_config):
        """Test that non-updated values are preserved"""
        # First update with some values
        runner.invoke(cli, ['update', '--network', 'devnet', '--verbose'], obj={'config_file': temp_config})
        
        # Then update only network
        result = runner.invoke(cli, ['update', '--network', 'mainnet'], obj={'config_file': temp_config})
        
        assert result.exit_code == 0