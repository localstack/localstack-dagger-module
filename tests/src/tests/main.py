import dagger
from dagger import dag, function, object_type
import requests


@object_type
class Tests:
    @function
    async def all(self, auth_token: dagger.Secret) -> str:
        """Run all tests"""
        await self.test_localstack_health()
        await self.test_localstack_pro(auth_token=auth_token)

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
