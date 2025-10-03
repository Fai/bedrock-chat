---
name: Bedrock SQL Knowledge Base Integration
about: Implement SQL Knowledge Base support for querying Redshift databases via Bedrock
title: "[Feature Request] Bedrock SQL Knowledge Base Integration"
labels: "enhancement, sql-kb, bedrock-integration"
assignees: ""
---

## Describe the solution you'd like

Implement application-layer support for Amazon Bedrock Knowledge Bases (SQL type) to enable natural language querying of existing Redshift Serverless databases through the Bedrock Chat interface.

### High-Level Architecture

```
Existing Redshift Serverless Database
          ↓
    Bedrock Knowledge Base (SQL type)
          ↓
    Backend API (Python/FastAPI)
          ↓
    Frontend UI (React/TypeScript)
          ↓
    User Chat Interface
```

### Key Capabilities

1. **SQL Knowledge Base Configuration**:
   - Create Bedrock KB with Redshift as data source
   - Configure field mapping (id, content, metadata)
   - Monitor ingestion job status
   - Support for multiple SQL KBs per bot

2. **Natural Language Querying**:
   - Convert user questions to SQL via Bedrock
   - Execute queries against Redshift via Bedrock KB API
   - Return structured results in conversational format
   - Display generated SQL for transparency

3. **User Interface**:
   - SQL KB configuration wizard in bot creation flow
   - Redshift connection form (workgroup, database, table)
   - Field mapping interface for semantic search
   - KB status indicators (creating, active, failed)
   - Structured data display in chat (table view)

4. **Infrastructure**:
   - IAM roles for Bedrock KB → Redshift access
   - Secrets Manager integration for credentials
   - Environment configuration for Redshift connection
   - Monitoring and error handling

## Why the solution is needed

### Business Problem

Customers have valuable structured data in Redshift databases that they want to query using natural language through AI-powered chatbots. Current Bedrock Chat only supports:
- **VECTOR**: Document-based knowledge bases (S3 + OpenSearch)
- **KENDRA**: Legacy search (being phased out)

There is **no support for SQL databases**, which is critical for:
- Customer order history
- Product inventory lookups
- Sales analytics
- Financial reporting
- Any structured relational data

### Customer Use Cases

**Example 1: Customer Order Queries**
- User: _"Show me all orders from customer ABC in Q1 2024"_
- Bot: Converts to SQL → Queries Redshift → Returns natural language answer with data table

**Example 2: Inventory Management**
- User: _"What's the current stock level for product XYZ?"_
- Bot: Retrieves real-time inventory data from Redshift

**Example 3: Business Analytics**
- User: _"What were our top-selling products last month?"_
- Bot: Performs aggregation query, presents insights with visualization

**Example 4: Financial Reports**
- User: _"Calculate total revenue by region for 2024"_
- Bot: Generates complex analytical query with joins and GROUP BY

### Why Bedrock SQL KB?

- **Native Integration**: Bedrock Knowledge Bases officially support Redshift
- **Natural Language**: No need for users to write SQL
- **Secure**: IAM-based access control, no credential exposure
- **Scalable**: Leverages Redshift Serverless auto-scaling
- **Cost-Effective**: Pay-per-query pricing with Bedrock KB

## Additional context

### Current State

**Type Definition Exists** (but not implemented):
```python
# backend/app/repositories/models/custom_bot_kb.py
type_kb_resource_type = Literal["VECTOR", "KENDRA", "SQL"]  # SQL type defined but unused
```

**Missing Implementation**:
- ❌ Backend API for SQL KB creation
- ❌ Frontend UI for SQL KB configuration
- ❌ IAM roles for Bedrock KB → Redshift access
- ❌ Query execution and result formatting
- ❌ Chat interface for structured data display

### Scope Definition

#### ✅ **In Scope (Our Implementation)**
1. Backend API development (Python/FastAPI)
2. Frontend UI development (React/TypeScript)
3. CDK infrastructure (IAM roles, Secrets Manager)
4. Testing and documentation
5. Integration with existing bot creation flow

#### ❌ **Out of Scope (Handled Separately)**
- Redshift Serverless deployment (customer/migration team)
- Database migration from MS SQL or other sources
- Data loading and ETL processes
- Network connectivity (VPN/Direct Connect)
- Database schema design and optimization

