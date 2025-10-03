# SQL Knowledge Base Implementation Plan

## Overview

This document outlines the implementation plan for adding SQL structured knowledge base support to the Bedrock Chat application. This feature will extend the current VECTOR-based knowledge base system to also support SQL databases for structured data querying via Amazon Bedrock Knowledge Bases.

## Current State Analysis

### Existing Technology Stack
- **Backend**: Python (FastAPI) with Pydantic for data validation
- **Frontend**: React with TypeScript, Tailwind CSS  
- **Infrastructure**: AWS CDK (TypeScript)
- **Knowledge Base Type**: VECTOR only (Amazon Bedrock Knowledge Bases)
- **Vector Database**: Amazon OpenSearch Serverless
- **Document Storage**: Amazon S3
- **Main Database**: Amazon DynamoDB (conversations, bots, users)
- **Search Types**: Hybrid and Semantic search
- **Embeddings**: Titan v2, Cohere Multilingual v3

### Current Knowledge Base Features
- Document chunking strategies (default, fixed_size, hierarchical, semantic, none)
- Web crawling support for external content ingestion
- Advanced parsing with Claude models
- OpenSearch Serverless backend with full-text and vector search
- Multi-language analyzer support (ICU, Kuromoji)

### SQL KB Infrastructure Already Present
✅ **Type Definition**: `type_kb_resource_type = Literal["VECTOR", "KENDRA", "SQL"]` exists in codebase
❌ **Implementation**: SQL type is defined but not implemented in UI or backend logic

## Implementation Plan

### Phase 1: Infrastructure & Database Setup

#### 1.1 CDK Infrastructure Changes
**Files to Create/Modify:**
- `cdk/lib/constructs/sql-database.ts` (NEW)
- `cdk/lib/bedrock-chat-stack.ts` (MODIFY)

**Tasks:**
1. Add Amazon Redshift Serverless construct
2. Configure VPC and security groups for database access
3. Set up database initialization scripts and schema management
4. Add IAM roles for Bedrock Knowledge Base SQL integration
5. Configure Redshift Data API access and monitoring
6. Set up S3 bucket for data staging and COPY operations

**Technical Specifications:**
```typescript
// Redshift Serverless Configuration
- Engine: Amazon Redshift Serverless
- Scaling: 8-64 RPU (Redshift Processing Units)
- VPC: Private subnets only
- Encryption: At rest and in transit
- Backup: Automated snapshots
- Monitoring: CloudWatch integration
- Data API: Enabled for programmatic access
```

#### 1.2 Database Schema Design
**Schema Components:**
1. **Knowledge Schema Registry** - Store table schemas and metadata
2. **Data Tables** - User-uploaded structured data
3. **Query Templates** - Predefined SQL query templates
4. **Access Controls** - Row-level security if needed

### Phase 2: Backend API Development

#### 2.1 Data Models Extension
**Files to Modify:**
- `backend/app/routes/schemas/bot_kb.py`
- `backend/app/repositories/models/custom_bot_kb.py`

**New Schema Classes:**
```python
class SqlDatabaseConfig(BaseSchema):
    connection_string: str
    schema_name: str
    table_names: list[str]
    query_templates: list[str] = []

class SqlKnowledgeBaseInput(BaseSchema):
    database_config: SqlDatabaseConfig
    search_params: SearchParams
    knowledge_base_id: str | None = None
```

#### 2.2 Repository Layer Updates  
**Files to Modify:**
- `backend/app/repositories/knowledge_base.py`

**New Functions:**
```python
def create_sql_knowledge_base(config: SqlKnowledgeBaseInput) -> str
def validate_database_schema(connection_string: str, schema_name: str) -> bool
def execute_sql_query(kb_id: str, query: str) -> list[dict]
def get_table_schema(kb_id: str, table_name: str) -> dict
```

#### 2.3 API Endpoints
**Files to Modify:**
- `backend/app/routes/bot.py` (or relevant route file)

**New Endpoints:**
- `POST /bots/{bot_id}/sql-knowledge-base` - Create SQL KB
- `GET /bots/{bot_id}/sql-knowledge-base/schema` - Get database schema
- `POST /bots/{bot_id}/sql-knowledge-base/query` - Execute SQL query
- `GET /bots/{bot_id}/sql-knowledge-base/tables` - List available tables

### Phase 3: Frontend Development

#### 3.1 Type Definitions
**Files to Modify:**
- `frontend/src/features/knowledgeBase/types/index.d.ts`

**New Types:**
```typescript
export type SqlDatabaseConfig = {
  connectionString: string;
  schemaName: string;
  tableNames: string[];
  queryTemplates?: string[];
};

export type SqlKnowledgeBase = {
  knowledgeBaseId: string | null;
  databaseConfig: SqlDatabaseConfig;
  searchParams: SearchParams;
};
```

#### 3.2 UI Components (New Files)
**Files to Create:**
- `frontend/src/features/knowledgeBase/components/SqlKnowledgeBaseConfig.tsx`
- `frontend/src/features/knowledgeBase/components/DatabaseSchemaUpload.tsx`
- `frontend/src/features/knowledgeBase/components/SqlQueryBuilder.tsx`
- `frontend/src/features/knowledgeBase/components/TableSchemaViewer.tsx`

#### 3.3 Integration Points
**Files to Modify:**
- Bot creation flow components
- Knowledge base configuration forms
- Search interface components
- Results display components

