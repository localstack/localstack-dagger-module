import os
import dagger
from dagger import dag, function, object_type
from typing import Optional


@object_type
class LocalstackDaggerModule:
    @function
    def serve(
        self, 
        auth_token: Optional[str] = None,
        configuration: Optional[str] = None,
        docker_sock: Optional[dagger.Socket] = None
    ) -> dagger.Service:
        """Start a LocalStack service with appropriate configuration.
        
        If auth_token is provided, starts LocalStack Pro edition.
        Otherwise starts LocalStack Community edition.
        
        Args:
            auth_token: Optional LocalStack auth token for Pro edition
            configuration: Optional string of configuration variables in format "KEY1=value1,KEY2=value2"
                         Example: "DEBUG=1,LS_LOG=trace"
            docker_sock: Optional Docker socket for container interactions
            
        Returns:
            A running LocalStack service container
        """
        # Determine image based on auth token
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
