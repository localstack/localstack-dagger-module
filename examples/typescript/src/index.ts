import { dag, Container, Directory, object, func, Secret } from "@dagger.io/dagger"
import { connect } from "@dagger.io/dagger"
import { S3Client, CreateBucketCommand, PutObjectCommand, GetObjectCommand } from "@aws-sdk/client-s3"
import { ECRClient, CreateRepositoryCommand } from "@aws-sdk/client-ecr"
import { Readable } from "stream"

/**
 * Example class demonstrating LocalStack Dagger module functionality
 */
@object()
export class Example {
  /**
   * Demonstrates basic LocalStack functionality using the community edition.
   * Creates an S3 bucket and object to verify the setup is working correctly.
   * 
   * @returns Promise<void>
   */
  @func()
  async localstack__quickstart() {
    await connect(async (client) => {
      // Start LocalStack using the module
      const service = client.localstack().start()
      
      await service.start()
      const endpoint = await service.endpoint()
      console.log(`LocalStack is running at ${endpoint}`)
  
      // Create S3 client
      const s3 = new S3Client({
        endpoint: `http://${endpoint}`,
        credentials: {
          accessKeyId: "test",
          secretAccessKey: "test"
        },
        region: "us-east-1",
        forcePathStyle: true
      })
  
      // Create a test bucket
      await s3.send(new CreateBucketCommand({
        Bucket: "test-bucket"
      }))
      console.log("S3 bucket created")
  
      // Create a test object
      await s3.send(new PutObjectCommand({
        Bucket: "test-bucket",
        Key: "test-object",
        Body: "Hello, LocalStack!"
      }))
      console.log("S3 object created")
  
      // Verify the object was created
      const response = await s3.send(new GetObjectCommand({
        Bucket: "test-bucket",
        Key: "test-object"
      }))
      
      const content = await streamToString(response.Body as Readable)
      console.log(`S3 object content: ${content}`)
    })
  }

  /**
   * Demonstrates LocalStack Pro functionality by starting a Pro instance
   * and creating an ECR repository.
   * 
   * @param authToken - LocalStack Pro authentication token
   * @returns Promise<void>
   */
  @func()
  async localstack__pro(authToken: Secret) {
    await connect(async (client) => {
      const service = client.localstack().start({
        authToken,
        configuration: "DEBUG=1,SERVICES=ecr",
      })

      await service.start()
      const endpoint = await service.endpoint()
      console.log(`LocalStack Pro is running at ${endpoint}`)

      // Create ECR client
      const ecr = new ECRClient({
        endpoint: `http://${endpoint}`,
        credentials: {
          accessKeyId: "test",
          secretAccessKey: "test"
        },
        region: "us-east-1"
      })

      // Create a test repository
      const repositoryName = "test-ecr-repo"
      await ecr.send(new CreateRepositoryCommand({
        repositoryName
      }))
      console.log(`ECR repository '${repositoryName}' created`)
    })
  }

  /**
   * Demonstrates LocalStack state management functionality using Cloud Pods.
   * Creates a test bucket, saves state to a pod, resets state, and loads it back.
   * 
   * @param authToken - LocalStack Pro authentication token
   * @returns Promise<void>
   */
  @func()
  async localstack__state(authToken: Secret) {
    await connect(async (client) => {
      const service = client.localstack().start({
        authToken
      })

      await service.start()
      const endpoint = await service.endpoint()

      // Create S3 client and test bucket
      const s3 = new S3Client({
        endpoint: `http://${endpoint}`,
        credentials: {
          accessKeyId: "test",
          secretAccessKey: "test"
        },
        region: "us-east-1",
        forcePathStyle: true
      })

      await s3.send(new CreateBucketCommand({
        Bucket: "test-bucket"
      }))
      console.log("Test bucket created")

      // Save state to Cloud Pod
      await client.localstack().state({
        authToken,
        save: "test-dagger-example-pod",
        endpoint: `http://${endpoint}`
      })

      console.log("State saved to Cloud Pod")

      // Reset state
      await client.localstack().state({
        reset: true,
        endpoint: `http://${endpoint}`
      })
      console.log("State reset")

      // Load state back
      await client.localstack().state({
        authToken,
        load: "test-dagger-example-pod",
        endpoint: `http://${endpoint}`
      })

      console.log("State loaded from Cloud Pod")
    })
  }

  /**
   * Demonstrates LocalStack ephemeral instance management.
   * Creates an ephemeral instance, lists instances, retrieves logs,
   * and cleans up by deleting the instance.
   * 
   * @param authToken - LocalStack Pro authentication token
   * @returns Promise<void>
   */
  @func()
  async localstack__ephemeral(authToken: Secret) {
    await connect(async (client) => {
      // Create a new ephemeral instance
      await client.localstack().ephemeral(
        authToken,
        "create",
        {
          name: "test-dagger-example-instance",
          lifetime: 60
        }
      )
      console.log("Instance created")

      // Wait for instance to be ready
      await new Promise(resolve => setTimeout(resolve, 15000))

      // List instances
      const listResponse = await client.localstack().ephemeral(
        authToken,
        "list"
      )
      console.log(`Ephemeral instances: ${listResponse}`)

      // Get instance logs
      const instanceLogs = await client.localstack().ephemeral(
        authToken,
        "logs",
        {
          name: "test-dagger-example-instance"
        }
      )
      console.log(`Instance logs: ${instanceLogs}`)

      // Delete instance
      await client.localstack().ephemeral(
        authToken,
        "delete",
        {
          name: "test-dagger-example-instance"
        }
      )
      console.log("Instance deleted")
    })
  }
}

/**
 * Helper function to convert a readable stream to a string.
 * Used for processing responses from AWS SDK operations.
 * 
 * @param stream - Readable stream to convert
 * @returns Promise<string> The stream contents as a string
 */
async function streamToString(stream: Readable): Promise<string> {
  const chunks: Buffer[] = []
  for await (const chunk of stream) {
    chunks.push(Buffer.from(chunk))
  }
  return Buffer.concat(chunks).toString("utf-8")
}
