# LocalStack Dagger Module

A Dagger module for running LocalStack (Community and Pro editions) as a service.

## Features

- Supports both LocalStack Community and Pro editions
- Automatic port mapping for:
  - Community Edition:
    - 127.0.0.1:4566:4566 (Main LocalStack endpoint)
    - 127.0.0.1:4510-4559:4510-4559 (Service-specific ports)
  - Pro Edition:
    - All Community Edition ports
    - 127.0.0.1:443:443 (HTTPS endpoint)

## Prerequisites

- Dagger CLI installed
- Docker or compatible container runtime
- LocalStack Pro auth token (optional, only for Pro edition)

## Usage

### Start LocalStack Community Edition

```bash
# Start the service with port mappings
dagger call serve up --ports 4566:4566 --ports 4510-4559:4510-4559
```

### Start LocalStack Pro Edition

```bash
# Start the service with port mappings including HTTPS port
dagger call serve --auth-token=<your-localstack-auth-token> up --ports 4566:4566 --ports 4510-4559:4510-4559 --ports 443:443
```

The service will be available at:
- Main endpoint: http://localhost:4566
- Service-specific ports: 4510-4559
- HTTPS endpoint (Pro only): https://localhost:443

## Development

To develop this module:

1. Clone the repository
2. Run `dagger develop` to set up the development environment
3. Make your changes in `.dagger/src/localstack_dagger_module/main.py`
4. Test your changes using the commands above 