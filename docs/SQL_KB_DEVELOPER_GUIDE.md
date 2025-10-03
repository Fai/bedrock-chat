# SQL Knowledge Base Developer Guide

## Architecture Overview

The SQL Knowledge Base feature integrates Amazon Bedrock Knowledge Bases with Amazon Redshift Serverless, enabling natural language queries over structured data.

### System Components

```
┌─────────────────┐
│  Frontend (React)│
│  - TypeScript    │
│  - UI Components │
└────────┬─────────┘
         │ HTTP/REST
         ▼
┌─────────────────────┐
│  Backend (FastAPI)  │
│  - API Endpoints    │
│  - Repository Layer │
└────────┬────────────┘
         │ AWS SDK
         ▼
┌──────────────────────────┐
│  Amazon Bedrock          │
│  Knowledge Base (SQL)    │
└────────┬─────────────────┘
         │
         ▼
┌──────────────────────────┐
│  Amazon Redshift         │
│  Serverless              │
└──────────────────────────┘
```

### Data Flow

1. **Bot Creation**:
   ```
   User → Frontend Form → POST /bot/{bot_id}/knowledge-base/sql
   → Backend validates → Bedrock Agent API creates KB
   → Starts ingestion job → Returns KB ID
   ```

2. **Natural Language Query**:
   ```
   User Query → POST /bot/{bot_id}/knowledge-base/query
   → Bedrock Agent Runtime API → Generates SQL
   → Executes on Redshift → Returns structured results
   → Frontend displays in table format
   ```

3. **Status Monitoring**:
   ```
   Frontend polls → GET /bot/{bot_id}/knowledge-base/status
   → Checks ingestion job → Returns status
   → Auto-refresh until complete
   ```

## Backend Implementation

### Directory Structure

```
backend/
├── app/
│   ├── routes/
│   │   ├── bot.py                    # SQL KB API endpoints
│   │   └── schemas/
│   │       └── bot_kb.py             # Pydantic schemas
│   ├── repositories/
│   │   ├── sql_knowledge_base.py     # Core business logic
│   │   └── models/
│   │       └── custom_bot_kb.py      # Data models
│   └── utils.py                      # Bedrock client helpers
└── tests/
    └── test_repositories/
        └── test_sql_knowledge_base.py # Unit tests
```

### API Endpoints

#### 1. Create SQL Knowledge Base

**Endpoint:** `POST /bot/{bot_id}/knowledge-base/sql`

**Request Body:**
```python
{
    "knowledge_base_type": "SQL",
    "database_config": {
        "workgroup_name": "my-workgroup",
        "workgroup_arn": "arn:aws:redshift-serverless:...",
        "database_name": "mydb",
        "table_name": "mytable",
        "field_mapping": {
            "id": "id",
            "content": "content",
            "metadata": "metadata"
        },
        "secret_arn": "arn:aws:secretsmanager:..."
    },
    "search_params": {
        "max_results": 10,
        "search_type": "hybrid"
    },
    "embedding_model_arn": "arn:aws:bedrock:...:foundation-model/amazon.titan-embed-text-v2:0"
}
```

**Response:**
```python
{
    "knowledge_base_type": "SQL",
    "knowledge_base_id": "ABC123XYZ",
    "data_source_ids": ["DS456"],
    "status": "CREATING",
    ...
}
```

**Implementation:**
```python
@router.post("/bot/{bot_id}/knowledge-base/sql", response_model=SqlKnowledgeBaseOutput)
def create_sql_knowledge_base_endpoint(
    request: Request,
    bot_id: str,
    sql_kb_input: SqlKnowledgeBaseInput,
):
    from app.repositories.sql_knowledge_base import create_sql_knowledge_base

    current_user: User = request.state.current_user

    # Verify bot ownership
    bot = find_bot_by_id(bot_id)
    if not bot.is_owned_by_user(current_user):
        raise PermissionError("The bot is not owned by the user.")

    # Create KB
    kb_id, data_source_id = create_sql_knowledge_base(
        bot_id=bot_id,
        sql_config=sql_config,
        kb_name=f"sql-kb-{bot_id}",
    )

    return SqlKnowledgeBaseOutput(...)
```

#### 2. Get Knowledge Base Status

**Endpoint:** `GET /bot/{bot_id}/knowledge-base/status?knowledge_base_id={kb_id}`

