#!/bin/bash

export AWS_ACCESS_KEY_ID=test
export AWS_SECRET_ACCESS_KEY=test
export AWS_REGION=us-east-1

# Check if LOCALSTACK_AUTH_TOKEN is set
if [ -z "$LOCALSTACK_AUTH_TOKEN" ]; then
    echo "Error: LOCALSTACK_AUTH_TOKEN environment variable is not set"
    echo "Please set your LocalStack Pro auth token:"
    echo "export LOCALSTACK_AUTH_TOKEN='your-token-here'"
    exit 1
fi

# Start LocalStack Pro
dagger -m github.com/localstack/localstack-dagger-module \
    call start \
    --auth-token=env:LOCALSTACK_AUTH_TOKEN \
    up

echo "Waiting for LocalStack to be ready..."
sleep 5

# Create a test S3 bucket using AWS CLI
aws --endpoint-url=http://localhost:4566 s3 mb s3://my-test-bucket

# Save the current state to a Cloud Pod
echo "Saving current state to Cloud Pod 'my-test-pod'..."
dagger -m github.com/localstack/localstack-dagger-module \
    call state \
    --auth-token=env:LOCALSTACK_AUTH_TOKEN \
    --save=my-test-pod

# Reset the state (this will remove all resources)
echo "Resetting LocalStack state..."
dagger -m github.com/localstack/localstack-dagger-module \
    call state \
    --reset

# Verify the bucket is gone
if ! aws --endpoint-url=http://localhost:4566 s3 ls s3://my-test-bucket 2>/dev/null; then
    echo "State reset successful - bucket no longer exists"
fi

# Load the saved state back
echo "Loading state from Cloud Pod 'my-test-pod'..."
dagger -m github.com/localstack/localstack-dagger-module \
    call state \
    --auth-token=env:LOCALSTACK_AUTH_TOKEN \
    --load=my-test-pod

# Verify the bucket is back
if aws --endpoint-url=http://localhost:4566 s3 ls s3://my-test-bucket 2>/dev/null; then
    echo "State restored successfully - bucket exists again"
fi
