# Bedrock SQL Knowledge Base Implementation - Code Timeline & Man-Day Estimate

## Executive Summary

**Scope**: Implement support for Amazon Bedrock Knowledge Bases (SQL type) in Bedrock Chat application to enable natural language querying of existing Redshift databases.

**Assumption**: Customer's Redshift Serverless database is **already deployed and populated** by another team. Our team only implements the application layer to connect and query it.

**Total Implementation Time**: 4-5 weeks
**Total Man-Days**: 40-50 days
**Team Size**: 3 engineers

---

## Scope Definition

### ✅ In Scope (Our Team)
- Backend API for Bedrock SQL KB creation and management
- Frontend UI for SQL KB configuration in bot creation flow
- Integration with existing Bedrock Knowledge Base (SQL type)
- Query execution via Bedrock KB API
- Result formatting and display in chat interface
- Testing and documentation

### ❌ Out of Scope (Other Team)
- MS SQL to Redshift migration (handled by migration team)
- AWS DMS setup and configuration
- Redshift Serverless deployment
- Network connectivity (VPN/Direct Connect)
- Database schema conversion
- Data loading and validation

---

## Team Composition & Rates

| Role | Quantity | Day Rate (Example) | Responsibilities |
|------|----------|-------------------|------------------|
| **Senior Backend Engineer** | 1 | $1,000/day | Python/FastAPI, Bedrock KB API integration |
| **Senior Frontend Engineer** | 1 | $900/day | React/TypeScript, SQL KB configuration UI |
| **Senior Cloud Architect** | 1 | $1,200/day | CDK infrastructure for KB integration |

**Blended Rate**: ~$1,033/day

---

## Implementation Phases - Detailed Breakdown

### **Phase 1: Backend API Development**
**Duration**: 2 weeks
**Man-Days**: 20 days

#### 1.1 Data Models Extension (3 days)
**Engineer**: Senior Backend Engineer

| Task | Time | Files to Create/Modify |
|------|------|------------------------|
| Extend bot KB schemas for SQL type | 1 day | `backend/app/routes/schemas/bot_kb.py`<br/>Add: `SqlKnowledgeBaseInput`, `SqlDatabaseConfig` |
| Update repository models | 1 day | `backend/app/repositories/models/custom_bot_kb.py`<br/>Add SQL KB fields to database model |
| Add Pydantic validation | 1 day | Schema validation for Redshift config |

**New Schema Classes**:
```python
# backend/app/routes/schemas/bot_kb.py
class SqlDatabaseConfig(BaseSchema):
    workgroup_name: str
    database_name: str
    table_name: str  # or view_name
    field_mapping: dict[str, str]  # {primaryKeyField, textField, metadataField}

class SqlKnowledgeBaseInput(BaseSchema):
    knowledge_base_type: Literal["SQL"] = "SQL"
    database_config: SqlDatabaseConfig
    search_params: SearchParams
    embedding_model_arn: str = "arn:aws:bedrock:us-east-1::foundation-model/amazon.titan-embed-text-v2:0"
```

#### 1.2 Bedrock KB Repository (7 days)
**Engineer**: Senior Backend Engineer

| Task | Time | Files to Create/Modify |
|------|------|------------------------|
| Create SQL KB via Bedrock API | 3 days | `backend/app/repositories/knowledge_base.py`<br/>Function: `create_sql_knowledge_base()` |
| Query execution via Bedrock KB | 2 days | Function: `query_sql_knowledge_base(kb_id, query)` |
| KB ingestion job monitoring | 1 day | Function: `get_ingestion_job_status(kb_id)` |
| Error handling & retries | 1 day | Exponential backoff for API failures |

