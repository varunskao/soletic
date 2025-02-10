import json
import time
import os
import click
from pathlib import Path
from dotenv import load_dotenv
from functools import wraps
from soletic.main import SolanaProgramAnalyzer
from click.core import ParameterSource
from typing import Dict


# Add a feature where configurations can be stored in a json file for use. In docker container, make sure this is referenced in the mount.
# DEFAULT_CONFIG_FILE = os.path.expanduser("~/.soletic_config.json")
# DEFAULT_LOG_FILE_PATH = os.path.expanduser("~/.soletic_logs/soletic.log")


def load_config():
    """Load configuration from a file."""
    config_file = os.getenv("SOLETIC_CONFIG_FILE_PATH")
    config_path = os.path.join(os.path.expanduser("~"), config_file)
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            return json.load(f)
    return {}


def save_config(config):
    """Save configuration to a file."""
    config_file = os.getenv("SOLETIC_CONFIG_FILE_PATH")
    config_path = os.path.join(os.path.expanduser("~"), config_file)
    with open(config_path, "w") as f:
        json.dump(config, f, indent=4)
    click.echo(f"\nConfiguration saved to {config_path}\n")


def get_cache_file():
    """Get cache file path from environment variable or default location"""
    cache_dir = os.getenv('SOLETIC_CACHE_DIR', os.path.expanduser("~/.soletic_cache"))
    Path(cache_dir).mkdir(parents=True, exist_ok=True)
    return Path(cache_dir) / 'soletic_cache.json'


def _is_api_key_defined():
    if not os.getenv("HELIUS_API_KEY"):
        click.echo("HELIUS_API_KEY not found. Please define HELIUS_API_KEY in your .env file.", err=True)
        return False
    return True


def require_config(func):
    """A custom decorator to ensure configuration is loaded into methods and API_KEY exists"""
    @click.pass_context
    @wraps(func)
    def wrapper(ctx, *args, **kwargs):
        if not ctx.obj:
            ctx.obj = load_config()

        if not _is_api_key_defined():
            ctx.exit(1)

        return ctx.invoke(func, *args, **kwargs)
    return wrapper


def ensure_log_directory(log_file: str | Path) -> bool:
    """
    Ensure the log directory exists and is writable.
    
    Args:
        log_file: Path to the log file
    
    Returns:
        bool: True if directory is ready for logging, False otherwise
        
    Raises:
        ValueError: If log_file is empty or None
        PermissionError: If unable to create/access directory
    """
    try:
        # Convert to Path object for better path handling
        log_file_path = os.path.join(os.path.expanduser("~"), log_file)
        log_path = Path(log_file_path)
        log_dir = log_path.parent

        # Create directory if it doesn't exist
        if not log_dir.exists():
            log_dir.mkdir(parents=True, exist_ok=True)
            
        # Verify directory is writable by attempting to write test file
        test_file = log_dir / '.write_test'
        try:
            test_file.touch()
            test_file.unlink()
        except OSError as e:
            return False
        
        return True
        
    except PermissionError as e:
        raise PermissionError(f"Permission denied creating log directory: {e}")
    except OSError as e:
        raise OSError(f"Failed to create log directory: {e}")


def create_cache_if_not_exists():
    """Set up cache directory and environment variable"""
    default_cache_dir = os.path.expanduser("~/.soletic_cache")
    
    # Create cache directory if it doesn't exist
    Path(default_cache_dir).mkdir(parents=True, exist_ok=True)
    
    # Set environment variable
    os.environ['SOLETIC_CACHE_DIR'] = default_cache_dir
    
    # Create an empty cache file if it doesn't exist
    cache_file = Path(default_cache_dir) / 'soletic_cache.json'
    if not cache_file.exists():
        with open(cache_file, 'w') as f:
            json.dump({}, f)
    
    return default_cache_dir


@click.group(context_settings=dict(help_option_names=["-h", "--help"]))
@click.pass_context
def cli(ctx):
    """
    soletic: A CLI tool for querying the Solana blockchain.

    Use this tool to query the Solana blockchain for when a contract was first deployed.
    Run the 'soletic setup' command to configure your preferences.
    """
    ctx.ensure_object(dict)
    try:
        ctx.obj = load_config()
    except FileNotFoundError:
        ctx.obj = {}  # Start with empty config if none exists


def _is_valid_config(config: Dict[str, str]):
    network_valid = config.get("network") in ["mainnet", "devnet"]
    cache_valid = isinstance(config.get("cache"), bool)
    return network_valid and cache_valid


# TODO: If the configuration file does not have specific values defined, we need to make sure to handle that scenario
@cli.command()
@click.option('-n', '--network', default=None, help='The choice of network: "mainnet" or "devnet".')
@click.option('--use-cache', default=True, help='Enable/disable cache.')
@click.option('--log-file', default=None, help='Override the default log file path.')
def setup(network, use_cache, log_file):
    """
    Set up soletic with network and other preferences.

    Setup will abide by the following priority: configuration file, command-line options, prompted respones.
    """
    if not _is_api_key_defined():
        return

    config = load_config()
    valid_config = _is_valid_config(config)
    
    if config and valid_config:
        click.echo("Existing configuration found:")
        for key, value in config.items():
            click.echo(f"  {key}: {value}")
        if not click.confirm("Would you like to update your configuration?", default=False):
            click.echo("Using existing configuration.")
            return

    # Prompt for new values, using existing values as defaults if available.
    if not network:
        network = click.prompt(
            "Which network do you want to use?", 
            type=click.Choice(["mainnet", "devnet"], case_sensitive=False),
            show_choices=True
        )

    # Ensure log directory exists if log file is specified
    log_file = log_file if log_file else os.getenv("DEFAULT_SOLETIC_LOG_FILE_PATH")
    ensure_log_directory(log_file)

    if use_cache:
        cache_dir = create_cache_if_not_exists()
        click.echo(f"\nCache directory initialized at {cache_dir}")

    # Update config dictionary.
    config.update({
        'network': network,
        'cache': use_cache,
        'log_file': log_file
    })

    click.echo("Configuration created:")
    for key, value in config.items():
        click.echo(f"  {key}: {value}")

    save_config(config)
    click.echo("Setup complete.\n")


