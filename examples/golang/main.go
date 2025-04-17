// A Golang module for LocalStack integration
//
// This module demonstrates how to use the LocalStack Dagger module
// to start and interact with LocalStack.

package main

import (
	"context"
	"fmt"
	"io"
	"strings"
	"time"

	"github.com/aws/aws-sdk-go-v2/aws"
	"github.com/aws/aws-sdk-go-v2/config"
	"github.com/aws/aws-sdk-go-v2/credentials"
	"github.com/aws/aws-sdk-go-v2/service/s3"
	"github.com/aws/aws-sdk-go-v2/service/ecr"
	"dagger/golang/internal/dagger"
)

type Golang struct{}

// Starts LocalStack and performs example S3 operations
func (m *Golang) LocalstackQuickstart(ctx context.Context) (string, error) {
	service := dag.Localstack().Start()

	// Start the service and get endpoint
	if _, err := service.Start(ctx); err != nil {
		return "", fmt.Errorf("failed to start LocalStack: %w", err)
	}
	
	endpoint, err := service.Endpoint(ctx)
	if err != nil {
		return "", fmt.Errorf("failed to get endpoint: %w", err)
	}

	// Create custom AWS configuration for LocalStack
	customResolver := aws.EndpointResolverWithOptionsFunc(func(service, region string, options ...interface{}) (aws.Endpoint, error) {
		return aws.Endpoint{
			URL:               fmt.Sprintf("http://%s", endpoint),
			HostnameImmutable: true,
			SigningRegion:    "us-east-1",
		}, nil
	})

	cfg, err := config.LoadDefaultConfig(ctx,
		config.WithRegion("us-east-1"),
		config.WithEndpointResolverWithOptions(customResolver),
		config.WithCredentialsProvider(credentials.NewStaticCredentialsProvider("test", "test", "")),
	)
	if err != nil {
		return "", fmt.Errorf("failed to load AWS config: %w", err)
	}

	// Create S3 client with path-style addressing
	s3Client := s3.NewFromConfig(cfg, func(o *s3.Options) {
		o.UsePathStyle = true
	})

	// Create a test bucket
	bucketName := "test-bucket"
	_, err = s3Client.CreateBucket(ctx, &s3.CreateBucketInput{
		Bucket: aws.String(bucketName),
	})
	if err != nil {
		return "", fmt.Errorf("failed to create bucket: %w", err)
	}

	// Create a test object
	content := "Hello, LocalStack!"
	_, err = s3Client.PutObject(ctx, &s3.PutObjectInput{
		Bucket: aws.String(bucketName),
		Key:    aws.String("test-object"),
		Body:   strings.NewReader(content),
	})
	if err != nil {
		return "", fmt.Errorf("failed to put object: %w", err)
	}

	// Get and verify the object
	result, err := s3Client.GetObject(ctx, &s3.GetObjectInput{
		Bucket: aws.String(bucketName),
		Key:    aws.String("test-object"),
	})
	if err != nil {
		return "", fmt.Errorf("failed to get object: %w", err)
	}

	// Read the object content
	data, err := io.ReadAll(result.Body)
	if err != nil {
		return "", fmt.Errorf("failed to read object content: %w", err)
	}
	defer result.Body.Close()

	output := fmt.Sprintf(`LocalStack is running at %s
S3 bucket created
S3 object created
S3 object content: %s`, endpoint, string(data))

	return output, nil
}

// Starts LocalStack Pro with custom configuration and creates an ECR repository
func (m *Golang) LocalstackPro(ctx context.Context, authToken *dagger.Secret) (string, error) {
	// Start LocalStack Pro using the module with custom configuration
	service := dag.Localstack().Start(dagger.LocalstackStartOpts{
		AuthToken: authToken,
	})

	// Start the service and wait for it to be ready
	if _, err := service.Start(ctx); err != nil {
		return "", fmt.Errorf("failed to start LocalStack Pro: %w", err)
	}

	endpoint, err := service.Endpoint(ctx)
	if err != nil {
		return "", fmt.Errorf("failed to get endpoint: %w", err)
	}

	// Create custom AWS configuration for LocalStack
	customResolver := aws.EndpointResolverWithOptionsFunc(func(service, region string, options ...interface{}) (aws.Endpoint, error) {
		return aws.Endpoint{
			URL:               fmt.Sprintf("http://%s", endpoint),
			HostnameImmutable: true,
			SigningRegion:    "us-east-1",
		}, nil
	})

	cfg, err := config.LoadDefaultConfig(ctx,
		config.WithRegion("us-east-1"),
		config.WithEndpointResolverWithOptions(customResolver),
		config.WithCredentialsProvider(credentials.NewStaticCredentialsProvider("test", "test", "")),
	)
	if err != nil {
		return "", fmt.Errorf("failed to load AWS config: %w", err)
	}

	// Create ECR client with path-style addressing
	ecrClient := ecr.NewFromConfig(cfg, func(o *ecr.Options) {
		o.BaseEndpoint = aws.String(fmt.Sprintf("http://%s", endpoint))
	})

	// Create a test ECR repository
	repositoryName := "test-ecr-repo"
	_, err = ecrClient.CreateRepository(ctx, &ecr.CreateRepositoryInput{
		RepositoryName: aws.String(repositoryName),
	})
	if err != nil {
		return "", fmt.Errorf("failed to create ECR repository: %w", err)
	}

	output := fmt.Sprintf(`LocalStack Pro is running at %s
ECR repository '%s' created`, endpoint, repositoryName)

	return output, nil
}