**Key Implementation**:
```python
# backend/app/repositories/knowledge_base.py
def create_sql_knowledge_base(
    bot_id: str,
    sql_config: SqlDatabaseConfig,
    kb_name: str
) -> str:
    """
    Create Bedrock Knowledge Base with Redshift data source

    Returns: knowledge_base_id
    """
    response = bedrock_agent.create_knowledge_base(
        name=kb_name,
        roleArn=os.getenv('BEDROCK_KB_ROLE_ARN'),
        knowledgeBaseConfiguration={
            'type': 'VECTOR',
            'vectorKnowledgeBaseConfiguration': {
                'embeddingModelArn': sql_config.embedding_model_arn
            }
        },
        storageConfiguration={
            'type': 'REDSHIFT',
            'redshiftConfiguration': {
                'workgroupName': sql_config.workgroup_name,
                'databaseName': sql_config.database_name,
                'tableName': sql_config.table_name,
                'credentialsSecretArn': os.getenv('REDSHIFT_SECRET_ARN'),
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
    Query Bedrock KB with natural language, get SQL results

    Returns: {answer: str, results: list[dict], sql_query: str}
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

#### 1.3 API Endpoints (5 days)
**Engineer**: Senior Backend Engineer

| Task | Time | Files to Create/Modify |
|------|------|------------------------|
| Create SQL KB endpoint | 2 days | `backend/app/routes/bot.py`<br/>`POST /bots/{bot_id}/knowledge-base/sql` |
| Get KB status endpoint | 1 day | `GET /bots/{bot_id}/knowledge-base/status` |
| Query KB endpoint | 2 days | `POST /bots/{bot_id}/knowledge-base/query` |

**New Endpoints**:
```python
# backend/app/routes/bot.py

@router.post("/bots/{bot_id}/knowledge-base/sql")
def create_sql_knowledge_base_endpoint(
    bot_id: str,
    sql_kb: SqlKnowledgeBaseInput,
    current_user: User = Depends(get_current_user)
):
    """Create Bedrock SQL Knowledge Base for bot"""
    kb_id = create_sql_knowledge_base(
        bot_id=bot_id,
        sql_config=sql_kb.database_config,
        kb_name=f"sql-kb-{bot_id}"
    )

    # Update bot with KB ID
    update_bot_kb(bot_id, kb_id, kb_type="SQL")

    return {"knowledge_base_id": kb_id, "status": "CREATING"}

