# soletic

`soletic` is a command-line tool that implements custom queries against the Solana blockchain. It allows users to retrieve the timestamp of when a Solana program was deployed for the first time. Demand for further functionalities can be submitted in the [Issues](https://github.com/varunskao/soletic/issues) github tab for this repository.

## Features
- Retrieve the timestamp of a Solana program's first deployment.
- Configure API key, network (mainnet, testnet, etc.), and verbosity level.
- Standard help documentation and man page for reference.
- Ability to run as a standalone Python package or within a Docker container.
- Supports unit testing for verification during development.
- Direct on-chain data access via Solana RPC endpoints (no third-party APIs).

## Installation
### Option 1: Clone and Use
```bash
# Clone the repository
git clone https://github.com/yourrepo/soletic.git
cd soletic

# Install dependencies
pip install -r requirements.txt

# Run the CLI
python soletic.py --help
```

### Option 2: Install via PyPI (Self-Hosted)
If you have a self-hosted PyPI instance, you can publish `soletic` and install it via:
```bash
pip install --index-url https://your-pypi-instance.com/simple/ soletic
```

### Option 3: Docker
Build and run `soletic` using Docker:
```bash
# Build the Docker image
docker build -t soletic .

# Run the container
docker run --rm soletic --help
```

## Configuration
Before running queries, `soletic` requires an initial setup:
```bash
soletic configure
```
This will prompt you to set:
- **API Key** (for RPC endpoint authentication)
- **Network** (e.g., mainnet, testnet, devnet)
- **Verbosity Level** (debug, info, warning, error)

## Usage
Retrieve the first deployment timestamp of a Solana program:
```bash
soletic query --program-id <PROGRAM_ID>
```

### Example
```bash
soletic query --program-id 3nL9Z9Pt3E5ZsiXz8z7MxEy7Q3X5wzDDyU9pD5KU3fAw
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