### Prerequisites

**Customer Must Provide** (from migration team or existing infrastructure):

```json
{
  "workgroup_name": "bedrock-sql-kb",
  "workgroup_arn": "arn:aws:redshift-serverless:us-east-1:123456789012:workgroup/bedrock-sql-kb",
  "database_name": "knowledge_base",
  "table_name": "customer_data_view",
  "field_mapping": {
    "id": "record_id",
    "content": "searchable_text",
    "metadata": "record_metadata"
  },
  "secret_arn": "arn:aws:secretsmanager:us-east-1:123456789012:secret:redshift-creds-xyz123"
}
```

**Requirements**:
- ✅ Redshift Serverless workgroup deployed and operational
- ✅ Database populated with customer data
- ✅ Secrets Manager secret with database credentials
- ✅ IAM permissions for Bedrock to access Redshift
- ✅ Table/view structured with fields suitable for Bedrock KB (id, content, metadata)

### Technical Implementation

#### Phase 1: Backend API (2 weeks, 20 man-days)

**Files to Create**:
- `backend/app/routes/schemas/sql_kb.py` - Pydantic schemas for SQL KB
- `backend/app/repositories/sql_knowledge_base.py` - Bedrock KB API integration

**Files to Modify**:
- `backend/app/routes/schemas/bot_kb.py` - Add `SqlKnowledgeBaseInput`, `SqlDatabaseConfig`
- `backend/app/repositories/knowledge_base.py` - Add `create_sql_knowledge_base()`
- `backend/app/routes/bot.py` - Add SQL KB endpoints

**New API Endpoints**:
```python
POST   /bots/{bot_id}/knowledge-base/sql       # Create SQL KB
GET    /bots/{bot_id}/knowledge-base/status    # Get ingestion status
POST   /bots/{bot_id}/knowledge-base/query     # Query KB with natural language
DELETE /bots/{bot_id}/knowledge-base           # Delete SQL KB
```

**Key Backend Functions**:
```python
# backend/app/repositories/knowledge_base.py

def create_sql_knowledge_base(
    bot_id: str,
    sql_config: SqlDatabaseConfig,
    kb_name: str
) -> str:
    """
    Create Bedrock Knowledge Base with Redshift data source

    Args:
        bot_id: Bot identifier
        sql_config: Redshift configuration (workgroup, database, table, field mapping)
        kb_name: Human-readable KB name

    Returns:
        knowledge_base_id: Bedrock KB ID
    """
    response = bedrock_agent.create_knowledge_base(
        name=kb_name,
        roleArn=os.getenv('BEDROCK_KB_ROLE_ARN'),
        knowledgeBaseConfiguration={
            'type': 'VECTOR',
            'vectorKnowledgeBaseConfiguration': {
                'embeddingModelArn': 'arn:aws:bedrock:us-east-1::foundation-model/amazon.titan-embed-text-v2:0'
            }
        },
        storageConfiguration={
            'type': 'REDSHIFT',
            'redshiftConfiguration': {
                'workgroupName': sql_config.workgroup_name,
                'databaseName': sql_config.database_name,
                'tableName': sql_config.table_name,
                'credentialsSecretArn': sql_config.secret_arn,
                'fieldMapping': {
                    'primaryKeyField': sql_config.field_mapping['id'],
                    'textField': sql_config.field_mapping['content'],
                    'metadataField': sql_config.field_mapping['metadata']
                }
            }
        }
    )

    kb_id = response['knowledgeBase']['knowledgeBaseId']

    # Start ingestion job
    bedrock_agent.start_ingestion_job(
        knowledgeBaseId=kb_id,
        dataSourceId=response['knowledgeBase']['dataSourceId']
    )

    return kb_id

def query_sql_knowledge_base(
    kb_id: str,
    query: str,
    user_id: str
) -> dict:
    """
    Query Bedrock SQL KB with natural language

    Returns: {answer: str, citations: list, sql_query: str}
    """
    response = bedrock_agent_runtime.retrieve_and_generate(
        input={'text': query},
        retrieveAndGenerateConfiguration={
            'type': 'KNOWLEDGE_BASE',
            'knowledgeBaseConfiguration': {
                'knowledgeBaseId': kb_id,
                'modelArn': os.getenv('DEFAULT_MODEL_ARN')
            }
        }
    )

    return {
        'answer': response['output']['text'],
        'citations': response.get('citations', []),
        'sql_query': extract_sql_from_citations(response)
    }
```

