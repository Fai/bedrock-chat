"""SQL Knowledge Base Schema Synchronization.

This module automatically syncs table schemas from Redshift to Bedrock Knowledge Bases.
It queries the Redshift information schema and updates the KB configuration.
"""

import logging
import time
from typing import Any

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def get_redshift_schema(
    workgroup_name: str,
    database: str,
    schema: str = "public",
    region: str = "us-east-1"
) -> dict[str, list[dict[str, str]]]:
    """
    Query Redshift to get table and column information from information_schema.

    Args:
        workgroup_name: Redshift Serverless workgroup name
        database: Database name
        schema: Schema name (default: public)
        region: AWS region

    Returns:
        Dictionary mapping table names to lists of column definitions
    """
    redshift_data = boto3.client('redshift-data', region_name=region)

    # Query to get all tables and their columns
    sql = f"""
    SELECT
        t.table_name,
        c.column_name,
        c.data_type,
        c.ordinal_position,
        CASE
            WHEN c.column_name LIKE '%id' OR c.column_name LIKE '%ID' THEN 'Unique identifier'
            WHEN c.column_name LIKE '%name' OR c.column_name LIKE '%Name' THEN 'Name or title'
            WHEN c.column_name LIKE '%price' OR c.column_name LIKE '%cost' THEN 'Price or cost value'
            WHEN c.column_name LIKE '%date' OR c.column_name LIKE '%time' THEN 'Date or timestamp'
            WHEN c.column_name LIKE '%desc%' THEN 'Description'
            ELSE 'Column: ' || c.column_name
        END as inferred_description
    FROM information_schema.tables t
    JOIN information_schema.columns c
        ON t.table_name = c.table_name
        AND t.table_schema = c.table_schema
    WHERE t.table_schema = '{schema}'
        AND t.table_type = 'BASE TABLE'
    ORDER BY t.table_name, c.ordinal_position
    """

    logger.info(f"Querying Redshift schema for database={database}, schema={schema}")

    try:
        # Execute query
        response = redshift_data.execute_statement(
            WorkgroupName=workgroup_name,
            Database=database,
            Sql=sql
        )

        statement_id = response['Id']
        logger.info(f"Query submitted with ID: {statement_id}")

        # Wait for query to complete
        while True:
            status_response = redshift_data.describe_statement(Id=statement_id)
            status = status_response['Status']

            if status == 'FINISHED':
                break
            elif status == 'FAILED':
                error = status_response.get('Error', 'Unknown error')
                raise Exception(f"Query failed: {error}")
            elif status == 'ABORTED':
                raise Exception("Query was aborted")

            logger.info(f"Query status: {status}, waiting...")
            time.sleep(1)

        # Get results
        result = redshift_data.get_statement_result(Id=statement_id)

        # Parse results into schema structure
        tables: dict[str, list[dict[str, str]]] = {}

        for record in result['Records']:
            table_name = record[0]['stringValue']
            column_name = record[1]['stringValue']
            data_type = record[2]['stringValue']
            inferred_desc = record[4]['stringValue']

            if table_name not in tables:
                tables[table_name] = []

            tables[table_name].append({
                'name': column_name,
                'data_type': data_type,
                'description': inferred_desc
            })

        logger.info(f"Found {len(tables)} tables with schema information")
        return tables

    except ClientError as e:
        logger.error(f"Error querying Redshift schema: {e}")
        raise


def update_kb_schema(
    knowledge_base_id: str,
    tables_schema: dict[str, list[dict[str, str]]],
    region: str = "us-east-1"
) -> None:
    """
    Update Bedrock Knowledge Base configuration with table schema.

    Args:
        knowledge_base_id: Bedrock Knowledge Base ID
        tables_schema: Dictionary of table schemas from get_redshift_schema()
        region: AWS region
    """
    bedrock_agent = boto3.client('bedrock-agent', region_name=region)

    try:
        # Get current KB configuration
        logger.info(f"Fetching current configuration for KB {knowledge_base_id}")
        kb_response = bedrock_agent.get_knowledge_base(knowledgeBaseId=knowledge_base_id)
        kb = kb_response['knowledgeBase']

        # Build table configuration for Bedrock
        tables_config = []

        for table_name, columns in tables_schema.items():
            columns_config = [
                {
                    'name': col['name'],
                    'description': col['description'],
                    'inclusion': 'INCLUDE'
                }
                for col in columns
            ]

            tables_config.append({
                'name': table_name,
                'description': f"Table: {table_name}",
                'inclusion': 'INCLUDE',
                'columns': columns_config
            })

        # Get existing configuration
        kb_config = kb['knowledgeBaseConfiguration']
        sql_config = kb_config['sqlKnowledgeBaseConfiguration']
        rds_config = sql_config['rdsConfiguration']
        query_gen_config = rds_config.get('queryGenerationConfiguration', {})

        # Update generationContext with new tables
        generation_context = query_gen_config.get('generationContext', {})
        generation_context['tables'] = tables_config

        # Preserve existing curated queries
        if 'curatedQueries' not in generation_context:
            generation_context['curatedQueries'] = []

        query_gen_config['generationContext'] = generation_context

        # Set default timeout if not present
        if 'executionTimeoutSeconds' not in query_gen_config:
            query_gen_config['executionTimeoutSeconds'] = 60

        rds_config['queryGenerationConfiguration'] = query_gen_config

        # Update KB
        logger.info(f"Updating KB {knowledge_base_id} with {len(tables_config)} tables")

        bedrock_agent.update_knowledge_base(
            knowledgeBaseId=knowledge_base_id,
            name=kb['name'],
            roleArn=kb['roleArn'],
            knowledgeBaseConfiguration={
                'type': 'SQL',
                'sqlKnowledgeBaseConfiguration': sql_config
            }
        )

        logger.info(f"Successfully updated KB schema with {len(tables_config)} tables")

    except ClientError as e:
        logger.error(f"Error updating KB configuration: {e}")
        raise


def sync_sql_kb_schema(
    knowledge_base_id: str,
    workgroup_name: str,
    database: str,
    schema: str = "public",
    region: str = "us-east-1"
) -> None:
    """
    Main function to sync Redshift schema to Bedrock Knowledge Base.

    Args:
        knowledge_base_id: Bedrock Knowledge Base ID
        workgroup_name: Redshift Serverless workgroup name
        database: Database name
        schema: Schema name (default: public)
        region: AWS region
    """
    logger.info(f"Starting schema sync for KB {knowledge_base_id}")

    # Step 1: Get schema from Redshift
    tables_schema = get_redshift_schema(
        workgroup_name=workgroup_name,
        database=database,
        schema=schema,
        region=region
    )

    if not tables_schema:
        logger.warning("No tables found in Redshift schema")
        return

    # Step 2: Update KB configuration
    update_kb_schema(
        knowledge_base_id=knowledge_base_id,
        tables_schema=tables_schema,
        region=region
    )

    logger.info("Schema sync completed successfully")


if __name__ == "__main__":
    # Example usage
    import sys

    if len(sys.argv) < 4:
        print("Usage: python sql_kb_schema_sync.py <kb_id> <workgroup_name> <database>")
        sys.exit(1)

    kb_id = sys.argv[1]
    workgroup = sys.argv[2]
    db = sys.argv[3]

    sync_sql_kb_schema(
        knowledge_base_id=kb_id,
        workgroup_name=workgroup,
        database=db
    )
