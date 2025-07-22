"""LocalStack module for managing LocalStack instances and state.

This module provides functions to start LocalStack containers, manage state through Cloud Pods,
and handle ephemeral LocalStack instances in the cloud using LocalStack Cloud and an auth token.
This module supports both Community and Pro versions of LocalStack.
"""

from .main import Localstack as Localstack