#### Phase 2: Frontend UI (2 weeks, 20 man-days)

**Files to Create**:
- `frontend/src/features/knowledgeBase/SqlKbWizard.tsx` - 4-step wizard
- `frontend/src/features/knowledgeBase/RedshiftConnectionForm.tsx` - Connection form
- `frontend/src/features/knowledgeBase/FieldMappingForm.tsx` - Field mapper
- `frontend/src/features/knowledgeBase/KbStatusBadge.tsx` - Status indicator
- `frontend/src/features/chat/SqlResultTable.tsx` - Structured result display

**Files to Modify**:
- `frontend/src/features/knowledgeBase/types/index.d.ts` - Add SQL KB types
- `frontend/src/pages/BotCreate.tsx` - Integrate SQL KB wizard
- `frontend/src/features/chat/ChatMessage.tsx` - Add SQL result rendering

**SQL KB Wizard Flow**:
```
Step 1: Select KB Type
  ○ Vector (Documents)
  ● SQL (Structured Data)

Step 2: Redshift Connection
  [Workgroup Name: _____________]
  [Database Name:  _____________]
  [Table/View Name: ____________]
  [Validate Connection →]

Step 3: Field Mapping
  Primary Key: [record_id    ▼]
  Content:     [searchable_text ▼]
  Metadata:    [record_metadata ▼]

Step 4: Review & Create
  Configuration Summary
  [← Back]  [Create Knowledge Base →]
```

**TypeScript Types**:
```typescript
// frontend/src/features/knowledgeBase/types/index.d.ts

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
  knowledgeBaseId: string | null;
  knowledgeBaseType: 'SQL';
  databaseConfig: SqlDatabaseConfig;
  searchParams: SearchParams;
  embeddingModelArn: string;
};

export type KnowledgeBaseStatus = {
  status: 'CREATING' | 'ACTIVE' | 'DELETING' | 'UPDATING' | 'FAILED';
  ingestionJobId?: string;
  ingestionJobStatus?: 'STARTING' | 'IN_PROGRESS' | 'COMPLETE' | 'FAILED';
  progress?: number;
  errorMessage?: string;
};
```

#### Phase 3: Infrastructure (1 week, 10 man-days)

**Files to Create**:
- `cdk/lib/constructs/bedrock-kb-role.ts` - IAM role for Bedrock KB
- `cdk/lib/constructs/sql-kb-secrets.ts` - Secrets Manager integration

**Files to Modify**:
- `cdk/lib/bedrock-chat-stack.ts` - Add Bedrock KB role
- `cdk/parameter.ts` - Add `sqlKnowledgeBaseConfig`

**IAM Role Policy** (Bedrock KB → Redshift):
```typescript
// cdk/lib/constructs/bedrock-kb-role.ts

export class BedrockKbRole extends Construct {
  public readonly role: iam.Role;

  constructor(scope: Construct, id: string, props: Props) {
    super(scope, id);

    this.role = new iam.Role(this, 'BedrockKbRole', {
      assumedBy: new iam.ServicePrincipal('bedrock.amazonaws.com'),
      description: 'IAM role for Bedrock Knowledge Base to access Redshift',
    });

    // Redshift Data API permissions
    this.role.addToPolicy(new iam.PolicyStatement({
      actions: [
        'redshift-data:ExecuteStatement',
        'redshift-data:DescribeStatement',
        'redshift-data:GetStatementResult',
        'redshift-serverless:GetCredentials',
      ],
      resources: [props.redshiftWorkgroupArn],
    }));

    // Secrets Manager permissions
    this.role.addToPolicy(new iam.PolicyStatement({
      actions: ['secretsmanager:GetSecretValue'],
      resources: [props.redshiftSecretArn],
    }));

    // CloudWatch Logs (for Bedrock KB)
    this.role.addToPolicy(new iam.PolicyStatement({
      actions: [
        'logs:CreateLogGroup',
        'logs:CreateLogStream',
        'logs:PutLogEvents',
      ],
      resources: ['arn:aws:logs:*:*:log-group:/aws/bedrock/*'],
    }));
  }
}
```

