import { Construct } from "constructs";
import { Duration, RemovalPolicy, CfnOutput } from "aws-cdk-lib";
import * as iam from "aws-cdk-lib/aws-iam";
import * as ecr from "aws-cdk-lib/aws-ecr";
import * as dynamodb from "aws-cdk-lib/aws-dynamodb";
import * as logs from "aws-cdk-lib/aws-logs";
import * as codebuild from "aws-cdk-lib/aws-codebuild";
import * as s3 from "aws-cdk-lib/aws-s3";
import * as ec2 from "aws-cdk-lib/aws-ec2";
import { Database } from "./database";

export interface AgentCoreProps {
  readonly database: Database;
  readonly envName: string;
  readonly envPrefix: string;
  readonly bedrockRegion: string;
  readonly vpc?: ec2.IVpc;
  readonly openSearchEndpoint?: string;
  readonly enableMemory?: boolean;
  readonly enableObservability?: boolean;
}

export class AgentCore extends Construct {
  readonly agentContainerRepository: ecr.Repository;
  readonly runtimeExecutionRole: iam.Role;
  readonly agentRuntimeTable: dynamodb.Table;
  readonly agentMemoryTable?: dynamodb.Table;
  readonly agentBuildProject: codebuild.Project;
  readonly runtimeInvokeRole: iam.Role;

