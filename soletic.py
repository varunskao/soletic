#!/usr/bin/env python3
import json
import os
import click
from datetime import datetime
# from typing import Dict
from dotenv import load_dotenv


# Add a feature where configurations can be stored in a json file for use. In docker container, make sure this is referenced in the mount.
CONFIG_FILE = os.path.expanduser("~/.soletic_config.json")
load_dotenv()


def load_config():
    """Load configuration from a file."""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {}


def save_config(config):
    """Save configuration to a file."""
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)
    click.echo(f"Configuration saved to {CONFIG_FILE}")


def require_config(func):
    """
    A custom decorator to ensure configuration is loaded into methods and API_KEY exists
    """
    @click.pass_context
    def wrapper(ctx, *args, **kwargs):
        # Load config once at the group level if not already present.
        if not ctx.obj:
            ctx.obj = load_config()

        # Check for API_KEY in the environment and add it to the config.
        if not os.getenv("API_KEY"):
            click.echo("HELIUS_API_KEY not found in environment. Please define HELIUS_API_KEY in your .env file.", err=True)
            ctx.exit(1)

        return ctx.invoke(func, *args, **kwargs)
    return wrapper


@click.group(context_settings=dict(help_option_names=["-h", "--help"]))
@click.pass_context
def cli(ctx):
    """
    soletic: A CLI tool for querying the Solana blockchain.

    Use this tool to query the Solana blockchain for when a contract was first deployed.
    Use the 'setup' command to configure your API key and preferences.
    """
    if ctx.obj is None:
        ctx.obj = load_config()


# @cli.command()
# @click.option('--network', default="mainnet" ,help='Your API key for accessing the Solana node.')
# @click.option('--cache/--no-cache', default=None, help='Whether to use a cache for improved performance.')
# @click.option('--verbose/--no-verbose', default=None, help='Enable verbose logging.')
# @click.option('--log-file', help='Path to the log file.')
# def setup(api_key, cache, verbose, log_file):

@cli.command()
@require_config
@click.option('--force', is_flag=True, help="Force updating the configuration without prompting.")
@click.pass_context
def setup(ctx, force):
    """
    Set up soletic with network and other preferences.

    Setup will abide by the following priority: configuration file, command-line options, prompted respones.
    """
    config = ctx.obj 

    if not os.getenv("HELIUS_API_KEY"):
        click.echo("No API_KEY found in .env file. Please define your api_key in a .env file in the root directory of the project as HELIUS_API_KEY=<YOUR_API_KEY>", err=True)
        return
    
    if config and not force:
        click.echo("Existing configuration found:")
        for key, value in config.items():
            click.echo(f"  {key}: {value}")
        if not click.confirm("Would you like to update your configuration?", default=False):
            click.echo("Using existing configuration.")
            return

    # Prompt for new values, using existing values as defaults if available.
    network = click.prompt(
        "Which network do you want to use?", 
        type=click.Choice(["mainnet", "devnet"], case_sensitive=False),
        show_choices=True
    )
    cache = click.confirm("Use cache for improved performance?", default=config.get('cache', True))
    verbose = click.confirm("Enable verbose logging?", default=config.get('verbose', False))
    log_file = click.prompt("Enter a log file path (or leave blank for console logging)", default=config.get('log_file', ''), show_default=True)

    # Update config dictionary.
    config.update({
        'network': network,
        'cache': cache,
        'verbose': verbose,
        'log_file': log_file.strip() or None
    })

    save_config(config)
    click.echo("Setup complete.")


@cli.command()
@require_config
@click.argument('program_id', type=str)
@click.pass_context
def getProgramDeploymentDate(ctx, program_id):
    """
    Retrieve the deployment date for a given Solana contract (program).

    PROGRAM_ID is the unique identifier for the program.
    """
    # Enable verbose logging if configured
    verbose = ctx.obj.get("verbose", False)
    if verbose:
        click.echo(f"Querying deployment date for program ID: {program_id}")

    # ----------------------------------------------------------
    # Replace the code below with the actual logic. I've just simulated an API call by returning the current time as the "deployment date"
    simulated_deployment_date = datetime.now().isoformat()
    # ----------------------------------------------------------

    click.echo(f"Program {program_id} was deployed on: {simulated_deployment_date}")


if __name__ == '__main__':
    cli()