**Environment Variables**:
```bash
# backend/.env
BEDROCK_KB_ROLE_ARN=arn:aws:iam::123456789012:role/BedrockKbRole
REDSHIFT_WORKGROUP_ARN=arn:aws:redshift-serverless:us-east-1:123456789012:workgroup/bedrock-sql-kb
REDSHIFT_SECRET_ARN=arn:aws:secretsmanager:us-east-1:123456789012:secret:redshift-creds-xyz123
BEDROCK_REGION=us-east-1
DEFAULT_MODEL_ARN=arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-5-sonnet-20241022-v2:0
```

#### Phase 4: Documentation & Deployment (1 week, 5 man-days)

**Documentation to Create**:
1. **User Guide**: `/docs/SQL_KNOWLEDGE_BASE_USER_GUIDE.md`
   - Prerequisites (Redshift database requirements)
   - Creating a SQL KB bot (step-by-step)
   - Field mapping best practices
   - Querying structured data
   - Troubleshooting

2. **API Documentation**: Update FastAPI auto-docs
   - New SQL KB endpoints
   - Request/response schemas
   - Example API calls

3. **Deployment Guide**: `/docs/SQL_KB_DEPLOYMENT.md`
   - Infrastructure setup (IAM roles, Secrets Manager)
   - Environment configuration
   - CDK deployment steps
   - Verification testing

### Implementation Timeline

**Total Duration**: 4-5 weeks
**Man-Days**: 55 days
**Team**: 3 engineers (Backend, Frontend, Cloud Architect)

| Phase | Duration | Man-Days | Key Deliverables |
|-------|----------|----------|------------------|
| **Phase 1**: Backend API | 2 weeks | 20 | API endpoints, Bedrock KB integration, tests (>80% coverage) |
| **Phase 2**: Frontend UI | 2 weeks | 20 | SQL KB wizard, chat enhancements, component tests |
| **Phase 3**: Infrastructure | 1 week | 10 | IAM roles, Secrets Manager, integration testing |
| **Phase 4**: Documentation | 1 week | 5 | User guide, API docs, deployment guide |

**Detailed Timeline**: See `/docs/SQL_KB_IMPLEMENTATION_TIMELINE.md`

### Cost Estimate

**Implementation Services**: $60,000 - $70,000 (fixed price)

**Includes**:
- Full-stack development (Backend + Frontend + Infrastructure)
- Testing (unit, integration, E2E)
- Documentation (user + developer + deployment guides)
- 2 weeks post-launch support

**Excludes**:
- Redshift Serverless deployment (customer responsibility)
- Database migration and data loading
- AWS infrastructure monthly costs (customer-paid)
- Ongoing maintenance beyond 2 weeks

**AWS Monthly Costs** (customer-paid, estimated):
- Bedrock KB API calls: $0.10/1K requests
- Redshift Serverless (existing): $0 additional (already deployed)
- Secrets Manager: $0.40/secret/month
- CloudWatch Logs: $5-10/month

**No additional AWS infrastructure costs** (leverages existing Redshift)

### Testing Strategy

1. **Unit Tests**:
   - Backend: pytest (>80% coverage)
   - Frontend: Vitest for components
   - CDK: Jest for infrastructure

2. **Integration Tests**:
   - Bedrock KB creation with test Redshift database
   - Query execution and result formatting
   - Error handling (KB creation failures, query timeouts)

3. **End-to-End Tests**:
   - Complete bot creation flow with SQL KB
   - Natural language query → SQL → result display
   - Multi-user access control validation

4. **Performance Tests**:
   - Query response time (target: <3 seconds P95)
   - Concurrent query load testing (50 users)
   - KB ingestion time measurement

### Success Criteria

**Functional**:
- [ ] Users can create bots with SQL Knowledge Base type
- [ ] SQL KB successfully connects to existing Redshift database
- [ ] Natural language queries return accurate results from Redshift
- [ ] Chat interface displays structured data in table format
- [ ] KB ingestion status visible and updates in real-time
- [ ] Generated SQL queries displayed for transparency
- [ ] Error handling for KB creation and query failures