### Phase 4: Integration & Testing

#### 4.1 End-to-End Integration
1. Bedrock Knowledge Base SQL type configuration
2. Database connection validation
3. Schema upload and validation
4. Query execution and result formatting
5. Error handling and user feedback

#### 4.2 Testing Strategy
1. **Unit Tests**: Individual component testing
2. **Integration Tests**: Database connection and query execution
3. **E2E Tests**: Complete user workflow testing
4. **Performance Tests**: Query optimization and connection pooling

## Implementation Priority

### Sprint 1: Infrastructure Foundation (Week 1-2)
- [x] CDK infrastructure for Redshift Serverless
- [x] Database schema design and initialization
- [x] Basic IAM setup for Bedrock SQL integration
- [x] VPC and security group configuration
- [x] S3 bucket setup for data staging

### Sprint 2: Backend Core (Week 2-3)
- [ ] Extend data models for SQL KB support
- [ ] Implement knowledge base repository methods
- [ ] Create API endpoints for SQL KB management
- [ ] Add database connection validation

### Sprint 3: Frontend Components (Week 3-4)
- [ ] Create SQL KB configuration UI
- [ ] Implement database schema upload interface
- [ ] Build basic SQL query interface
- [ ] Integrate with existing bot creation flow

### Sprint 4: Advanced Features (Week 4-5)
- [ ] SQL query builder component
- [ ] Table schema viewer
- [ ] Query templates management
- [ ] Result formatting and display

### Sprint 5: Integration & Testing (Week 5-6)
- [ ] End-to-end integration testing
- [ ] Performance optimization
- [ ] Error handling improvement
- [ ] Documentation and user guides

## Technical Considerations

### Security
- **Connection Security**: Use IAM database authentication where possible
- **Data Encryption**: Ensure encryption at rest and in transit
- **Access Control**: Implement proper user permissions and row-level security
- **SQL Injection Prevention**: Use parameterized queries only

### Performance
- **Connection Pooling**: Implement efficient database connection management
- **Query Optimization**: Add query performance monitoring
- **Caching**: Consider query result caching for frequently accessed data
- **Resource Limits**: Set appropriate timeouts and resource constraints

### Scalability
- **Redshift Serverless**: Auto-scaling with RPU-based capacity
- **Data API**: Serverless query execution without connection management
- **Resource Monitoring**: CloudWatch metrics and alarms
- **Cost Optimization**: Pay-per-use RPU billing and automatic scaling

### Compatibility
- **Backward Compatibility**: Ensure existing VECTOR KBs continue working
- **Migration Path**: Provide clear migration guidance
- **Feature Flags**: Consider feature flags for gradual rollout
- **API Versioning**: Maintain API compatibility

## Success Criteria

### Functional Requirements
- [ ] Users can create SQL-based knowledge bases
- [ ] Support for Redshift database connections
- [ ] Schema upload and validation functionality  
- [ ] Natural language to SQL query conversion
- [ ] Structured data search and retrieval
- [ ] Integration with existing chat interface
- [ ] S3 data staging for bulk data import

### Non-Functional Requirements
- [ ] Query response time < 2 seconds for typical queries
- [ ] Support for databases up to 100GB
- [ ] 99.9% uptime for database connectivity
- [ ] Secure handling of database credentials
- [ ] Comprehensive error handling and user feedback

## Risk Assessment

### High Risk
- **Database Performance**: Complex queries may impact response times
- **Security**: Database credentials and access management
- **Cost**: Redshift Serverless RPU costs with scaling
- **Data Transfer**: Large data uploads and S3 staging costs

### Medium Risk  
- **Integration Complexity**: Bedrock Knowledge Base SQL type integration
- **UI/UX**: Making SQL features accessible to non-technical users
- **Migration**: Ensuring smooth deployment without disrupting existing features

### Low Risk
- **Type Safety**: Existing TypeScript infrastructure supports extension
- **Architecture**: Well-structured codebase facilitates new feature addition

## Rollback Plan

### Immediate Rollback
- Feature flag to disable SQL KB creation
- Database connection pool shutdown
- Route to fallback VECTOR KB only

### Complete Rollback
- CDK stack rollback to previous version
- Database resource cleanup
- Frontend component removal or disabling

## Monitoring & Observability

### Metrics to Track
- SQL KB creation success rate
- Query execution time and success rate
- Database connection pool utilization
- Error rates and types
- User engagement with SQL KB features

### Alerts
- Database connectivity issues
- Query timeout errors
- High resource utilization
- Failed knowledge base creation attempts

## Documentation Updates Required

### User Documentation
- [ ] SQL knowledge base user guide
- [ ] Database schema requirements
- [ ] Query optimization best practices
- [ ] Troubleshooting guide

### Developer Documentation
- [ ] API documentation updates
- [ ] Database schema documentation
- [ ] Deployment guide updates
- [ ] Architecture documentation updates

## Next Steps

1. **Review and Approval**: Get stakeholder approval for implementation plan
2. **Environment Setup**: Prepare development and testing environments
3. **Sprint Planning**: Break down tasks into detailed user stories
4. **Development Start**: Begin with Sprint 1 infrastructure work
5. **Regular Reviews**: Weekly progress reviews and plan adjustments

---

*Last Updated: 2025-10-02*
*Document Version: 1.0*
*Author: AI Assistant*