import dagger
from dagger import dag, function, object_type
import requests
import boto3
import time
import io
import json
import uuid


@object_type
class Tests:
    @function
    async def all(self, auth_token: dagger.Secret) -> str:
        """Run all tests"""
        await self.test_localstack_health()
        await self.test_localstack_pro(auth_token=auth_token)
        await self.test_state_operations(auth_token=auth_token)
        await self.test_ephemeral_operations(auth_token=auth_token)

    @function
    async def test_localstack_health(self) -> str:
        """Test if LocalStack starts and responds to /_localstack/info endpoint"""
        # Start LocalStack using the module
        service = dag.localstack().start()
        
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
        service = dag.localstack().start(auth_token=auth_token)
        
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
        service = dag.localstack().start(auth_token=auth_token)
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
            state_module = dag.localstack()
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

    @function
    async def test_ephemeral_operations(self, auth_token: dagger.Secret) -> str:
        """Test LocalStack ephemeral instance operations (create/list/logs/delete)"""
        # Generate a unique instance name for testing
        instance_name = f"test-instance-{uuid.uuid4().hex[:8]}"
        
        try:
            # Create an ephemeral instance
            ephemeral_module = dag.localstack()
            create_response = await ephemeral_module.ephemeral(
                auth_token=auth_token,
                operation="create",
                name=instance_name,
                lifetime=5  # Short lifetime for testing
            )

            # Wait for instance to be ready
            time.sleep(15)
            
            # Parse and verify create response
            create_data = json.loads(create_response)
            if not create_data.get("instance_name"):
                raise Exception("Failed to create ephemeral instance: no instance_name in response")
            
            # List instances and verify our instance exists
            list_response = await ephemeral_module.ephemeral(
                auth_token=auth_token,
                operation="list"
            )
            
            list_data = json.loads(list_response)
            instance_found = False
            for instance in list_data:
                if instance.get("instance_name") == instance_name:
                    instance_found = True
                    break
                    
            if not instance_found:
                raise Exception(f"Created instance {instance_name} not found in list response")
            
            # Get instance logs and verify they contain version information
            logs_response = await ephemeral_module.ephemeral(
                auth_token=auth_token,
                operation="logs",
                name=instance_name
            )
            
            if "version" not in logs_response.lower():
                raise Exception("Instance logs do not contain version information")
            
            # Delete the instance
            delete_response = await ephemeral_module.ephemeral(
                auth_token=auth_token,
                operation="delete",
                name=instance_name
            )
            
            if not delete_response.startswith("Successfully deleted"):
                raise Exception(f"Unexpected delete response: {delete_response}")
            
            return "Success: Ephemeral instance operations working correctly"
            
        except Exception as e:
            return f"Test failed: {str(e)}"
        finally:
            # Cleanup: Try to delete the instance if something went wrong
            try:
                await ephemeral_module.ephemeral(
                    auth_token=auth_token,
                    operation="delete",
                    name=instance_name
                )
            except:
                pass
