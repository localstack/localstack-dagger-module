#!/bin/bash

# Start LocalStack Community edition
dagger -m github.com/localstack/localstack-dagger-module call start up

# Wait for LocalStack to be ready
echo "Waiting for LocalStack to be ready..."
sleep 5

# Test the deployment by checking LocalStack health
curl http://localhost:4566/_localstack/health

echo "LocalStack Community edition is now running!"
echo "Access your AWS services at: http://localhost:4566"
