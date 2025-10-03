import {
  RemovalPolicy,
  Duration,
  CfnOutput,
} from "aws-cdk-lib";
import {
  Vpc,
  SecurityGroup,
  Port,
  SubnetType,
} from "aws-cdk-lib/aws-ec2";
import {
  CfnWorkgroup,
  CfnNamespace,
} from "aws-cdk-lib/aws-redshiftserverless";
import {
  Secret,
  SecretStringGenerator,
} from "aws-cdk-lib/aws-secretsmanager";
import {
  Role,
  ServicePrincipal,
  ManagedPolicy,
  PolicyStatement,
  Effect,
} from "aws-cdk-lib/aws-iam";
import {
  Function,
  Runtime,
  Code,
  Architecture,
} from "aws-cdk-lib/aws-lambda";
import {
  Bucket,
  BucketEncryption,
  BlockPublicAccess,
} from "aws-cdk-lib/aws-s3";
import { Construct } from "constructs";

export interface SqlDatabaseProps {
  readonly vpc: Vpc;
  readonly envPrefix: string;
  readonly bedrockRegion: string;
}

export class SqlDatabase extends Construct {
  public readonly namespace: CfnNamespace;
  public readonly workgroup: CfnWorkgroup;
  public readonly secret: Secret;
  public readonly securityGroup: SecurityGroup;
  public readonly initializerFunction: Function;
  public readonly dataBucket: Bucket;
  public readonly bedrockRole: Role;