**Response:**
```python
{
    "knowledge_base_id": "ABC123XYZ",
    "status": "ACTIVE",  # CREATING | ACTIVE | FAILED
    "ingestion_job_id": "JOB789",
    "ingestion_job_status": "COMPLETE",  # STARTING | IN_PROGRESS | COMPLETE | FAILED
    "error_message": null
}
```

#### 3. Query Knowledge Base

**Endpoint:** `POST /bot/{bot_id}/knowledge-base/query?knowledge_base_id={kb_id}`

**Request Body:**
```python
{
    "query": "What are the top 5 products by revenue?",
    "max_results": 10
}
```

**Response:**
```python
{
    "answer": "The top 5 products by revenue are...",
    "sql_query": "SELECT * FROM products ORDER BY revenue DESC LIMIT 5",
    "results": [
        {"id": 1, "name": "Product A", "revenue": 10000},
        ...
    ],
    "citations": [...]
}
```

#### 4. Delete Knowledge Base

**Endpoint:** `DELETE /bot/{bot_id}/knowledge-base?knowledge_base_id={kb_id}`

**Response:**
```python
{
    "success": true,
    "message": "Knowledge Base ABC123XYZ deleted successfully"
}
```

### Repository Layer

**File:** `backend/app/repositories/sql_knowledge_base.py`

Key functions:

```python
def create_sql_knowledge_base(
    bot_id: str,
    sql_config: SqlDatabaseConfigModel,
    kb_name: str,
) -> tuple[str, str]:
    """
    Create Bedrock Knowledge Base with Redshift data source

    Returns:
        tuple: (knowledge_base_id, data_source_id)
    """
    client = get_bedrock_agent_client()

    response = client.create_knowledge_base(
        name=kb_name,
        roleArn=os.getenv("BEDROCK_KB_ROLE_ARN"),
        knowledgeBaseConfiguration={
            "type": "VECTOR",
            "vectorKnowledgeBaseConfiguration": {
                "embeddingModelArn": sql_config.embedding_model_arn
            },
        },
        storageConfiguration={
            "type": "REDSHIFT",
            "redshiftConfiguration": {
                "workgroupName": sql_config.workgroup_name,
                "databaseName": sql_config.database_name,
                "tableName": sql_config.table_name,
                "credentialsSecretArn": sql_config.secret_arn,
                "fieldMapping": {
                    "primaryKeyField": sql_config.field_mapping["id"],
                    "textField": sql_config.field_mapping["content"],
                    "metadataField": sql_config.field_mapping["metadata"],
                },
            },
        },
    )

    kb_id = response["knowledgeBase"]["knowledgeBaseId"]

    # Start ingestion job
    data_source_id = get_data_source_id(client, kb_id)
    if data_source_id:
        client.start_ingestion_job(
            knowledgeBaseId=kb_id,
            dataSourceId=data_source_id
        )

    return (kb_id, data_source_id)
```

### Testing

**File:** `backend/tests/test_repositories/test_sql_knowledge_base.py`

```python
@patch.dict(os.environ, {"BEDROCK_KB_ROLE_ARN": "arn:aws:iam::..."})
@patch("app.repositories.sql_knowledge_base.get_bedrock_agent_client")
def test_create_sql_knowledge_base_success(self, mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_client.create_knowledge_base.return_value = {
        "knowledgeBase": {"knowledgeBaseId": "test-kb-123"}
    }

    kb_id, data_source_id = create_sql_knowledge_base(
        bot_id="test-bot-001",
        sql_config=self.sql_config,
        kb_name="test-sql-kb",
    )

    self.assertEqual(kb_id, "test-kb-123")
```

**Run tests:**
```bash
cd backend
poetry run python tests/test_repositories/test_sql_knowledge_base.py
```

## Frontend Implementation

### Directory Structure

```
frontend/
├── src/
│   ├── features/
│   │   ├── knowledgeBase/
│   │   │   ├── types/
│   │   │   │   └── index.d.ts           # TypeScript types
│   │   │   └── components/
│   │   │       ├── SqlDatabaseConfigForm.tsx
│   │   │       ├── KnowledgeBaseStatusBadge.tsx
│   │   │       └── *.test.tsx           # Component tests
│   │   └── chat/
│   │       └── components/
│   │           └── SqlResultsTable.tsx
│   └── hooks/
│       └── useSqlKnowledgeBaseApi.ts    # API client
└── package.json
```

### TypeScript Types

