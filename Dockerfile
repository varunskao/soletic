# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set environment variables
ENV SOLETIC_CONFIG_FILE_PATH=.soletic_config.json \
    DEFAULT_SOLETIC_LOG_FILE_PATH=.soletic_logs/soletic.log \
    SOLETIC_CACHE_DIR=.soletic_cache

# Install git and any necessary build dependencies
RUN apt-get update && \
    apt-get install -y git && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set working directory in the container
WORKDIR /app

# Clone the repository
RUN git clone https://github.com/varunskao/soletic.git .

# Create necessary directories
RUN mkdir -p .soletic_logs .soletic_cache

# Install the package
RUN pip install --no-cache-dir .

ENTRYPOINT ["soletic"]