  constructor(scope: Construct, id: string, props: SqlDatabaseProps) {
    super(scope, id);

    const { vpc, envPrefix, bedrockRegion } = props;
    const sepHyphen = envPrefix ? "-" : "";

    // Create security group for Redshift Serverless
    this.securityGroup = new SecurityGroup(this, "RedshiftSecurityGroup", {
      vpc,
      description: "Security group for SQL Knowledge Base Redshift cluster",
      allowAllOutbound: false,
    });

    // Allow HTTPS outbound for AWS services
    this.securityGroup.addEgressRule(
      SecurityGroup.anyIpv4(),
      Port.tcp(443),
      "Allow HTTPS outbound for AWS services"
    );

    // Allow Redshift connections from within the security group
    this.securityGroup.addIngressRule(
      this.securityGroup,
      Port.tcp(5439),
      "Allow Redshift connections from within security group"
    );

    // Create S3 bucket for data staging and unloading
    this.dataBucket = new Bucket(this, "RedshiftDataBucket", {
      bucketName: `${envPrefix}${sepHyphen}redshift-kb-data-${this.node.addr.slice(-8)}`,
      encryption: BucketEncryption.S3_MANAGED,
      blockPublicAccess: BlockPublicAccess.BLOCK_ALL,
      enforceSSL: true,
      removalPolicy: RemovalPolicy.DESTROY,
      versioned: false,
    });

    // Create database credentials secret
    this.secret = new Secret(this, "RedshiftSecret", {
      description: "Credentials for SQL Knowledge Base Redshift cluster",
      generateSecretString: {
        secretStringTemplate: JSON.stringify({ 
          username: "kb_admin",
          engine: "redshift-serverless"
        }),
        generateStringKey: "password",
        excludeCharacters: '"@/\\`',
        requireEachIncludedType: true,
        passwordLength: 32,
      },
    });

    // Create IAM role for Redshift to access S3 and other AWS services
    const redshiftServiceRole = new Role(this, "RedshiftServiceRole", {
      assumedBy: new ServicePrincipal("redshift.amazonaws.com"),
      description: "Service role for Redshift Serverless to access S3 and other AWS services",
      managedPolicies: [
        ManagedPolicy.fromAwsManagedPolicyName("AmazonS3ReadOnlyAccess"),
      ],
    });

    // Grant S3 bucket access to Redshift service role
    this.dataBucket.grantReadWrite(redshiftServiceRole);

    // Create Redshift Serverless namespace
    this.namespace = new CfnNamespace(this, "RedshiftNamespace", {
      namespaceName: `${envPrefix}${sepHyphen}kb-namespace`,
      adminUsername: "kb_admin",
      adminUserPassword: this.secret.secretValueFromJson("password").unsafeUnwrap(),
      dbName: "knowledge_base",
      defaultIamRoleArn: redshiftServiceRole.roleArn,
      iamRoles: [redshiftServiceRole.roleArn],
      kmsKeyId: "alias/aws/redshift", // Use default AWS managed key
      logExports: ["userlog", "connectionlog", "useractivitylog"],
    });

    // Get private subnet IDs for the workgroup
    const privateSubnets = vpc.privateSubnets.map(subnet => subnet.subnetId);

    // Create Redshift Serverless workgroup
    this.workgroup = new CfnWorkgroup(this, "RedshiftWorkgroup", {
      workgroupName: `${envPrefix}${sepHyphen}kb-workgroup`,
      namespaceName: this.namespace.namespaceName,
      baseCapacity: 8, // Minimum 8 RPU (Redshift Processing Units)
      maxCapacity: 64, // Maximum capacity for auto-scaling
      enhancedVpcRouting: true,
      publiclyAccessible: false,
      subnetIds: privateSubnets,
      securityGroupIds: [this.securityGroup.securityGroupId],
      configParameters: [
        {
          parameterKey: "enable_user_activity_logging",
          parameterValue: "true",
        },
        {
          parameterKey: "query_group",
          parameterValue: "knowledge_base",
        },
      ],
    });

    // Ensure workgroup depends on namespace
    this.workgroup.addDependency(this.namespace);

    // Create IAM role for Bedrock Knowledge Base to access Redshift
    this.bedrockRole = new Role(this, "BedrockKnowledgeBaseRedshiftRole", {
      assumedBy: new ServicePrincipal("bedrock.amazonaws.com"),
      description: "Role for Bedrock Knowledge Base to access Redshift cluster",
      inlinePolicies: {
        RedshiftDataAccess: new PolicyStatement({
          effect: Effect.ALLOW,
          actions: [
            "redshift-data:BatchExecuteStatement",
            "redshift-data:CancelStatement",
            "redshift-data:DescribeStatement",
            "redshift-data:DescribeTable",
            "redshift-data:ExecuteStatement",
            "redshift-data:GetStatementResult",
            "redshift-data:ListDatabases",
            "redshift-data:ListSchemas",
            "redshift-data:ListStatements",
            "redshift-data:ListTables",
          ],
          resources: ["*"], // Redshift Data API doesn't support resource-level permissions
        }).document,
        RedshiftServerlessAccess: new PolicyStatement({
          effect: Effect.ALLOW,
          actions: [
            "redshift-serverless:GetWorkgroup",
            "redshift-serverless:GetNamespace",
          ],
          resources: [
            this.workgroup.attrWorkgroupWorkgroupArn,
            this.namespace.attrNamespaceNamespaceArn,
          ],
        }).document,
      },
    });

    // Add permissions for the database secret
    this.bedrockRole.addToPolicy(
      new PolicyStatement({
        effect: Effect.ALLOW,
        actions: [
          "secretsmanager:GetSecretValue",
          "secretsmanager:DescribeSecret",
        ],
        resources: [this.secret.secretArn],
      })
    );

    // Create Lambda function for database initialization
    this.initializerFunction = new Function(this, "RedshiftInitializer", {
      runtime: Runtime.PYTHON_3_11,
      handler: "index.handler",
      architecture: Architecture.ARM_64,
      timeout: Duration.minutes(10),
      vpc,
      vpcSubnets: {
        subnetType: SubnetType.PRIVATE_WITH_EGRESS,
      },
      securityGroups: [this.securityGroup],
      code: Code.fromInline(`
import json
import boto3
import time
import logging
from typing import Dict, Any

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda function to initialize Redshift database schema for Knowledge Base.
    """
    try:
        # Get parameters from environment
        workgroup_name = "${this.workgroup.workgroupName}"
        database_name = "knowledge_base"
        secret_arn = "${this.secret.secretArn}"
        
        # Initialize Redshift Data API client
        redshift_data = boto3.client('redshift-data')
        secrets_client = boto3.client('secretsmanager')
        
        # Get database credentials
        secret_response = secrets_client.get_secret_value(SecretId=secret_arn)
        secret_data = json.loads(secret_response['SecretString'])
        username = secret_data['username']
        
        logger.info(f"Initializing Redshift database schema for workgroup: {workgroup_name}")
        
        # Function to execute SQL and wait for completion
        def execute_sql(sql: str, description: str) -> None:
            logger.info(f"Executing: {description}")
            response = redshift_data.execute_statement(
                WorkgroupName=workgroup_name,
                Database=database_name,
                DbUser=username,
                Sql=sql
            )
            
            statement_id = response['Id']
            logger.info(f"Statement ID: {statement_id}")
            
            # Wait for completion
            while True:
                result = redshift_data.describe_statement(Id=statement_id)
                status = result['Status']
                
                if status == 'FINISHED':
                    logger.info(f"Statement completed successfully: {description}")
                    break
                elif status in ['FAILED', 'ABORTED']:
                    error_msg = result.get('Error', 'Unknown error')
                    logger.error(f"Statement failed: {description} - {error_msg}")
                    raise Exception(f"SQL execution failed: {error_msg}")
                else:
                    logger.info(f"Statement status: {status}, waiting...")
                    time.sleep(2)
        
        # Create schema for knowledge base tables
        execute_sql(
            "CREATE SCHEMA IF NOT EXISTS knowledge_base;",
            "Creating knowledge_base schema"
        )
        
        # Create table for storing knowledge base metadata
        execute_sql("""
            CREATE TABLE IF NOT EXISTS knowledge_base.kb_metadata (
                kb_id VARCHAR(255) PRIMARY KEY,
                name VARCHAR(500) NOT NULL,
                description VARCHAR(MAX),
                schema_name VARCHAR(255) NOT NULL,
                table_names VARCHAR(MAX), -- JSON array as string
                query_templates VARCHAR(MAX), -- JSON object as string
                created_at TIMESTAMP DEFAULT GETDATE(),
                updated_at TIMESTAMP DEFAULT GETDATE(),
                created_by VARCHAR(255),
                status VARCHAR(50) DEFAULT 'active'
            );
        """, "Creating kb_metadata table")
        
        # Create table for storing custom schemas
        execute_sql("""
            CREATE TABLE IF NOT EXISTS knowledge_base.custom_schemas (
                schema_id VARCHAR(255) PRIMARY KEY,
                kb_id VARCHAR(255) REFERENCES knowledge_base.kb_metadata(kb_id),
                schema_definition VARCHAR(MAX) NOT NULL, -- JSON as string
                sample_data VARCHAR(MAX), -- JSON as string
                created_at TIMESTAMP DEFAULT GETDATE()
            );
        """, "Creating custom_schemas table")
        
        # Create table for query templates
        execute_sql("""
            CREATE TABLE IF NOT EXISTS knowledge_base.query_templates (
                template_id VARCHAR(255) PRIMARY KEY,
                kb_id VARCHAR(255) REFERENCES knowledge_base.kb_metadata(kb_id),
                template_name VARCHAR(255) NOT NULL,
                sql_template VARCHAR(MAX) NOT NULL,
                description VARCHAR(MAX),
                parameters VARCHAR(MAX), -- JSON array as string
                created_at TIMESTAMP DEFAULT GETDATE(),
                created_by VARCHAR(255)
            );
        """, "Creating query_templates table")
        
        logger.info("Database initialization completed successfully")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Redshift database initialization completed successfully'
            })
        }
        
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        }
      `),
      environment: {
        WORKGROUP_NAME: this.workgroup.workgroupName!,
        SECRET_ARN: this.secret.secretArn,
        DATABASE_NAME: "knowledge_base",
      },
    });

    // Grant Lambda permissions to access Redshift Data API
    this.initializerFunction.addToRolePolicy(
      new PolicyStatement({
        effect: Effect.ALLOW,
        actions: [
          "redshift-data:ExecuteStatement",
          "redshift-data:DescribeStatement",
          "redshift-data:GetStatementResult",
          "redshift-serverless:GetWorkgroup",
        ],
        resources: ["*"], // Redshift Data API doesn't support resource-level permissions
      })
    );

    // Grant Lambda permissions to access the database secret
    this.secret.grantRead(this.initializerFunction);

    // Output important values
    new CfnOutput(this, "RedshiftWorkgroupName", {
      value: this.workgroup.workgroupName!,
      description: "Redshift Serverless workgroup name",
      exportName: `${envPrefix}${sepHyphen}RedshiftWorkgroupName`,
    });

    new CfnOutput(this, "RedshiftNamespaceName", {
      value: this.namespace.namespaceName!,
      description: "Redshift Serverless namespace name",
      exportName: `${envPrefix}${sepHyphen}RedshiftNamespaceName`,
    });

    new CfnOutput(this, "RedshiftSecretArn", {
      value: this.secret.secretArn,
      description: "Redshift database secret ARN",
      exportName: `${envPrefix}${sepHyphen}RedshiftSecretArn`,
    });

    new CfnOutput(this, "BedrockKnowledgeBaseRedshiftRoleArn", {
      value: this.bedrockRole.roleArn,
      description: "IAM Role ARN for Bedrock Knowledge Base Redshift integration",
      exportName: `${envPrefix}${sepHyphen}BedrockKnowledgeBaseRedshiftRoleArn`,
    });

    new CfnOutput(this, "RedshiftDataBucketName", {
      value: this.dataBucket.bucketName,
      description: "S3 bucket for Redshift data staging",
      exportName: `${envPrefix}${sepHyphen}RedshiftDataBucketName`,
    });

    new CfnOutput(this, "RedshiftInitializerFunctionArn", {
      value: this.initializerFunction.functionArn,
      description: "Redshift initializer Lambda function ARN",
      exportName: `${envPrefix}${sepHyphen}RedshiftInitializerFunctionArn`,
    });
  }

  /**
   * Allow connections from a security group or construct
   */
  public allowConnectionsFrom(
    other: SecurityGroup | Construct,
    description?: string
  ): void {
    if (other instanceof SecurityGroup) {
      this.securityGroup.addIngressRule(
        other,
        Port.tcp(5439),
        description || "Allow Redshift connections"
      );
    }
  }

  /**
   * Grant Lambda function access to connect to Redshift
   */
  public grantConnect(lambda: Function): void {
    this.allowConnectionsFrom(lambda);
    this.secret.grantRead(lambda);
    
    // Grant Redshift Data API permissions
    lambda.addToRolePolicy(
      new PolicyStatement({
        effect: Effect.ALLOW,
        actions: [
          "redshift-data:ExecuteStatement",
          "redshift-data:DescribeStatement",
          "redshift-data:GetStatementResult",
          "redshift-serverless:GetWorkgroup",
        ],
        resources: ["*"],
      })
    );
  }

  /**
   * Grant S3 bucket access for data staging
   */
  public grantDataBucketAccess(grantee: Role | Function): void {
    this.dataBucket.grantReadWrite(grantee);
  }
}