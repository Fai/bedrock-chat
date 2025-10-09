import * as cdk from 'aws-cdk-lib';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as rds from 'aws-cdk-lib/aws-rds';
import * as secretsmanager from 'aws-cdk-lib/aws-secretsmanager';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as cr from 'aws-cdk-lib/custom-resources';
import { Construct } from 'constructs';

export interface AuroraKnowledgeBaseProps {
  vpc: ec2.IVpc;
  bedrockKbRole: iam.IRole;
  envName: string;
  minCapacity?: number;  // Default: 0.5 ACU
  maxCapacity?: number;  // Default: 4 ACU
}

export class AuroraKnowledgeBase extends Construct {
  public readonly cluster: rds.DatabaseCluster;
  public readonly secret: secretsmanager.ISecret;
  public readonly clusterArn: string;

  constructor(scope: Construct, id: string, props: AuroraKnowledgeBaseProps) {
    super(scope, id);

    // Create security group for Aurora
    const auroraSecurityGroup = new ec2.SecurityGroup(this, 'AuroraSecurityGroup', {
      vpc: props.vpc,
      description: 'Security group for Aurora KB cluster',
      allowAllOutbound: false,
    });

    // Create database credentials secret
    const databaseCredentialsSecret = new secretsmanager.Secret(this, 'DBCredentials', {
      secretName: `${props.envName}-bedrock-kb-aurora-credentials`,
      generateSecretString: {
        secretStringTemplate: JSON.stringify({ username: 'bedrock_admin' }),
        generateStringKey: 'password',
        excludePunctuation: true,
        includeSpace: false,
        passwordLength: 32,
      },
    });

    // Create Aurora Serverless v2 cluster
    const cluster = new rds.DatabaseCluster(this, 'AuroraCluster', {
      engine: rds.DatabaseClusterEngine.auroraPostgres({
        version: rds.AuroraPostgresEngineVersion.VER_16_4,
      }),
      credentials: rds.Credentials.fromSecret(databaseCredentialsSecret),
      defaultDatabaseName: 'bedrock_kb',
      vpc: props.vpc,
      vpcSubnets: {
        subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS,
      },
      securityGroups: [auroraSecurityGroup],
      writer: rds.ClusterInstance.serverlessV2('writer', {
        publiclyAccessible: false,
        enablePerformanceInsights: true,
        performanceInsightRetention: rds.PerformanceInsightRetention.DEFAULT, // 7 days
      }),
      serverlessV2MinCapacity: props.minCapacity ?? 0.5,
      serverlessV2MaxCapacity: props.maxCapacity ?? 4,
      backup: {
        retention: cdk.Duration.days(7),
        preferredWindow: '03:00-04:00',
      },
      preferredMaintenanceWindow: 'sun:04:00-sun:05:00',
      storageEncrypted: true,
      cloudwatchLogsExports: ['postgresql'],
      enableDataApi: true,  // Enable RDS Data API
      removalPolicy: cdk.RemovalPolicy.SNAPSHOT,
      deletionProtection: true,
    });

    // Grant Bedrock KB role access to cluster
    cluster.grantDataApiAccess(props.bedrockKbRole);
    databaseCredentialsSecret.grantRead(props.bedrockKbRole);

    // Custom resource to initialize database schema
    const dbInitFunction = new lambda.Function(this, 'DBInitFunction', {
      runtime: lambda.Runtime.PYTHON_3_12,
      handler: 'index.handler',
      code: lambda.Code.fromInline(`
import json
import boto3
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

rds_data = boto3.client('rds-data')

def handler(event, context):
    logger.info(f"Event: {json.dumps(event)}")
    
    if event['RequestType'] == 'Delete':
        return {'PhysicalResourceId': 'db-init'}

    cluster_arn = event['ResourceProperties']['ClusterArn']
    secret_arn = event['ResourceProperties']['SecretArn']
    database = event['ResourceProperties']['Database']

    # SQL commands to initialize schema
    sql_commands = [
        "CREATE EXTENSION IF NOT EXISTS vector;",
        "CREATE SCHEMA IF NOT EXISTS bedrock_integration;",
        """
        CREATE TABLE IF NOT EXISTS bedrock_integration.kb_vectors (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            embedding vector(1024) NOT NULL,
            chunks TEXT NOT NULL,
            metadata JSONB DEFAULT '{}'::jsonb,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_kb_vectors_embedding
        ON bedrock_integration.kb_vectors
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64);
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_kb_vectors_chunks
        ON bedrock_integration.kb_vectors
        USING GIN (to_tsvector('english', chunks));
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_kb_vectors_metadata
        ON bedrock_integration.kb_vectors
        USING GIN (metadata);
        """,
        """
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """,
        """
        DROP TRIGGER IF EXISTS update_kb_vectors_updated_at ON bedrock_integration.kb_vectors;
        CREATE TRIGGER update_kb_vectors_updated_at
            BEFORE UPDATE ON bedrock_integration.kb_vectors
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
        """,
    ]

    for i, sql in enumerate(sql_commands):
        try:
            logger.info(f"Executing SQL command {i+1}/{len(sql_commands)}")
            response = rds_data.execute_statement(
                resourceArn=cluster_arn,
                secretArn=secret_arn,
                database=database,
                sql=sql
            )
            logger.info(f"SQL command {i+1} executed successfully")
        except Exception as e:
            logger.error(f"Error executing SQL command {i+1}: {e}")
            if event['RequestType'] == 'Create':
                raise

    logger.info("Database initialization completed successfully")
    return {'PhysicalResourceId': 'db-init'}
      `),
      timeout: cdk.Duration.minutes(5),
      vpc: props.vpc,
      vpcSubnets: {
        subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS,
      },
    });

    // Grant Lambda permissions
    cluster.grantDataApiAccess(dbInitFunction);
    databaseCredentialsSecret.grantRead(dbInitFunction);

    // Create custom resource
    const dbInitProvider = new cr.Provider(this, 'DBInitProvider', {
      onEventHandler: dbInitFunction,
    });

    new cdk.CustomResource(this, 'DBInitResource', {
      serviceToken: dbInitProvider.serviceToken,
      properties: {
        ClusterArn: cluster.clusterArn,
        SecretArn: databaseCredentialsSecret.secretArn,
        Database: 'bedrock_kb',
      },
    });

    this.cluster = cluster;
    this.secret = databaseCredentialsSecret;
    this.clusterArn = cluster.clusterArn;

    // Outputs
    new cdk.CfnOutput(this, 'AuroraClusterArn', {
      value: cluster.clusterArn,
      description: 'Aurora cluster ARN for Bedrock KB',
    });

    new cdk.CfnOutput(this, 'AuroraSecretArn', {
      value: databaseCredentialsSecret.secretArn,
      description: 'Aurora credentials secret ARN',
    });

    new cdk.CfnOutput(this, 'AuroraClusterEndpoint', {
      value: cluster.clusterEndpoint.hostname,
      description: 'Aurora cluster endpoint',
    });

    new cdk.CfnOutput(this, 'AuroraDatabaseName', {
      value: 'bedrock_kb',
      description: 'Aurora database name',
    });

    new cdk.CfnOutput(this, 'AuroraTableName', {
      value: 'bedrock_integration.kb_vectors',
      description: 'Aurora table name for vectors',
    });
  }
}
