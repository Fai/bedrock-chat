# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Bedrock Chat (BrChat) is a multilingual generative AI platform powered by Amazon Bedrock. It supports chat, custom bots with knowledge (RAG), bot sharing via a bot store, and task automation using agents.

**Main branch:** v3

## Architecture

Three-tier AWS serverless application:

- **Frontend:** React + Tailwind CSS, deployed via CloudFront + S3
- **Backend:** Python FastAPI with AWS Lambda Web Adapter, exposed via API Gateway
- **Infrastructure:** AWS CDK (TypeScript) for infrastructure as code

Key AWS services:
- Amazon Bedrock for LLM inference
- Amazon Bedrock Knowledge Bases for RAG (backed by OpenSearch Serverless)
- DynamoDB for conversation/bot storage with row-level access control
- Amazon Cognito for authentication
- EventBridge Pipes + Step Functions for knowledge base embedding pipeline
- Amazon Athena for usage analytics

## Repository Structure

```
bedrock-chat/
├── cdk/                    # AWS CDK infrastructure code (TypeScript)
│   ├── lib/
│   │   ├── constructs/     # Reusable CDK constructs (Auth, API, Database, etc.)
│   │   ├── bedrock-chat-stack.ts
│   │   └── utils/
│   ├── parameter.ts        # Type-safe multi-environment configuration (recommended)
│   └── cdk.json           # CDK config and context (legacy config method)
├── backend/               # Python FastAPI backend
│   ├── app/
│   │   ├── routes/        # API route handlers
│   │   ├── repositories/  # Data access layer (DynamoDB, OpenSearch)
│   │   ├── usecases/      # Business logic
│   │   ├── agents/        # Agent tools (knowledge, internet search, etc.)
│   │   └── main.py        # FastAPI application entry point
│   ├── embedding_statemachine/  # Step Functions handlers for KB ingestion
│   └── pyproject.toml     # Poetry dependencies
└── frontend/              # React frontend (Vite)
    ├── src/
    │   ├── components/    # Shared UI components
    │   ├── features/      # Feature-specific components (agent, discover, etc.)
    │   ├── hooks/         # React hooks
    │   └── pages/         # Page components
    └── package.json
```

## Common Development Commands

### CDK (Infrastructure)

```bash
cd cdk
npm ci                                    # Install dependencies
npx cdk bootstrap                         # One-time bootstrap per region
npx cdk deploy --all                      # Deploy all stacks
npx cdk deploy --all -c envName=dev       # Deploy specific environment
npx cdk destroy                           # Destroy all stacks
npm run build                             # Compile TypeScript
npm test                                  # Run Jest tests
```

### Backend (Python)

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install poetry
poetry install                            # Install dependencies

# Configure environment variables (see backend/README.md for list)
export CONVERSATION_TABLE_NAME=BedrockChatStack-DatabaseConversationTablexxxx
export BOT_TABLE_NAME=BedrockChatStack-DatabaseBotTablexxxx
# ... (see backend/README.md for complete list)

# Run local server
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# API docs available at:
# - http://127.0.0.1:8000/docs (Swagger)
# - http://127.0.0.1:8000/redoc (Redoc)

# Run specific test
poetry run python tests/test_bedrock.py
poetry run python tests/test_repositories/test_conversation.py
```

### Frontend (React)

```bash
cd frontend
npm ci                                    # Install dependencies

# Configure .env.local (copy from .env.template)
# Fill in values from `cdk deploy` outputs

npm run dev                               # Start dev server
npm run build                             # Build for production
npm run lint                              # Run ESLint
npm test                                  # Run tests with Vitest
npm run preview                           # Preview production build
npx ladle serve                           # Start component explorer
```

### Pre-commit Hooks (Lefthook)

```bash
# Install lefthook (https://github.com/evilmartians/lefthook)
brew install lefthook  # macOS

# Setup (from repository root)
lefthook install

