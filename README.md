# LocalStack Dagger Module

A Dagger module for running LocalStack (Community and Pro editions) as a service.

## Features

- Supports both LocalStack Community and Pro editions
- Secure handling of authentication tokens using Dagger secrets
- Automatic port mapping for:
  - Community Edition:
    - 127.0.0.1:4566:4566 (Main LocalStack endpoint)
  - Pro Edition:
    - All Community Edition ports
    - 127.0.0.1:443:443 (HTTPS endpoint)
- Configurable environment variables for LocalStack customization
- Docker socket mounting for container interactions
- Management of ephemeral LocalStack instances in the cloud

## Prerequisites

- Dagger CLI installed
- Docker or compatible container runtime
- LocalStack Pro auth token (optional, only for Pro edition)

## Security

This module uses Dagger's secret management system to handle sensitive data like authentication tokens securely. The auth token can be passed using an environment variable:

```bash
export LOCALSTACK_AUTH_TOKEN=your-token-here
dagger call start --auth-token=env:LOCALSTACK_AUTH_TOKEN up
```

The token will be then securely handled by Dagger and never exposed in logs or command output.

## Inputs

### Required Ports

| Port | Description | Edition |
|------|-------------|---------|
| 4566 | Main LocalStack endpoint | Community & Pro |
| 443 | HTTPS endpoint | Pro only |

### Configuration

#### `start`

| Input | Description | Default | Example |
|-------|-------------|---------|---------|
| `auth-token` | LocalStack Pro auth token (as Dagger secret) | `None` | `dagger call start --auth-token=env:LOCALSTACK_AUTH_TOKEN` |
| `configuration` | Configuration variables for LocalStack container | `None` | `dagger call start --configuration='DEBUG=1,PERSISTENCE=1'` |
| `docker-sock` | Unix socket path for Docker daemon | `None` | `dagger call start --docker-sock=/var/run/docker.sock` |
| `image-name` | Custom LocalStack image name | `None` | `dagger call start --image-name=localstack/snowflake:latest` |

#### `state`

| Input | Description | Default | Example |
|-------|-------------|---------|---------|
| `auth-token` | LocalStack auth token (as Dagger secret, required for save/load) | `None` | `dagger call state --auth-token=env:LOCALSTACK_AUTH_TOKEN` |
| `load` | Name of the LocalStack Cloud Pod to load | `None` | `dagger call state --load=my-pod` |
| `save` | Name of the LocalStack Cloud Pod to save | `None` | `dagger call state --save=my-pod` |
| `reset` | Reset the LocalStack state | `False` | `dagger call state --reset` |

#### `ephemeral`

| Input | Description | Default | Example |
|-------|-------------|---------|---------|
| `auth-token` | LocalStack Pro auth token (required) | Required | `dagger call ephemeral --auth-token=env:LOCALSTACK_AUTH_TOKEN` |
| `operation` | Operation to perform (`create`/`list`/`delete`/`logs`) | Required | `dagger call ephemeral --operation=create` |
| `name` | Name of the ephemeral instance | Required for `create`/`delete`/`logs` | `dagger call ephemeral --name=my-instance` |
| `lifetime` | Lifetime of the instance in minutes (`create` operation only) | 60 | `dagger call ephemeral --lifetime=120` |
| `auto-load-pod` | Pod configuration to auto-load (`create` operation only) | `None` | `dagger call ephemeral --auto-load-pod=my-pod` |
| `extension-auto-install` | Extension to auto-install (`create` operation only) | `None` | `dagger call ephemeral --extension-auto-install=my-extension --operation=create` |

## Usage

### Start LocalStack Community Edition

```bash
# Basic start
dagger call start up
```

### Start LocalStack Pro Edition

```bash
# Set auth token in environment
export LOCALSTACK_AUTH_TOKEN=your-token-here

# Basic start with auth token from environment
dagger call start --auth-token=env:LOCALSTACK_AUTH_TOKEN up
```

## Development

To develop this module:

1. Clone the repository
2. Run `dagger develop` to set up the development environment
3. Make your changes in `.dagger/src/localstack_dagger_module/main.py`
4. Test your changes using the commands above
