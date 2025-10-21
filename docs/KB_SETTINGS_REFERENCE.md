# AWS Bedrock Knowledge Base Settings Reference

**Document Purpose:** Comprehensive reference for all AWS Bedrock Knowledge Base configuration settings based on official AWS documentation. Use this as the authoritative source when implementing the KB UI Settings Refactor Plan.

**Last Updated:** 2025 (Based on latest AWS documentation)
**Related Documents:** [KB_UI_SETTINGS_REFACTOR_PLAN.md](./KB_UI_SETTINGS_REFACTOR_PLAN.md)

---

## Table of Contents

1. [Knowledge Base Types Overview](#knowledge-base-types-overview)
2. [Chunking Configuration](#chunking-configuration)
3. [Parsing Configuration](#parsing-configuration)
4. [Storage Configuration](#storage-configuration)
5. [Search & Retrieval Configuration](#search--retrieval-configuration)
6. [Embedding Models](#embedding-models)
7. [Complete Settings Matrix](#complete-settings-matrix)

---

## Knowledge Base Types Overview

### 1. Vector Knowledge Bases
Store and retrieve unstructured data using vector embeddings.

**Supported Vector Stores:**
- Amazon OpenSearch Serverless ✅
- Amazon OpenSearch Managed Cluster ✅
- Amazon S3 Vectors ✅ (Preview)
- Amazon RDS (Aurora PostgreSQL) ✅
- Pinecone ✅
- Redis Enterprise Cloud ✅
- MongoDB Atlas ✅

### 2. Structured Data Knowledge Bases
Query structured data using natural language to SQL conversion.

**Supported Query Engines:**
- Amazon Redshift Serverless ✅
- Amazon Redshift Provisioned ✅
- Amazon SageMaker Lakehouse ✅ (New)

---

## Chunking Configuration

### Overview
Chunking splits documents into smaller pieces for embedding and retrieval. **Only applicable to Vector Knowledge Bases.**

### Chunking Strategy Types

#### 1. Default Chunking
**Strategy:** `default`

**Description:** Uses Amazon Bedrock's default chunking behavior (approximately 300 tokens per chunk).

**Configuration:**
```json
{
  "chunkingStrategy": "default"
}
```

**Parameters:** None

**Use Case:** Quick setup without custom tuning

**Applicable To:**
- ✅ OpenSearch Serverless
- ✅ OpenSearch Managed Cluster
- ✅ S3 Vectors
- ✅ RDS (Aurora)
- ✅ Other vector stores
- ❌ Structured Data KBs

---

#### 2. Fixed Size Chunking
**Strategy:** `fixed_size`

**Description:** Splits documents into chunks of approximately specified token size with configurable overlap.

**Configuration:**
```json
{
  "chunkingStrategy": "fixed_size",
  "fixedSizeChunkingConfiguration": {
    "maxTokens": 300,
    "overlapPercentage": 20
  }
}
```

**Parameters:**

| Parameter | Type | Required | Min | Max | Default | Description |
|-----------|------|----------|-----|-----|---------|-------------|
| `maxTokens` | Integer | Yes | 1 | See limits* | 300 | Maximum tokens per chunk |
| `overlapPercentage` | Integer | Yes | 1 | 99 | 20 | Percentage overlap between chunks |

**Token Limits by Storage Type:**

| Storage Type | Max Tokens (Titan V2) | Max Tokens (Cohere v3) |
|--------------|----------------------|------------------------|
| OpenSearch Serverless | 8,192 | 512 |
| OpenSearch Managed | 8,192 | 512 |
| **S3 Vectors** | **500** ⚠️ | **500** ⚠️ |
| RDS (Aurora) | 8,192 | 512 |
| Other Stores | 8,192 | 512 |

**Use Case:** Precise control over chunk size and overlap

**Applicable To:**
- ✅ OpenSearch Serverless (up to 8,192/512 tokens)
- ✅ OpenSearch Managed Cluster (up to 8,192/512 tokens)
- ✅ S3 Vectors ⚠️ **500 token limit**
- ✅ RDS (Aurora) (up to 8,192/512 tokens)
- ✅ Other vector stores
- ❌ Structured Data KBs

---

#### 3. Hierarchical Chunking
**Strategy:** `hierarchical`

**Description:** Creates two layers of chunks - large parent chunks containing smaller child chunks for multi-level retrieval.

**Configuration:**
```json
{
  "chunkingStrategy": "hierarchical",
  "hierarchicalChunkingConfiguration": {
    "levelConfigurations": [
      {
        "maxTokens": 1500  // Parent chunk size
      },
      {
        "maxTokens": 300   // Child chunk size
      }
    ],
    "overlapTokens": 60
  }
}
```

**Parameters:**

| Parameter | Type | Required | Min | Max | Default | Description |
|-----------|------|----------|-----|-----|---------|-------------|
| `levelConfigurations` | Array | Yes | 2 items | 2 items | - | Parent and child chunk sizes |
| `levelConfigurations[0].maxTokens` | Integer | Yes | 1 | See limits* | 1500 | Parent chunk max tokens |
| `levelConfigurations[1].maxTokens` | Integer | Yes | 1 | See limits* | 300 | Child chunk max tokens |
| `overlapTokens` | Integer | Yes | 1 | - | 60 | Token overlap between chunks |

**Token Limits by Storage Type:**

| Storage Type | Parent Max | Child Max |
|--------------|------------|-----------|
| OpenSearch Serverless | 8,192 (Titan) / 512 (Cohere) | 8,192 (Titan) / 512 (Cohere) |
| **S3 Vectors** | **500** ⚠️ | **500** ⚠️ |
| RDS (Aurora) | 8,192 (Titan) / 512 (Cohere) | 8,192 (Titan) / 512 (Cohere) |

**Use Case:** Better context retention with hierarchical retrieval

**Applicable To:**
- ✅ OpenSearch Serverless
- ✅ OpenSearch Managed Cluster
- ✅ S3 Vectors ⚠️ **500 token limit on both levels**
- ✅ RDS (Aurora)
- ✅ Other vector stores
- ❌ Structured Data KBs

---

#### 4. Semantic Chunking
**Strategy:** `semantic`

**Description:** Splits documents based on semantic meaning using natural language processing to determine chunk boundaries.

**Configuration:**
```json
{
  "chunkingStrategy": "semantic",
  "semanticChunkingConfiguration": {
    "maxTokens": 300,
    "bufferSize": 0,
    "breakpointPercentileThreshold": 95
  }
}
```

**Parameters:**

| Parameter | Type | Required | Min | Max | Default | Description |
|-----------|------|----------|-----|-----|---------|-------------|
| `maxTokens` | Integer | Yes | 1 | See limits* | 300 | Maximum tokens per semantic chunk |
| `bufferSize` | Integer | Yes | 0 | 1 | 0 | Number of sentences to buffer |
| `breakpointPercentileThreshold` | Integer | Yes | 50 | 99 | 95 | Percentile threshold for semantic boundaries |

**Token Limits by Storage Type:**

| Storage Type | Max Tokens (Titan V2) | Max Tokens (Cohere v3) |
|--------------|----------------------|------------------------|
| OpenSearch Serverless | 8,192 | 512 |
| **S3 Vectors** | **500** ⚠️ | **500** ⚠️ |
| RDS (Aurora) | 8,192 | 512 |

**Additional Costs:** ⚠️ Uses a foundation model, incurring additional inference charges

**Use Case:** Preserve semantic coherence across chunks

**Applicable To:**
- ✅ OpenSearch Serverless
- ✅ OpenSearch Managed Cluster
- ✅ S3 Vectors ⚠️ **500 token limit**
- ✅ RDS (Aurora)
- ✅ Other vector stores
- ❌ Structured Data KBs

---

#### 5. None (No Chunking)
**Strategy:** `none`

**Description:** Each file is treated as a single chunk. Recommended to pre-process documents by splitting into separate files.

**Configuration:**
```json
{
  "chunkingStrategy": "none"
}
```

**Parameters:** None

**Use Case:** Pre-chunked documents or small files

**Applicable To:**
- ✅ All vector stores
- ❌ Structured Data KBs

---

## Parsing Configuration

### Overview
Parsing extracts text and multimodal content from documents. **Only applicable to Vector Knowledge Bases.**

### Parsing Strategy Types

#### 1. Default Parser
**Strategy:** No configuration (default behavior)

**Description:** Amazon Bedrock's default parser converts document contents to text before chunking.

**Configuration:** Omit `parsingConfiguration` field

**Supported Formats:**
- Plain text (.txt, .md)
- HTML (.html)
- Microsoft Word (.doc, .docx)
- CSV (.csv)
- Excel (.xls, .xlsx)
- PDF (.pdf)

**File Size Limits:**
- Documents: 50 MB max
- Images: 3.75 MB max

**Applicable To:**
- ✅ All vector stores
- ❌ Structured Data KBs

---

#### 2. Bedrock Foundation Model Parser
**Strategy:** `BEDROCK_FOUNDATION_MODEL`

**Description:** Uses a foundation model (Claude) for advanced document parsing including multimodal content.

**Configuration:**
```json
{
  "parsingStrategy": "BEDROCK_FOUNDATION_MODEL",
  "bedrockFoundationModelConfiguration": {
    "modelArn": "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-5-sonnet-20240620-v1:0",
    "parsingModality": "MULTIMODAL",
    "parsingPrompt": {
      "parsingPromptText": "Instructions for interpreting document contents"
    }
  }
}
```

**Parameters:**

| Parameter | Type | Required | Min Length | Max Length | Description |
|-----------|------|----------|------------|------------|-------------|
| `modelArn` | String | Yes | 1 | 2048 | ARN of foundation model |
| `parsingModality` | Enum | No | - | - | Currently only `MULTIMODAL` |
| `parsingPrompt.parsingPromptText` | String | No | - | - | Custom parsing instructions |

**Supported Models:**
- `anthropic.claude-3-5-sonnet-20240620-v1:0`
- `anthropic.claude-3-haiku-20240307-v1:0`

**Additional Costs:** ⚠️ Incurs foundation model inference charges

**Use Case:** Complex documents with tables, images, diagrams

**Applicable To:**
- ✅ OpenSearch Serverless
- ✅ OpenSearch Managed Cluster
- ✅ S3 Vectors
- ✅ RDS (Aurora)
- ✅ Other vector stores
- ❌ Structured Data KBs

---

#### 3. Bedrock Data Automation Parser
**Strategy:** `BEDROCK_DATA_AUTOMATION`

**Description:** Uses Amazon Bedrock's Data Automation parser for specialized document processing.

**Configuration:**
```json
{
  "parsingStrategy": "BEDROCK_DATA_AUTOMATION",
  "bedrockDataAutomationConfiguration": {
    // Configuration options (optional)
  }
}
```

**Parameters:** Configuration object (details vary)

**Use Case:** Specialized data extraction workflows

**Applicable To:**
- ✅ Vector stores (configuration dependent)
- ❌ Structured Data KBs

---

## Storage Configuration

### OpenSearch Serverless Configuration

**Configuration Object:** `opensearchServerlessConfiguration`

**Required Parameters:**

| Parameter | Type | Required | Min | Max | Pattern | Description |
|-----------|------|----------|-----|-----|---------|-------------|
| `collectionArn` | String | Yes | 0 | 2048 | `arn:aws:aoss:[a-z]{2}(-gov)?-[a-z]+-\d{1}:\d{12}:collection/[a-z0-9-]{3,32}` | ARN of OpenSearch collection |
| `vectorIndexName` | String | Yes | 0 | 2048 | `.*` | Name of vector index |
| `fieldMapping.vectorField` | String | Yes | 0 | 2048 | `.*` | Field name for vector embeddings |
| `fieldMapping.textField` | String | Yes | 0 | 2048 | `.*` | Field name for raw text |
| `fieldMapping.metadataField` | String | Yes | 0 | 2048 | `.*` | Field name for metadata |

**Vector Index Configuration:**
- Engine: `faiss` or `nmslib`
- Space Type: `l2` (Euclidean) or `cosinesimil` (Cosine)
- Dimensions: Match embedding model (1024 for Titan V2, 1024 for Cohere v3)

**Unique Features:**
- ✅ **Hybrid Search** (semantic + keyword)
- ✅ **Custom Analyzer Support** (ICU, Kuromoji for Japanese)
- ✅ **No chunk size limits** (beyond embedding model limits)
- ✅ **Full-text search capabilities**

**Example:**
```json
{
  "storageConfiguration": {
    "type": "OPENSEARCH_SERVERLESS",
    "opensearchServerlessConfiguration": {
      "collectionArn": "arn:aws:aoss:us-east-1:123456789012:collection/my-kb-collection",
      "vectorIndexName": "bedrock-knowledge-base-default-index",
      "fieldMapping": {
        "vectorField": "bedrock-knowledge-base-default-vector",
        "textField": "AMAZON_BEDROCK_TEXT_CHUNK",
        "metadataField": "AMAZON_BEDROCK_METADATA"
      }
    }
  }
}
```

---

### S3 Vectors Configuration

**Configuration Object:** `s3VectorsConfiguration`

**Parameters:**

| Parameter | Type | Required | Min | Max | Description |
|-----------|------|----------|-----|-----|-------------|
| `vectorBucketArn` | String | No | - | - | ARN of S3 bucket for vector storage |
| `indexArn` | String | No | - | - | ARN of vector index |
| `indexName` | String | No | 3 | 63 | Name of vector index |

**Vector Index Configuration:**
- Dimensions: 1-4096 (must match embedding model)
- Distance Metric: Cosine or Euclidean
- Embedding Type: Floating-point only (binary not supported)

**Metadata Limits:**
- Total metadata per vector: **40 KB max**
- Filterable metadata: **2 KB max**

**Unique Features & Constraints:**
- ⚠️ **Semantic search ONLY** (no hybrid search)
- ⚠️ **500 token chunk limit** (hard constraint)
- ✅ **Cost-effective** (lower than OpenSearch)
- ✅ **Sub-second query latency**
- ✅ **Long-term vector storage**

**Supported Embedding Models:**
- Amazon Titan Text Embedding V2 ✅
- Amazon Titan Image Embedding ✅
- Cohere English Embedding V3 ✅

**Supported Regions (Preview):**
- us-east-1, us-east-2, us-west-2, eu-central-1, ap-southeast-2

**Example:**
```json
{
  "storageConfiguration": {
    "type": "S3_VECTORS",
    "s3VectorsConfiguration": {
      "vectorBucketArn": "arn:aws:s3:::my-vector-bucket",
      "indexName": "my-knowledge-base-index"
    }
  }
}
```

---

### RDS (Aurora PostgreSQL) Configuration

**Configuration Object:** `rdsConfiguration`

**Required Parameters:**

| Parameter | Type | Required | Min | Max | Pattern | Description |
|-----------|------|----------|-----|-----|---------|-------------|
| `resourceArn` | String | Yes | - | - | ARN pattern | ARN of RDS cluster |
| `credentialsSecretArn` | String | Yes | - | - | ARN pattern | ARN of Secrets Manager secret |
| `databaseName` | String | Yes | 0 | 63 | `[a-zA-Z0-9_-]+` | Database name |
| `tableName` | String | Yes | 0 | 63 | `[a-zA-Z0-9_.-]+` | Table name |
| `fieldMapping.primaryKeyField` | String | Yes | 0 | 63 | `[a-zA-Z0-9_-]+` | Primary key column |
| `fieldMapping.vectorField` | String | Yes | 0 | 63 | `[a-zA-Z0-9_-]+` | Vector embeddings column |
| `fieldMapping.textField` | String | Yes | 0 | 63 | `[a-zA-Z0-9_-]+` | Text content column |
| `fieldMapping.metadataField` | String | Yes | 0 | 63 | `[a-zA-Z0-9_-]+` | Metadata column |
| `fieldMapping.customMetadataField` | String | No | 0 | 63 | `[a-zA-Z0-9_-]+` | Custom metadata column |

**Table Schema Requirements:**
```sql
CREATE TABLE knowledge_base_table (
    id UUID PRIMARY KEY,
    embedding VECTOR,  -- pgvector extension
    chunks TEXT,
    metadata JSONB,
    custom_metadata TEXT
);

-- Required indexes
CREATE INDEX ON knowledge_base_table USING ivfflat (embedding);
CREATE INDEX ON knowledge_base_table (chunks);
CREATE INDEX ON knowledge_base_table USING gin (metadata);
```

**Unique Features:**
- ✅ **Hybrid Search** (semantic + keyword)
- ✅ **SQL database integration**
- ✅ **Custom metadata columns**

**Example:**
```json
{
  "storageConfiguration": {
    "type": "RDS",
    "rdsConfiguration": {
      "resourceArn": "arn:aws:rds:us-east-1:123456789012:cluster:my-aurora-cluster",
      "credentialsSecretArn": "arn:aws:secretsmanager:us-east-1:123456789012:secret:my-db-creds",
      "databaseName": "knowledge_db",
      "tableName": "kb_vectors",
      "fieldMapping": {
        "primaryKeyField": "id",
        "vectorField": "embedding",
        "textField": "chunks",
        "metadataField": "metadata"
      }
    }
  }
}
```

---

### Redshift Configuration (Structured Data)

**Configuration Object:** `redshiftConfiguration` (for structured data KBs)

**Required Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `workgroupArn` | String | Yes (Serverless) | ARN of Redshift Serverless workgroup |
| `clusterIdentifier` | String | Yes (Provisioned) | Cluster identifier for Redshift Provisioned |
| `credentialsSecretArn` | String | Yes | ARN of Secrets Manager secret with DB credentials |
| `databaseName` | String | Yes | Name of Redshift database |
| `tableName` | String | Yes | Name of table/view to query |
| `authType` | String | Yes | `IAM`, `USERNAME_PASSWORD`, or `SECRETS_MANAGER` |

**Field Mapping for SQL KBs:**
- Uses schema metadata from Redshift or AWS Glue Data Catalog
- No vector embeddings required
- Natural language queries converted to SQL

**Unique Features:**
- ✅ **Natural Language to SQL** (NL2SQL)
- ✅ **Query structured data directly**
- ❌ **No chunking** (not applicable)
- ❌ **No parsing** (structured data)
- ❌ **No embeddings** (uses SQL queries)
- ✅ **Hybrid search** (supported via SQL)

**Optional Query Configurations:**
- `maxQueryTimeoutSeconds`: Maximum query execution time
- `tableDescriptions`: Descriptions for tables to improve SQL generation
- `columnDescriptions`: Descriptions for columns
- `tableInclusions`: Specific tables to include
- `tableExclusions`: Specific tables to exclude
- `curatedQueries`: Example questions with SQL queries

**Example:**
```json
{
  "storageConfiguration": {
    "type": "REDSHIFT",
    "redshiftConfiguration": {
      "workgroupArn": "arn:aws:redshift-serverless:us-east-1:123456789012:workgroup/my-workgroup",
      "credentialsSecretArn": "arn:aws:secretsmanager:us-east-1:123456789012:secret:redshift-creds",
      "databaseName": "sales_db",
      "tableName": "products",
      "authType": "SECRETS_MANAGER"
    }
  }
}
```

---

## Search & Retrieval Configuration

### Search Type Options

#### 1. Hybrid Search
**Value:** `HYBRID`

**Description:** Combines semantic search (vector embeddings) with keyword search (full-text).

**How It Works:**
1. Semantic search finds conceptually similar content via vector similarity
2. Keyword search finds exact/partial text matches
3. Results are merged and ranked

**Supported Storage Types:**
- ✅ **OpenSearch Serverless** (requires filterable text field)
- ✅ **OpenSearch Managed Cluster** (requires filterable text field)
- ❌ **S3 Vectors** (NOT supported)
- ✅ **RDS (Aurora)** (requires text column index)
- ✅ **MongoDB Atlas** (with text index)
- ✅ **Redshift** (structured data KBs)

**Requirements:**
- Vector store must have a filterable text field
- Text field must be indexed for full-text search

**Best For:**
- Queries with specific terminology
- Mixed conceptual and exact-match queries
- Technical documentation with jargon

---

#### 2. Semantic Search
**Value:** `SEMANTIC`

**Description:** Searches only vector embeddings for conceptually similar content.

**How It Works:**
1. Query text is converted to vector embedding
2. Vector similarity search (cosine/euclidean distance)
3. Returns most similar vectors

**Supported Storage Types:**
- ✅ **All vector stores** (universal support)
- ✅ **OpenSearch Serverless**
- ✅ **S3 Vectors** (ONLY option)
- ✅ **RDS (Aurora)**
- ✅ **All others**

**Best For:**
- Conceptual queries
- Paraphrased questions
- Multilingual searches (with appropriate embedding model)

---

### Retrieval Configuration Parameters

**Configuration Object:** `retrievalConfiguration`

| Parameter | Type | Min | Max | Default | Description |
|-----------|------|-----|-----|---------|-------------|
| `numberOfResults` | Integer | 1 | 100 | 5 | Number of chunks to retrieve |
| `searchType` | Enum | - | - | `HYBRID` | `HYBRID` or `SEMANTIC` |

**Metadata Filtering:**
- Up to 5 filters per query
- Operators: `equals`, `notEquals`, `greaterThan`, `lessThan`, `greaterThanOrEquals`, `lessThanOrEquals`, `in`, `notIn`, `contains`
- Logical operators: `AND`, `OR`

**Reranking:**
- Optional reranking models to improve result relevance
- Additional costs apply

**Example:**
```json
{
  "retrievalConfiguration": {
    "vectorSearchConfiguration": {
      "numberOfResults": 10,
      "searchType": "HYBRID",
      "filter": {
        "andAll": [
          {
            "equals": {
              "key": "category",
              "value": "electronics"
            }
          },
          {
            "greaterThan": {
              "key": "price",
              "value": 100
            }
          }
        ]
      }
    }
  }
}
```

---

## Embedding Models

### Supported Models

#### Amazon Titan Text Embedding V2
**Model ARN:** `arn:aws:bedrock:<region>::foundation-model/amazon.titan-embed-text-v2:0`

**Specifications:**
- Dimensions: 1024, 512, or 256 (configurable)
- Max Input Tokens: 8,192
- Languages: English, 100+ languages
- Normalization: L2 normalized

**Best For:**
- General-purpose text embedding
- Cost-sensitive applications
- S3 Vectors (recommended)

**Chunking Limits:**
- OpenSearch/RDS: Up to 8,192 tokens
- S3 Vectors: **500 tokens max**

---

#### Cohere Embed Multilingual V3
**Model ARN:** `arn:aws:bedrock:<region>::foundation-model/cohere.embed-multilingual-v3`

**Specifications:**
- Dimensions: 1024
- Max Input Tokens: 512
- Languages: 100+ languages
- Compression: Multilingual optimization

**Best For:**
- Multilingual applications
- Non-English content
- Cross-lingual search

**Chunking Limits:**
- OpenSearch/RDS: Up to 512 tokens
- S3 Vectors: **500 tokens max**

---

#### Amazon Titan Image Embedding
**Model ARN:** `arn:aws:bedrock:<region>::foundation-model/amazon.titan-embed-image-v1`

**Specifications:**
- Dimensions: 1024
- Input: Images + optional text
- Formats: JPEG, PNG

**Best For:**
- Multimodal search
- Image + text retrieval
- Visual similarity search

**Supported With:**
- ✅ S3 Vectors
- ✅ OpenSearch (with custom configuration)

---

## Complete Settings Matrix

### Vector Knowledge Bases

| Setting | OpenSearch Serverless | OpenSearch Managed | S3 Vectors | RDS (Aurora) | Others |
|---------|----------------------|-------------------|------------|--------------|--------|
| **Chunking** |
| Default | ✅ | ✅ | ✅ | ✅ | ✅ |
| Fixed Size | ✅ (up to 8192/512) | ✅ (up to 8192/512) | ✅ (**500 max**) | ✅ (up to 8192/512) | ✅ |
| Hierarchical | ✅ (up to 8192/512) | ✅ (up to 8192/512) | ✅ (**500 max**) | ✅ (up to 8192/512) | ✅ |
| Semantic | ✅ (up to 8192/512) | ✅ (up to 8192/512) | ✅ (**500 max**) | ✅ (up to 8192/512) | ✅ |
| None | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Parsing** |
| Default Parser | ✅ | ✅ | ✅ | ✅ | ✅ |
| Foundation Model | ✅ | ✅ | ✅ | ✅ | ✅ |
| Data Automation | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Search** |
| Semantic Search | ✅ | ✅ | ✅ | ✅ | ✅ |
| Hybrid Search | ✅ | ✅ | ❌ | ✅ | Varies |
| **Analyzer** |
| Custom Analyzer | ✅ (ICU, Kuromoji) | ✅ (ICU, Kuromoji) | ❌ | ❌ | ❌ |
| **Data Sources** |
| File Upload | ✅ | ✅ | ✅ | ✅ | ✅ |
| S3 Bucket | ✅ | ✅ | ✅ | ✅ | ✅ |
| Web Crawling | ✅ | ✅ | ✅ | ✅ | ✅ |
| Confluence | ✅ | ✅ | ✅ | ✅ | ✅ |
| Salesforce | ✅ | ✅ | ✅ | ✅ | ✅ |
| SharePoint | ✅ | ✅ | ✅ | ✅ | ✅ |

### Structured Data Knowledge Bases

| Setting | Redshift Serverless | Redshift Provisioned | SageMaker Lakehouse |
|---------|-------------------|---------------------|---------------------|
| **Chunking** | ❌ Not applicable | ❌ Not applicable | ❌ Not applicable |
| **Parsing** | ❌ Not applicable | ❌ Not applicable | ❌ Not applicable |
| **Search** |
| NL2SQL | ✅ | ✅ | ✅ |
| Hybrid Search | ✅ (via SQL) | ✅ (via SQL) | ✅ (via SQL) |
| **Data Sources** | Database connection | Database connection | Data lake connection |
| **Query Config** |
| Table Descriptions | ✅ | ✅ | ✅ |
| Column Descriptions | ✅ | ✅ | ✅ |
| Table Inclusions | ✅ | ✅ | ✅ |
| Table Exclusions | ✅ | ✅ | ✅ |
| Curated Queries | ✅ | ✅ | ✅ |
| Max Query Timeout | ✅ | ✅ | ✅ |

---

## Critical Constraints by KB Type

### OpenSearch Serverless
✅ **Supports:** All chunking, parsing, hybrid search, custom analyzers
⚠️ **Limits:** Standard embedding model token limits (8192/512)
💰 **Cost:** Higher than S3 Vectors (compute + storage)

### S3 Vectors (Preview)
✅ **Supports:** All chunking strategies, parsing, semantic search
⚠️ **Critical Limits:**
- **500 token max per chunk** (fixed_size, hierarchical, semantic)
- **Semantic search ONLY** (no hybrid)
- **40 KB metadata per vector, 2 KB filterable**
- **Floating-point embeddings only** (no binary)
💰 **Cost:** Lower than OpenSearch (storage-optimized)
📍 **Regions:** Limited (us-east-1, us-east-2, us-west-2, eu-central-1, ap-southeast-2)

### RDS (Aurora PostgreSQL)
✅ **Supports:** All chunking, parsing, hybrid search
⚠️ **Requires:** pgvector extension, specific table schema, indexes
💰 **Cost:** RDS instance costs + storage

### Redshift (Structured Data)
✅ **Supports:** NL2SQL, query configuration, hybrid search via SQL
❌ **Does NOT Support:** Chunking, parsing, embeddings, file upload
⚠️ **Requires:** Database connection, credentials, schema metadata
💰 **Cost:** Redshift query costs

---

## Implementation Checklist for Frontend

### Phase 1: Conditional Rendering

- [ ] **Hide OpenSearch Analyzer when:**
  - `storageType === 'S3_VECTOR'`
  - `knowledgeBaseKind === 'SQL'`

- [ ] **Hide Chunking Configuration when:**
  - `knowledgeBaseKind === 'SQL'`

- [ ] **Hide Parsing Configuration when:**
  - `knowledgeBaseKind === 'SQL'`

- [ ] **Enforce 500 Token Limit when:**
  - `storageType === 'S3_VECTOR'`
  - For all chunking strategies: fixed_size, hierarchical, semantic

- [ ] **Force Semantic Search when:**
  - `storageType === 'S3_VECTOR'`
  - Disable hybrid search option

- [ ] **Hide File Upload / URL Inputs when:**
  - `knowledgeBaseKind === 'SQL'`

- [ ] **Show Database Connection Form when:**
  - `knowledgeBaseKind === 'SQL'`

### Phase 2: Validation Rules

- [ ] **Fixed Size Chunking Validation:**
  - OpenSearch/RDS: `maxTokens` ≤ 8192 (Titan) or 512 (Cohere)
  - S3 Vectors: `maxTokens` ≤ 500
  - `overlapPercentage`: 1-99

- [ ] **Hierarchical Chunking Validation:**
  - OpenSearch/RDS: parent/child ≤ 8192 (Titan) or 512 (Cohere)
  - S3 Vectors: parent/child ≤ 500
  - `overlapTokens` ≥ 1

- [ ] **Semantic Chunking Validation:**
  - OpenSearch/RDS: `maxTokens` ≤ 8192 (Titan) or 512 (Cohere)
  - S3 Vectors: `maxTokens` ≤ 500
  - `bufferSize`: 0-1
  - `breakpointPercentileThreshold`: 50-99

- [ ] **Search Type Validation:**
  - S3 Vectors: Force `searchType = 'semantic'`
  - Others: Allow `'hybrid'` or `'semantic'`

- [ ] **SQL KB Validation:**
  - Require: workgroupArn, databaseName, tableName, secretArn
  - Require field mapping: id, content, metadata columns

### Phase 3: User Experience

- [ ] **Add Warning Alerts:**
  - S3 Vectors: "⚠️ 500 token limit, semantic search only"
  - Semantic Chunking: "⚠️ Additional costs apply (foundation model usage)"
  - Foundation Model Parsing: "⚠️ Additional costs apply"

- [ ] **Add Info Badges:**
  - "OpenSearch only" for Analyzer settings
  - "Vector KBs only" for Chunking
  - "Vector KBs only" for Parsing

- [ ] **Update Help Text:**
  - Mention applicability per KB type
  - Link to AWS documentation

---

## AWS Documentation References

- [Knowledge Base Setup](https://docs.aws.amazon.com/bedrock/latest/userguide/knowledge-base-setup.html)
- [Chunking Strategies](https://docs.aws.amazon.com/bedrock/latest/userguide/kb-chunking-parsing.html)
- [S3 Vectors with Bedrock](https://docs.aws.amazon.com/AmazonS3/latest/userguide/s3-vectors-bedrock-kb.html)
- [Structured Data KBs](https://docs.aws.amazon.com/bedrock/latest/userguide/knowledge-base-structured-create.html)
- [CreateKnowledgeBase API](https://docs.aws.amazon.com/bedrock/latest/APIReference/API_agent_CreateKnowledgeBase.html)
- [ChunkingConfiguration API](https://docs.aws.amazon.com/bedrock/latest/APIReference/API_agent_ChunkingConfiguration.html)
- [StorageConfiguration API](https://docs.aws.amazon.com/bedrock/latest/APIReference/API_agent_StorageConfiguration.html)

---

## Notes for Implementation Team

1. **S3 Vectors 500 Token Limit is CRITICAL**
   This is a hard constraint in the AWS API. UI must prevent users from entering values > 500 when S3 Vectors is selected.

2. **Hybrid Search is NOT Available for S3 Vectors**
   The API will reject hybrid search for S3 Vectors. UI should hide this option and force semantic.

3. **SQL KBs Have No Chunking/Parsing**
   These settings don't make sense for structured data. Hide entire sections when SQL KB is selected.

4. **OpenSearch Analyzer Only for OpenSearch**
   S3 Vectors and other stores don't use OpenSearch analyzers. Hide this configuration.

5. **Embedding Model Affects Token Limits**
   Cohere has 512 max, Titan has 8192 max (except S3 Vectors which is always 500).

6. **Preview Features**
   S3 Vectors is in preview - show beta badge and warning about potential changes.

7. **Cost Warnings**
   Semantic chunking and foundation model parsing incur additional charges - warn users.

---

**End of Reference Document**