  constructor(scope: Construct, id: string, props: AgentCoreProps) {
    super(scope, id);

    // ECR Repository for agent container images
    this.agentContainerRepository = new ecr.Repository(
      this,
      "AgentContainerRepository",
      {
        repositoryName: `${props.envPrefix}bedrock-chat-agents`,
        removalPolicy: RemovalPolicy.DESTROY,
        emptyOnDelete: true,
        imageScanOnPush: true,
        imageTagMutability: ecr.TagMutability.MUTABLE,
        lifecycleRules: [
          {
            description: "Keep last 10 images",
            maxImageCount: 10,
          },
        ],
      }
    );

    // DynamoDB table for agent runtime registry
    // Maps bot IDs to AgentCore runtime ARNs and metadata
    this.agentRuntimeTable = new dynamodb.Table(
      this,
      "AgentRuntimeTable",
      {
        partitionKey: {
          name: "BotId",
          type: dynamodb.AttributeType.STRING,
        },
        billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
        tableName: `${props.envPrefix}AgentRuntimeRegistry`,
        removalPolicy: RemovalPolicy.DESTROY,
        pointInTimeRecovery: true,
        stream: dynamodb.StreamViewType.NEW_AND_OLD_IMAGES,
        timeToLiveAttribute: "ExpiresAt",
      }
    );

    // Optional: DynamoDB table for agent memory (if enabled)
    if (props.enableMemory) {
      this.agentMemoryTable = new dynamodb.Table(this, "AgentMemoryTable", {
        partitionKey: {
          name: "SessionId",
          type: dynamodb.AttributeType.STRING,
        },
        sortKey: {
          name: "Timestamp",
          type: dynamodb.AttributeType.NUMBER,
        },
        billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
        tableName: `${props.envPrefix}AgentMemory`,
        removalPolicy: RemovalPolicy.DESTROY,
        pointInTimeRecovery: true,
        timeToLiveAttribute: "ExpiresAt",
      });

      // Add GSI for querying by user ID
      this.agentMemoryTable.addGlobalSecondaryIndex({
        indexName: "UserIdIndex",
        partitionKey: {
          name: "UserId",
          type: dynamodb.AttributeType.STRING,
        },
        sortKey: {
          name: "Timestamp",
          type: dynamodb.AttributeType.NUMBER,
        },
      });
    }

    // IAM role for AgentCore runtime execution
    // This role will be assumed by the agent containers
    this.runtimeExecutionRole = new iam.Role(
      this,
      "AgentRuntimeExecutionRole",
      {
        assumedBy: new iam.CompositePrincipal(
          new iam.ServicePrincipal("bedrock.amazonaws.com"),
          new iam.ServicePrincipal("bedrock-agentcore.amazonaws.com"),
          new iam.ServicePrincipal("lambda.amazonaws.com"),
          new iam.ServicePrincipal("ecs-tasks.amazonaws.com")
        ),
        description:
          "Execution role for Bedrock AgentCore runtime containers",
      }
    );

    // Grant Bedrock permissions
    this.runtimeExecutionRole.addToPolicy(
      new iam.PolicyStatement({
        actions: ["bedrock:*"],
        resources: ["*"],
      })
    );

    // Grant access to bot and conversation tables via the existing table access role
    this.runtimeExecutionRole.addToPolicy(
      new iam.PolicyStatement({
        actions: ["sts:AssumeRole"],
        resources: [props.database.tableAccessRole.roleArn],
      })
    );

    // Grant access to runtime registry table
    this.agentRuntimeTable.grantReadWriteData(this.runtimeExecutionRole);

    // Grant access to memory table if enabled
    if (this.agentMemoryTable) {
      this.agentMemoryTable.grantReadWriteData(this.runtimeExecutionRole);
    }

    // Grant ECR pull permissions
    this.agentContainerRepository.grantPull(this.runtimeExecutionRole);

    // If OpenSearch is configured, grant access
    if (props.openSearchEndpoint) {
      this.runtimeExecutionRole.addToPolicy(
        new iam.PolicyStatement({
          actions: ["es:*", "aoss:*"],
          resources: ["*"],
        })
      );
    }

    // Add CloudWatch Logs permissions
    this.runtimeExecutionRole.addManagedPolicy(
      iam.ManagedPolicy.fromAwsManagedPolicyName(
        "service-role/AWSLambdaBasicExecutionRole"
      )
    );

    // Add X-Ray permissions for observability (if enabled)
    if (props.enableObservability) {
      this.runtimeExecutionRole.addManagedPolicy(
        iam.ManagedPolicy.fromAwsManagedPolicyName("AWSXRayDaemonWriteAccess")
      );
    }

    // S3 bucket for CodeBuild artifacts
    const buildArtifactBucket = new s3.Bucket(this, "BuildArtifactBucket", {
      // Don't specify bucketName - let CDK generate a unique name
      removalPolicy: RemovalPolicy.DESTROY,
      autoDeleteObjects: true,
      encryption: s3.BucketEncryption.S3_MANAGED,
    });

    // CodeBuild role for building agent containers
    const buildRole = new iam.Role(this, "AgentBuildRole", {
      assumedBy: new iam.ServicePrincipal("codebuild.amazonaws.com"),
    });

    // Grant ECR push permissions
    this.agentContainerRepository.grantPullPush(buildRole);

    // Grant CloudWatch Logs permissions
    buildRole.addToPolicy(
      new iam.PolicyStatement({
        actions: [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
        ],
        resources: ["*"],
      })
    );

    // Grant S3 access for artifacts
    buildArtifactBucket.grantReadWrite(buildRole);

    // Grant access to read bot configurations
    props.database.botTable.grantReadData(buildRole);

    // CodeBuild project for building agent containers
    this.agentBuildProject = new codebuild.Project(
      this,
      "AgentBuildProject",
      {
        projectName: `${props.envPrefix}AgentCoreBuild`,
        description:
          "Builds and pushes agent containers to ECR for AgentCore deployment",
        role: buildRole,
        environment: {
          buildImage: codebuild.LinuxBuildImage.STANDARD_7_0,
          privileged: true, // Required for Docker builds
          computeType: codebuild.ComputeType.LARGE,
          environmentVariables: {
            AWS_DEFAULT_REGION: {
              value: props.bedrockRegion,
            },
            AWS_ACCOUNT_ID: {
              value: scope.node.tryGetContext("account") || "",
            },
            IMAGE_REPO_NAME: {
              value: this.agentContainerRepository.repositoryName,
            },
            IMAGE_URI: {
              value: this.agentContainerRepository.repositoryUri,
            },
          },
        },
        buildSpec: codebuild.BuildSpec.fromObject({
          version: "0.2",
          phases: {
            pre_build: {
              commands: [
                "echo Logging in to Amazon ECR...",
                "aws ecr get-login-password --region $AWS_DEFAULT_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com",
                "COMMIT_HASH=$(echo $CODEBUILD_RESOLVED_SOURCE_VERSION | cut -c 1-7)",
                "IMAGE_TAG=${COMMIT_HASH:=latest}",
              ],
            },
            build: {
              commands: [
                "echo Build started on `date`",
                "echo Building the Docker image for ARM64 architecture...",
                "cd backend",
                "docker buildx create --use",
                "docker buildx build --platform linux/arm64 -t $IMAGE_URI:$IMAGE_TAG -t $IMAGE_URI:latest -f agentcore_runtime/Dockerfile . --push",
              ],
            },
            post_build: {
              commands: [
                "echo Build completed on `date`",
                'echo "Image pushed to $IMAGE_URI:$IMAGE_TAG"',
              ],
            },
          },
        }),
        timeout: Duration.minutes(30),
        cache: codebuild.Cache.local(
          codebuild.LocalCacheMode.DOCKER_LAYER,
          codebuild.LocalCacheMode.CUSTOM
        ),
      }
    );

    // IAM role for invoking AgentCore runtimes
    // This will be assumed by the main Lambda handler
    this.runtimeInvokeRole = new iam.Role(this, "AgentRuntimeInvokeRole", {
      assumedBy: new iam.ServicePrincipal("lambda.amazonaws.com"),
      description: "Role for invoking Bedrock AgentCore runtimes",
    });

    // Grant permissions to invoke AgentCore runtimes
    this.runtimeInvokeRole.addToPolicy(
      new iam.PolicyStatement({
        actions: [
          "bedrock-agentcore:InvokeAgentRuntime",
          "bedrock-agentcore:CreateAgentRuntime",
          "bedrock-agentcore:UpdateAgentRuntime",
          "bedrock-agentcore:DeleteAgentRuntime",
          "bedrock-agentcore:GetAgentRuntime",
          "bedrock-agentcore:ListAgentRuntimes",
        ],
        resources: ["*"],
      })
    );

    // Grant access to runtime registry table
    this.agentRuntimeTable.grantReadWriteData(this.runtimeInvokeRole);

    // Grant CodeBuild start permissions
    this.runtimeInvokeRole.addToPolicy(
      new iam.PolicyStatement({
        actions: ["codebuild:StartBuild", "codebuild:BatchGetBuilds"],
        resources: [this.agentBuildProject.projectArn],
      })
    );

    // Grant IAM PassRole for runtime execution role
    this.runtimeInvokeRole.addToPolicy(
      new iam.PolicyStatement({
        actions: ["iam:PassRole"],
        resources: [this.runtimeExecutionRole.roleArn],
      })
    );

    // Outputs
    new CfnOutput(this, "AgentContainerRepositoryUri", {
      value: this.agentContainerRepository.repositoryUri,
      description: "ECR repository URI for agent containers",
      exportName: `${props.envPrefix}AgentContainerRepositoryUri`,
    });

    new CfnOutput(this, "AgentRuntimeTableName", {
      value: this.agentRuntimeTable.tableName,
      description: "DynamoDB table for agent runtime registry",
      exportName: `${props.envPrefix}AgentRuntimeTableName`,
    });

    if (this.agentMemoryTable) {
      new CfnOutput(this, "AgentMemoryTableName", {
        value: this.agentMemoryTable.tableName,
        description: "DynamoDB table for agent memory",
        exportName: `${props.envPrefix}AgentMemoryTableName`,
      });
    }

    new CfnOutput(this, "AgentBuildProjectName", {
      value: this.agentBuildProject.projectName,
      description: "CodeBuild project for building agent containers",
      exportName: `${props.envPrefix}AgentBuildProjectName`,
    });

    new CfnOutput(this, "RuntimeExecutionRoleArn", {
      value: this.runtimeExecutionRole.roleArn,
      description: "IAM role ARN for AgentCore runtime execution",
      exportName: `${props.envPrefix}RuntimeExecutionRoleArn`,
    });
  }
}