**File:** `frontend/src/features/knowledgeBase/types/index.d.ts`

```typescript
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
```

### API Client Hook

**File:** `frontend/src/hooks/useSqlKnowledgeBaseApi.ts`

```typescript
const useSqlKnowledgeBaseApi = () => {
  const http = useHttp();

  return {
    createSqlKnowledgeBase: (botId: string, params: CreateSqlKnowledgeBaseRequest) => {
      return http.post<CreateSqlKnowledgeBaseResponse>(
        `bot/${botId}/knowledge-base/sql`,
        params
      );
    },

    getKnowledgeBaseStatus: (botId: string, knowledgeBaseId: string) => {
      return http.get<KnowledgeBaseStatusInfo>(
        `bot/${botId}/knowledge-base/status?knowledge_base_id=${knowledgeBaseId}`,
        {
          refreshInterval: (data) => {
            // Poll every 5 seconds during creation/ingestion
            if (data?.status === 'CREATING' ||
                data?.ingestionJobStatus === 'IN_PROGRESS') {
              return 5000;
            }
            return 0;
          },
        }
      );
    },
  };
};
```

### Components

#### SqlDatabaseConfigForm

Form component for collecting Redshift connection details:

```typescript
<SqlDatabaseConfigForm
  config={sqlConfig}
  onChange={setSqlConfig}
  errors={validationErrors}
/>
```

Features:
- Input validation with real-time feedback
- ARN format validation
- Helpful hints for each field
- Accessible form design

#### KnowledgeBaseStatusBadge

Visual status indicator with auto-refresh:

```typescript
<KnowledgeBaseStatusBadge
  status="ACTIVE"
  ingestionJobStatus="COMPLETE"
/>
```

Features:
- Color-coded badges
- Animated icons for in-progress states
- Error message tooltips

#### SqlResultsTable

Table display for SQL query results:

```typescript
<SqlResultsTable
  results={queryResults}
  sqlQuery={generatedSql}
  maxRows={100}
/>
```

Features:
- Responsive table layout
- Collapsible SQL query display
- Smart value formatting
- Row truncation for large datasets

### Testing

**Run frontend tests:**
```bash
cd frontend
npm test
```

**Test coverage:**
- SqlDatabaseConfigForm: 9 tests
- KnowledgeBaseStatusBadge: 14 tests
- SqlResultsTable: 15 tests

## Infrastructure (CDK)

### Required IAM Role

**File:** `cdk/lib/constructs/bedrock-kb-role.ts` (to be created)

```typescript
import * as iam from 'aws-cdk-lib/aws-iam';
import * as cdk from 'aws-cdk-lib';

export class BedrockKbRole extends cdk.Stack {
  public readonly role: iam.Role;

  constructor(scope: cdk.App, id: string) {
    super(scope, id);

    this.role = new iam.Role(this, 'BedrockKbRole', {
      assumedBy: new iam.ServicePrincipal('bedrock.amazonaws.com'),
      description: 'IAM role for Bedrock Knowledge Base to access Redshift',
    });

    // Redshift Data API permissions
    this.role.addToPolicy(
      new iam.PolicyStatement({
        actions: [
          'redshift-data:ExecuteStatement',
          'redshift-data:DescribeStatement',
          'redshift-data:GetStatementResult',
          'redshift-serverless:GetCredentials',
        ],
        resources: ['*'], // TODO: Scope to specific workgroup ARN
      })
    );

    // Secrets Manager permissions
    this.role.addToPolicy(
      new iam.PolicyStatement({
        actions: ['secretsmanager:GetSecretValue'],
        resources: ['*'], // TODO: Scope to specific secret ARN
      })
    );
  }
}
```

### Environment Variables

**Required in backend:**

```bash
# .env or Lambda environment variables
BEDROCK_KB_ROLE_ARN=arn:aws:iam::123456789012:role/BedrockKbRole
DEFAULT_MODEL_ARN=arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-5-sonnet-20241022-v2:0
```

**Add to `.env.template`:**
```bash
# SQL Knowledge Base Configuration
BEDROCK_KB_ROLE_ARN=
DEFAULT_MODEL_ARN=arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-5-sonnet-20241022-v2:0
```

## Deployment

### Step 1: Deploy Infrastructure

```bash
cd cdk
npm install
npx cdk deploy --all
```

This will create the Bedrock KB IAM role.

### Step 2: Update Environment Variables

Add the role ARN to your Lambda function environment variables:

