import os
import dagger
from dagger import dag, function, object_type
from typing import Optional
import base64


@object_type
class LocalstackDaggerModule:
    @function
    def serve(
        self, 
        auth_token: Optional[str] = None,
        configuration: Optional[str] = None,
        docker_sock: Optional[dagger.Socket] = None,
        image_name: Optional[str] = None
    ) -> dagger.Service:
        """Start a LocalStack service with appropriate configuration.
        
        If image_name is provided, starts that specific image.
        If auth_token is provided but no image_name, starts LocalStack Pro edition.
        Otherwise starts LocalStack Community edition.
        
        Args:
            auth_token: Optional LocalStack auth token for Pro edition
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
            container = container.with_env_variable("LOCALSTACK_AUTH_TOKEN", auth_token)
            
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
    def state(
        self,
        auth_token: str,
        load: Optional[str] = None
    ) -> str:
        """Load a LocalStack Cloud Pod state into a running LocalStack instance.
        
        Args:
            auth_token: LocalStack auth token (required)
            load: Name of the Cloud Pod to load
            
        Returns:
            Output from the pod load command or error message if LocalStack is not running
        """
        # Calculate state secret
        state_secret = base64.b64encode(auth_token.encode("utf-8")).decode("utf-8")
        
        # Create a minimal container just for making HTTP requests
        container = (
            dag.container()
            .from_("curlimages/curl:latest")
        )
            
        # Check if LocalStack is running
        try:
            health_check = container.with_exec(
                ["curl", "-s", "-f", "http://host.docker.internal:4566/_localstack/info"]
            )
            health_check.sync()
        except:
            return "Error: LocalStack is not running. Please start it first using the serve function."
            
        # Execute the pod load request if a pod name is provided
        if load:
            load_cmd = container.with_exec([
                "curl", "-s", "-f",
                "-X", "PUT",
                f"http://host.docker.internal:4566/_localstack/pods/{load}",
                "-H", "Content-Type: application/json",
                "-H", f"x-localstack-state-secret: {state_secret}",
                "-d", "{}"
            ])
            try:
                return load_cmd.stdout()
            except:
                return f"Error: Failed to load pod '{load}'. Please check the pod name and your auth token."
            
        return "No pod name provided to load"