@cli.command()
@require_config
@click.option('-n', '--network', default=None, type=click.Choice(['mainnet', 'devnet'], case_sensitive=False), help='The choice of network: "mainnet" or "devnet".')
@click.option('--use-cache', default=None, help='Disable cache.')
@click.option('--log-file', default=None, help='Update the file to which logs are written.')
@click.pass_context
def update(ctx, network, use_cache, log_file):
    """
    Set up soletic with network and other preferences.

    Setup will abide by the following priority: configuration file, command-line options, prompted respones.
    """

    if not ctx.obj:
        click.echo("Must run `soletic setup` before `soletic update` to configure the tool.")
        return

    params_to_check = ['network', 'use_cache', 'log_file']
    
    # Check if any of these were provided on the command line.
    if not any(ctx.get_parameter_source(name) != ParameterSource.DEFAULT for name in params_to_check):
        click.echo("Nothing was updated; no parameters were passed.")
        return

    config = ctx.obj 

    # Ensure log directory exists if log file is specified
    if log_file:
        ensure_log_directory(log_file)

    # Update config dictionary.
    config.update({
        'network': network if network else config.get("network"),
        'cache': use_cache if use_cache else config.get("cache"),
        'log_file': log_file if log_file else config.get("log_file")
    })

    save_config(config)

    click.echo("\nConfiguration updated to:")
    for key, value in config.items():
        click.echo(f"  {key}: {value}")
    click.echo("\n")


@cli.command(name="get-deployment-time")
@require_config
@click.option('-n', '--network', default=None ,help='Override the configuration setting, if required: "mainnet" or "devnet".')
@click.option('-v', '--verbose', is_flag=True, default=False, help='Enable verbose logging.')
@click.option('-d', '--debug', is_flag=True, default=False, help='Enable debug logging.')
@click.option('--ignore-cache', is_flag=True, default=False, help='Override cache setting.')
@click.option('-f', '--format', default="unix", help='Default format is unix time. Options are: "unix" or "datetime".')
@click.argument('program_address', type=str)
@click.pass_context
def getProgramDeploymentTime(ctx, program_address, network, verbose, debug, ignore_cache, format):
    """
    Retrieve the deployment date for a given Solana contract (program).

    program_address is the unique identifier for the program.
    """
    if not ctx.obj:
        click.echo("Must run `soletic setup` before `soletic commands` to configure the tool.")
        return

    network = network if network else ctx.obj["network"]
    cache = (not ignore_cache) if ignore_cache else ctx.obj["cache"]

    spa = SolanaProgramAnalyzer(log_file=ctx.obj["log_file"], verbose=verbose, debug=debug)
    response_or_err = spa.get_deployment_timestamp(program_address=program_address, network=network, use_cache=cache)
    if isinstance(response_or_err, int):
        if format == "unix": 
            click.echo(response_or_err)
        if format == "datetime":
            click.echo(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(response_or_err)))
    else:
        click.echo(response_or_err)


@cli.command(name="clear-cache")
def clear_cache():
    """Clear the Soletic cache directory containing a map of program address to deployment time"""
    try:
        cache_file = get_cache_file()
        if cache_file.exists():
            with open(cache_file, 'w') as f:
                json.dump({}, f)
            click.echo("Cache cleared successfully.")
        else:
            click.echo("No cache file found.")
    except Exception as e:
        click.echo(f"Error clearing cache: {e}")


@cli.command(name="list-config")
def list_config():
    """Show the stored configuration file"""
    config = load_config()
    if not config:
        click.echo("No configuration defined, please run `soletic setup`.")
    for setting, value in config.items():
        click.echo(f"   {setting}: {value}")


@cli.command(name="list-settings")
@require_config
@click.pass_context
def list_settings(ctx):
    """Show the directories of soletic related directories"""
    config = ctx.obj if ctx.obj else load_config()
    if not config:
        click.echo("No configuration defined, please run `soletic setup`.")
    else:
        click.echo(f"CLI config exists in {os.getenv('SOLETIC_CONFIG_FILE_PATH')}")
        if config.get("log_file"):
            click.echo(f"Log files exists in {ctx.obj.get("log_file")}")
        else:
            click.echo(f"Log files exists in {os.getenv('DEFAULT_SOLETIC_LOG_FILE_PATH')}")


@cli.command(name="del-config")
@require_config
@click.pass_context
def delete_config(ctx):
    """Delete the configuration file."""
    config_file = os.getenv("SOLETIC_CONFIG_FILE_PATH")
    config_path = os.path.join(os.path.expanduser("~"), config_file)
    
    try:
        if os.path.exists(config_path):
            os.remove(config_path)
            click.echo(f"Configuration file deleted successfully.")
        else:
            click.echo(f"Configuration file not found.")
    except OSError as e:
        click.echo(f"Error deleting configuration file: {e}", err=True)
        ctx.exit(1)


if __name__ == '__main__':
    load_dotenv()
    cli(obj={})