```bash
export BEDROCK_KB_ROLE_ARN=$(aws cloudformation describe-stacks \
  --stack-name BedrockKbRoleStack \
  --query 'Stacks[0].Outputs[?OutputKey==`RoleArn`].OutputValue' \
  --output text)
```

### Step 3: Deploy Backend

Backend is deployed as part of the main CDK stack. No additional steps needed.

### Step 4: Deploy Frontend

```bash
cd frontend
npm install
npm run build
# Deployed via CloudFront/S3 (part of main CDK stack)
```

## Development Workflow

### Adding a New Feature

1. **Backend**:
   - Add schema to `backend/app/routes/schemas/bot_kb.py`
   - Add repository function to `backend/app/repositories/sql_knowledge_base.py`
   - Add API endpoint to `backend/app/routes/bot.py`
   - Add tests to `backend/tests/test_repositories/test_sql_knowledge_base.py`

2. **Frontend**:
   - Add TypeScript type to `frontend/src/features/knowledgeBase/types/index.d.ts`
   - Add API method to `frontend/src/hooks/useSqlKnowledgeBaseApi.ts`
   - Create component in `frontend/src/features/knowledgeBase/components/`
   - Add component tests

3. **Test**:
   ```bash
   # Backend
   cd backend && poetry run python tests/test_repositories/test_sql_knowledge_base.py

   # Frontend
   cd frontend && npm test
   ```

4. **Commit**:
   ```bash
   git add .
   git commit -m "feat(sql-kb): add new feature"
   ```

### Code Style

**Backend (Python):**
- Follow PEP 8
- Use type hints for all functions
- Google-style docstrings
- Black formatter (pre-commit hook)

**Frontend (TypeScript):**
- ESLint configuration
- Prettier formatter (pre-commit hook)
- Functional components with hooks
- Tailwind CSS for styling

## Troubleshooting

### Backend Issues

**Issue:** `BEDROCK_KB_ROLE_ARN environment variable is not set`

**Solution:**
```bash
export BEDROCK_KB_ROLE_ARN=arn:aws:iam::123456789012:role/BedrockKbRole
```

**Issue:** `Access Denied` when creating KB

**Solution:** Verify the Bedrock KB role has correct permissions for Redshift and Secrets Manager.

### Frontend Issues

**Issue:** TypeScript compilation errors

**Solution:**
```bash
cd frontend
rm -rf node_modules
npm install
npm run build
```

**Issue:** Tests failing

**Solution:**
```bash
# Check test dependencies
npm list vitest @testing-library/react

# Reinstall if needed
npm install --save-dev vitest @testing-library/react @testing-library/jest-dom
```

## Performance Optimization

### Backend

1. **Caching**: Cache KB status responses (5-minute TTL)
2. **Connection Pooling**: Bedrock SDK handles automatically
3. **Async Processing**: Use background tasks for long-running ingestion

### Frontend

1. **Lazy Loading**: Load SQL KB components only when needed
2. **Memoization**: Use `useMemo` for expensive computations
3. **Debouncing**: Debounce status polling during creation

### Database

1. **Indexes**: Add indexes on frequently queried columns
2. **Materialized Views**: Use for complex aggregations
3. **Redshift RPU**: Scale up for better query performance

## Security Best Practices

1. **IAM Roles**: Use least-privilege permissions
2. **Secrets Rotation**: Enable automatic rotation for Redshift credentials
3. **Input Validation**: Sanitize all user inputs
4. **Audit Logging**: Enable CloudTrail for all Bedrock API calls
5. **Network Security**: Use VPC endpoints for Redshift access

## Monitoring and Alerts

### CloudWatch Metrics

Monitor:
- Bedrock API call count and latency
- Redshift query execution time
- Lambda function duration and errors

### CloudWatch Alarms

Set alarms for:
- Failed KB creation (> 5% failure rate)
- Slow queries (> 30 seconds)
- High error rate in Lambda (> 1%)

## Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines on:
- Code reviews
- Pull request process
- Testing requirements
- Documentation standards

## Resources

- [Amazon Bedrock Knowledge Bases Documentation](https://docs.aws.amazon.com/bedrock/latest/userguide/knowledge-base.html)
- [Amazon Redshift Serverless Documentation](https://docs.aws.amazon.com/redshift/latest/mgmt/serverless-whatis.html)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Testing Library](https://testing-library.com/docs/react-testing-library/intro/)
