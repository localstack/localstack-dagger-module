import dagger
from dagger import dag, function, object_type
import requests
import boto3
import time
import json


@object_type
class Examples:
    @function
    async def localstack_dagger_module__quickstart(self) -> str:
        """Example showing how to start LocalStack Community edition."""
        # Start LocalStack using the module
        service = dag.localstack_dagger_module().start()
        
        await service.start()
        endpoint = await service.endpoint()

        # Create a test bucket
        s3 = boto3.client(
            's3',
            endpoint_url=f"http://{endpoint}",
            aws_access_key_id='test',
            aws_secret_access_key='test',
            region_name='us-east-1'
        )
        s3.create_bucket(Bucket='test-bucket')

        print("S3 bucket created")

        # Create a test object
        s3.put_object(
            Bucket='test-bucket',
            Key='test.txt',
            Body='Hello LocalStack'
        )

        print("S3 object created")
        
        # Get the object
        response = s3.get_object(Bucket='test-bucket', Key='test.txt')
        content = response['Body'].read().decode('utf-8')

        print(f"S3 object content: {content}")

        return f"Success: LocalStack Community edition is running at {endpoint}"

    @function
    async def localstack_dagger_module__pro(self, auth_token: dagger.Secret) -> str:
        """Example showing how to start LocalStack Pro with custom configuration."""
        # Start LocalStack Pro using the module
        service = dag.localstack_dagger_module().start(
            auth_token=auth_token,
            configuration="DEBUG=1,SERVICES=ecr",
            docker_sock="/var/run/docker.sock"
        )
        
        await service.start()
        endpoint = await service.endpoint()

        # Create a test ECR repository
        ecr = boto3.client(
            'ecr',
            endpoint_url=f"http://{endpoint}",
            aws_access_key_id='test',
            aws_secret_access_key='test',
            region_name='us-east-1'
        )
        ecr.create_repository(RepositoryName='test-repo')

        print("ECR repository created")

        return f"Success: LocalStack Pro is running at {endpoint}"

    @function
    async def localstack_dagger_module_state(self, auth_token: dagger.Secret) -> str:
        """Example showing how to manage LocalStack state using Cloud Pods."""
        # Start LocalStack Pro
        service = dag.localstack_dagger_module().start(auth_token=auth_token)
        await service.start()
        endpoint = await service.endpoint()

        try:
            # Create a test bucket
            s3 = boto3.client(
                's3',
                endpoint_url=f"http://{endpoint}",
                aws_access_key_id='test',
                aws_secret_access_key='test',
                region_name='us-east-1'
            )
            s3.create_bucket(Bucket='test-bucket')

            # Save state to Cloud Pod
            await dag.localstack_dagger_module().state(
                auth_token=auth_token,
                save="test-pod",
                endpoint=f"http://{endpoint}"
            )

            # Reset state
            await dag.localstack_dagger_module().state(
                reset=True,
                endpoint=f"http://{endpoint}"
            )

            # Load state back
            await dag.localstack_dagger_module().state(
                auth_token=auth_token,
                load="test-pod",
                endpoint=f"http://{endpoint}"
            )

            return "Success: State operations completed"
        except Exception as e:
            return f"Error: {str(e)}"

    @function
    async def localstack_dagger_module_ephemeral(self, auth_token: dagger.Secret) -> str:
        """Example showing how to manage LocalStack Ephemeral Instances."""
        try:
            # Create a new ephemeral instance
            await dag.localstack_dagger_module().ephemeral(
                auth_token=auth_token,
                operation="create",
                name="test-instance",
                lifetime=60,
                auto_load_pod="test-pod"
            )
            
            # Wait for instance to be ready
            time.sleep(15)
            
            # List instances
            list_response = await dag.localstack_dagger_module().ephemeral(
                auth_token=auth_token,
                operation="list"
            )
            
            # Get instance logs
            await dag.localstack_dagger_module().ephemeral(
                auth_token=auth_token,
                operation="logs",
                name="test-instance"
            )
            
            # Delete instance
            await dag.localstack_dagger_module().ephemeral(
                auth_token=auth_token,
                operation="delete",
                name="test-instance"
            )
            
            return "Success: Ephemeral instance operations completed"
        except Exception as e:
            return f"Error: {str(e)}"
