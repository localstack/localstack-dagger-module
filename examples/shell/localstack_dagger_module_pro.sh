#!/bin/bash

# Check if LOCALSTACK_AUTH_TOKEN is set
if [ -z "$LOCALSTACK_AUTH_TOKEN" ]; then
    echo "Error: LOCALSTACK_AUTH_TOKEN environment variable is not set"
    echo "Please set your LocalStack Pro auth token:"
    echo "export LOCALSTACK_AUTH_TOKEN='your-token-here'"
    exit 1
fi

# Start LocalStack Pro with custom configuration
dagger -m github.com/localstack/localstack-dagger-module \
    call start \
    --auth-token=env:LOCALSTACK_AUTH_TOKEN \
    --configuration='DEBUG=1' \
    --docker-sock=/var/run/docker.sock \
    up

# Wait for LocalStack to be ready
echo "Waiting for LocalStack Pro to be ready..."
sleep 5

# Test the deployment by checking LocalStack health
curl http://localhost:4566/_localstack/health

echo "LocalStack Pro is now running!"
echo "Access your AWS services at: http://localhost:4566"
