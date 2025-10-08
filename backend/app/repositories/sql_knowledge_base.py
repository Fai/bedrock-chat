"""
SQL Knowledge Base Repository

This module handles creation, querying, and management of SQL-type Knowledge Bases
that connect to Amazon Redshift Serverless databases.
"""

import logging
import os
from typing import Any

from app.repositories.models.custom_bot_kb import SqlDatabaseConfigModel
from app.routes.schemas.bot_kb import SqlQueryOutput
from app.utils import get_bedrock_agent_client, get_bedrock_agent_runtime_client

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def create_sql_knowledge_base(
    bot_id: str,
    sql_config: SqlDatabaseConfigModel,
    kb_name: str,
) -> tuple[str, str]:
    """
    Create Bedrock Knowledge Base with Redshift data source

    Args:
        bot_id: Bot identifier
        sql_config: Redshift database configuration
        kb_name: Human-readable knowledge base name

    Returns:
        tuple: (knowledge_base_id, data_source_id)

    Raises:
        Exception: If KB creation fails
    """
    client = get_bedrock_agent_client()
    bedrock_kb_role_arn = os.getenv("BEDROCK_KB_ROLE_ARN")

    if not bedrock_kb_role_arn:
        raise ValueError("BEDROCK_KB_ROLE_ARN environment variable is not set")

    try:
        logger.info(f"Creating SQL Knowledge Base for bot {bot_id}")

        # Create Knowledge Base with Redshift data source
        response = client.create_knowledge_base(
            name=kb_name,
            description=f"SQL Knowledge Base for bot {bot_id}",
            roleArn=bedrock_kb_role_arn,
            knowledgeBaseConfiguration={
                "type": "VECTOR",
                "vectorKnowledgeBaseConfiguration": {
                    "embeddingModelArn": sql_config.embedding_model_arn
                },
            },
            storageConfiguration={
                "type": "RDS",
                "rdsConfiguration": {
                    "resourceArn": sql_config.workgroup_arn,
                    "databaseName": sql_config.database_name,
                    "tableName": sql_config.table_name,
                    "credentialsSecretArn": sql_config.secret_arn,
                    "fieldMapping": {
                        "primaryKeyField": sql_config.field_mapping.get("id", "id"),
                        "vectorField": sql_config.field_mapping.get("embedding", "embedding"),
                        "textField": sql_config.field_mapping.get(
                            "content", "content"
                        ),
                        "metadataField": sql_config.field_mapping.get(
                            "metadata", "metadata"
                        ),
                    },
                },
            },
        )

        kb_id = response["knowledgeBase"]["knowledgeBaseId"]
        logger.info(f"Successfully created KB {kb_id}")

        # Get the data source ID from the knowledge base
        kb_details = client.get_knowledge_base(knowledgeBaseId=kb_id)
        data_sources = client.list_data_sources(knowledgeBaseId=kb_id)

        data_source_id = None
        if data_sources.get("dataSourceSummaries"):
            data_source_id = data_sources["dataSourceSummaries"][0]["dataSourceId"]

        logger.info(f"KB {kb_id} has data source {data_source_id}")

        # Start ingestion job
        if data_source_id:
            try:
                ingestion_response = client.start_ingestion_job(
                    knowledgeBaseId=kb_id, dataSourceId=data_source_id
                )
                ingestion_job_id = ingestion_response["ingestionJob"]["ingestionJobId"]
                logger.info(
                    f"Started ingestion job {ingestion_job_id} for KB {kb_id}"
                )
            except Exception as e:
                logger.warning(f"Could not start ingestion job: {e}")

        return (kb_id, data_source_id or "")

    except Exception as e:
        logger.error(f"Failed to create SQL Knowledge Base: {e}")
        raise


