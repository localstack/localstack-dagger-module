import os
import dagger
from dagger import dag, function, object_type
from typing import Optional
import base64
from datetime import datetime
import requests
import json


@object_type
class LocalstackDaggerModule:
    @function
    def serve(
        self, 
        auth_token: Optional[dagger.Secret] = None,
        configuration: Optional[str] = None,
        docker_sock: Optional[dagger.Socket] = None,
        image_name: Optional[str] = None
    ) -> dagger.Service:
        """Start a LocalStack service with appropriate configuration.
        
        If image_name is provided, starts that specific image.
        If auth_token is provided but no image_name, starts LocalStack Pro edition.
        Otherwise starts LocalStack Community edition.
        
        Args:
            auth_token: Optional secret containing LocalStack Pro auth token
            configuration: Optional string of configuration variables in format "KEY1=value1,KEY2=value2"
                         Example: "DEBUG=1,LS_LOG=trace"
            docker_sock: Optional Docker socket for container interactions
            image_name: Optional custom LocalStack image name to use
            
        Returns:
            A running LocalStack service container
        """
        # Determine image based on parameters
        if image_name:
            image = image_name
        else:
            image = "localstack/localstack-pro:latest" if auth_token else "localstack/localstack:latest"
        
        # Start with base container config
        container = dag.container().from_(image)
        
        # Mount Docker socket if provided
        if docker_sock:
            container = container.with_unix_socket("/var/run/docker.sock", docker_sock)
            
        # Add auth token if provided
        if auth_token:
            container = container.with_secret_variable("LOCALSTACK_AUTH_TOKEN", auth_token)
            
        # Add configuration variables if provided
        if configuration:
            for config_pair in configuration.split(','):
                if '=' in config_pair:
                    key, value = config_pair.strip().split('=', 1)
                    container = container.with_env_variable(key, value)
            
        # Add common ports (4566)
        container = (
            container
            .with_exposed_port(4566)
        )
        
        # Add port 443 for Pro edition
        if auth_token:
            container = container.with_exposed_port(443)
            
        # Return as service
        return container.as_service()

    @function
    async def state(
        self,
        auth_token: Optional[dagger.Secret] = None,
        load: Optional[str] = None,
        save: Optional[str] = None,
        reset: bool = False
    ) -> str:
        """Load, save, or reset LocalStack state.
        
        Args:
            auth_token: Secret containing LocalStack auth token (required for save/load)
            load: Name of the Cloud Pod to load
            save: Name of the Cloud Pod to save
            reset: Reset the LocalStack state
            
        Returns:
            Output from the pod operation or error message if LocalStack is not running
        """
        # Create a minimal container for making HTTP requests
        container = (
            dag.container()
            .from_("curlimages/curl:latest")
        )
            
        # Check if LocalStack is running
        try:
            health_check = container.with_env_variable(
                # Dirty hack to avoid caching. Reference: https://docs.dagger.io/cookbook/#invalidate-cache
                "CACHEBUSTER", 
                str(datetime.now())
            ).with_exec(
                ["curl", "-s", "-f", "http://host.docker.internal:4566/_localstack/info"]
            )
            await health_check.sync()
        except:
            return "Error: LocalStack is not running. Please start it first using the serve function."
            
        # Handle reset operation
        if reset:
            try:
                status_code = await container.with_env_variable(
                    # Dirty hack to avoid caching. Reference: https://docs.dagger.io/cookbook/#invalidate-cache
                    "CACHEBUSTER", 
                    str(datetime.now())
                ).with_exec([
                    "curl", "-s", "-I",
                    "-X", "POST",
                    "http://host.docker.internal:4566/_localstack/state/reset"
                ]).stdout()
                
                if "200 OK" in status_code:
                    return "LocalStack state reset successfully."
                else:
                    return f"Error: Reset failed. Server response: {status_code}"
            except Exception as e:
                return f"Error: Reset failed: {str(e)}"
            
        if (save or load) and not auth_token:
            return "Error: auth_token is required for save and load operations."
            
        if (save or load) and auth_token:
            # Use a separate container to calculate state secret to avoid exposing token
            state_secret_container = (
                dag.container()
                .from_("python:3.9-slim")
                .with_secret_variable("AUTH_TOKEN", auth_token)
                .with_exec(["python", "-c", "import os,base64; print(base64.b64encode(os.environ['AUTH_TOKEN'].encode()).decode())"])
            )
            state_secret = await state_secret_container.stdout()
            
            # Add auth token to main container
            container = container.with_secret_variable("LOCALSTACK_AUTH_TOKEN", auth_token)
            
            # Execute the pod operation based on the provided parameters
            if save:
                try:
                    response = await container.with_env_variable(
                        # Dirty hack to avoid caching. Reference: https://docs.dagger.io/cookbook/#invalidate-cache
                        "CACHEBUSTER", 
                        str(datetime.now())
                    ).with_exec([
                        "curl", "-s", "-f",
                        "-X", "POST",
                        f"http://host.docker.internal:4566/_localstack/pods/{save}",
                        "-H", "Content-Type: application/json",
                        "-H", f"x-localstack-state-secret: {state_secret}",
                        "-d", "{}"
                    ]).stdout()
                    return response
                except:
                    return f"Error: Failed to save pod '{save}'. Please check the pod name and your auth token."
            elif load:
                try:
                    response = await container.with_env_variable(
                        # Dirty hack to avoid caching. Reference: https://docs.dagger.io/cookbook/#invalidate-cache
                        "CACHEBUSTER", 
                        str(datetime.now())
                    ).with_exec([
                        "curl", "-s", "-f",
                        "-X", "PUT",
                        f"http://host.docker.internal:4566/_localstack/pods/{load}",
                        "-H", "Content-Type: application/json",
                        "-H", f"x-localstack-state-secret: {state_secret}",
                        "-d", "{}"
                    ]).stdout()
                    return response
                except:
                    return f"Error: Failed to load pod '{load}'. Please check the pod name and your auth token."
            
        return "No operation specified. Please provide either --load, --save, or --reset parameter."

    @function
    async def ephemeral(
        self,
        auth_token: dagger.Secret,
        operation: str,
        name: Optional[str] = None,
        lifetime: Optional[int] = None,
        auto_load_pod: Optional[str] = None,
        extension_auto_install: Optional[str] = None
    ) -> str:
        """Manage ephemeral LocalStack instances in the cloud.
        
        Args:
            auth_token: LocalStack auth token (required)
            operation: Operation to perform (create, list, delete, logs)
            name: Name of the ephemeral instance (required for create, delete, logs)
            lifetime: Lifetime of the instance in minutes (optional, default: 60)
            auto_load_pod: Auto load pod configuration (optional)
            extension_auto_install: Extension auto install configuration (optional)
            
        Returns:
            Response from the API operation
        """
        if not auth_token:
            return "Error: auth_token is required for ephemeral instance operations"

        # Base API endpoint
        api_endpoint = "https://api.localstack.cloud/v1"
        
        # Get auth token value from secret
        auth_token_value = await auth_token.plaintext()
        
        # Common headers
        headers = {
            "content-type": "application/json",
            "ls-api-key": auth_token_value
        }

        if operation == "create":
            if not name:
                return "Error: name is required for create operation"
                
            # First check if instance exists
            try:
                list_response = requests.get(
                    f"{api_endpoint}/compute/instances",
                    headers=headers
                ).json()
                
                # Check if instance exists
                instance_exists = any(
                    instance.get("instance_name") == name 
                    for instance in list_response
                )
                
                if instance_exists:
                    # Delete existing instance
                    requests.delete(
                        f"{api_endpoint}/compute/instances/{name}",
                        headers=headers
                    )
            except Exception as e:
                pass
                
            data = {
                "instance_name": name,
                "lifetime": lifetime or 60,
            }
            
            # Only add env_vars if either auto_load_pod or extension_auto_install is provided
            if auto_load_pod or extension_auto_install:
                env_vars = {}
                if auto_load_pod:
                    env_vars["AUTO_LOAD_POD"] = auto_load_pod
                if extension_auto_install:
                    env_vars["EXTENSION_AUTO_INSTALL"] = extension_auto_install
                data["env_vars"] = env_vars
            
            try:
                response = requests.post(
                    f"{api_endpoint}/compute/instances",
                    headers=headers,
                    json=data
                ).json()

                return json.dumps(response, indent=2)
            except Exception as e:
                return f"Error: Failed to create ephemeral instance '{name}': {str(e)}"

        elif operation == "list":
            try:
                response = requests.get(
                    f"{api_endpoint}/compute/instances",
                    headers=headers
                ).json()
                return json.dumps(response, indent=2)
            except Exception as e:
                return f"Error: Failed to list ephemeral instances: {str(e)}"

        elif operation == "delete":
            if not name:
                return "Error: name is required for delete operation"
                
            try:
                requests.delete(
                    f"{api_endpoint}/compute/instances/{name}",
                    headers=headers
                )
                return f"Successfully deleted instance: {name}"
            except Exception as e:
                return f"Error: Failed to delete ephemeral instance '{name}': {str(e)}"

        elif operation == "logs":
            if not name:
                return "Error: name is required for logs operation"
                
            try:
                response = requests.get(
                    f"{api_endpoint}/compute/instances/{name}/logs",
                    headers=headers
                ).json()
                
                if not response:
                    return "No logs available for this instance."
                
                # Format logs with each line on a new line
                log_output = []
                for log_line in response:
                    content = log_line.get('content', '')
                    if content:
                        log_output.append(content)
                
                return "\n".join(log_output) if log_output else "No log content available."
            except Exception as e:
                return f"Error: Failed to fetch logs for instance '{name}': {str(e)}"

        else:
            return "Error: Invalid operation. Supported operations are: create, list, delete, logs"