**Non-Functional**:
- [ ] Query response time < 3 seconds (P95)
- [ ] Backend test coverage > 80%
- [ ] All frontend components have Ladle stories
- [ ] API documentation complete (FastAPI auto-docs)
- [ ] Production deployment successful with zero downtime

### Security Considerations

- **Authentication**: IAM-based (no database credentials in code)
- **Authorization**: Row-level access control via user ID
- **Encryption**: TLS in transit, KMS at rest (via Secrets Manager)
- **Audit**: CloudTrail logging for all Bedrock KB API calls
- **Secrets**: AWS Secrets Manager with automatic rotation

### Monitoring & Observability

**Metrics to Track**:
- SQL KB creation success rate
- Query execution time (P50, P95, P99)
- Bedrock KB API error rates
- KB ingestion job status
- User engagement with SQL KB bots

**Alerts**:
- KB creation failure (SNS notification)
- Query timeout > 5 seconds
- Bedrock KB API throttling
- Ingestion job failure

### Rollback Plan

**Feature Flag**:
```typescript
// frontend/.env
VITE_ENABLE_SQL_KB=false  // Disable SQL KB in UI
```

**Immediate Rollback**:
1. Set feature flag to `false`
2. Users cannot create new SQL KB bots
3. Existing SQL KB bots continue working

**Complete Rollback**:
1. Delete Bedrock KB IAM role (if no SQL KBs exist)
2. Revert backend API endpoints
3. Revert frontend UI components

## Implementation feasibility

- [x] **Yes, we are able to implement the feature and create a pull request.**

### Development Team

**Required Skills**:
- Senior Backend Engineer: Python, FastAPI, AWS SDK (boto3), Bedrock APIs
- Senior Frontend Engineer: React, TypeScript, Tailwind CSS, SWR
- Senior Cloud Architect: AWS CDK, IAM, Secrets Manager, Redshift

**Estimated Effort**: 55 man-days (4-5 weeks)

### Dependencies

**External**:
- Amazon Bedrock Knowledge Bases (SQL connector)
- Amazon Redshift Serverless (customer-deployed)
- AWS Secrets Manager
- AWS IAM

**Internal**:
- Existing Bedrock Chat infrastructure
- Current CDK deployment pipeline
- Backend FastAPI framework
- Frontend React/TypeScript stack

### Constraints

- **Redshift must be ready**: Database deployed and populated before implementation starts
- **Bedrock region support**: Target region must support Bedrock KB SQL type (us-east-1, us-west-2, etc.)
- **Field mapping requirement**: Redshift table/view must have suitable fields for Bedrock KB (id, content, metadata)
- **Secret ARN required**: Secrets Manager secret with Redshift credentials must exist

## Related Issues

- #XXX - Original SQL KB type definition (if exists)
- #XXX - Bedrock Knowledge Bases enhancement request (if exists)

## References

**AWS Documentation**:
- [Amazon Bedrock Knowledge Bases - SQL Data Source](https://docs.aws.amazon.com/bedrock/latest/userguide/knowledge-base-ds-sql.html)
- [Redshift Data API](https://docs.aws.amazon.com/redshift/latest/mgmt/data-api.html)
- [Bedrock Agent Runtime API](https://docs.aws.amazon.com/bedrock/latest/APIReference/API_agent-runtime_RetrieveAndGenerate.html)

**Project Documentation**:
- `/docs/SQL_KB_IMPLEMENTATION_TIMELINE.md` - Detailed implementation timeline
- `/docs/AGENT.md` - Existing agent tool implementation patterns
- `/docs/LOCAL_DEVELOPMENT.md` - Local development setup

---

**Priority**: High
**Estimated Effort**: 55 man-days (4-5 weeks)
**Estimated Cost**: $60,000 - $70,000
**Business Value**: Enable AI-powered querying of enterprise SQL databases
**Risk Level**: Low-Medium (depends on Redshift availability)

---

*Submitted by: [Your Name]*
*Date: 2025-10-02*
*Customer: [Customer Name - if applicable]*
