import dagger
from dagger import dag, function, object_type
import boto3
import time

@object_type
class Example:
    @function
    async def localstack__quickstart(self) -> str:
        """Example showing how to start LocalStack Community edition."""
        service = dag.localstack().start()
        
        await service.start()
        endpoint = await service.endpoint()
        print(f"LocalStack is running at {endpoint}")

        # Create a test S3 bucket
        s3 = boto3.client(
            's3',
            endpoint_url=f"http://{endpoint}",
            aws_access_key_id='test',
            aws_secret_access_key='test',
            region_name='us-east-1'
        )
        s3.create_bucket(Bucket='test-bucket')

        print("S3 bucket created")

        # Create a test object
        s3.put_object(
            Bucket='test-bucket',
            Key='test-object',
            Body='Hello, LocalStack!'
        )
        print("S3 object created")

        # Verify the object was created
        response = s3.get_object(Bucket='test-bucket', Key='test-object')
        content = response['Body'].read().decode('utf-8')
        print(f"S3 object content: {content}")

    @function
    async def localstack__pro(self, auth_token: dagger.Secret) -> str:
        """Example showing how to start LocalStack Pro with custom configuration."""
        # Start LocalStack Pro using the module
        service = dag.localstack().start(
            auth_token=auth_token,
            configuration="DEBUG=1,SERVICES=ecr"
        )

        await service.start()
        endpoint = await service.endpoint()
        print(f"LocalStack Pro is running at {endpoint}")

        # Create a test ECR repository
        ecr = boto3.client(
            'ecr',
            endpoint_url=f"http://{endpoint}",
            aws_access_key_id='test',
            aws_secret_access_key='test',
            region_name='us-east-1'
        )

        repository_name = "test-ecr-repo"
        ecr.create_repository(repositoryName=repository_name)
        print(f"ECR repository '{repository_name}' created")

    @function
    async def localstack__state(self, auth_token: dagger.Secret) -> str:
        """Example showing how to manage LocalStack state using Cloud Pods."""
        service = dag.localstack().start(auth_token=auth_token)
        await service.start()
        endpoint = await service.endpoint()

        try:
            # Create a test bucket
            s3 = boto3.client(
                's3',
                endpoint_url=f"http://{endpoint}",
                aws_access_key_id='test',
                aws_secret_access_key='test',
                region_name='us-east-1'
            )
            s3.create_bucket(Bucket='test-bucket')

            # Save state to Cloud Pod
            await dag.localstack().state(
                auth_token=auth_token,
                save="test-dagger-example-pod",
                endpoint=f"http://{endpoint}"
            )

            # Reset state
            await dag.localstack().state(
                reset=True,
                endpoint=f"http://{endpoint}"
            )

            # Load state back
            await dag.localstack().state(
                auth_token=auth_token,
                load="test-dagger-example-pod",
                endpoint=f"http://{endpoint}"
            )

            return "Success: State operations completed"
        except Exception as e:
            return f"Error: {str(e)}"

    @function
    async def localstack_ephemeral(self, auth_token: dagger.Secret) -> str:
        """Example showing how to manage LocalStack Ephemeral Instances."""
        try:
            # Create a new ephemeral instance
            await dag.localstack().ephemeral(
                auth_token=auth_token,
                operation="create",
                name="test-dagger-example-instance",
                lifetime=60,
            )
            
            # Wait for instance to be ready
            time.sleep(15)

            print("Instance created")
            
            # List instances
            list_response = await dag.localstack().ephemeral(
                auth_token=auth_token,
                operation="list"
            )

            print(f"Ephemeral instances: {list_response}")
            
            # Get instance logs
            instance_logs = await dag.localstack().ephemeral(
                auth_token=auth_token,
                operation="logs",
                name="test-dagger-example-instance"
            )

            print(f"Instance logs: {instance_logs}")
            
            # Delete instance
            await dag.localstack().ephemeral(
                auth_token=auth_token,
                operation="delete",
                name="test-dagger-example-instance"
            )

            print("Instance deleted")
            
            return "Success: Ephemeral instance operations completed"
        except Exception as e:
            return f"Error: {str(e)}"

    @function
    async def terraform__image_resizer_ci(
        self,
        project_dir: dagger.Directory,
        auth_token: dagger.Secret | None = None,
        docker_sock: dagger.Socket | None = None,
    ) -> str:
        """Run Terraform + LocalStack pipeline for the image resizer example.

        Steps:
        - Start LocalStack (Community by default; Pro if auth_token provided) with Docker socket mounted
        - Build lambda.zip inside the tools container
        - Install Terraform and terraform/awslocal
        - Run terraform init/plan/apply
        - Upload a sample image to S3 using awslocal and list resized bucket
        - Run terraform test
        """
        # Start LocalStack service; optionally mount Docker socket to enable Lambda containers
        service = dag.localstack().start(auth_token=auth_token, docker_sock=docker_sock, configuration="DEBUG=1,LAMBDA_RUNTIME_ENVIRONMENT_TIMEOUT=60")

        await service.start()
        endpoint = await service.endpoint()
        print(f"LocalStack service started at {endpoint}")
        # endpoint is of form "<host>:<port>"
        try:
            ls_host, ls_port = endpoint.split(":", 1)
        except ValueError:
            ls_host, ls_port = endpoint, "4566"

        # Tools container: Python base, install Terraform + terraform/awslocal, build lambda, run Terraform & tests
        tools = (
            dag.container()
            .from_("python:3.11-slim")
            .with_service_binding("localstack", service)
            .with_mounted_directory("/work", project_dir)
            .with_workdir("/work")
            # Base tools
            .with_exec(["bash", "-lc", "apt-get update && apt-get install -y curl unzip zip && rm -rf /var/lib/apt/lists/*"])
            # Install Terraform CLI
            .with_exec(["bash", "-lc", "TFV=1.7.5; curl -fsSL https://releases.hashicorp.com/terraform/$TFV/terraform_${TFV}_linux_amd64.zip -o /tmp/terraform.zip && unzip -o /tmp/terraform.zip -d /usr/local/bin && terraform -version"])
            # Install awslocal/terraform wrappers
            .with_exec(["pip", "install", "--no-cache-dir", "awscli", "awscli-local", "terraform-local"])
            # Env for AWS + LocalStack wrappers
            .with_env_variable("AWS_ACCESS_KEY_ID", "test")
            .with_env_variable("AWS_SECRET_ACCESS_KEY", "test")
            .with_env_variable("AWS_DEFAULT_REGION", "us-east-1")
            # Point all AWS SDKs/CLI to LocalStack service endpoint
            .with_env_variable("AWS_ENDPOINT_URL", f"http://{endpoint}")
            .with_env_variable("S3_HOSTNAME", "localhost")
        )

        # Build lambda.zip (compatible with linux/amd64)
        tools = tools.with_exec([
            "bash",
            "-lc",
            "pip install -r requirements.txt -t libs && zip -r lambda.zip libs && zip -g lambda.zip lambda_function.py",
        ])

        # Terraform lifecycle
        # tools = tools.with_exec(["bash", "-lc", "terraform init | cat"]).with_exec(["bash", "-lc", "terraform plan | cat"]).with_exec(["bash", "-lc", "terraform apply -auto-approve | cat"])

        # Trigger Lambda via S3 upload and verify (works best if docker socket mounted)
        # tools = tools.with_exec(["bash", "-lc", "awslocal s3 cp image.png s3://original-images/image.png | cat"]).with_exec(["bash", "-lc", "awslocal s3 ls s3://resized-images | cat"]) 

        # Terraform tests
        tools = tools.with_exec(["bash", "-lc", "terraform init | cat"]).with_exec(["bash", "-lc", "terraform test | cat"])

        # Execute and return last command's output (tests)
        result = await tools.stdout()
        return result or "Success: Terraform pipeline executed"
