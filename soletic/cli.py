import json
import time
import os
import click
from dotenv import load_dotenv
from functools import wraps
from soletic.main import get_deployment_timestamp
from click.core import ParameterSource


# Add a feature where configurations can be stored in a json file for use. In docker container, make sure this is referenced in the mount.
CONFIG_FILE = os.getenv(
    "SOLETIC_CONFIG_PATH",
    os.path.expanduser("~/.soletic_config.json")
)
load_dotenv()


def load_config():
    """Load configuration from a file."""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
            # return Context(**json.load(f))
    return {}


def save_config(config):
    """Save configuration to a file."""
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)
    click.echo(f"Configuration saved to {CONFIG_FILE}")


def require_config(func):
    """A custom decorator to ensure configuration is loaded into methods and API_KEY exists"""
    @click.pass_context
    @wraps(func)
    def wrapper(ctx, *args, **kwargs):
        if not ctx.obj:
            ctx.obj = load_config()

        # Check for API_KEY in the environment and add it to the config.
        if not os.getenv("HELIUS_API_KEY"):
            click.echo("HELIUS_API_KEY not found in environment. Please define HELIUS_API_KEY in your .env file.", err=True)
            ctx.exit(1)

        return ctx.invoke(func, *args, **kwargs)
    return wrapper

def ensure_log_directory(log_file):
    """Ensure the log directory exists"""
    if log_file:
        log_dir = os.path.dirname(log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)

@click.group(context_settings=dict(help_option_names=["-h", "--help"]))
@click.pass_context
def cli(ctx):
    """
    soletic: A CLI tool for querying the Solana blockchain.

    Use this tool to query the Solana blockchain for when a contract was first deployed.
    Use the 'setup' command to configure your API key and preferences.
    """
    ctx.ensure_object(dict)
    try:
        ctx.obj = load_config()
    except FileNotFoundError:
        ctx.obj = {}  # Start with empty config if none exists


# TODO: If the configuration file does not have specific values defined, we need to make sure to handle that scenario
@cli.command()
@require_config
@click.option('-n', '--network', default=None ,help='The choice of network: "mainnet" or "devnet".')
@click.option('--cache', default=True, help='Whether to use a cache for improved performance.')
@click.option('-v', '--verbose', default=False, help='Enable verbose logging.')
@click.option('--log-file', help='Path to the log file. Defaults to console logging if not specified.')
@click.pass_context
def setup(ctx, force, network, cache, verbose, log_file):
    """
    Set up soletic with network and other preferences.

    Setup will abide by the following priority: configuration file, command-line options, prompted respones.
    """
    config = ctx.obj 
    
    if config:
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
    if log_file:
        ensure_log_directory(log_file)

    # Update config dictionary.
    config.update({
        'network': network,
        'cache': cache,
        'verbose': verbose,
        'log_file': log_file
    })

    save_config(config)

    click.echo("Setup complete.")


@cli.command()
@require_config
@click.option('-n', '--network', default=None ,help='The choice of network: "mainnet" or "devnet".')
@click.option('--cache', default=True, help='Whether to use a cache for improved performance.')
@click.option('-v', '--verbose', default=False, help='Enable verbose logging.')
@click.option('--log-file', help='Path to the log file. Defaults to console logging if not specified.')
@click.pass_context
def update(ctx, network, cache, verbose, log_file):
    """
    Set up soletic with network and other preferences.

    Setup will abide by the following priority: configuration file, command-line options, prompted respones.
    """
    params_to_check = ['network', 'cache', 'verbose', 'log_file']
    
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
        'network': network if network else config.get("network", "mainnet"),
        'cache': cache if cache else config.get("cache", True),
        'verbose': verbose if verbose else config.get("verbose", False),
        'log_file': log_file if log_file else config.get("log_file", None)
    })

    save_config(config)

    click.echo("Configuration updated to:")
    for key, value in config.items():
        click.echo(f"  {key}: {value}")


@cli.command(name="get-deployment-time")
@require_config
@click.option('-n', '--network', default=None ,help='Override the configuration setting, if required: "mainnet" or "devnet".')
@click.option('-v', '--verbose', default=False, help='Override the configuration setting to enable verbose logging.')
@click.option('-f', '--format', default="unix", help='Default format is unix time. Options are: "unix" or "datetime".')
@click.argument('program_address', type=str)
@click.pass_context
def getProgramDeploymentDate(ctx, program_address, network, verbose, format):
    """
    Retrieve the deployment date for a given Solana contract (program).

    program_address is the unique identifier for the program.
    """
    # Enable verbose logging if configured
    if network: 
        ctx.obj.update({"network": network})
    if verbose: 
        ctx.obj.update({"verbose": verbose})

    response_or_err = get_deployment_timestamp(program_address, ctx.obj)
    if isinstance(response_or_err, int):
        if format == "unix": 
            click.echo(response_or_err)
        if format == "datetime":
            click.echo(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(response_or_err)))
    else:
        click.echo(response_or_err)


if __name__ == '__main__':
    cli(obj={})