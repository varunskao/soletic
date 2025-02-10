# soletic

`soletic`, a portmanteau between [solana](https://solana.com/es) and [kinetic](https://kinetic.xyz/) (a leading Solana DEX Aggregator), is a command-line tool that implements custom queries against the Solana blockchain. It allows users to retrieve the timestamp of when a Solana program was deployed for the first time. Demand for further functionalities can be submitted in the [Issues](https://github.com/varunskao/soletic/issues) github tab for this repository.

## Features
- Retrieve the timestamp of a Solana program's first deployment.
- Support for [Helius](https://www.helius.dev/) RPC Provider.
- Support for mainnet and devnet.
- Standard help documentation for reference.
- Ability to run as a standalone Python package or within a Docker container.
- Supports unit testing for verification during development.
- Direct on-chain data access via Solana RPC endpoints (no third-party APIs).

## Installation
### Option 1: Clone and Use
```bash
# Clone the repository
git clone https://github.com/varunskao/soletic.git
cd soletic

# Install dependencies
pip install -e .

# Run the CLI
soletic --help
```

### Option 2: Install via PyPI (Self-Hosted)
If you have a self-hosted PyPI instance, you can publish `soletic` and install it via:
```bash
pip install --index-url https://your-pypi-instance.com/simple/ soletic
```

### Option 3: Docker
Build and run `soletic` using Docker. 
```bash
# Build the Docker image
docker build -t soletic .

# Run the container
docker run -d -e HELIUS_API_KEY=<YOUR_HELIUS_API_KEY> soletic
```
_Note: for the docker container to make the right calls, you must either pass in your `HELIUS_API_KEY` into the `docker run` command or you must update the docker file and add your api key when setting the env variables._ 

## Configuration
Before running queries, `soletic` requires an initial setup: (___Note: you must add a `HELIUS_API_KEY` to a .env file in order for the tool to work ___)
```bash
soletic setup
```
This will prompt you to set the **network** (e.g., mainnet or devnet). By default, this simple setup process sets up a cache to make future calls to the same address more performant and writes logs to a log file for debugging. The cache lives in `~/.soletic_cache/` and the logs in `~/.soletic_logs/soletic.log`

### Setup
The setup process can also be configured using the various flags available:
```bash
--network (-n). # Options are mainnet or -n devnet
--use-cache # Defaults to True. # Eg: --use-cache False
--log-file. # Defaults to `~/.soletic_logs/soletic.log` # Eg: --log-file "/my_specific_log_dir/log_file.log"

# ---- Example 1 ----
soletic setup -n mainnet
# Console Output:
#
# Cache directory initialized at /home/varunkao/.soletic_cache
# Configuration created:
#   network: mainnet
#   cache: True
#   log_file: .soletic_logs/soletic.log
# 
# Configuration saved to /home/varunkao/.soletic_config.json
# 
# Setup complete.


# ---- Example 2 ----
soletic setup -n mainnet --use-cache False
# Console Output:
#
# Cache directory initialized at /home/user/.soletic_cache
# Configuration created:
#   network: mainnet
#   cache: False
#   log_file: .soletic_logs/soletic.log
# 
# Configuration saved to /home/user/.soletic_config.json
# 
# Setup complete.
```

### Update
Once the `soletic` tool is setup, if you want to modify the configuration, use `soletic update`:
```bash
soletic update
```
You can use this to modify the network to connect to, the use of the cache, and the destination of log files for all susbequent calls of the `soletic`. Here is an example of how to use it:

```bash
soletic update --network devnet
# Console Output:
#
# Configuration saved to /home/user/.soletic_config.json

# Configuration updated to:
#   network: devnet 
#   cache: True
#   log_file: .soletic_logs/soletic.log

soletic update --use-cache False
soletic update --log-file "test_log.log"
```

## Usage
Retrieve the first deployment timestamp of a Solana program:
```bash
soletic get-deployment-time <PROGRAM_ADDRESS>
```
There are a few flags that can be passed for flexibility:
1. `--format datetime` (or `-f`) - converts the timestamp from the [unix](https://unixtime.org/) standard to a human readable date and time.
2. `--network mainnet` (or `-n`) - a way to override the configuration defined network.
3. `--verbose` (or `-v`) - a glimpse under the hood of the logic to understand the flow.
3. `--debug` (or `-d`) - More detailed logs - helpful to debug errors.
4. `--ignore-cache` - Use this flag to bypass the cache if the tool has been configured to use it

### Basic Example
Let's try and query for the deployment time of the Radium Concentrated Liquidity (`CAMMCzo5YL8w4VFF8KVHrK22GGUsp5VTaW7grrKgrWqK`) program: 
```bash
soletic get-deployment-time CAMMCzo5YL8w4VFF8KVHrK22GGUsp5VTaW7grrKgrWqK
# Console Output:
#
# 1660709269 
```

### Formatting Example
```bash
soletic get-deployment-time CAMMCzo5YL8w4VFF8KVHrK22GGUsp5VTaW7grrKgrWqK -f datetime
# Console Output:
#
# '2022-08-17 00:07:49' 
```

### Verbose Example
```bash
soletic get-deployment-time CAMMCzo5YL8w4VFF8KVHrK22GGUsp5VTaW7grrKgrWqK -v
# Console Output:
#
# LOGIC - get_deployment_timestamp | Start Logic
# LOGIC - get_last_n_signatures | Start
# 1660709269
```

## Tool Helpers
There are a few other CLI calls to help work with the package

1. Clear cache directory:
```bash
soletic clear-cache
# Console Output:
#
# Cache cleared successfully.
```
_Note: once a block reaches finality, the likelyhood of the deployment time changing is very low, which is why we would never recommend clearing the cache. In fact, building a database with these values is recommended_

2. Delete current config:
```bash
soletic del-config
# Console Output:
#
# Configuration file deleted successfully.
```

3. View the current configuration settings:
```bash
soletic list-config 
# Console Output:
#
#   network: mainnet
#   cache: True
#   log_file: .soletic_logs/soletic.log
```

4. View the related directories the tool uses:
```bash
soletic list-settings
# Console Output:
#
# CLI config exists in .soletic_config.json
# Log files exists in .soletic_logs/soletic.log
```


### Help Documentation
Access help docs via:
```bash
soletic --help
```
Or refer to the manual page:
```bash
man soletic
```

## Development & Testing
To run unit tests:
```bash
pytest tests/
```
For development mode:
```bash
pip install -e .
```

## Contributions
Contributions are welcome! Please submit a pull request or open an issue if you find bugs or have feature suggestions.

## License
This project is licensed under the MIT License.