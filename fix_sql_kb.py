#!/usr/bin/env python3
"""
Script to manually create SQL Knowledge Base for an existing bot.
This is a temporary fix until the bot creation flow is updated.
"""

import os
import sys
import boto3
import json

# Configuration - UPDATE THESE VALUES
BOT_ID = "your-bot-id-here"  # Replace with your bot ID
WORKGROUP_NAME = "your-workgroup-name"  # Replace with your Redshift workgroup name
WORKGROUP_ARN = "arn:aws:redshift-serverless:us-east-1:123456789012:workgroup/your-workgroup"
DATABASE_NAME = "your_database"
TABLE_NAME = "your_table"
SECRET_ARN = "arn:aws:secretsmanager:us-east-1:123456789012:secret:your-secret"
BEDROCK_KB_ROLE_ARN = os.getenv("BEDROCK_KB_ROLE_ARN")  # From environment or CDK output
EMBEDDING_MODEL_ARN = "arn:aws:bedrock:us-east-1::foundation-model/amazon.titan-embed-text-v2:0"

# Field mapping (columns in your Redshift table)
FIELD_MAPPING = {
    "id": "id",
    "content": "content",
    "metadata": "metadata"
}

def create_sql_knowledge_base():
    """Create Bedrock Knowledge Base with Redshift data source"""

    if not BEDROCK_KB_ROLE_ARN:
        print("ERROR: BEDROCK_KB_ROLE_ARN environment variable is not set")
        print("Get it from CDK outputs: aws cloudformation describe-stacks --stack-name YourStackName")
        sys.exit(1)

    client = boto3.client('bedrock-agent')

    try:
        print(f"Creating SQL Knowledge Base for bot {BOT_ID}...")

        # Create Knowledge Base
        response = client.create_knowledge_base(
            name=f"sql-kb-{BOT_ID}",
            description=f"SQL Knowledge Base for bot {BOT_ID}",
            roleArn=BEDROCK_KB_ROLE_ARN,
            knowledgeBaseConfiguration={
                'type': 'VECTOR',
                'vectorKnowledgeBaseConfiguration': {
                    'embeddingModelArn': EMBEDDING_MODEL_ARN
                },
            },
            storageConfiguration={
                'type': 'REDSHIFT',
                'redshiftConfiguration': {
                    'workgroupName': WORKGROUP_NAME,
                    'databaseName': DATABASE_NAME,
                    'tableName': TABLE_NAME,
                    'credentialsSecretArn': SECRET_ARN,
                    'fieldMapping': {
                        'primaryKeyField': FIELD_MAPPING['id'],
                        'textField': FIELD_MAPPING['content'],
                        'metadataField': FIELD_MAPPING['metadata'],
                    },
                },
            },
        )

        kb_id = response['knowledgeBase']['knowledgeBaseId']
        print(f"✅ Knowledge Base created successfully: {kb_id}")

        # Get data source ID
        data_sources = client.list_data_sources(knowledgeBaseId=kb_id)
        if data_sources.get('dataSourceSummaries'):
            data_source_id = data_sources['dataSourceSummaries'][0]['dataSourceId']
            print(f"✅ Data Source ID: {data_source_id}")

            # Start ingestion job
            ingestion_response = client.start_ingestion_job(
                knowledgeBaseId=kb_id,
                dataSourceId=data_source_id
            )
            ingestion_job_id = ingestion_response['ingestionJob']['ingestionJobId']
            print(f"✅ Ingestion job started: {ingestion_job_id}")
            print(f"\nNow update your bot in DynamoDB:")
            print(f"  - Set bedrock_knowledge_base.knowledge_base_id = '{kb_id}'")
            print(f"  - Set bedrock_knowledge_base.data_source_ids = ['{data_source_id}']")
            print(f"\nOr use the AWS Console:")
            print(f"  1. Go to DynamoDB")
            print(f"  2. Find your BOT_TABLE")
            print(f"  3. Update the bot item with PK=BOT#{BOT_ID}")
            print(f"  4. Set BedrockKnowledgeBase.KnowledgeBaseId = '{kb_id}'")

        return kb_id

    except Exception as e:
        print(f"❌ Error creating Knowledge Base: {e}")
        sys.exit(1)

if __name__ == "__main__":
    print("=" * 60)
    print("SQL Knowledge Base Creation Script")
    print("=" * 60)
    print(f"\nConfiguration:")
    print(f"  Bot ID: {BOT_ID}")
    print(f"  Workgroup: {WORKGROUP_NAME}")
    print(f"  Database: {DATABASE_NAME}")
    print(f"  Table: {TABLE_NAME}")
    print(f"  KB Role: {BEDROCK_KB_ROLE_ARN or 'NOT SET'}")
    print()

    if BOT_ID == "your-bot-id-here":
        print("⚠️  Please update the configuration values in this script first!")
        print("Edit the variables at the top of the file.")
        sys.exit(1)

    kb_id = create_sql_knowledge_base()
    print(f"\n✅ Done! Knowledge Base ID: {kb_id}")
    print("\nNext steps:")
    print("  1. Wait for ingestion to complete (5-15 minutes)")
    print("  2. Update your bot's knowledge_base_id in DynamoDB")
    print("  3. Test querying through the chat interface")
