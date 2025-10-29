"""
S3 Vector Knowledge Base Repository

This module handles creation, querying, and management of VECTOR-type Knowledge Bases
that use Amazon S3 Vectors as the storage backend (preview feature).
"""

import logging
import os
from typing import Any

from app.repositories.models.custom_bot_kb import BedrockKnowledgeBaseModel
from app.utils import get_bedrock_agent_client, get_bedrock_agent_runtime_client
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def create_s3_vector_knowledge_base(
    bot_id: str,
    kb_config: BedrockKnowledgeBaseModel,
    kb_name: str,
    document_bucket_arn: str,
    document_prefix: str = "",
) -> tuple[str, str | None]:
    """
    Create Bedrock Knowledge Base with S3 Vector storage (Quick Create)

    This uses AWS Bedrock's Quick Create feature which automatically provisions
    an S3 vector bucket and vector index without manual configuration.

    Args:
        bot_id: Bot identifier
        kb_config: Knowledge base configuration with embeddings model and chunking
        kb_name: Human-readable knowledge base name
        document_bucket_arn: S3 ARN for source documents
        document_prefix: Optional S3 prefix for documents (e.g., "documents/bot123/")

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
        logger.info(f"Creating S3 Vector Knowledge Base for bot {bot_id}")
        logger.info(f"  - Name: {kb_name}")
        logger.info(f"  - Storage Type: S3 Vectors (Quick Create)")
        logger.info(f"  - Embeddings Model: {kb_config.embeddings_model}")
        logger.info(f"  - Document Bucket: {document_bucket_arn}")
        logger.info(f"  - Document Prefix: {document_prefix or '(root)'}")

        # Map embeddings model to ARN
        embeddings_model_arn = _get_embeddings_model_arn(kb_config.embeddings_model)

        # Build chunking configuration
        chunking_config = _build_chunking_configuration(kb_config.chunking_configuration)

        # Create Knowledge Base with S3 Vector storage
        # Support both Quick Create (auto-provisioned) and custom bucket configuration
        s3_vectors_config = {}
        
        # Add custom bucket configuration if provided
        if hasattr(kb_config, 's3_vector') and kb_config.s3_vector:
            if hasattr(kb_config.s3_vector, 'vector_bucket_arn') and kb_config.s3_vector.vector_bucket_arn:
                s3_vectors_config["vectorBucketArn"] = kb_config.s3_vector.vector_bucket_arn
                logger.info(f"  - Using custom vector bucket: {kb_config.s3_vector.vector_bucket_arn}")
            
            if hasattr(kb_config.s3_vector, 'index_name') and kb_config.s3_vector.index_name:
                s3_vectors_config["indexName"] = kb_config.s3_vector.index_name
                logger.info(f"  - Using custom index name: {kb_config.s3_vector.index_name}")
        
        if not s3_vectors_config:
            logger.info("  - Using Quick Create: Bedrock will auto-create vector bucket and index")

        response = client.create_knowledge_base(
            name=kb_name,
            description=f"S3 Vector Knowledge Base for bot {bot_id}",
            roleArn=bedrock_kb_role_arn,
            knowledgeBaseConfiguration={
                "type": "VECTOR",
                "vectorKnowledgeBaseConfiguration": {
                    "embeddingModelArn": embeddings_model_arn,
                    "embeddingModelConfiguration": {
                        "bedrockEmbeddingModelConfiguration": {
                            "dimensions": _get_embedding_dimensions(kb_config.embeddings_model),
                            "embeddingDataType": "FLOAT32"  # S3 Vectors supports FLOAT32
                        }
                    }
                },
            },
            storageConfiguration={
                "type": "S3_VECTORS"
            },
        )

        kb_id = response["knowledgeBase"]["knowledgeBaseId"]
        logger.info(f"✓ Successfully created S3 Vector KB: {kb_id}")

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
                        **({"inclusionPrefixes": [document_prefix]} if document_prefix else {})
                    },
                },
                vectorIngestionConfiguration={
                    "chunkingConfiguration": chunking_config,
                    **(
                        {
                            "parsingConfiguration": {
                                "parsingStrategy": "BEDROCK_FOUNDATION_MODEL",
                                "bedrockFoundationModelConfiguration": {
                                    "modelArn": _get_parsing_model_arn(kb_config.parsing_model)
                                },
                            }
                        }
                        if kb_config.parsing_model != "disabled"
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
                # Non-fatal: can be started later

        except ClientError as e:
            logger.error(f"Failed to create data source: {e}")
            # Non-fatal: KB is created, data source can be added later

        return kb_id, data_source_id

    except ClientError as e:
        logger.error(f"Failed to create S3 Vector Knowledge Base: {e}")
        logger.error(f"Error Code: {e.response.get('Error', {}).get('Code', 'Unknown')}")
        logger.error(f"Error Message: {e.response.get('Error', {}).get('Message', 'Unknown')}")
        raise


def _get_embeddings_model_arn(model_name: str) -> str:
    """
    Map embeddings model name to Bedrock inference profile ARN for better performance

    Args:
        model_name: Model name from type_kb_embeddings_model

    Returns:
        Bedrock inference profile ARN
    """
    region = os.getenv("BEDROCK_REGION", "us-east-1")

    # Use inference profiles for better throughput and cross-region routing
    model_map = {
        "titan_v2": f"arn:aws:bedrock:{region}::inference-profile/us.amazon.titan-embed-text-v2:0",
        "cohere_multilingual_v3": f"arn:aws:bedrock:{region}::inference-profile/us.cohere.embed-multilingual-v3",
    }

    return model_map.get(model_name, model_map["titan_v2"])


def _get_embedding_dimensions(model_name: str) -> int:
    """
    Get embedding dimensions for the model

    Args:
        model_name: Model name from type_kb_embeddings_model

    Returns:
        Number of dimensions
    """
    dimensions_map = {
        "titan_v2": 1024,  # Titan Embeddings V2
        "cohere_multilingual_v3": 1024,  # Cohere Multilingual V3
    }

    return dimensions_map.get(model_name, 1024)


def _get_parsing_model_arn(model_name: str) -> str:
    """
    Map parsing model name to Bedrock ARN

    Args:
        model_name: Model name from type_kb_parsing_model

    Returns:
        Full Bedrock model ARN
    """
    region = os.getenv("BEDROCK_REGION", "us-east-1")

    model_map = {
        "anthropic.claude-3-5-sonnet-v1": f"arn:aws:bedrock:{region}::foundation-model/anthropic.claude-3-5-sonnet-20241022-v2:0",
        "anthropic.claude-3-haiku-v1": f"arn:aws:bedrock:{region}::foundation-model/anthropic.claude-3-haiku-20240307-v1:0",
        "anthropic.claude-3-sonnet-v1": f"arn:aws:bedrock:{region}::foundation-model/anthropic.claude-3-sonnet-20240229-v1:0",
    }

    return model_map.get(model_name, model_map["anthropic.claude-3-haiku-v1"])


def _build_chunking_configuration(chunking_config: Any) -> dict:
    """
    Build chunking configuration for Bedrock API

    Args:
        chunking_config: Chunking configuration object

    Returns:
        Bedrock API chunking configuration dict
        
    Raises:
        ValueError: If token limits exceed S3 Vector constraints
    """
    strategy = chunking_config.chunking_strategy

    # S3 Vector token limit validation
    def _validate_s3_vector_tokens(tokens: int, field_name: str):
        if tokens > 500:
            raise ValueError(f"S3 Vector storage has a maximum limit of 500 tokens per chunk. {field_name} cannot exceed 500 tokens.")

    if strategy == "default":
        return {
            "chunkingStrategy": "HIERARCHICAL",  # Bedrock's default hierarchical chunking
            "hierarchicalChunkingConfiguration": {
                "levelConfigurations": [
                    {"maxTokens": 500},  # S3 Vector limit - Parent chunks
                    {"maxTokens": 300},   # Child chunks
                ],
                "overlapTokens": 60,
            },
        }

    elif strategy == "fixed_size":
        max_tokens = chunking_config.max_tokens or 300
        _validate_s3_vector_tokens(max_tokens, "maxTokens")
        
        return {
            "chunkingStrategy": "FIXED_SIZE",
            "fixedSizeChunkingConfiguration": {
                "maxTokens": max_tokens,
                "overlapPercentage": chunking_config.overlap_percentage or 20,
            },
        }

    elif strategy == "hierarchical":
        parent_tokens = chunking_config.max_parent_token_size or 1500
        child_tokens = chunking_config.max_child_token_size or 300
        
        _validate_s3_vector_tokens(parent_tokens, "maxParentTokenSize")
        _validate_s3_vector_tokens(child_tokens, "maxChildTokenSize")
        
        return {
            "chunkingStrategy": "HIERARCHICAL",
            "hierarchicalChunkingConfiguration": {
                "levelConfigurations": [
                    {"maxTokens": parent_tokens},
                    {"maxTokens": child_tokens},
                ],
                "overlapTokens": chunking_config.overlap_tokens or 60,
            },
        }

    elif strategy == "semantic":
        max_tokens = chunking_config.max_tokens or 300
        _validate_s3_vector_tokens(max_tokens, "maxTokens")
        
        return {
            "chunkingStrategy": "SEMANTIC",
            "semanticChunkingConfiguration": {
                "maxTokens": max_tokens,
                "bufferSize": chunking_config.buffer_size or 0,
                "breakpointPercentileThreshold": chunking_config.breakpoint_percentile_threshold or 95,
            },
        }

    elif strategy == "none":
        return {
            "chunkingStrategy": "NONE",
        }

    else:
        # Fallback to default
        logger.warning(f"Unknown chunking strategy: {strategy}, using default")
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


def get_s3_vector_kb_info(knowledge_base_id: str) -> dict:
    """
    Get S3 Vector Knowledge Base details

    Args:
        knowledge_base_id: Knowledge base ID

    Returns:
        Knowledge base details from Bedrock API
    """
    client = get_bedrock_agent_client()

    try:
        response = client.get_knowledge_base(knowledgeBaseId=knowledge_base_id)
        return response["knowledgeBase"]
    except ClientError as e:
        logger.error(f"Failed to get KB info: {e}")
        raise


def delete_s3_vector_knowledge_base(knowledge_base_id: str) -> bool:
    """
    Delete S3 Vector Knowledge Base

    Note: This deletes the KB configuration but does NOT delete the auto-created
    S3 vector bucket. The vector bucket must be cleaned up separately.

    Args:
        knowledge_base_id: Knowledge base ID

    Returns:
        True if deletion successful
    """
    client = get_bedrock_agent_client()

    try:
        logger.info(f"Deleting S3 Vector KB: {knowledge_base_id}")

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

        logger.warning(
            f"Note: Auto-created S3 vector bucket for KB {knowledge_base_id} was NOT deleted. "
            "Clean up manually if needed to avoid storage costs."
        )

        return True

    except ClientError as e:
        logger.error(f"Failed to delete S3 Vector KB: {e}")
        raise