// Demonstrates LocalStack state management using Cloud Pods
func (m *Golang) LocalstackState(ctx context.Context, authToken *dagger.Secret) (string, error) {
	// Start LocalStack Pro
	service := dag.Localstack().Start(dagger.LocalstackStartOpts{
		AuthToken: authToken,
	})

	// Start the service and wait for it to be ready
	if _, err := service.Start(ctx); err != nil {
		return "", fmt.Errorf("failed to start LocalStack Pro: %w", err)
	}

	endpoint, err := service.Endpoint(ctx)
	if err != nil {
		return "", fmt.Errorf("failed to get endpoint: %w", err)
	}

	// Create custom AWS configuration for LocalStack
	customResolver := aws.EndpointResolverWithOptionsFunc(func(service, region string, options ...interface{}) (aws.Endpoint, error) {
		return aws.Endpoint{
			URL:               fmt.Sprintf("http://%s", endpoint),
			HostnameImmutable: true,
			SigningRegion:    "us-east-1",
		}, nil
	})

	cfg, err := config.LoadDefaultConfig(ctx,
		config.WithRegion("us-east-1"),
		config.WithEndpointResolverWithOptions(customResolver),
		config.WithCredentialsProvider(credentials.NewStaticCredentialsProvider("test", "test", "")),
	)
	if err != nil {
		return "", fmt.Errorf("failed to load AWS config: %w", err)
	}

	// Create S3 client with path-style addressing
	s3Client := s3.NewFromConfig(cfg, func(o *s3.Options) {
		o.UsePathStyle = true
	})

	// Create a test bucket
	bucketName := "test-bucket"
	_, err = s3Client.CreateBucket(ctx, &s3.CreateBucketInput{
		Bucket: aws.String(bucketName),
	})
	if err != nil {
		return "", fmt.Errorf("failed to create bucket: %w", err)
	}

	// Save state to Cloud Pod
	result, err := dag.Localstack().State(ctx, dagger.LocalstackStateOpts{
		AuthToken: authToken,
		Save:      "test-dagger-example-pod",
		Endpoint:  fmt.Sprintf("http://%s", endpoint),
	})
	if err != nil {
		return "", fmt.Errorf("failed to save state: %w", err)
	}

	// Reset state
	result, err = dag.Localstack().State(ctx, dagger.LocalstackStateOpts{
		Reset:    true,
		Endpoint: fmt.Sprintf("http://%s", endpoint),
	})
	if err != nil {
		return "", fmt.Errorf("failed to reset state: %w", err)
	}

	// Load state back
	result, err = dag.Localstack().State(ctx, dagger.LocalstackStateOpts{
		AuthToken: authToken,
		Load:      "test-dagger-example-pod",
		Endpoint:  fmt.Sprintf("http://%s", endpoint),
	})
	if err != nil {
		return "", fmt.Errorf("failed to load state: %w", err)
	}

	return result, nil
}

// Demonstrates LocalStack ephemeral instance management
func (m *Golang) LocalstackEphemeral(ctx context.Context, authToken *dagger.Secret) (string, error) {
	// Create a new ephemeral instance
	result, err := dag.Localstack().Ephemeral(ctx, authToken, "create", dagger.LocalstackEphemeralOpts{
		Name:     "test-dagger-example-instance",
		Lifetime: 60,
	})
	if err != nil {
		return "", fmt.Errorf("failed to create ephemeral instance: %w", err)
	}
	fmt.Println("Instance created")

	// Wait for instance to be ready
	time.Sleep(15 * time.Second)

	// List instances
	result, err = dag.Localstack().Ephemeral(ctx, authToken, "list", dagger.LocalstackEphemeralOpts{})
	if err != nil {
		return "", fmt.Errorf("failed to list ephemeral instances: %w", err)
	}
	fmt.Printf("Ephemeral instances: %s\n", result)

	// Get instance logs
	result, err = dag.Localstack().Ephemeral(ctx, authToken, "logs", dagger.LocalstackEphemeralOpts{
		Name: "test-dagger-example-instance",
	})
	if err != nil {
		return "", fmt.Errorf("failed to get instance logs: %w", err)
	}
	fmt.Printf("Instance logs: %s\n", result)

	// Delete instance
	result, err = dag.Localstack().Ephemeral(ctx, authToken, "delete", dagger.LocalstackEphemeralOpts{
		Name: "test-dagger-example-instance",
	})
	if err != nil {
		return "", fmt.Errorf("failed to delete instance: %w", err)
	}
	fmt.Println("Instance deleted")

	return "Success: Ephemeral instance operations completed", nil
}
