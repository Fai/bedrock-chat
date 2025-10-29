"""
Aurora PostgreSQL Vector Knowledge Base Repository

This module handles creation, querying, and management of VECTOR-type Knowledge Bases
that use Amazon Aurora PostgreSQL with pgvector extension as the storage backend.
"""

import logging
import os
from typing import Any, Optional

from app.repositories.models.custom_bot_kb import AuroraVectorConfigModel
from app.utils import get_bedrock_agent_client, get_bedrock_agent_runtime_client
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def create_aurora_knowledge_base(
    bot_id: str,
    aurora_config: AuroraVectorConfigModel,
    kb_name: str,
    document_bucket_arn: str,
    document_prefix: str = "",
) -> tuple[str, str | None]:
    """
    Create Bedrock Knowledge Base with Aurora PostgreSQL pgvector storage

    Args:
        bot_id: Bot identifier
        aurora_config: Aurora cluster configuration
        kb_name: Human-readable knowledge base name
        document_bucket_arn: S3 ARN for source documents
        document_prefix: Optional S3 prefix for documents

    Returns:
        tuple: (knowledge_base_id, data_source_id or None)

    Raises:
        ValueError: If required environment variables are missing
        ClientError: If Bedrock API calls fail
    """
    client = get_bedrock_agent_client()
    bedrock_kb_role_arn = os.getenv("BEDROCK_KB_ROLE_ARN")

    if not bedrock_kb_role_arn:
        raise ValueError("BEDROCK_KB_ROLE_ARN environment variable is not set")

    try:
        logger.info(f"Creating Aurora Vector Knowledge Base for bot {bot_id}")
        logger.info(f"  - Cluster ARN: {aurora_config.cluster_arn}")
        logger.info(f"  - Database: {aurora_config.database_name}")
        logger.info(f"  - Table: {aurora_config.table_name}")

        # Map embeddings model to ARN
        embeddings_model_arn = _get_embeddings_model_arn(
            aurora_config.embeddings_model
        )

        # Build chunking configuration
        chunking_config = _build_chunking_configuration(
            aurora_config.chunking_configuration
        )

        # Create Knowledge Base with Aurora RDS storage
        response = client.create_knowledge_base(
            name=kb_name,
            description=f"Aurora Vector Knowledge Base for bot {bot_id}",
            roleArn=bedrock_kb_role_arn,
            knowledgeBaseConfiguration={
                "type": "VECTOR",
                "vectorKnowledgeBaseConfiguration": {
                    "embeddingModelArn": embeddings_model_arn,
                    "embeddingModelConfiguration": {
                        "bedrockEmbeddingModelConfiguration": {
                            "dimensions": aurora_config.embedding_dimensions,
                            "embeddingDataType": "FLOAT32",  # Aurora supports FLOAT32
                        }
                    },
                },
            },
            storageConfiguration={
                "type": "RDS",
                "rdsConfiguration": {
                    "resourceArn": aurora_config.cluster_arn,
                    "credentialsSecretArn": aurora_config.secret_arn,
                    "databaseName": aurora_config.database_name,
                    "tableName": aurora_config.table_name,
                    "fieldMapping": {
                        "primaryKeyField": "id",
                        "vectorField": "embedding",
                        "textField": "chunks",
                        "metadataField": "metadata",
                    },
                },
            },
        )

        kb_id = response["knowledgeBase"]["knowledgeBaseId"]
        logger.info(f"✓ Successfully created Aurora Vector KB: {kb_id}")

        # Create S3 data source for document ingestion
        data_source_id = None
        try:
            data_source_response = client.create_data_source(
                knowledgeBaseId=kb_id,
                name=f"{kb_name}-s3-source",
                description=f"S3 data source for bot {bot_id}",
                dataSourceConfiguration={
                    "type": "S3",
                    "s3Configuration": {
                        "bucketArn": document_bucket_arn,
                        **(
                            {"inclusionPrefixes": [document_prefix]}
                            if document_prefix
                            else {}
                        ),
                    },
                },
                vectorIngestionConfiguration={
                    "chunkingConfiguration": chunking_config,
                    **(
                        {
                            "parsingConfiguration": {
                                "parsingStrategy": "BEDROCK_FOUNDATION_MODEL",
                                "bedrockFoundationModelConfiguration": {
                                    "modelArn": _get_parsing_model_arn(
                                        aurora_config.parsing_model
                                    )
                                },
                            }
                        }
                        if aurora_config.parsing_model != "disabled"
                        else {
                            "parsingConfiguration": {
                                "parsingStrategy": "BEDROCK_DATA_AUTOMATION"
                            }
                        }
                    ),
                },
            )

            data_source_id = data_source_response["dataSource"]["dataSourceId"]
            logger.info(f"✓ Created S3 data source: {data_source_id}")

            # Start ingestion job
            try:
                ingestion_response = client.start_ingestion_job(
                    knowledgeBaseId=kb_id, dataSourceId=data_source_id
                )
                ingestion_job_id = ingestion_response["ingestionJob"]["ingestionJobId"]
                logger.info(f"✓ Started ingestion job: {ingestion_job_id}")
            except ClientError as e:
                logger.warning(f"Could not start ingestion job: {e}")

        except ClientError as e:
            logger.error(f"Failed to create data source: {e}")

        return kb_id, data_source_id

    except ClientError as e:
        logger.error(f"Failed to create Aurora Vector Knowledge Base: {e}")
        logger.error(f"Error Code: {e.response.get('Error', {}).get('Code', 'Unknown')}")
        logger.error(f"Error Message: {e.response.get('Error', {}).get('Message', 'Unknown')}")
        raise


