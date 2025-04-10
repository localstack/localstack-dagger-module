#!/bin/bash

# Check if LOCALSTACK_AUTH_TOKEN is set
if [ -z "$LOCALSTACK_AUTH_TOKEN" ]; then
    echo "Error: LOCALSTACK_AUTH_TOKEN environment variable is not set"
    echo "Please set your LocalStack Pro auth token:"
    echo "export LOCALSTACK_AUTH_TOKEN='your-token-here'"
    exit 1
fi

# Create a new ephemeral instance
echo "Creating new ephemeral instance 'my-temp-instance'..."
dagger -m github.com/localstack/localstack-dagger-module \
    call ephemeral \
    --auth-token=env:LOCALSTACK_AUTH_TOKEN \
    --operation=create \
    --name=my-temp-instance \
    --lifetime=60

# Wait for instance to be ready
echo "Waiting for instance to be ready..."
sleep 15

# List all active ephemeral instances
echo "Listing all active ephemeral instances..."
dagger -m github.com/localstack/localstack-dagger-module \
    call ephemeral \
    --auth-token=env:LOCALSTACK_AUTH_TOKEN \
    --operation=list

# Get logs for our instance
echo "Getting logs for 'my-temp-instance'..."
dagger -m github.com/localstack/localstack-dagger-module \
    call ephemeral \
    --auth-token=env:LOCALSTACK_AUTH_TOKEN \
    --operation=logs \
    --name=my-temp-instance

# Delete the instance
echo "Deleting 'my-temp-instance'..."
dagger -m github.com/localstack/localstack-dagger-module \
    call ephemeral \
    --auth-token=env:LOCALSTACK_AUTH_TOKEN \
    --operation=delete \
    --name=my-temp-instance

echo "Ephemeral instance operations completed!"
