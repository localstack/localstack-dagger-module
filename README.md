# LocalStack Dagger Module

A Dagger module for running LocalStack (Community and Pro editions) as a service.

## Features

- Supports both LocalStack Community and Pro editions
- Automatic port mapping for:
  - Community Edition:
    - 127.0.0.1:4566:4566 (Main LocalStack endpoint)
  - Pro Edition:
    - All Community Edition ports
    - 127.0.0.1:443:443 (HTTPS endpoint)
- Configurable environment variables for LocalStack customization
- Docker socket mounting for container interactions

## Prerequisites

- Dagger CLI installed
- Docker or compatible container runtime
- LocalStack Pro auth token (optional, only for Pro edition)

## Inputs

### Required Ports

| Port | Description | Edition |
|------|-------------|---------|
| 4566 | Main LocalStack endpoint | Community & Pro |
| 443 | HTTPS endpoint | Pro only |

### Configuration

#### `serve`

| Input | Description | Default | Example |
|-------|-------------|---------|---------|
| `auth_token` | LocalStack Pro authentication token | `None` | `dagger call serve --auth-token=<your-token>` |
| `configuration` | Configuration variables for LocalStack container | `None` | `dagger call serve --configuration='DEBUG=1,PERSISTENCE=1'` |
| `docker-sock` | Unix socket path for Docker daemon | `None` | `dagger call serve --docker-sock=/var/run/docker.sock` |
| `image-name` | Custom LocalStack image name | `None` | `dagger call serve --image-name=localstack/snowflake:latest` |

#### `state`

| Input | Description | Default | Example |
|-------|-------------|---------|---------|
| `auth_token` | LocalStack Pro authentication token (required for save/load) | `None` | `dagger call state --auth-token=<your-token>` |
| `load` | Name of the LocalStack Cloud Pod to load | `None` | `dagger call state --load=my-pod` |
| `save` | Name of the LocalStack Cloud Pod to save | `None` | `dagger call state --save=my-pod` |
| `reset` | Reset the LocalStack state | `False` | `dagger call state --reset` |

## Usage

### Start LocalStack Community Edition

```bash
# Basic start
dagger call serve up --ports 4566:4566
```

### Start LocalStack Pro Edition

```bash
# Basic start
dagger call serve --auth-token=<your-token> up --ports 4566:4566 --ports 443:443

# Save current state to a Cloud Pod (requires auth token)
dagger call state --auth-token=<your-token> --save=my-pod

# Load state from a Cloud Pod (requires auth token)
dagger call state --auth-token=<your-token> --load=my-pod

# Reset LocalStack state (no auth token required)
dagger call state --reset
```

## Development

To develop this module:

1. Clone the repository
2. Run `dagger develop` to set up the development environment
3. Make your changes in `.dagger/src/localstack_dagger_module/main.py`
4. Test your changes using the commands above 
