#!/usr/bin/env python3
import json
import time
import os
import click
# from typing import Dict
from dotenv import load_dotenv
from solders.pubkey import Pubkey

from soletic.get_program_deployment_time import get_deployment_timestamp
# from dataclasses import dataclass


# Add a feature where configurations can be stored in a json file for use. In docker container, make sure this is referenced in the mount.
CONFIG_FILE = os.path.expanduser("~/.soletic_config.json")
load_dotenv()


# TODO: Potentially create context objects as required
# @dataclass
# class Context:
#     network: str
#     cache: bool
#     verbose: bool
#     log_file: str


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


# TODO: If the configuration file does not have specific values defined, we need to make sure to handle that scenario
@cli.command()
@require_config
@click.option('--force', is_flag=True, help="Force updating the configuration without prompting.")
@click.option('--network', default=None ,help='The choice of network: "mainnet" or "devnet".')
@click.option('--cache/--no-cache', default=None, help='Whether to use a cache for improved performance.')
@click.option('--verbose/--no-verbose', default=None, help='Enable verbose logging.')
@click.option('--log-file', help='Path to the log file.')
@click.pass_context
def setup(ctx, force, network, cache, verbose, log_file):
    """
    Set up soletic with network and other preferences.

    Setup will abide by the following priority: configuration file, command-line options, prompted respones.
    """
    config = ctx.obj 
    
    if config and not force:
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
            type=click.Choice(["mainnet", "devnet", "testnet"], case_sensitive=False),
            show_choices=True
        )
    if not cache:
        cache = click.confirm("Use cache for improved performance?", default=config.get('cache', True))
    if not verbose:
        verbose = click.confirm("Enable verbose logging?", default=config.get('verbose', False))
    # TODO: I'm not sure if we need to specify this for the user, let's just default to console logging and allow them to pass in a flag if required
    if not log_file:
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
def getProgramDeploymentDate(ctx, program_address):
    """
    Retrieve the deployment date for a given Solana contract (program).

    PROGRAM_ID is the unique identifier for the program.
    """
    # Enable verbose logging if configured
    verbose = ctx.obj.get("verbose", False)
    if verbose:
        click.echo(f"Querying deployment date for program ID: {program_address}")

    deployment_timestamp = get_deployment_timestamp(ctx.obj, program_address, num_transactions=50)
    if deployment_timestamp:
        formatted_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(deployment_timestamp))
        click.echo(f"Program {program_address} was deployed on: {formatted_time} (Unix time: {deployment_timestamp}).")
    else:
        click.echo(f"Could not determine the deployment timestamp for Program {program_address}.")


if __name__ == '__main__':
    cli()