# Hooks run automatically on commit:
# - backend: black (formatting), mypy (type checking)
# - frontend: prettier (formatting), eslint (linting)
```

## Key Implementation Details

### Multi-Environment Deployments

Configure environments in `cdk/parameter.ts` (type-safe, recommended):

```typescript
bedrockChatParams.set("dev", {
  bedrockRegion: "us-west-2",
  allowedIpV4AddressRanges: ["10.0.0.0/8"],
  enableRagReplicas: false,  // Cost-saving for dev
});

bedrockChatParams.set("prod", {
  bedrockRegion: "us-east-1",
  enableLambdaSnapStart: true,
  enableRagReplicas: true,
});
```

Deploy: `npx cdk deploy --all -c envName=dev`

**Note:** Main stacks are prefixed (e.g., `dev-BedrockChatStack`), but dynamic stacks (`BrChatKbStack*`, `ApiPublishmentStack*`) are not. All resources tagged with `CDKEnvironment`.

### Row-Level Access Control

The backend uses DynamoDB with a dedicated `tableAccessRole` that the Lambda assumes. User IDs from Cognito JWT are used as partition keys for row-level isolation.

See: `cdk/lib/constructs/database.ts` and `backend/app/repositories/common.py:get_conversation_table_client()`

### Large Message Handling

Messages exceeding 300KB are stored in S3 (`LARGE_MESSAGE_BUCKET`) with a reference in DynamoDB to avoid item size limits.

See: `backend/app/repositories/conversation.py:store_conversation()`

### Knowledge Base Embedding Pipeline

When a bot with knowledge is created/updated:
1. DynamoDB Stream triggers EventBridge Pipe
2. Step Functions orchestrates:
   - CodeBuild creates CloudFormation stack with Bedrock Knowledge Base
   - Knowledge Base ID stored back in DynamoDB
   - Bot status updated to `AVAILABLE`

See: `cdk/lib/constructs/embedding.ts` and `backend/embedding_statemachine/`

### RAG Implementation

Custom bots use Amazon Bedrock Knowledge Bases for RAG. The system:
- Searches knowledge base via `vector_search.py:search_related_docs()`
- Injects retrieved documents into prompt via `prompt.py:build_rag_prompt()`
- Supports both tool-based and prompt-based RAG flows

See: `backend/app/usecases/chat.py:prepare_conversation()` and `backend/app/vector_search.py`

### Agent Tools

Agent tools are modular and located in `backend/app/agents/tools/`:
- `knowledge.py` - Query knowledge bases
- `internet_search.py` - Web search
- `bedrock_agent.py` - Invoke Bedrock Agents

All tools implement `AgentTool` interface. Add new tools by creating a new file and registering in `agents/utils.py:get_tools()`.

See: `docs/AGENT.md` for development guide

### Bot Store

Optional feature using dedicated OpenSearch Serverless collection for bot search/discovery. Controlled by `enableBotStore` in CDK config.

See: `cdk/lib/constructs/bot-store.ts` and `backend/app/repositories/bot_store.py`

### Frontend State Management

- **Zustand** for global state (auth, user preferences)
- **XState** for complex state machines (chat streaming)
- **SWR** for API data fetching with caching

See: `frontend/src/hooks/` and state machine implementations in `frontend/src/features/`

### Authentication

Cognito User Pools with optional external IdP support (Google, custom OIDC).

User groups:
- `Admin` - Administrative features
- `CreatingBotAllowed` - Can create custom bots (default auto-join)
- `PublishAllowed` - Can publish bot APIs

See: `docs/ADMINISTRATOR.md`, `docs/PUBLISH_API.md`, and `cdk/lib/constructs/auth.ts`

## Configuration Options

Key parameters in `cdk/parameter.ts` or `cdk/cdk.json`:

- `bedrockRegion` - Region where Bedrock is available (default: us-east-1)
- `allowedIpV4AddressRanges` / `allowedIpV6AddressRanges` - IP allowlists for WAF
- `enableRagReplicas` - Enable standby replicas for RAG OpenSearch (production: true, dev: false)
- `enableBotStoreReplicas` - Enable standby replicas for bot store (can't be changed after creation)
- `enableLambdaSnapStart` - Enable Lambda SnapStart for faster cold starts (not all regions)
- `enableBedrockCrossRegionInference` - Use cross-region inference profiles
- `globalAvailableModels` - Restrict available models (empty array = all models)
- `selfSignUpEnabled` - Allow user self-registration
- `autoJoinUserGroups` - Groups new users auto-join (default: `["CreatingBotAllowed"]`)
- `allowedSignUpEmailDomains` - Restrict signup email domains
- `allowedCountries` - Geo-restriction via ISO-3166 country codes
- `enableFrontendWaf` - Deploy frontend WAF in us-east-1 (disable if restricted by policy)

## Testing

### Unit Tests

**Backend Tests**:
Located in `backend/tests/`, run with:
```bash
poetry run python tests/test_bedrock.py
poetry run python tests/test_repositories/test_conversation.py
poetry run python tests/test_repositories/test_s3_vector_kb.py
poetry run python tests/test_repositories/test_sql_knowledge_base.py
```

**Frontend Tests**:
Located alongside components, run with:
```bash
cd frontend
npm test
```

**CDK Tests**:
Located in `cdk/test/`, run with:
```bash
cd cdk
npm test
```

### E2E Testing

For comprehensive end-to-end testing including S3 Vector and SQL Knowledge Base features, see:
- **[E2E Testing Guide](docs/E2E_TESTING_GUIDE.md)** - Complete testing workflows
- **[SQL KB User Guide](docs/SQL_KB_USER_GUIDE.md)** - SQL KB specific testing
- **[SQL KB Developer Guide](docs/SQL_KB_DEVELOPER_GUIDE.md)** - Technical implementation details

### Architecture Review

For production deployment considerations:
- **[AWS Well-Architected Review](docs/AWS_WELL_ARCHITECTED_REVIEW.md)** - Security, cost, and operational assessment

## Important Notes for Development

1. **Local backend development requires OpenSearch access:** Configure `devAccessIamRoleArn` in CDK config with your IAM role ARN to grant OpenSearch data access permissions.

2. **Message size limits:** DynamoDB items have a 400KB limit. Messages >300KB automatically use S3 storage.

3. **Bot stack creation is dynamic:** Custom bot stacks (`BrChatKbStack*`) are created at runtime via CodeBuild, not during main CDK deployment.

4. **V3 migration:** This is V3 of the application. V2 migrations require running `docs/migration/migrate_v2_v3.py`. See `docs/migration/V2_TO_V3.md`.

5. **Supported models:** Model IDs are defined in `frontend/src/constants/index.ts`. The list includes Claude, Nova, Mistral, DeepSeek, and Llama models. Ensure models are enabled in Bedrock console.

6. **API Gateway timeout:** Lambda has a 15-minute timeout, but API Gateway times out at 30 seconds. Long-running operations use WebSocket connections (see `cdk/lib/constructs/websocket.ts`).

7. **Deployment regions:** Deploy in regions where OpenSearch Serverless and Ingestion APIs are available. As of August 2025, supported regions include: us-east-1, us-east-2, us-west-1, us-west-2, ap-south-1, ap-northeast-1, ap-northeast-2, ap-southeast-1, ap-southeast-2, ca-central-1, eu-central-1, eu-west-1, eu-west-2, eu-south-2, eu-north-1, sa-east-1.

## Deployment

**Quick deployment via CloudShell:**
```bash
git clone https://github.com/aws-samples/bedrock-chat.git
cd bedrock-chat
chmod +x bin.sh
./bin.sh
```

**Optional parameters:** `--disable-self-register`, `--enable-lambda-snapstart`, `--ipv4-ranges`, `--ipv6-ranges`, `--allowed-signup-email-domains`, `--bedrock-region`, `--version`

See README.md for complete deployment instructions and optional parameters.
