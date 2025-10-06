from app.routes.schemas.bot_kb import (
    type_kb_chunking_strategy,
    type_kb_embeddings_model,
    type_kb_parsing_model,
    type_kb_search_type,
    type_kb_web_crawling_scope,
    type_os_character_filter,
    type_os_token_filter,
    type_os_tokenizer,
    type_kb_resource_type,
    type_kb_storage_type,
)
from typing import Self
from pydantic import BaseModel, validator, model_validator


class SearchParamsModel(BaseModel):
    max_results: int
    search_type: type_kb_search_type


class AnalyzerParamsModel(BaseModel):
    character_filters: list[type_os_character_filter]
    tokenizer: type_os_tokenizer
    token_filters: list[type_os_token_filter]


class OpenSearchParamsModel(BaseModel):
    analyzer: AnalyzerParamsModel | None


class DefaultParamsModel(BaseModel):
    chunking_strategy: type_kb_chunking_strategy = "default"


class FixedSizeParamsModel(BaseModel):
    chunking_strategy: type_kb_chunking_strategy = "fixed_size"
    max_tokens: int | None = None
    overlap_percentage: int | None = None


class HierarchicalParamsModel(BaseModel):
    chunking_strategy: type_kb_chunking_strategy = "hierarchical"
    overlap_tokens: int | None = None
    max_parent_token_size: int | None = None
    max_child_token_size: int | None = None


class SemanticParamsModel(BaseModel):
    chunking_strategy: type_kb_chunking_strategy = "semantic"
    max_tokens: int | None = None
    buffer_size: int | None = None
    breakpoint_percentile_threshold: int | None = None


class NoneParamsModel(BaseModel):
    chunking_strategy: type_kb_chunking_strategy = "none"


class WebCrawlingFiltersModel(BaseModel):
    exclude_patterns: list[str]
    include_patterns: list[str]


class KnowledgeBaseConfiguration(BaseModel):
    type: type_kb_resource_type


class KnowledgeBase(BaseModel):
    knowledge_base_configuration: KnowledgeBaseConfiguration


class BedrockAgentGetKnowledgeBaseResponse(BaseModel):
    knowledge_base: KnowledgeBase


class BedrockKnowledgeBaseModel(BaseModel):
    embeddings_model: type_kb_embeddings_model
    open_search: OpenSearchParamsModel | None = None  # Optional for S3 vector store
    storage_type: type_kb_storage_type = "OPENSEARCH_SERVERLESS"  # Default to existing behavior
    chunking_configuration: (
        DefaultParamsModel
        | FixedSizeParamsModel
        | HierarchicalParamsModel
        | SemanticParamsModel
        | NoneParamsModel
        | None
    )
    search_params: SearchParamsModel
    knowledge_base_id: str | None = None
    exist_knowledge_base_id: str | None = None
    data_source_ids: list[str] | None = None
    parsing_model: type_kb_parsing_model = "disabled"
    web_crawling_scope: type_kb_web_crawling_scope = "DEFAULT"
    web_crawling_filters: WebCrawlingFiltersModel = WebCrawlingFiltersModel(
        exclude_patterns=[], include_patterns=[]
    )


# SQL Knowledge Base Models
class SqlDatabaseConfigModel(BaseModel):
    """Redshift database configuration model"""

    workgroup_name: str
    workgroup_arn: str
    database_name: str
    table_name: str
    field_mapping: dict[str, str]
    secret_arn: str
    embedding_model_arn: str = "arn:aws:bedrock:us-east-1::foundation-model/amazon.titan-embed-text-v2:0"  # Default to Titan v2


class SqlKnowledgeBaseModel(BaseModel):
    """SQL Knowledge Base model for DynamoDB storage"""

    knowledge_base_type: type_kb_resource_type = "SQL"
    database_config: SqlDatabaseConfigModel
    search_params: SearchParamsModel
    embedding_model_arn: str
    knowledge_base_id: str | None = None
    data_source_ids: list[str] | None = None
