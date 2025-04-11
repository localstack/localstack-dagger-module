# LocalStack Dagger Module

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![LocalStack Dagger Module Tests](https://github.com/localstack/localstack-dagger-module/actions/workflows/test.yml/badge.svg)](https://github.com/localstack/localstack-dagger-module/actions/workflows/test.yml)

A [Dagger](https://dagger.io/) module for running [LocalStack](https://github.com/localstack/localstack) (Community and Pro image) as a service within your Dagger pipelines.

This module simplifies integrating LocalStack into your development and testing workflows by:

-   Starting LocalStack Community or Pro editions as a Dagger service.
-   Securely handling LocalStack Auth Tokens using Dagger secrets.
-   Automatically exposing standard LocalStack ports (`4566` for Community/Pro, `443` for Pro).
-   Allowing customization of the LocalStack container via environment variables.
-   Optionally mounting the Docker socket for tests interacting with external containers.
-   Managing LocalStack state using [Cloud Pods](https://docs.localstack.cloud/user-guide/state-management/cloud-pods/) (`save`/`load`/`reset`).
-   Managing [LocalStack Ephemeral Instances](https://docs.localstack.cloud/user-guide/cloud-sandbox/ephemeral-instance/) (`create`/`list`/`delete`/`logs`).

## Prerequisites

-   [Dagger CLI installed](https://docs.dagger.io/install)
-   Docker or a compatible container runtime
-   LocalStack Auth Token (required for Pro features, Cloud Pods, and Ephemeral Instances)

## Installation

You can install this module locally to use it in your own Dagger projects or pipelines:

```bash
dagger install github.com/localstack/localstack-dagger-module
```

You can then call its functions from the Dagger CLI or your Dagger SDK code.

## Usage

### Start LocalStack Community

This is the simplest way to start the default LocalStack Community edition.

```bash 
dagger -m github.com/localstack/localstack-dagger-module call start up
```

LocalStack will run and be accessible at `localhost:4566` and with any integration that LocalStack supports.

### Start LocalStack Pro

To use LocalStack Pro features, Cloud Pods, or Ephemeral Instances, you need an Auth Token.

```bash 
# 1. Set your LocalStack Pro auth token as an environment variable
export LOCALSTACK_AUTH_TOKEN="your-pro-token"

# 2. Start LocalStack Pro using the token from the environment
dagger -m github.com/localstack/localstack-dagger-module \
    call start --auth-token=env:LOCALSTACK_AUTH_TOKEN \
    up
```

If the token is invalid or missing when Pro usage is implied, LocalStack might behave unexpectedly or functionality might be limited.

### Customizing LocalStack

You can pass configuration variables in the following manner:

```bash
dagger -m github.com/localstack/localstack-dagger-module call start \
    --auth-token=env:LOCALSTACK_AUTH_TOKEN \
    --configuration='SERVICES=s3' \
    up
```

### Mounting Docker Socket

To run emulated AWS services that rely on a container, like Lambda or ECS, you would need to mount Docker Socket into the LocalStack container.

```bash 
dagger -m github.com/localstack/localstack-dagger-module call start \
    --auth-token=env:LOCALSTACK_AUTH_TOKEN \
    --docker-sock /var/run/docker.sock \
    up
```

### Managing State with Cloud Pods

Cloud pods are persistent state snapshots of your LocalStack instance that can easily be stored, versioned, shared, and restored. Cloud Pods require a LocalStack Auth Token.

```bash 
# Set your auth token
export LOCALSTACK_AUTH_TOKEN="your-pro-token"

# Save the current state of your running LocalStack instance to a Cloud Pod
# Assumes you have a running instance started via 'dagger call start ... up' 
# And some cloud resources created via an integration
dagger -m github.com/localstack/localstack-dagger-module call state \
    --auth-token=env:LOCALSTACK_AUTH_TOKEN \
    --save=dagger-test-pod

# Reset the state of the running LocalStack instance
dagger -m github.com/localstack/localstack-dagger-module call state \
    --reset

# Load state from a Cloud Pod into your running LocalStack instance
dagger -m github.com/localstack/localstack-dagger-module call state \
    --auth-token=env:LOCALSTACK_AUTH_TOKEN \
    --load=dagger-test-pod
```

### Managing Ephemeral Instances

Ephemeral Instances allows you to run a LocalStack instance in the cloud. Ephemeral Instances require a LocalStack Pro Auth Token.

```bash
# Set your auth token
export LOCALSTACK_AUTH_TOKEN="your-pro-token"

# Create a new Ephemeral Instance in LocalStack Cloud
dagger -m github.com/localstack/localstack-dagger-module call ephemeral \
    --auth-token=env:LOCALSTACK_AUTH_TOKEN \
    --operation=create \
    --name=my-temp-instance \
    --lifetime=120

# List active Ephemeral Instances
dagger -m github.com/localstack/localstack-dagger-module call ephemeral \
    --auth-token=env:LOCALSTACK_AUTH_TOKEN \
    --operation=list

# Get logs for an Ephemeral Instance
dagger -m github.com/localstack/localstack-dagger-module call ephemeral \
    --auth-token=env:LOCALSTACK_AUTH_TOKEN \
    --operation=logs \
    --name=my-temp-instance

# Delete an Ephemeral Instance
dagger -m github.com/localstack/localstack-dagger-module call ephemeral \
    --auth-token=env:LOCALSTACK_AUTH_TOKEN \
    --operation=delete \
    --name=my-temp-instance
```

## Inputs

### `start` 

Used to configure and start the main LocalStack service.

| Input           | Description                                                                 | Default                             | Example                                                       |
| --------------- | --------------------------------------------------------------------------- | ----------------------------------- | ------------------------------------------------------------- |
| `auth-token`    | LocalStack Pro auth token (as Dagger `Secret`). Required for Pro features.  | `None`                              | `dagger call start --auth-token=env:LOCALSTACK_AUTH_TOKEN`      |
| `configuration` | Comma-separated `KEY=VALUE` pairs for LocalStack environment variables.     | `None`                              | `dagger call start --configuration='DEBUG=1,PERSISTENCE=1'`     |
| `docker-sock`   | Path to the Unix socket for the Docker daemon to mount into the container.  | `None`                              | `dagger call start --docker-sock=/var/run/docker.sock`        |
| `image-name`    | Custom LocalStack Docker image name and tag.                                | `localstack/localstack:latest`      | `dagger call start --image-name=localstack/snowflake:latest` |

### `state`

Used to manage the state of a running LocalStack instance using Cloud Pods (Pro only).

| Input        | Description                                                                          | Default   | Example                                          |
| ------------ | ------------------------------------------------------------------------------------ | --------- | ------------------------------------------------ |
| `auth-token` | LocalStack Pro Auth Token (as Dagger `Secret`). Required for `save` and `load`.      | `None`    | `dagger call state --auth-token=env:LOCALSTACK_AUTH_TOKEN` |
| `load`       | Name of the LocalStack Cloud Pod to load into the running instance.                  | `None`    | `dagger call state --load=my-pod`                  |
| `save`       | Name under which to save the current state as a LocalStack Cloud Pod.                | `None`    | `dagger call state --save=my-pod`                  |
| `reset`      | If `true`, resets the state of the running LocalStack instance.                      | `False`   | `dagger call state --reset`                      |

### `ephemeral`

Used to manage LocalStack Ephemeral Instances in LocalStack Cloud (Pro only).

| Input                    | Description                                                                                                | Default   | Example                                                  |
| ------------------------ | ---------------------------------------------------------------------------------------------------------- | --------- | -------------------------------------------------------- |
| `auth-token`             | LocalStack Pro Auth Token (as Dagger `Secret`). Required for all operations.                               | Required  | `dagger call ephemeral --auth-token=env:LOCALSTACK_AUTH_TOKEN` |
| `operation`              | Action to perform: `create`, `list`, `delete`, `logs`.                                                     | Required  | `dagger call ephemeral --operation=create`             |
| `name`                   | Name of the ephemeral instance. Required for `create`, `delete`, `logs`.                                   | `None`    | `dagger call ephemeral --name=my-instance`             |
| `lifetime`               | Lifetime of the instance in minutes (only for `create` operation).                                         | `60`      | `dagger call ephemeral --lifetime=120`                   |
| `auto-load-pod`          | Name of a Cloud Pod to automatically load when the ephemeral instance starts (only for `create` operation). | `None`    | `dagger call ephemeral --auto-load-pod=my-pod`         |
| `extension-auto-install` | Name of an extension to automatically install when the ephemeral instance starts (only for `create` operation). | `None`    | `dagger call ephemeral --extension-auto-install=my-extension --operation=create` |

## Development

To contribute or make local changes to this module:

1. Clone the repository:
  ```bash
  git clone https://github.com/localstack/localstack-dagger-module.git
  cd localstack-dagger-module
  ```
2. Run `dagger develop` to set up the development environment.
3. Make your changes, typically within the Dagger module source files (e.g., in `.dagger/src/`).
4. Test your changes locally using `dagger call` or `dagger test` as described in the sections above.

## License

This project is licensed under the Apache License 2.0. See the [LICENSE](./LICENSE) file for details.
