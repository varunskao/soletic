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

## Configuration
Before running queries, `soletic` requires an initial setup:
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

### Example
Let's try and query for the deployment time of the Radium Concentrated Liquidity program: 
```bash
soletic get-deployment-time CAMMCzo5YL8w4VFF8KVHrK22GGUsp5VTaW7grrKgrWqK
# Console Output:
#
# 1660709269 
```
By default, the `get-deployment-time` call will return a timestamp in the developer friendly [unix](https://unixtime.org/) standard, but for those who want to see a human readable date and time, you can pass the `--format datetime` flag or `-f datetime`.

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