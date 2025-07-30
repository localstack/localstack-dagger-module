import os
import dagger
from dagger import dag, function, object_type, Doc
from typing import Optional, Annotated
import base64
from datetime import datetime
import requests
import json


@object_type
class Localstack:
    """LocalStack service management functions."""

    @function
    def start(
        self, 
        auth_token: Annotated[Optional[dagger.Secret], Doc("LocalStack Pro Auth Token for authentication")] = None,
        configuration: Annotated[Optional[str], Doc("Configuration variables in format 'KEY1=value1,KEY2=value2'")] = None,
        docker_sock: Annotated[Optional[dagger.Socket], Doc("Docker socket for container interactions")] = None,
        image_name: Annotated[Optional[str], Doc("Custom LocalStack image name to use")] = None
    ) -> dagger.Service:
        """Start a LocalStack service with appropriate configuration."""
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
            
        # Add Auth Token if provided
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
        auth_token: Annotated[Optional[dagger.Secret], Doc("LocalStack Auth Token (required for save/load)")] = None,
        load: Annotated[Optional[str], Doc("Name of the Cloud Pod to load")] = None,
        save: Annotated[Optional[str], Doc("Name of the Cloud Pod to save")] = None,
        endpoint: Annotated[Optional[str], Doc("LocalStack endpoint (defaults to host.docker.internal:4566)")] = None,
        reset: Annotated[bool, Doc("Reset the LocalStack state")] = False
    ) -> str:
        """Load, save, or reset LocalStack state."""
        # Base URL for LocalStack API
        localstack_url = endpoint or "http://host.docker.internal:4566"
        
        # Check if LocalStack is running
        try:
            health_response = requests.get(f"{localstack_url}/_localstack/info")
            health_response.raise_for_status()
        except requests.RequestException:
            return "Error: LocalStack is not running. Please start it first using the start function."
            
        # Handle reset operation
        if reset:
            try:
                reset_response = requests.post(f"{localstack_url}/_localstack/state/reset")
                reset_response.raise_for_status()
                return "LocalStack state reset successfully."
            except requests.RequestException as e:
                return f"Error: Reset failed: {str(e)}"
            
        if (save or load) and not auth_token:
            return "Error: auth_token is required for save and load operations."
            
        if (save or load) and auth_token:
            # Use a separate container to calculate state secret to avoid exposing token
            state_secret_container = (
                dag.container()
                .from_("python:3.9-slim")
                .with_secret_variable("LOCALSTACK_AUTH_TOKEN", auth_token)
                .with_exec(["python", "-c", "import os,base64; print(base64.b64encode(os.environ['LOCALSTACK_AUTH_TOKEN'].encode()).decode())"])
            )
            state_secret = await state_secret_container.stdout()
            
            # Common headers
            headers = {
                "Content-Type": "application/json",
                "x-localstack-state-secret": state_secret.strip()
            }
            
            # Execute the pod operation based on the provided parameters
            if save:
                try:
                    save_response = requests.post(
                        f"{localstack_url}/_localstack/pods/{save}",
                        headers=headers,
                        json={}
                    )
                    save_response.raise_for_status()
                    return save_response.text
                except requests.RequestException:
                    return f"Error: Failed to save pod '{save}'. Please check the pod name and your Auth Token."
            elif load:
                try:
                    load_response = requests.put(
                        f"{localstack_url}/_localstack/pods/{load}",
                        headers=headers,
                        json={}
                    )
                    load_response.raise_for_status()
                    return load_response.text
                except requests.RequestException:
                    return f"Error: Failed to load pod '{load}'. Please check the pod name and your Auth Token."
            
        return "No operation specified. Please provide either --load, --save, or --reset parameter."

    @function
    async def ephemeral(
        self,
        auth_token: Annotated[dagger.Secret, Doc("LocalStack Auth Token (required)")],
        operation: Annotated[str, Doc("Operation to perform (create, list, delete, logs)")],
        name: Annotated[Optional[str], Doc("Name of the ephemeral instance (required for create, delete, logs)")] = None,
        lifetime: Annotated[Optional[int], Doc("Lifetime of the instance in minutes (default: 60)")] = None,
        auto_load_pod: Annotated[Optional[str], Doc("Auto load pod configuration")] = None,
        extension_auto_install: Annotated[Optional[str], Doc("Extension auto install configuration")] = None
    ) -> str:
        """Manage ephemeral LocalStack instances in the cloud."""
        if not auth_token:
            return "Error: auth_token is required for ephemeral instance operations"

        # Base API endpoint
        api_endpoint = "https://api.localstack.cloud/v1"
        
        # Get Auth Token value from secret
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