def get_ingestion_job_status(
    knowledge_base_id: str, data_source_id: str
) -> dict[str, Any]:
    """
    Get the status of the most recent ingestion job

    Args:
        knowledge_base_id: Knowledge Base ID
        data_source_id: Data Source ID

    Returns:
        dict: Ingestion job status information
    """
    client = get_bedrock_agent_client()

    try:
        response = client.list_ingestion_jobs(
            knowledgeBaseId=knowledge_base_id,
            dataSourceId=data_source_id,
            maxResults=1,
        )

        if not response.get("ingestionJobSummaries"):
            return {
                "status": "NOT_STARTED",
                "ingestion_job_id": None,
                "ingestion_job_status": None,
            }

        job = response["ingestionJobSummaries"][0]

        return {
            "status": "IN_PROGRESS" if job["status"] != "COMPLETE" else "ACTIVE",
            "ingestion_job_id": job["ingestionJobId"],
            "ingestion_job_status": job["status"],
            "started_at": job.get("startedAt"),
            "updated_at": job.get("updatedAt"),
            "statistics": job.get("statistics", {}),
        }

    except Exception as e:
        logger.error(f"Failed to get ingestion job status: {e}")
        return {
            "status": "UNKNOWN",
            "ingestion_job_id": None,
            "ingestion_job_status": None,
            "error": str(e),
        }


def query_sql_knowledge_base(
    knowledge_base_id: str, query: str, user_id: str, max_results: int = 10
) -> SqlQueryOutput:
    """
    Query SQL Knowledge Base with natural language

    Args:
        knowledge_base_id: Knowledge Base ID
        query: Natural language query
        user_id: User identifier (for logging)
        max_results: Maximum number of results

    Returns:
        SqlQueryOutput: Query results with answer, citations, and SQL query
    """
    client = get_bedrock_agent_runtime_client()
    default_model_arn = os.getenv(
        "DEFAULT_MODEL_ARN",
        "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-5-sonnet-20241022-v2:0",
    )

    try:
        logger.info(f"Querying KB {knowledge_base_id} for user {user_id}: {query}")

        response = client.retrieve_and_generate(
            input={"text": query},
            retrieveAndGenerateConfiguration={
                "type": "KNOWLEDGE_BASE",
                "knowledgeBaseConfiguration": {
                    "knowledgeBaseId": knowledge_base_id,
                    "modelArn": default_model_arn,
                    "retrievalConfiguration": {
                        "vectorSearchConfiguration": {"numberOfResults": max_results}
                    },
                },
            },
        )

        answer = response.get("output", {}).get("text", "")
        citations = response.get("citations", [])

        # Extract SQL query from citations (if available)
        sql_query = extract_sql_from_citations(citations)

        # Extract structured results from citations
        results = extract_results_from_citations(citations)

        logger.info(f"Query successful, generated answer length: {len(answer)}")

        return SqlQueryOutput(
            answer=answer, citations=citations, sql_query=sql_query, results=results
        )

    except Exception as e:
        logger.error(f"Failed to query SQL Knowledge Base: {e}")
        raise


def extract_sql_from_citations(citations: list[dict]) -> str | None:
    """
    Extract SQL query from Bedrock KB citations

    Args:
        citations: List of citation objects from Bedrock

    Returns:
        str | None: Extracted SQL query or None
    """
    for citation in citations:
        retrieved_references = citation.get("retrievedReferences", [])
        for reference in retrieved_references:
            metadata = reference.get("metadata", {})
            if "sql_query" in metadata:
                return metadata["sql_query"]

            # Sometimes SQL is in the content
            content = reference.get("content", {}).get("text", "")
            if "SELECT" in content.upper() and "FROM" in content.upper():
                return content

    return None


def extract_results_from_citations(citations: list[dict]) -> list[dict] | None:
    """
    Extract structured query results from citations

    Args:
        citations: List of citation objects from Bedrock

    Returns:
        list[dict] | None: Structured results or None
    """
    results = []

    for citation in citations:
        retrieved_references = citation.get("retrievedReferences", [])
        for reference in retrieved_references:
            # Extract metadata as structured result
            metadata = reference.get("metadata", {})
            if metadata:
                results.append(metadata)

    return results if results else None


def delete_sql_knowledge_base(knowledge_base_id: str) -> bool:
    """
    Delete a SQL Knowledge Base

    Args:
        knowledge_base_id: Knowledge Base ID to delete

    Returns:
        bool: True if deletion successful
    """
    client = get_bedrock_agent_client()

    try:
        logger.info(f"Deleting SQL Knowledge Base {knowledge_base_id}")

        client.delete_knowledge_base(knowledgeBaseId=knowledge_base_id)

        logger.info(f"Successfully deleted KB {knowledge_base_id}")
        return True

    except Exception as e:
        logger.error(f"Failed to delete SQL Knowledge Base: {e}")
        return False