def query_aurora_knowledge_base(
    knowledge_base_id: str,
    query: str,
    max_results: int = 5,
    min_similarity_score: float = 0.0,
    metadata_filter: Optional[dict] = None,
) -> dict:
    """
    Query Aurora Vector Knowledge Base using Bedrock Agent Runtime

    Args:
        knowledge_base_id: Knowledge base ID
        query: Query text
        max_results: Maximum number of results to return
        min_similarity_score: Minimum similarity score threshold
        metadata_filter: Optional metadata filters

    Returns:
        dict: Query results with citations and metadata
    """
    client = get_bedrock_agent_runtime_client()

    try:
        logger.info(f"Querying Aurora Vector KB: {knowledge_base_id}")
        logger.info(f"  - Query: {query[:100]}...")
        logger.info(f"  - Max results: {max_results}")

        # Build retrieval configuration
        retrieval_config = {
            "vectorSearchConfiguration": {
                "numberOfResults": max_results,
                "overrideSearchType": "HYBRID",  # Use both vector and text search
            }
        }

        # Add metadata filter if provided
        if metadata_filter:
            retrieval_config["vectorSearchConfiguration"]["filter"] = {
                "andAll": [
                    {
                        "equals": {
                            "key": key,
                            "value": value
                        }
                    }
                    for key, value in metadata_filter.items()
                ]
            }

        # Execute query
        response = client.retrieve(
            knowledgeBaseId=knowledge_base_id,
            retrievalQuery={"text": query},
            retrievalConfiguration=retrieval_config,
        )

        # Process results
        citations = []
        for result in response.get("retrievalResults", []):
            score = result.get("score", 0.0)
            
            # Apply similarity score threshold
            if score < min_similarity_score:
                continue

            citations.append({
                "text": result.get("content", {}).get("text", ""),
                "score": score,
                "metadata": result.get("metadata", {}),
                "location": result.get("location", {}),
            })

        logger.info(f"✓ Retrieved {len(citations)} results")

        return {
            "citations": citations,
            "total_results": len(citations),
            "knowledge_base_id": knowledge_base_id,
        }

    except ClientError as e:
        logger.error(f"Failed to query Aurora Vector KB: {e}")
        raise


def delete_aurora_knowledge_base(knowledge_base_id: str) -> bool:
    """
    Delete Aurora Vector Knowledge Base

    Args:
        knowledge_base_id: Knowledge base ID

    Returns:
        True if deletion successful
    """
    client = get_bedrock_agent_client()

    try:
        logger.info(f"Deleting Aurora Vector KB: {knowledge_base_id}")

        # Delete all data sources first
        data_sources = client.list_data_sources(knowledgeBaseId=knowledge_base_id)
        for ds in data_sources.get("dataSourceSummaries", []):
            client.delete_data_source(
                knowledgeBaseId=knowledge_base_id, dataSourceId=ds["dataSourceId"]
            )
            logger.info(f"✓ Deleted data source: {ds['dataSourceId']}")

        # Delete the knowledge base
        client.delete_knowledge_base(knowledgeBaseId=knowledge_base_id)
        logger.info(f"✓ Deleted knowledge base: {knowledge_base_id}")

        return True

    except ClientError as e:
        logger.error(f"Failed to delete Aurora Vector KB: {e}")
        raise


