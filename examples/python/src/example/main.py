import dagger
from dagger import dag, function, object_type
import boto3
import time

@object_type
class Example:
    @function
    async def localstack__quickstart(self) -> str:
        """Example showing how to start LocalStack Community edition."""
        service = dag.localstack().start()
        
        await service.start()
        endpoint = await service.endpoint()
        print(f"LocalStack is running at {endpoint}")

        # Create a test S3 bucket
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
            Key='test-object',
            Body='Hello, LocalStack!'
        )
        print("S3 object created")

        # Verify the object was created
        response = s3.get_object(Bucket='test-bucket', Key='test-object')
        content = response['Body'].read().decode('utf-8')
        print(f"S3 object content: {content}")

    @function
    async def localstack__pro(self, auth_token: dagger.Secret) -> str:
        """Example showing how to start LocalStack Pro with custom configuration."""
        # Start LocalStack Pro using the module
        service = dag.localstack().start(
            auth_token=auth_token,
            configuration="DEBUG=1,SERVICES=ecr"
        )

        await service.start()
        endpoint = await service.endpoint()
        print(f"LocalStack Pro is running at {endpoint}")

        # Create a test ECR repository
        ecr = boto3.client(
            'ecr',
            endpoint_url=f"http://{endpoint}",
            aws_access_key_id='test',
            aws_secret_access_key='test',
            region_name='us-east-1'
        )

        repository_name = "test-ecr-repo"
        ecr.create_repository(repositoryName=repository_name)
        print(f"ECR repository '{repository_name}' created")

    @function
    async def localstack__state(self, auth_token: dagger.Secret) -> str:
        """Example showing how to manage LocalStack state using Cloud Pods."""
        service = dag.localstack().start(auth_token=auth_token)
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
            await dag.localstack().state(
                auth_token=auth_token,
                save="test-dagger-example-pod",
                endpoint=f"http://{endpoint}"
            )

            # Reset state
            await dag.localstack().state(
                reset=True,
                endpoint=f"http://{endpoint}"
            )

            # Load state back
            await dag.localstack().state(
                auth_token=auth_token,
                load="test-dagger-example-pod",
                endpoint=f"http://{endpoint}"
            )

            return "Success: State operations completed"
        except Exception as e:
            return f"Error: {str(e)}"

    @function
    async def localstack_ephemeral(self, auth_token: dagger.Secret) -> str:
        """Example showing how to manage LocalStack Ephemeral Instances."""
        try:
            # Create a new ephemeral instance
            await dag.localstack().ephemeral(
                auth_token=auth_token,
                operation="create",
                name="test-dagger-example-instance",
                lifetime=60,
            )
            
            # Wait for instance to be ready
            time.sleep(15)

            print("Instance created")
            
            # List instances
            list_response = await dag.localstack().ephemeral(
                auth_token=auth_token,
                operation="list"
            )

            print(f"Ephemeral instances: {list_response}")
            
            # Get instance logs
            instance_logs = await dag.localstack().ephemeral(
                auth_token=auth_token,
                operation="logs",
                name="test-dagger-example-instance"
            )

            print(f"Instance logs: {instance_logs}")
            
            # Delete instance
            await dag.localstack().ephemeral(
                auth_token=auth_token,
                operation="delete",
                name="test-dagger-example-instance"
            )

            print("Instance deleted")
            
            return "Success: Ephemeral instance operations completed"
        except Exception as e:
            return f"Error: {str(e)}"
