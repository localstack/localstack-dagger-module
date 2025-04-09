import dagger
from dagger import dag, function, object_type
import requests
import boto3
import time
import io


@object_type
class Tests:
    @function
    async def all(self, auth_token: dagger.Secret) -> str:
        """Run all tests"""
        await self.test_localstack_health()
        await self.test_localstack_pro(auth_token=auth_token)
        await self.test_state_operations(auth_token=auth_token)

    @function
    async def test_localstack_health(self) -> str:
        """Test if LocalStack starts and responds to /_localstack/info endpoint"""
        # Start LocalStack using the module
        service = dag.localstack_dagger_module().serve()
        
        await service.start()
        endpoint = await service.endpoint()

        try:
            response = requests.get(f"http://{endpoint}/_localstack/info")
            response.raise_for_status()

            info = response.json()
            if "version" in info:
                return f"Success: LocalStack is healthy"
            else:
                raise Exception("LocalStack info endpoint missing version field")
        except Exception as e:
            raise Exception(f"Test failed: {str(e)}")
        except requests.RequestException as e:
            raise Exception(f"Failed to connect to LocalStack: {str(e)}")
        except ValueError as e:
            raise Exception(f"Invalid JSON response from LocalStack: {str(e)}")

    @function
    async def test_localstack_pro(self, auth_token: dagger.Secret) -> str:
        """Test if LocalStack starts with Pro services available"""
        # Start LocalStack Pro using the module
        service = dag.localstack_dagger_module().serve(auth_token=auth_token)
        
        await service.start()
        endpoint = await service.endpoint()

        try:
            # Check health endpoint for LocalStack
            response = requests.get(f"http://{endpoint}/_localstack/health")
            response.raise_for_status()

            health_info = response.json()
            services = health_info.get("services", {})
            
            # Check if ECS (a Pro service) exists and is running
            if "ecs" in services:
                return "Success: LocalStack is running with Pro services"
            else:
                raise Exception("Pro services are not available")
        except Exception as e:
            raise Exception(f"Test failed: {str(e)}")
        except requests.RequestException as e:
            raise Exception(f"Failed to connect to LocalStack: {str(e)}")
        except ValueError as e:
            raise Exception(f"Invalid JSON response from LocalStack: {str(e)}")

    @function
    async def test_state_operations(self, auth_token: dagger.Secret) -> str:
        """Test LocalStack state operations (save/load/reset) with AWS resources"""
        # Start LocalStack Pro
        service = dag.localstack_dagger_module().serve(auth_token=auth_token)
        await service.start()
        endpoint = await service.endpoint()

        # Configure boto3 client
        s3 = boto3.client(
            's3',
            endpoint_url=f"http://{endpoint}",
            aws_access_key_id='test',
            aws_secret_access_key='test',
            region_name='us-east-1'
        )

        try:
            # Create a test bucket
            s3.create_bucket(Bucket='test-bucket')

            # Create test object
            test_data = "Hello LocalStack"
            s3.put_object(
                Bucket='test-bucket',
                Key='test.txt',
                Body=test_data
            )

            # Save state to Cloud Pod
            state_module = dag.localstack_dagger_module()
            await state_module.state(
                auth_token=auth_token,
                save="test-dagger-pod",
                endpoint=f"http://{endpoint}"
            )

            # Reset state
            await state_module.state(reset=True, endpoint=f"http://{endpoint}")

            time.sleep(5)

            # Verify bucket is gone
            try:
                s3.head_bucket(Bucket='test-bucket')
                raise Exception("State reset failed: bucket still exists")
            except s3.exceptions.ClientError:
                # Expected - bucket should not exist
                pass

            # Load state back
            await state_module.state(
                auth_token=auth_token,
                load="test-dagger-pod",
                endpoint=f"http://{endpoint}"
            )

            # Wait briefly for state to be loaded
            time.sleep(5)

            # Verify bucket exists
            s3.head_bucket(Bucket='test-bucket')

            # Verify object content
            response = s3.get_object(Bucket='test-bucket', Key='test.txt')
            content = response['Body'].read().decode('utf-8')

            if content != "Hello LocalStack":
                raise Exception(f"State load failed: object content mismatch. Expected 'Hello LocalStack', got '{content}'")

            return "Success: State save/load/reset operations working correctly"

        except Exception as e:
            return f"Test failed: {str(e)}"