def get_aurora_knowledge_base_status(knowledge_base_id: str) -> dict:
    """
    Get Aurora Vector Knowledge Base status and metadata

    Args:
        knowledge_base_id: Knowledge base ID

    Returns:
        dict: Knowledge base status and configuration
    """
    client = get_bedrock_agent_client()

    try:
        response = client.get_knowledge_base(knowledgeBaseId=knowledge_base_id)
        kb = response["knowledgeBase"]

        return {
            "knowledge_base_id": kb["knowledgeBaseId"],
            "name": kb["name"],
            "status": kb["status"],
            "description": kb.get("description", ""),
            "storage_type": kb["storageConfiguration"]["type"],
            "cluster_arn": kb["storageConfiguration"]["rdsConfiguration"]["resourceArn"],
            "database_name": kb["storageConfiguration"]["rdsConfiguration"]["databaseName"],
            "table_name": kb["storageConfiguration"]["rdsConfiguration"]["tableName"],
            "embedding_model": kb["knowledgeBaseConfiguration"]["vectorKnowledgeBaseConfiguration"]["embeddingModelArn"],
            "created_at": kb.get("createdAt"),
            "updated_at": kb.get("updatedAt"),
        }

    except ClientError as e:
        logger.error(f"Failed to get Aurora Vector KB status: {e}")
        raise


def _get_embeddings_model_arn(model_name: str) -> str:
    """Map embeddings model name to Bedrock ARN"""
    region = os.getenv("BEDROCK_REGION", "us-east-1")

    model_map = {
        "titan_v2": f"arn:aws:bedrock:{region}::foundation-model/amazon.titan-embed-text-v2:0",
        "cohere_multilingual_v3": f"arn:aws:bedrock:{region}::foundation-model/cohere.embed-multilingual-v3",
        "amazon_nova_embed_text_v1": f"arn:aws:bedrock:{region}::foundation-model/amazon.nova-embed-text-v1:0",
    }

    return model_map.get(model_name, model_map["titan_v2"])


def _get_parsing_model_arn(model_name: str) -> str:
    """Map parsing model name to Bedrock ARN"""
    region = os.getenv("BEDROCK_REGION", "us-east-1")

    model_map = {
        "anthropic.claude-3-5-sonnet-v1": f"arn:aws:bedrock:{region}::foundation-model/anthropic.claude-3-5-sonnet-20241022-v2:0",
        "anthropic.claude-3-haiku-v1": f"arn:aws:bedrock:{region}::foundation-model/anthropic.claude-3-haiku-20240307-v1:0",
    }

    return model_map.get(model_name, model_map["anthropic.claude-3-haiku-v1"])


def _build_chunking_configuration(chunking_config: Any) -> dict:
    """Build chunking configuration for Bedrock API"""
    strategy = chunking_config.chunking_strategy

    if strategy == "hierarchical":
        return {
            "chunkingStrategy": "HIERARCHICAL",
            "hierarchicalChunkingConfiguration": {
                "levelConfigurations": [
                    {"maxTokens": chunking_config.max_parent_token_size or 1500},
                    {"maxTokens": chunking_config.max_child_token_size or 300},
                ],
                "overlapTokens": chunking_config.overlap_tokens or 60,
            },
        }
    elif strategy == "fixed_size":
        return {
            "chunkingStrategy": "FIXED_SIZE",
            "fixedSizeChunkingConfiguration": {
                "maxTokens": chunking_config.max_tokens or 300,
                "overlapPercentage": chunking_config.overlap_percentage or 20,
            },
        }
    elif strategy == "semantic":
        return {
            "chunkingStrategy": "SEMANTIC",
            "semanticChunkingConfiguration": {
                "maxTokens": chunking_config.max_tokens or 300,
                "bufferSize": chunking_config.buffer_size or 0,
                "breakpointPercentileThreshold": chunking_config.breakpoint_percentile_threshold or 95,
            },
        }
    else:
        # Default to hierarchical
        return {
            "chunkingStrategy": "HIERARCHICAL",
            "hierarchicalChunkingConfiguration": {
                "levelConfigurations": [
                    {"maxTokens": 1500},
                    {"maxTokens": 300},
                ],
                "overlapTokens": 60,
            },
        }
