import os
import dagger
from dagger import dag, function, object_type, client
from typing import Optional


@object_type
class LocalstackDaggerModule:
    @function
    def serve(self, auth_token: Optional[str] = None) -> dagger.Service:
        """Start a LocalStack service with appropriate configuration based on auth token.
        
        If auth_token is provided, starts LocalStack Pro edition.
        Otherwise starts LocalStack Community edition.
        
        Args:
            auth_token: Optional LocalStack auth token for Pro edition
            
        Returns:
            A running LocalStack service container
        """
        # Determine image based on auth token
        image = "localstack/localstack-pro:latest" if auth_token else "localstack/localstack:latest"
        
        # Start with base container config
        container = dag.container().from_(image)
        
        # Add auth token if provided
        if auth_token:
            container = container.with_env_variable("LOCALSTACK_AUTH_TOKEN", auth_token)
            
        # Add common ports (4566 and 4510-4559)
        container = (
            container
            .with_exposed_port(4566)
        )
        
        # Add port 443 for Pro edition
        if auth_token:
            container = container.with_exposed_port(443)
            
        # Return as service
        return container.as_service()
