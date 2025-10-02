from typing import Literal

from app.routes.schemas.base import BaseSchema
from pydantic import Field

# Ref: https://docs.aws.amazon.com/bedrock/latest/APIReference/API_agent_ChunkingConfiguration.html
type_kb_chunking_strategy = Literal[
    "default",
    "fixed_size",
    "hierarchical",
    "semantic",
    "none",
]
type_kb_embeddings_model = Literal["titan_v2", "cohere_multilingual_v3"]
type_kb_search_type = Literal["hybrid", "semantic"]
type_kb_parsing_model = Literal[
    "anthropic.claude-3-5-sonnet-v1",
    "anthropic.claude-3-haiku-v1",
    "anthropic.claude-3-sonnet-v1",
    "disabled",
]
type_kb_web_crawling_scope = Literal["DEFAULT", "HOST_ONLY", "SUBDOMAINS"]

# OpenSearch Serverless Analyzer
# Ref: https://docs.aws.amazon.com/opensearch-service/latest/developerguide/serverless-genref.html
type_os_character_filter = Literal["icu_normalizer"]
type_os_tokenizer = Literal["kuromoji_tokenizer", "icu_tokenizer"]
type_os_token_filter = Literal[
    "kuromoji_baseform",
    "kuromoji_part_of_speech",
    "kuromoji_stemmer",
    "cjk_width",
    "ja_stop",
    "lowercase",
    "icu_folding",
]

# Knowledge Base Type
# Ref: https://docs.aws.amazon.com/bedrock/latest/APIReference/API_agent_KnowledgeBaseConfiguration.html#bedrock-Type-agent_KnowledgeBaseConfiguration-type
type_kb_resource_type = Literal["VECTOR", "KENDRA", "SQL"]


class SearchParams(BaseSchema):
    max_results: int
    search_type: type_kb_search_type


class AnalyzerParams(BaseSchema):
    character_filters: list[type_os_character_filter]
    tokenizer: type_os_tokenizer
    token_filters: list[type_os_token_filter]


class OpenSearchParams(BaseSchema):
    analyzer: AnalyzerParams | None


class DefaultParams(BaseSchema):
    chunking_strategy: type_kb_chunking_strategy = "default"


class FixedSizeParams(BaseSchema):
    chunking_strategy: type_kb_chunking_strategy = "fixed_size"
    max_tokens: int | None = None
    overlap_percentage: int | None = None


class HierarchicalParams(BaseSchema):
    chunking_strategy: type_kb_chunking_strategy = "hierarchical"
    overlap_tokens: int | None = None
    max_parent_token_size: int | None = None
    max_child_token_size: int | None = None


class SemanticParams(BaseSchema):
    chunking_strategy: type_kb_chunking_strategy = "semantic"
    max_tokens: int | None = None
    buffer_size: int | None = None
    breakpoint_percentile_threshold: int | None = None


class NoneParams(BaseSchema):
    chunking_strategy: type_kb_chunking_strategy = "none"


class WebCrawlingFilters(BaseSchema):
    exclude_patterns: list[str] = Field(default_factory=list)
    include_patterns: list[str] = Field(default_factory=list)


class BedrockKnowledgeBaseInput(BaseSchema):
    embeddings_model: type_kb_embeddings_model
    open_search: OpenSearchParams
    chunking_configuration: (
        DefaultParams
        | FixedSizeParams
        | HierarchicalParams
        | SemanticParams
        | NoneParams
    )
    search_params: SearchParams
    knowledge_base_id: str | None = None
    exist_knowledge_base_id: str | None = None
    parsing_model: type_kb_parsing_model = "disabled"
    web_crawling_scope: type_kb_web_crawling_scope = "DEFAULT"
    web_crawling_filters: WebCrawlingFilters = WebCrawlingFilters(
        exclude_patterns=[], include_patterns=[]
    )


class BedrockKnowledgeBaseOutput(BaseSchema):
    embeddings_model: type_kb_embeddings_model
    open_search: OpenSearchParams
    chunking_configuration: (
        DefaultParams
        | FixedSizeParams
        | HierarchicalParams
        | SemanticParams
        | NoneParams
        | None
    )
    search_params: SearchParams
    knowledge_base_id: str | None = None
    exist_knowledge_base_id: str | None = None
    data_source_ids: list[str] | None = None
    parsing_model: type_kb_parsing_model = "disabled"
    web_crawling_scope: type_kb_web_crawling_scope = "DEFAULT"
    web_crawling_filters: WebCrawlingFilters = WebCrawlingFilters(
        exclude_patterns=[], include_patterns=[]
    )


# SQL Knowledge Base Schemas
class SqlDatabaseConfig(BaseSchema):
    """Configuration for Redshift database connection"""

    workgroup_name: str = Field(
        ..., description="Redshift Serverless workgroup name"
    )
    workgroup_arn: str = Field(..., description="Redshift Serverless workgroup ARN")
    database_name: str = Field(..., description="Database name in Redshift")
    table_name: str = Field(
        ..., description="Table or view name for Bedrock Knowledge Base"
    )
    field_mapping: dict[str, str] = Field(
        ...,
        description="Field mapping for Bedrock KB (id, content, metadata)",
        example={"id": "record_id", "content": "searchable_text", "metadata": "metadata"},
    )
    secret_arn: str = Field(
        ..., description="AWS Secrets Manager ARN with Redshift credentials"
    )


class SqlKnowledgeBaseInput(BaseSchema):
    """Input schema for creating SQL Knowledge Base"""

    knowledge_base_type: Literal["SQL"] = "SQL"
    database_config: SqlDatabaseConfig
    search_params: SearchParams
    embedding_model_arn: str = Field(
        default="arn:aws:bedrock:us-east-1::foundation-model/amazon.titan-embed-text-v2:0",
        description="Embedding model ARN for vector search",
    )
    knowledge_base_id: str | None = Field(
        default=None, description="Existing KB ID if updating"
    )


class SqlKnowledgeBaseOutput(BaseSchema):
    """Output schema for SQL Knowledge Base"""

    knowledge_base_type: Literal["SQL"] = "SQL"
    database_config: SqlDatabaseConfig
    search_params: SearchParams
    embedding_model_arn: str
    knowledge_base_id: str | None = None
    data_source_ids: list[str] | None = None
    status: Literal["CREATING", "ACTIVE", "DELETING", "UPDATING", "FAILED"] | None = (
        None
    )


class KnowledgeBaseStatusOutput(BaseSchema):
    """Knowledge Base ingestion status"""

    knowledge_base_id: str
    status: Literal["CREATING", "ACTIVE", "DELETING", "UPDATING", "FAILED"]
    ingestion_job_id: str | None = None
    ingestion_job_status: Literal[
        "STARTING", "IN_PROGRESS", "COMPLETE", "FAILED"
    ] | None = None
    progress_percent: int | None = None
    error_message: str | None = None


class SqlQueryInput(BaseSchema):
    """Input for querying SQL Knowledge Base"""

    query: str = Field(..., description="Natural language query")
    max_results: int = Field(default=10, description="Maximum results to return")


class SqlQueryOutput(BaseSchema):
    """Output from SQL Knowledge Base query"""

    answer: str = Field(..., description="Natural language answer")
    citations: list[dict] | None = Field(
        default=None, description="Source citations from KB"
    )
    sql_query: str | None = Field(default=None, description="Generated SQL query")
    results: list[dict] | None = Field(
        default=None, description="Structured query results"
    )