@router.get("/bots/{bot_id}/knowledge-base/status")
def get_kb_status(
    bot_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get ingestion job status"""
    kb_id = get_bot_kb_id(bot_id)
    status = get_ingestion_job_status(kb_id)
    return status

@router.post("/bots/{bot_id}/knowledge-base/query")
def query_kb(
    bot_id: str,
    query: QueryInput,
    current_user: User = Depends(get_current_user)
):
    """Query SQL KB with natural language"""
    kb_id = get_bot_kb_id(bot_id)
    result = query_sql_knowledge_base(kb_id, query.text, current_user.id)
    return result
```

#### 1.4 Backend Testing (5 days)
**Engineer**: Senior Backend Engineer

| Task | Time | Files to Create/Modify |
|------|------|------------------------|
| Unit tests for KB repository | 2 days | `backend/tests/test_repositories/test_knowledge_base_sql.py` |
| API endpoint tests | 2 days | `backend/tests/test_routes/test_bot_sql_kb.py` |
| Integration tests (mock Bedrock) | 1 day | Mock `bedrock_agent` API responses |

**Test Coverage Target**: >80%

**Deliverables**:
- Backend APIs functional
- All tests passing
- API documentation updated (FastAPI auto-docs)

---

### **Phase 2: Frontend UI Development**
**Duration**: 2 weeks
**Man-Days**: 20 days

#### 2.1 Type Definitions (2 days)
**Engineer**: Senior Frontend Engineer

| Task | Time | Files to Create/Modify |
|------|------|------------------------|
| TypeScript types for SQL KB | 1 day | `frontend/src/features/knowledgeBase/types/index.d.ts` |
| API client hooks | 1 day | `frontend/src/hooks/useKnowledgeBase.ts` |

**New Types**:
```typescript
// frontend/src/features/knowledgeBase/types/index.d.ts
export type SqlDatabaseConfig = {
  workgroupName: string;
  databaseName: string;
  tableName: string;
  fieldMapping: {
    id: string;
    content: string;
    metadata: string;
  };
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
  progress?: number;
  errorMessage?: string;
};
```

#### 2.2 SQL KB Configuration UI (10 days)
**Engineer**: Senior Frontend Engineer

| Task | Time | Files to Create/Modify |
|------|------|------------------------|
| SQL KB setup wizard component | 4 days | `frontend/src/features/knowledgeBase/SqlKbWizard.tsx` |
| Redshift connection form | 2 days | `frontend/src/features/knowledgeBase/RedshiftConnectionForm.tsx` |
| Field mapping UI | 2 days | `frontend/src/features/knowledgeBase/FieldMappingForm.tsx` |
| KB status indicator | 1 day | `frontend/src/features/knowledgeBase/KbStatusBadge.tsx` |
| Integration with bot creation | 1 day | Update `frontend/src/pages/BotCreate.tsx` |

**SQL KB Wizard** (4-step wizard):
```typescript
// frontend/src/features/knowledgeBase/SqlKbWizard.tsx
export const SqlKbWizard: React.FC<Props> = ({ botId, onComplete }) => {
  const [step, setStep] = useState(1);

  return (
    <Wizard currentStep={step}>
      {/* Step 1: Select KB Type (VECTOR vs SQL) */}
      <WizardStep title="Knowledge Base Type">
        <KnowledgeBaseTypeSelector
          selected={kbType}
          onChange={setKbType}
        />
      </WizardStep>

      {/* Step 2: Redshift Connection */}
      <WizardStep title="Database Connection">
        <RedshiftConnectionForm
          workgroup={workgroup}
          database={database}
          onValidate={validateConnection}
        />
      </WizardStep>

      {/* Step 3: Table & Field Mapping */}
      <WizardStep title="Field Mapping">
        <FieldMappingForm
          tableName={tableName}
          fields={availableFields}
          mapping={fieldMapping}
          onChange={setFieldMapping}
        />
      </WizardStep>

      {/* Step 4: Review & Create */}
      <WizardStep title="Review">
        <SqlKbSummary config={sqlConfig} />
        <Button onClick={handleCreate}>Create Knowledge Base</Button>
      </WizardStep>
    </Wizard>
  );
};
```

#### 2.3 Chat Interface Enhancement (5 days)
**Engineer**: Senior Frontend Engineer

| Task | Time | Files to Create/Modify |
|------|------|------------------------|
| SQL query display in chat | 2 days | Update `frontend/src/features/chat/ChatMessage.tsx` |
| Structured result table | 2 days | `frontend/src/features/chat/SqlResultTable.tsx` |
| Query transparency toggle | 1 day | Show/hide generated SQL option |

**SQL Result Display**:
```typescript
// frontend/src/features/chat/SqlResultTable.tsx
export const SqlResultTable: React.FC<{ results: any[] }> = ({ results }) => {
  if (!results || results.length === 0) return null;

  const columns = Object.keys(results[0]);

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full border border-gray-300">
        <thead className="bg-gray-100">
          <tr>
            {columns.map(col => (
              <th key={col} className="px-4 py-2 text-left">{col}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {results.map((row, idx) => (
            <tr key={idx} className="border-t">
              {columns.map(col => (
                <td key={col} className="px-4 py-2">{row[col]}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
```

#### 2.4 Frontend Testing (3 days)
**Engineer**: Senior Frontend Engineer

| Task | Time | Files to Create/Modify |
|------|------|------------------------|
| Component tests (Vitest) | 2 days | `*.test.tsx` for all new components |
| Ladle stories | 1 day | `*.stories.tsx` for component gallery |

**Deliverables**:
- SQL KB wizard functional
- Chat interface displays SQL results
- All components tested and documented in Ladle

---

### **Phase 3: Infrastructure & Integration**
**Duration**: 1 week
**Man-Days**: 10 days

#### 3.1 CDK Infrastructure (5 days)
**Engineer**: Senior Cloud Architect

| Task | Time | Files to Create/Modify |
|------|------|------------------------|
| IAM role for Bedrock KB | 2 days | `cdk/lib/constructs/bedrock-kb-role.ts`<br/>Permissions: Redshift Data API, Secrets Manager |
| Secrets Manager for Redshift credentials | 1 day | `cdk/lib/constructs/secrets.ts`<br/>Store workgroup ARN, database name |
| CDK parameter configuration | 1 day | `cdk/parameter.ts`<br/>Add `sqlKnowledgeBaseConfig` |
| Unit tests for CDK | 1 day | `cdk/test/bedrock-kb.test.ts` |

**IAM Role Policy**:
```typescript
// cdk/lib/constructs/bedrock-kb-role.ts
export class BedrockKbRole extends Construct {
  public readonly role: iam.Role;

  constructor(scope: Construct, id: string, props: Props) {
    super(scope, id);

    this.role = new iam.Role(this, 'BedrockKbRole', {
      assumedBy: new iam.ServicePrincipal('bedrock.amazonaws.com'),
      description: 'Role for Bedrock Knowledge Base to access Redshift',
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

    // S3 permissions (if needed for Bedrock)
    this.role.addToPolicy(new iam.PolicyStatement({
      actions: ['s3:GetObject', 's3:ListBucket'],
      resources: ['arn:aws:s3:::bedrock-*/*'],
    }));
  }
}
```

#### 3.2 Environment Configuration (2 days)
**Engineer**: Senior Cloud Architect

| Task | Time | Files to Create/Modify |
|------|------|------------------------|
| Backend environment variables | 1 day | `backend/.env.template`<br/>Add: `REDSHIFT_WORKGROUP_ARN`, `REDSHIFT_SECRET_ARN`, `BEDROCK_KB_ROLE_ARN` |
| Frontend environment variables | 1 day | `frontend/.env.template`<br/>Add: `VITE_ENABLE_SQL_KB=true` |

**Environment Variables**:
```bash
# backend/.env.template
BEDROCK_KB_ROLE_ARN=arn:aws:iam::123456789012:role/BedrockKbRole
REDSHIFT_WORKGROUP_ARN=arn:aws:redshift-serverless:us-east-1:123456789012:workgroup/bedrock-sql-kb
REDSHIFT_SECRET_ARN=arn:aws:secretsmanager:us-east-1:123456789012:secret:redshift-creds-xyz123
BEDROCK_REGION=us-east-1
```

#### 3.3 Integration Testing (3 days)
**Engineers**: All team members

| Task | Time | Responsibility |
|------|------|---------------|
| End-to-end flow testing | 2 days | Backend + Frontend Engineers |
| IAM permissions validation | 1 day | Cloud Architect |

**Test Scenarios**:
1. Create bot with SQL KB
2. Monitor ingestion job status
3. Query KB with natural language
4. Display SQL results in chat
5. Handle KB creation failures

**Deliverables**:
- Infrastructure deployed
- E2E tests passing
- IAM permissions validated

---

### **Phase 4: Documentation & Deployment**
**Duration**: 1 week (can overlap with Phase 3)
**Man-Days**: 5 days

#### 4.1 Documentation (3 days)
**Engineers**: Senior Backend + Frontend Engineers

| Task | Time | Files to Create/Modify |
|------|------|------------------------|
| User guide for SQL KB | 1 day | `docs/SQL_KNOWLEDGE_BASE_USER_GUIDE.md` |
| API documentation updates | 1 day | FastAPI auto-docs + README |
| Deployment guide | 1 day | `docs/SQL_KB_DEPLOYMENT.md` |

**User Guide Sections**:
1. Prerequisites (existing Redshift database)
2. Creating a SQL Knowledge Base bot
3. Field mapping best practices
4. Querying structured data
5. Troubleshooting common issues

#### 4.2 Production Deployment (2 days)
**Engineer**: Senior Cloud Architect

| Task | Time | Files to Create/Modify |
|------|------|------------------------|
| Deploy to production | 1 day | `cdk deploy --all` |
| Smoke testing | 1 day | Validate all features in prod |

**Deliverables**:
- Production deployment complete
- Documentation published
- Feature ready for customer use

---

## Total Man-Day Summary

| Phase | Duration | Man-Days | Cost Estimate ($1,033/day) |
|-------|----------|----------|----------------------------|
| **Phase 1**: Backend API | 2 weeks | 20 | $20,660 |
| **Phase 2**: Frontend UI | 2 weeks | 20 | $20,660 |
| **Phase 3**: Infrastructure & Integration | 1 week | 10 | $10,330 |
| **Phase 4**: Documentation & Deployment | 1 week | 5 | $5,165 |
| | | | |
| **Total** | **4-5 weeks** | **55 days** | **$56,815** |

**With 15% contingency**: **$65,337**

---

## Pricing Models for Sales Quotes

### Option 1: Fixed Price (Recommended)
**Price**: $60,000 - $70,000

**Includes**:
- Backend API development (Python/FastAPI)
- Frontend UI development (React/TypeScript)
- CDK infrastructure (IAM roles, Secrets Manager)
- Testing (>80% backend coverage)
- Documentation (user guide, API docs, deployment guide)
- 2 weeks of post-launch support

**Excludes**:
- Redshift Serverless deployment (handled by migration team)
- Database migration and data loading
- AWS infrastructure monthly costs (customer-paid)
- Ongoing maintenance beyond 2 weeks

### Option 2: Time & Materials
**Hourly Rate**: $125-$150/hour (based on role)
**Estimated Hours**: 440 hours (55 days × 8 hrs)
**Estimated Total**: $55,000 - $66,000

**Best For**: Projects with uncertain requirements

### Option 3: Phased Approach

| Phase | Price |
|-------|-------|
| Phase 1: Backend API | $20,000 - $24,000 |
| Phase 2: Frontend UI | $20,000 - $24,000 |
| Phase 3: Infrastructure | $10,000 - $12,000 |
| Phase 4: Documentation | $5,000 - $6,000 |

**Total**: $55,000 - $66,000

---

## Prerequisites & Dependencies

### Customer Must Provide

**Redshift Database** (deployed by migration team):
- [ ] Redshift Serverless workgroup name
- [ ] Database name and schema
- [ ] Table/view name for Bedrock KB
- [ ] Field names for mapping (id, content, metadata)
- [ ] Secrets Manager ARN with Redshift credentials

**Example Configuration** (provided by migration team):
```json
{
  "workgroup_name": "bedrock-sql-kb",
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

**AWS Resources** (deployed by migration team):
- [ ] Redshift Serverless workgroup (with auto-pause configured)
- [ ] Secrets Manager secret with database credentials
- [ ] VPC and security groups (if needed)
- [ ] Data already loaded into Redshift table

### Our Team Requires

**Development Environment**:
- [ ] AWS account access (dev + prod)
- [ ] Bedrock model access (Titan, Claude)
- [ ] Test Redshift database with sample data
- [ ] GitHub repository access

**Technical Information**:
- [ ] Redshift workgroup ARN
- [ ] Secret ARN for credentials
- [ ] Target AWS region (must support Bedrock KB SQL)

---

## Risk Assessment & Mitigation

### Technical Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Bedrock KB API rate limits | Medium | Low | Implement exponential backoff |
| Redshift query timeout | High | Medium | Optimize views, add caching |
| IAM permission issues | High | Low | Test in dev environment first |
| Frontend-backend mismatch | Medium | Low | API contract testing |

### Schedule Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Dependency on migration team | High | Get Redshift config early in Phase 1 |
| API changes during development | Medium | Use feature flags for gradual rollout |
| Testing environment delays | Medium | Use LocalStack for local Bedrock mock |

---

## Assumptions

1. **Redshift database is ready**: Migration team has completed data loading before Phase 1 starts
2. **Schema is stable**: Database schema will not change during implementation
3. **Bedrock KB SQL available**: Target AWS region supports Bedrock Knowledge Base SQL connector
4. **Single Redshift instance**: One Redshift workgroup per bot (not multi-tenant in single DB)
5. **Standard field mapping**: Redshift views follow Bedrock KB field mapping requirements

---

## Payment Milestones (4 Payments)

1. **Contract Signing**: 30% ($18,000 - $21,000)
2. **Backend API Complete**: 30% ($18,000 - $21,000)
3. **Frontend UI Complete**: 30% ($18,000 - $21,000)
4. **Production Deployment**: 10% ($6,000 - $7,000)

---

## Success Criteria

### Functional Requirements
- [ ] Users can create bots with SQL Knowledge Base type
- [ ] SQL KB connects to existing Redshift database
- [ ] Natural language queries return accurate results
- [ ] Chat interface displays structured data in tables
- [ ] KB ingestion status visible in UI
- [ ] Error handling for KB creation failures

### Non-Functional Requirements
- [ ] Query response time < 3 seconds (P95)
- [ ] Backend test coverage > 80%
- [ ] Frontend components have Ladle stories
- [ ] API documentation complete (FastAPI auto-docs)
- [ ] Production deployment successful

---

## Sales Quote Template

```
Bedrock SQL Knowledge Base - Implementation Services

Scope: Application-layer development for Bedrock SQL KB support
(Redshift database deployment handled separately by migration team)

Implementation Services: $60,000 - $70,000
- 4-5 week delivery timeline
- 3 engineer team (Backend, Frontend, Cloud Architect)
- Backend API development (Python/FastAPI)
- Frontend UI (React/TypeScript wizard)
- CDK infrastructure (IAM roles, configuration)
- Testing & documentation
- 2 weeks post-launch support

Payment Terms:
Net 30 days, milestone-based (4 payments)

Prerequisites:
- Redshift Serverless workgroup deployed
- Database populated with customer data
- Secrets Manager configured
- Workgroup ARN and credentials provided

Deliverables:
- SQL KB configuration wizard in bot creation
- Natural language querying of Redshift data
- Structured result display in chat
- User documentation and deployment guide
```

---

## Next Steps for Sales Team

1. **Confirm scope** with customer: No migration work, only application integration
2. **Request Redshift details** from migration team:
   - Workgroup name and ARN
   - Database/table structure
   - Secret ARN for credentials
3. **Present fixed-price quote**: $60,000 - $70,000 for 4-5 weeks
4. **Schedule kickoff** after migration team confirms Redshift is ready

---

*Last Updated: 2025-10-02*
*Version: 2.0 (Simplified - Code Implementation Only)*
*Contact: [Sales Team Email]*
