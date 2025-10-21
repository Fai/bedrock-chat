# AWS Bedrock Knowledge Base Types - Complete Reference

**Document Version**: 1.0
**Last Updated**: 2025-10-08
**Status**: Official AWS Documentation Summary

---

## Table of Contents

1. [Overview](#overview)
2. [Knowledge Base Types](#knowledge-base-types)
3. [Vector Store Knowledge Bases](#vector-store-knowledge-bases)
4. [SQL Knowledge Bases](#sql-knowledge-bases)
5. [Kendra GenAI Index](#kendra-genai-index)
6. [Storage Backend Comparison](#storage-backend-comparison)
7. [Limitations and Quotas](#limitations-and-quotas)
8. [Regional Availability](#regional-availability)

---

## Overview

AWS Bedrock Knowledge Bases support three primary types of knowledge bases, each optimized for different use cases and data types.

### Knowledge Base Type Matrix

| KB Type | Configuration Type | Use Case | Data Format | Query Method |
|---------|-------------------|----------|-------------|--------------|
| **VECTOR** | `"VECTOR"` | Semantic search, RAG | Unstructured text, documents | Vector similarity search |
| **SQL** | `"SQL"` | Structured data queries | Relational databases | Natural Language to SQL |
| **KENDRA** | `"KENDRA"` | Enterprise search | Mixed structured/unstructured | Hybrid search (keyword + semantic) |

---

## Knowledge Base Types

### 1. VECTOR Knowledge Bases

**Purpose**: Store and retrieve unstructured data using vector embeddings for semantic similarity search.

**Configuration Type**: `knowledgeBaseConfiguration.type = "VECTOR"`

**Supported Storage Backends**:
- Amazon OpenSearch Serverless
- Amazon S3 Vectors (Preview)
- Amazon Aurora PostgreSQL with pgvector
- Pinecone
- Redis Enterprise Cloud
- MongoDB Atlas

**Key Features**:
- Semantic search using embeddings
- Similarity scoring (cosine, Euclidean, dot product)
- Metadata filtering
- Chunking strategies (FIXED_SIZE, HIERARCHICAL, SEMANTIC, NONE)
- Multiple embedding model support

**Best For**:
- Document retrieval (PDFs, Word docs, text files)
- Knowledge articles and FAQs
- Unstructured text content
- Customer support documentation

---

### 2. SQL Knowledge Bases

**Purpose**: Query structured data in data warehouses and data lakes using natural language.

**Configuration Type**: `knowledgeBaseConfiguration.type = "SQL"`

**Supported Storage Backends**:
- Amazon Redshift Serverless (via RDS configuration)
- Amazon Aurora PostgreSQL (via RDS configuration)
- Amazon Athena (future support)

**Key Features**:
- Natural Language to SQL conversion
- Direct database querying
- Structured data retrieval
- Join operations across tables
- Aggregations and analytics

**Best For**:
- Business intelligence queries
- Analytics and reporting
- Structured database queries
- Data warehouse queries
- Transactional data analysis

**Important Note**: Currently uses `knowledgeBaseConfiguration.type = "VECTOR"` with `storageConfiguration.type = "RDS"` for Redshift/Aurora integration.

---

### 3. Kendra GenAI Index

**Purpose**: Leverage Amazon Kendra's hybrid search capabilities for enterprise-grade search.

**Configuration Type**: `knowledgeBaseConfiguration.type = "KENDRA"`

**Key Features**:
- Hybrid search (keyword + semantic)
- Native connector support (SharePoint, S3, Salesforce, etc.)
- Document ranking and relevance tuning
- Access control and security filtering
- Pre-built NLP capabilities

**Best For**:
- Enterprise search applications
- Multi-source content aggregation
- Complex access control requirements
- Established Kendra deployments

**Limitations**:
- Higher cost compared to vector stores
- Regional availability constraints
- Requires separate Kendra index management

---

## Vector Store Knowledge Bases

### Storage Backend Options

#### 1. OpenSearch Serverless

**Pros**:
- Fully managed, serverless
- Auto-scaling capabilities
- Rich query language
- Supports both floating-point and binary vectors
- Metadata filtering

**Cons**:
- Minimum 4 OCU allocation (~$700/month minimum)
- Higher cost for small workloads
- Cannot use OpenSearch domains behind VPC

**Configuration**:
```python
storageConfiguration={
    "type": "OPENSEARCH_SERVERLESS",
    "opensearchServerlessConfiguration": {
        "collectionArn": "arn:aws:aoss:...",
        "vectorIndexName": "bedrock-knowledge-base-index",
        "fieldMapping": {
            "vectorField": "embedding",
            "textField": "text",
            "metadataField": "metadata"
        }
    }
}
```

**Best Practices**:
- Use FAISS engine for vector index
- Set appropriate shard count based on data size
- Enable standby replicas for production (high availability)
- Use collection-level encryption

---

#### 2. Amazon S3 Vectors (Preview)

**Pros**:
- 99% cost reduction vs OpenSearch Serverless
- $0.13/month per 1 million 1024-dimension vectors
- Sub-second query latency
- Auto-provisioned by Bedrock (Quick Create)
- Simple setup, no index management

**Cons**:
- **Preview feature** (not production-ready)
- **500 token chunking limit** (critical constraint)
- Semantic search only (no hybrid search)
- Limited regional availability (5 regions)
- Floating-point vectors only (no binary)

**Supported Regions**:
- US East (N. Virginia) - us-east-1
- US East (Ohio) - us-east-2
- US West (Oregon) - us-west-2
- Europe (Frankfurt) - eu-central-1
- Asia Pacific (Sydney) - ap-southeast-2

**Limitations**:
- **Maximum 500 tokens per chunk** (enforced by metadata size)
- Maximum 40 KB metadata per vector
- Maximum 2 KB filterable metadata per vector
- Binary embeddings not supported
- 10,000 vector buckets per region per account

**Configuration**:
```python
storageConfiguration={
    "type": "S3_VECTORS",
    "s3VectorsConfiguration": {}  # Empty for Quick Create
}
```

**Best For**:
- Cost-sensitive deployments
- Short document chunks (< 500 tokens)
- Simple semantic search use cases
- Development and testing

**NOT Suitable For**:
- Long-form documents requiring large chunks
- Production deployments (preview status)
- Hybrid search requirements
- Regions outside the 5 supported ones

---

#### 3. Amazon Aurora PostgreSQL with pgvector

**Pros**:
- Native AWS integration
- Relational database benefits (ACID transactions)
- Cost-effective for existing Aurora users
- Advanced querying capabilities
- Fine-grained access control
- Multi-tenant support

**Cons**:
- Requires manual database setup
- Must manage indexes and performance tuning
- Not serverless (provisioned capacity)
- Standard RDS PostgreSQL NOT supported (Aurora only)

**Requirements**:
- Aurora PostgreSQL version 16.4 or higher
- pgvector extension 0.5.0 or higher (HNSW indexing support)
- RDS Data API enabled
- AWS Secrets Manager for credentials

**Required Table Schema**:
```sql
CREATE TABLE bedrock_integration.bedrock_kb (
    id UUID PRIMARY KEY,
    embedding vector(1024),  -- Dimension matches embedding model
    chunks TEXT NOT NULL,
    metadata JSONB
);

-- Required indexes
CREATE INDEX ON bedrock_integration.bedrock_kb
    USING hnsw (embedding vector_cosine_ops)
    WITH (ef_construction=256);

CREATE INDEX ON bedrock_integration.bedrock_kb (chunks);
```

**Configuration**:
```python
storageConfiguration={
    "type": "RDS",
    "rdsConfiguration": {
        "resourceArn": "arn:aws:rds:us-east-1:123456789012:cluster:my-aurora-cluster",
        "credentialsSecretArn": "arn:aws:secretsmanager:us-east-1:123456789012:secret:...",
        "databaseName": "postgres",
        "tableName": "bedrock_integration.bedrock_kb",
        "fieldMapping": {
            "primaryKeyField": "id",
            "vectorField": "embedding",
            "textField": "chunks",
            "metadataField": "metadata"
        }
    }
}
```

**Best Practices**:
- Use Aurora Quick Create for automated setup
- Enable RDS Data API for serverless access
- Use HNSW indexing for performance
- Set appropriate `ef_construction` and `ef_search` parameters
- Monitor RDS Performance Insights
- Use read replicas for high query volumes
- Enable encryption at rest

**Cost Considerations**:
- Aurora Serverless v2: Pay per ACU (0.5-128 ACU)
- Provisioned: Instance pricing (db.r6g.large ~$0.24/hr)
- Storage: $0.10/GB/month
- I/O: $0.20 per 1M requests (Serverless v2)

---

#### 4. Third-Party Vector Stores

**Pinecone**:
- Managed vector database service
- Serverless and pod-based options
- Simple API
- Good documentation

**Redis Enterprise Cloud**:
- In-memory vector search
- Ultra-low latency
- Hybrid data structures

**MongoDB Atlas**:
- Native vector search
- Combined document + vector storage
- Familiar MongoDB interface

**Common Requirements**:
- Endpoint URL
- Credentials in AWS Secrets Manager
- Field mapping configuration
- API key or connection string

---

## SQL Knowledge Bases

### Current Implementation Architecture

**Important**: AWS Bedrock SQL Knowledge Bases currently use VECTOR KB type with RDS storage for querying structured data.

```python
knowledgeBaseConfiguration={
    "type": "VECTOR",  # Not "SQL"
    "vectorKnowledgeBaseConfiguration": {
        "embeddingModelArn": "arn:aws:bedrock:us-east-1::foundation-model/amazon.titan-embed-text-v2:0"
    }
}
storageConfiguration={
    "type": "RDS",
    "rdsConfiguration": {
        "resourceArn": "arn:aws:redshift-serverless:us-east-1:123456789012:workgroup/...",
        "databaseName": "mydb",
        "tableName": "my_table",
        "credentialsSecretArn": "arn:aws:secretsmanager:...",
        "fieldMapping": {
            "primaryKeyField": "id",
            "vectorField": "embedding",
            "textField": "content",
            "metadataField": "metadata"
        }
    }
}
```

### Supported Backends

#### 1. Amazon Redshift Serverless

**Pros**:
- Fully managed data warehouse
- Auto-scaling compute
- Cost-effective for infrequent queries (auto-pause)
- Petabyte-scale data
- Standard SQL support

**Cons**:
- Higher cost for frequent queries
- Cold start latency after auto-pause
- Minimum 8 RPU base capacity ($0.36/hour)

**ARN Format**:
```
arn:aws:redshift-serverless:us-east-1:123456789012:workgroup/<workgroup-name>
```

**Cost**:
- $0.36/hour per RPU (8 RPU minimum = $2.88/hour)
- Auto-pause after 60 minutes of inactivity
- $45/TB/month for managed storage

**Best For**:
- Large datasets (> 100 GB)
- Complex analytics queries
- Infrequent query patterns
- Data warehouse consolidation

---

#### 2. Amazon Aurora PostgreSQL

**Pros**:
- Lower cost for frequent queries
- Faster query response times
- Better for transactional workloads
- Read replicas for high availability
- Point-in-time recovery

**Cons**:
- Limited to 128 TB storage
- Requires more management than Redshift
- Not optimized for analytics at scale

**ARN Format**:
```
arn:aws:rds:us-east-1:123456789012:cluster:<cluster-name>
```

**Cost**:
- Aurora Serverless v2: $0.12/hour per ACU (0.5 ACU minimum = $0.06/hour)
- Provisioned: $0.087/hour (db.t4g.medium) to $3.26/hour (db.r6g.xlarge)
- Storage: $0.10/GB/month
- I/O: $0.20 per 1M requests

**Best For**:
- Small to medium datasets (< 10 TB)
- Frequent query patterns
- Transactional + analytical workloads
- Cost-sensitive deployments

---

### Natural Language to SQL Query Flow

1. User submits natural language query
2. Bedrock generates SQL query from NL input
3. SQL executes on Redshift/Aurora database
4. Results retrieved and formatted
5. LLM generates natural language response with data

**Example**:
- **User Query**: "What were the top 5 products by revenue last month?"
- **Generated SQL**: `SELECT product_name, SUM(revenue) FROM sales WHERE date >= '2025-09-01' AND date < '2025-10-01' GROUP BY product_name ORDER BY SUM(revenue) DESC LIMIT 5;`
- **Response**: Natural language answer with structured data

---

## Kendra GenAI Index

### Overview

Amazon Kendra provides hybrid search combining keyword matching with semantic understanding.

**Configuration Type**: `knowledgeBaseConfiguration.type = "KENDRA"`

### Key Features

- **Hybrid Search**: Combines BM25 (keyword) with neural semantic search
- **Native Connectors**: SharePoint, Salesforce, ServiceNow, S3, Confluence, etc.
- **Document Ranking**: ML-powered relevance scoring
- **Access Control**: Integrate with AD, SAML, OAuth
- **Faceted Search**: Filter by metadata attributes

### Limitations

- Higher cost: $1.40/hour for Enterprise edition
- Limited regional availability
- Requires separate index management
- Complex setup compared to vector stores

### Use Cases

- Enterprise search portals
- Multi-source content aggregation
- Compliance-heavy environments
- Legacy Kendra deployments

---

## Storage Backend Comparison

### Cost Comparison (12 Months, 1M vectors, 1024 dimensions, 100 queries/day)

| Storage Type | Setup | Monthly Cost | 12-Month Total | Notes |
|--------------|-------|--------------|----------------|-------|
| **S3 Vectors** | Auto | $0.13 | $1.56 | Preview only, 500 token limit |
| **Aurora Serverless v2** | Manual | $43.80 | $525.60 | 0.5 ACU base, scales to 1 ACU |
| **Aurora Provisioned (db.t4g.medium)** | Manual | $62.64 | $751.68 | Fixed capacity |
| **OpenSearch Serverless** | Auto | $700.80 | $8,409.60 | 4 OCU minimum |
| **Redshift Serverless** | Manual | $259.20 | $3,110.40 | 8 RPU base, auto-pause |

### Performance Comparison

| Storage Type | Query Latency | Scalability | Setup Complexity |
|--------------|---------------|-------------|------------------|
| **S3 Vectors** | < 1 second | Auto | Very Low (Quick Create) |
| **Aurora** | < 100ms | High (read replicas) | Medium (manual schema) |
| **OpenSearch** | < 50ms | Very High (auto-scaling) | Low (managed) |
| **Redshift** | 1-5 seconds | Very High (MPP) | Medium (manual setup) |
| **Pinecone** | < 50ms | Very High | Low (managed) |

### Feature Comparison

| Feature | S3 Vectors | Aurora | OpenSearch | Redshift | Pinecone |
|---------|-----------|---------|------------|----------|----------|
| **Quick Create** | ✅ Yes | ⚠️ Partial | ✅ Yes | ❌ No | ❌ No |
| **Auto-Scaling** | ✅ Yes | ⚠️ Serverless v2 | ✅ Yes | ⚠️ Limited | ✅ Yes |
| **Hybrid Search** | ❌ No | ❌ No | ✅ Yes | ❌ No | ❌ No |
| **Metadata Filtering** | ✅ Yes (2 KB) | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes |
| **Binary Vectors** | ❌ No | ✅ Yes | ✅ Yes | ❌ No | ✅ Yes |
| **Multi-Tenancy** | ⚠️ Limited | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes |
| **ACID Transactions** | ❌ No | ✅ Yes | ❌ No | ✅ Yes | ❌ No |

---

## Limitations and Quotas

### General Knowledge Base Limits

| Resource | Limit | Notes |
|----------|-------|-------|
| **Knowledge Bases per Account** | 100 | Soft limit, can request increase |
| **Data Sources per KB** | 10 | Soft limit |
| **Metadata per Vector** | 40 KB | Hard limit |
| **Filterable Metadata per Vector** | 2 KB | Hard limit for query filtering |
| **Max Document Size** | 50 MB | Per document in S3 data source |
| **Max Documents per Ingestion Job** | 1,000,000 | Soft limit |

### S3 Vectors Specific Limits

| Resource | Limit | Impact |
|----------|-------|--------|
| **Chunk Token Limit** | 500 tokens | **CRITICAL**: Cannot exceed |
| **Vector Buckets per Region** | 10,000 | Per AWS account |
| **Supported Regions** | 5 regions | us-east-1/2, us-west-2, eu-central-1, ap-southeast-2 |
| **Vector Types** | Floating-point only | No binary vectors |
| **Search Type** | Semantic only | No keyword/hybrid search |

### Aurora PostgreSQL Limits

| Resource | Limit | Notes |
|----------|-------|-------|
| **Maximum Storage** | 128 TB | Per Aurora cluster |
| **Maximum ACUs** | 128 ACU | Serverless v2 |
| **Read Replicas** | 15 | Per cluster |
| **pgvector Version** | 0.5.0+ | Required for HNSW indexing |
| **Aurora Version** | 16.4+ | Required for Bedrock integration |

### Redshift Serverless Limits

| Resource | Limit | Notes |
|----------|-------|-------|
| **Base RPU Capacity** | 8 RPU | Minimum ($0.36/hour) |
| **Maximum RPU Capacity** | 512 RPU | $23.04/hour |
| **Auto-Pause Timeout** | 60 minutes | Minimum idle time |
| **Cold Start Latency** | 30-60 seconds | After auto-pause |

### Embedding Model Limits

| Model | Max Input Tokens | Dimensions | Cost per 1K Tokens |
|-------|------------------|------------|-------------------|
| **Titan Text v2** | 8,192 | 1024, 512, 256 | $0.0001 |
| **Titan Text v1** | 8,192 | 1536 | $0.0001 |
| **Cohere Embed English** | 512 | 1024 | $0.0001 |
| **Cohere Embed Multilingual v3** | 512 | 1024 | $0.0001 |

---

## Regional Availability

### Bedrock Knowledge Bases Availability

**Supported Regions** (as of January 2025):
- US East (N. Virginia) - us-east-1
- US East (Ohio) - us-east-2
- US West (Oregon) - us-west-2
- Europe (Frankfurt) - eu-central-1
- Europe (Ireland) - eu-west-1
- Asia Pacific (Singapore) - ap-southeast-1
- Asia Pacific (Sydney) - ap-southeast-2
- Asia Pacific (Tokyo) - ap-northeast-1

### S3 Vectors Preview Regions

**Limited Availability** (Preview):
- US East (N. Virginia) - us-east-1 ✅
- US East (Ohio) - us-east-2 ✅
- US West (Oregon) - us-west-2 ✅
- Europe (Frankfurt) - eu-central-1 ✅
- Asia Pacific (Sydney) - ap-southeast-2 ✅

### Aurora PostgreSQL with pgvector

**Available in all Aurora PostgreSQL regions** (40+ regions globally)

### Important Regional Considerations

1. **S3 Vectors**: Only 5 regions during preview
2. **OpenSearch Serverless**: Not available in all Bedrock regions (check availability)
3. **Redshift Serverless**: Available in 20+ regions
4. **Cross-Region**: KB and storage must be in same region
5. **Data Residency**: Ensure compliance with data sovereignty requirements

---

## Best Practices Summary

### Choosing the Right Knowledge Base Type

**Use VECTOR KB with S3 Vectors when**:
- ✅ Cost is primary concern ($0.13/month vs $700/month)
- ✅ Documents have short chunks (< 500 tokens)
- ✅ Deploying in supported regions
- ✅ Semantic search only (no hybrid search needed)
- ⚠️ Preview status is acceptable

**Use VECTOR KB with Aurora when**:
- ✅ Need relational database benefits
- ✅ Frequent queries (> 100/day)
- ✅ Multi-tenant requirements
- ✅ Budget is moderate ($50-100/month)
- ✅ Existing Aurora infrastructure

**Use VECTOR KB with OpenSearch when**:
- ✅ Need hybrid search (keyword + semantic)
- ✅ High query volume (1000s/day)
- ✅ Complex metadata filtering
- ✅ Budget allows ($700+/month)
- ✅ Production-critical workloads

**Use SQL KB with Redshift when**:
- ✅ Large datasets (> 100 GB)
- ✅ Complex analytics queries
- ✅ Infrequent query patterns
- ✅ Data warehouse use cases

**Use SQL KB with Aurora when**:
- ✅ Small to medium datasets (< 10 TB)
- ✅ Frequent queries
- ✅ Transactional + analytical hybrid
- ✅ Cost-sensitive (40-65% cheaper than Redshift)

**Use Kendra GenAI Index when**:
- ✅ Enterprise search requirements
- ✅ Multi-source content aggregation
- ✅ Complex access control
- ✅ Existing Kendra deployment

---

## References

- [AWS Bedrock Knowledge Bases Documentation](https://docs.aws.amazon.com/bedrock/latest/userguide/knowledge-base.html)
- [CreateKnowledgeBase API Reference](https://docs.aws.amazon.com/bedrock/latest/APIReference/API_agent_CreateKnowledgeBase.html)
- [Aurora PostgreSQL with pgvector](https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/AuroraPostgreSQL.VectorDB.html)
- [S3 Vectors Documentation](https://docs.aws.amazon.com/AmazonS3/latest/userguide/s3-vectors-bedrock-kb.html)
- [S3 Vectors Limitations](https://docs.aws.amazon.com/AmazonS3/latest/userguide/s3-vectors-limitations.html)
- [Bedrock Quotas](https://docs.aws.amazon.com/bedrock/latest/userguide/quotas.html)

---

**Document Maintained By**: Development Team
**Next Review**: After S3 Vectors GA release
