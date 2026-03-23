"""LocalStack module for managing LocalStack instances and state.

This module provides functions to start LocalStack containers, manage state through Cloud Pods,
and handle ephemeral LocalStack instances in the cloud using LocalStack Cloud and an auth token.
This module requires a LocalStack Auth Token for authentication.
"""

from .main import Localstack as Localstack
