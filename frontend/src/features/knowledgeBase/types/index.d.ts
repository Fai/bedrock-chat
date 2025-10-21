// Vector storage backend type
export type VectorStorageType = 'OPENSEARCH_SERVERLESS' | 'S3_VECTOR' | 'AURORA_POSTGRESQL';

// Knowledge Base resource type
export type KnowledgeBaseResourceType = 'VECTOR' | 'SQL';

// SQL database configuration
export type SqlDatabaseConfig = {
  workgroupName: string;
  workgroupArn: string;
  databaseName: string;
  tableName: string;
  secretArn: string;
  fieldMapping: {
    id: string;
    content: string;
    metadata: string;
    embedding: string;
  };
};

// SQL Knowledge Base type
export type SqlKnowledgeBase = {
  knowledgeBaseId: string | null;
  knowledgeBaseType: 'SQL';
  databaseConfig: SqlDatabaseConfig;
  searchParams: SearchParams;
  embeddingModelArn: string;
};

// S3 Vector specific configuration
export type S3VectorConfig = {
  vectorBucketArn?: string;  // Optional: Custom S3 bucket for vectors
  indexName?: string;        // Optional: Custom index name
};

// Aurora PostgreSQL specific configuration
export type AuroraPostgreSQLConfig = {
  clusterArn: string;        // Aurora cluster ARN
  clusterName: string;       // Display name
  databaseName: string;      // Database name
  tableName: string;         // Table name (e.g., bedrock_integration.kb_vectors)
  secretArn: string;         // Secrets Manager ARN with credentials
};

export type BedrockKnowledgeBase = {
  knowledgeBaseId: string | null;
  existKnowledgeBaseId: string | null;
  dataSourceIds?: string[]; // only present after bot is ready

  // Storage type selection (defaults to OPENSEARCH_SERVERLESS for backward compatibility)
  storageType?: VectorStorageType;

  embeddingsModel: EmbeddingsModel;
  chunkingConfiguration: ChunkingConfiguration;

  // OpenSearch config - only for OPENSEARCH_SERVERLESS storage
  openSearch?: OpenSearchParams | null;

  // S3 Vector config - only for S3_VECTOR storage
  s3Vector?: S3VectorConfig | null;

  // Aurora PostgreSQL config - only for AURORA_POSTGRESQL storage
  auroraPostgreSQL?: AuroraPostgreSQLConfig | null;

  searchParams: SearchParams;
  parsingModel?: ParsingModel;
  webCrawlingScope?: WebCrawlingScope;
  webCrawlingFilters?: WebCrawlingFilters;
};

export type EmbeddingsModel = 'titan_v2' | 'cohere_multilingual_v3';

export type ParsingModel = 'anthropic.claude-3-5-sonnet-v1' | 'anthropic.claude-3-haiku-v1' | 'disabled';

export type ChunkingStrategy = 'default' | 'fixed_size' | 'hierarchical' | 'semantic' | 'none';

export type WebCrawlingScope = 'DEFAULT' | 'SUBDOMAINS' | 'HOST_ONLY';

export type WebCrawlingFilters = {
  excludePatterns: string[];
  includePatterns: string[];
};

export type ChunkingConfiguration = DefaultParams | FixedSizeParams | HierarchicalParams | SemanticParams | NoneParams;

export type OpenSearchParams = {
  analyzer: {
    characterFilters: CharacterFilter[];
    tokenizer: Tokenizer;
    tokenFilters: TokenFilter[];
  } | null;
};

export type DefaultParams = {
  chunkingStrategy: 'default';
};

export type FixedSizeParams = {
  chunkingStrategy: 'fixed_size';
  maxTokens: number;
  overlapPercentage: number;
};

export type HierarchicalParams = {
  chunkingStrategy: 'hierarchical';
  overlapTokens: number;
  maxParentTokenSize: number;
  maxChildTokenSize: number;
};

export type SemanticParams = {
  chunkingStrategy: 'semantic';
  maxTokens: number;
  bufferSize: number;
  breakpointPercentileThreshold: number;
};

export type NoneParams = {
  chunkingStrategy: 'none';
};

export type CharacterFilter = 'icu_normalizer'; // static

export type Tokenizer = 'kuromoji_tokenizer' | 'icu_tokenizer';

export type TokenFilter =
  | 'kuromoji_baseform'
  | 'kuromoji_part_of_speech'
  | 'kuromoji_stemmer'
  | 'cjk_width'
  | 'ja_stop'
  | 'lowercase'
  | 'icu_folding';

export type SearchParams = {
  maxResults: number;
  searchType: SearchType;
};

export type SearchType = 'hybrid' | 'semantic';

// SQL Knowledge Base Types
export type KnowledgeBaseResourceType = 'VECTOR' | 'SQL';

export type SqlDatabaseConfig = {
  workgroupName: string;
  workgroupArn: string;
  databaseName: string;
  tableName: string;
  fieldMapping: {
    id: string;
    content: string;
    metadata: string;
  };
  secretArn: string;
};

export type SqlKnowledgeBase = {
  knowledgeBaseType: 'SQL';
  knowledgeBaseId: string | null;
  dataSourceIds?: string[];
  databaseConfig: SqlDatabaseConfig;
  searchParams: SearchParams;
  embeddingModelArn: string;
};

export type KnowledgeBaseStatus =
  | 'CREATING'
  | 'ACTIVE'
  | 'DELETING'
  | 'UPDATING'
  | 'FAILED'
  | 'NOT_STARTED'
  | 'UNKNOWN';

export type IngestionJobStatus =
  | 'STARTING'
  | 'IN_PROGRESS'
  | 'COMPLETE'
  | 'FAILED';

export type KnowledgeBaseStatusInfo = {
  knowledgeBaseId: string;
  status: KnowledgeBaseStatus;
  ingestionJobId?: string | null;
  ingestionJobStatus?: IngestionJobStatus | null;
  errorMessage?: string;
};

export type SqlQueryResult = {
  answer: string;
  citations?: Array<{
    retrievedReferences?: Array<{
      metadata?: Record<string, unknown>;
      content?: {
        text?: string;
      };
    }>;
  }> | null;
  sqlQuery?: string | null;
  results?: Array<Record<string, unknown>> | null;
};
