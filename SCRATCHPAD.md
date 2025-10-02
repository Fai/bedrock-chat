# SQL Knowledge Base Implementation - Development Scratchpad

## Current Session: 2025-10-02

### Implementation Progress

#### ✅ Completed
1. **Backend Data Models** (backend/app/routes/schemas/bot_kb.py)
   - Added SQL KB schemas: SqlDatabaseConfig, SqlKnowledgeBaseInput/Output
   - Added query schemas: SqlQueryInput/Output, KnowledgeBaseStatusOutput
   - Decision: Keep separate from VECTOR KB schemas for clarity

2. **Backend Repository Models** (backend/app/repositories/models/custom_bot_kb.py)
   - Added SqlDatabaseConfigModel, SqlKnowledgeBaseModel
   - Decision: Follow existing pattern with BaseModel for DynamoDB storage

3. **Backend Repository Functions** (backend/app/repositories/sql_knowledge_base.py)
   - create_sql_knowledge_base(): Creates Bedrock KB with Redshift data source
   - get_ingestion_job_status(): Monitors ingestion progress
   - query_sql_knowledge_base(): Natural language to SQL query
   - delete_sql_knowledge_base(): KB cleanup
   - Helper functions: extract_sql_from_citations(), extract_results_from_citations()
   - Decision: Separate file from knowledge_base.py to keep SQL logic isolated

#### 🔄 In Progress
- None currently

#### 📋 Next Steps
1. API Endpoints (backend/app/routes/bot.py)
   - POST /bots/{bot_id}/knowledge-base/sql
   - GET /bots/{bot_id}/knowledge-base/status
   - POST /bots/{bot_id}/knowledge-base/query
   - DELETE /bots/{bot_id}/knowledge-base

2. Unit Tests (backend/tests/)
   - test_repositories/test_sql_knowledge_base.py
   - test_routes/test_bot_sql_kb.py
   - Target: >80% coverage

3. Frontend TypeScript Types
4. Frontend UI Components
5. CDK Infrastructure (IAM roles)

### Key Decisions

1. **Architecture**
   - SQL KB uses same Bedrock Knowledge Base API but with REDSHIFT storage type
   - Separate repository file (sql_knowledge_base.py) for better maintainability
   - Reuse existing SearchParams for consistency with VECTOR KB

2. **Field Mapping**
   - Required fields: id, content, metadata (Bedrock KB requirement)
   - Stored in SqlDatabaseConfig for flexibility
   - Customer must provide mapping during bot creation

3. **Environment Variables Required**
   - BEDROCK_KB_ROLE_ARN: IAM role for Bedrock → Redshift access
   - DEFAULT_MODEL_ARN: Default LLM for query processing
   - These will be added to backend/.env.template

4. **Error Handling**
   - Fail fast on missing env vars (BEDROCK_KB_ROLE_ARN)
   - Graceful degradation on ingestion job status checks
   - Log all errors for debugging

### Issues & Resolutions

#### Issue #1: Embedding Model ARN
- **Problem**: SQL KB still uses vector embeddings for semantic search
- **Resolution**: Added embedding_model_arn field to SqlDatabaseConfig with Titan v2 default
- **Rationale**: Bedrock KB SQL type combines structured data with vector search

#### Issue #2: Data Source ID Retrieval
- **Problem**: Create KB response doesn't directly return data source ID
- **Resolution**: Added list_data_sources() call after KB creation
- **Rationale**: Need data source ID for ingestion job monitoring

### Code Style Notes

1. **Docstrings**: Using Google-style docstrings (Args, Returns, Raises)
2. **Type Hints**: Full type annotations for all functions
3. **Logging**: logger.info for operations, logger.error for failures
4. **Error Handling**: Try-except with specific error messages

### Testing Strategy

1. **Unit Tests**
   - Mock bedrock_agent_client and bedrock_agent_runtime_client
   - Test happy path and error cases
   - Verify field mapping correctness

2. **Integration Tests**
   - Requires test Redshift database
   - Optional: Use LocalStack for local Bedrock mock

3. **Coverage Target**: >80% for all new code

### Dependencies

**Python Libraries** (already in project):
- boto3 (AWS SDK)
- pydantic (data validation)
- logging (built-in)

**AWS Services**:
- Amazon Bedrock (Knowledge Bases, Agent Runtime)
- Amazon Redshift Serverless (customer-deployed)
- AWS Secrets Manager (credentials)

### Environment Setup

**Required Environment Variables**:
```bash
BEDROCK_KB_ROLE_ARN=arn:aws:iam::123456789012:role/BedrockKbRole
DEFAULT_MODEL_ARN=arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-5-sonnet-20241022-v2:0
BEDROCK_REGION=us-east-1
```

**Customer Prerequisites**:
- Redshift Serverless workgroup deployed
- Database with table/view having fields: id, content, metadata
- Secrets Manager secret with Redshift credentials
- Workgroup ARN and Secret ARN documented

### Git Strategy

**Branch**: feature/sql-knowledge-base
**Commits**: Atomic, conventional commits
- feat: for new features
- fix: for bug fixes
- test: for test additions
- docs: for documentation

**Current Commit**: feat(backend): add SQL Knowledge Base data models and repository

### Performance Considerations

1. **Query Latency**: Target <3 seconds (P95)
2. **Ingestion Time**: Depends on table size, monitor with get_ingestion_job_status()
3. **Concurrent Queries**: Bedrock KB handles concurrency, no client-side pooling needed

### Security Considerations

1. **IAM**: Least privilege - KB role only has Redshift Data API + Secrets Manager read
2. **Credentials**: Never logged, always in Secrets Manager
3. **User Isolation**: Row-level access via existing bot permissions (not KB-level)

---

**Last Updated**: 2025-10-02 15:45 UTC
**Developer**: Claude Code
**Status**: Backend foundation complete, moving to API endpoints
