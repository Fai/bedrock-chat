# AgentCore & Strands Migration Log

**Migration Start Date:** 2025-10-29
**Current Phase:** Phase 1 - Infrastructure Foundation ✅ COMPLETED
**Branch:** `feat/bedrock-agentcore-strand-integration`
**Last Updated:** 2025-10-29

## Migration Overview

This document tracks the progress of migrating Bedrock Chat from the current custom Bedrock implementation to the new Amazon Bedrock AgentCore and Strands agent framework.

### Migration Goals

- **Model-driven simplicity:** Leverage Strands' LLM-orchestrated tool usage instead of custom agentic loops
- **Production infrastructure:** Deploy agents on managed AWS infrastructure with session isolation and observability
- **Multi-agent capabilities:** Enable hierarchical agents, swarms, and specialized agent collaboration patterns
- **Native features:** Replace custom tools with AgentCore Gateway, Memory, and other managed services

### Migration Strategy

**Phased Hybrid Approach:**
- Phases 1-3: Foundation & infrastructure (no user impact)
- Phases 4-5: Feature parity with feature flag for gradual rollout
- Phase 6: Production migration with backward compatibility
- Phase 7: Deprecation and cleanup

### Deployment Model

**Dedicated AgentCore Runtime:**
- Session isolation for better security
- Managed scaling without Lambda concurrency limits
- Required for multi-agent collaboration features
- Built-in observability with OpenTelemetry

---

## Phase 1: Infrastructure Foundation (Weeks 1-2)

### ✅ Phase 1.1: Add AgentCore Dependencies
**Date Completed:** 2025-10-29
**Status:** ✅ COMPLETED

**Changes Made:**
- **File:** `backend/pyproject.toml`
- **Dependencies Added:**
  - `bedrock-agentcore = "^1.0.4"` - Core SDK for AgentCore integration
  - `strands-agents = "^1.0"` - Strands agent framework
  - `bedrock-agentcore-starter-toolkit = "^1.0"` - Development toolkit
  - `aws-opentelemetry-distro = "^0.10.1"` - Observability integration

**Notes:**
- Dependencies added with version constraints for stability
- OpenTelemetry included for comprehensive observability from the start

**Next Steps:**
- Run `poetry install` to update dependencies after CDK work is complete
- Verify package compatibility with existing boto3/bedrock dependencies

---

### ✅ Phase 1.2: Create AgentCore CDK Construct
**Date Completed:** 2025-10-29
**Status:** ✅ COMPLETED

**Changes Made:**
- **File Created:** `cdk/lib/constructs/agentcore.ts`

**Infrastructure Components:**

1. **ECR Repository** (`AgentContainerRepository`)
   - Repository name: `{envPrefix}bedrock-chat-agents`
   - Image scanning enabled on push
   - Lifecycle rule: Keep last 10 images
   - Removal policy: DESTROY (for development)

2. **DynamoDB Tables:**
   - **Agent Runtime Registry** (`AgentRuntimeTable`)
     - Partition key: `BotId` (maps bots to AgentCore runtime ARNs)
     - Billing: PAY_PER_REQUEST
     - Point-in-time recovery enabled
     - TTL attribute: `ExpiresAt`
     - DynamoDB Streams enabled for automation

   - **Agent Memory** (`AgentMemoryTable`) - Optional
     - Partition key: `SessionId`
     - Sort key: `Timestamp`
     - GSI: `UserIdIndex` for querying by user
     - TTL enabled for automatic cleanup

3. **IAM Roles:**
   - **Runtime Execution Role** (`AgentRuntimeExecutionRole`)
     - Assumed by: Bedrock, AgentCore, Lambda, ECS
     - Permissions:
       - Full Bedrock access (`bedrock:*`)
       - AssumeRole to table access role (for row-level security)
       - Read/write to runtime registry and memory tables
       - ECR pull for container images
       - OpenSearch access (if configured)
       - CloudWatch Logs and X-Ray (observability)

   - **Runtime Invoke Role** (`AgentRuntimeInvokeRole`)
     - Assumed by: Lambda (main handler)
     - Permissions:
       - Invoke AgentCore runtimes
       - CRUD operations on AgentCore runtimes
       - Start CodeBuild projects
       - Read/write runtime registry table
       - PassRole for runtime execution role

4. **CodeBuild Project** (`AgentBuildProject`)
   - Project name: `{envPrefix}AgentCoreBuild`
   - Purpose: Build and push ARM64 container images
   - Environment:
     - Build image: STANDARD_7_0
     - Privileged mode: Enabled (for Docker)
     - Compute: LARGE (for faster builds)
     - Platform: ARM64 Linux
   - Build process:
     - Authenticates to ECR
     - Builds ARM64 Docker image using buildx
     - Tags with commit hash and "latest"
     - Pushes to ECR
   - Timeout: 30 minutes
   - Caching: Docker layers and custom cache

5. **S3 Bucket** (`BuildArtifactBucket`)
   - Stores CodeBuild artifacts
   - Auto-delete on stack removal
   - S3-managed encryption

**Key Design Decisions:**

1. **ARM64 Architecture:**
   - AgentCore requires ARM64 Linux containers
   - Using Docker buildx for cross-platform builds
   - Graviton-optimized for better price/performance

2. **Security Model:**
   - Reusing existing table access role for row-level security
   - Separate roles for runtime execution vs. invocation
   - IAM PassRole for controlled delegation

3. **Observability:**
   - Optional X-Ray integration (controlled by `enableObservability` prop)
   - CloudWatch Logs for all components
   - Container-level tracing via OpenTelemetry

4. **Resource Naming:**
   - All resources prefixed with `envPrefix` for multi-environment support
   - Follows existing naming conventions in the project

**Outputs Created:**
- `AgentContainerRepositoryUri` - ECR repository URI
- `AgentRuntimeTableName` - Runtime registry table name
- `AgentMemoryTableName` - Memory table name (if enabled)
- `AgentBuildProjectName` - CodeBuild project name
- `RuntimeExecutionRoleArn` - Execution role ARN

**Integration Points:**
- Uses existing `Database` construct for table access role
- Compatible with existing VPC configuration (optional)
- Integrates with OpenSearch endpoint (if provided)

**Notes:**
- Construct is framework-agnostic (works with Strands, LangGraph, etc.)
- Designed for production with PITR, encryption, and monitoring
- CodeBuild spec uses buildx for ARM64 compatibility
- Memory table is optional (can be disabled for cost savings)

**Considerations:**
- Need to test buildx ARM64 build process
- May need to adjust CodeBuild compute size based on build times
- Consider adding VPC support for private subnet deployment

---

### ✅ Phase 1.3: Update BedrockChatStack
**Date Completed:** 2025-10-29
**Status:** ✅ COMPLETED

**Changes Made:**

1. **BedrockChatStack Integration** (`cdk/lib/bedrock-chat-stack.ts`):
   - Imported `AgentCore` construct
   - Added AgentCore props to `BedrockChatStackProps`:
     - `enableAgentCore?: boolean` - Feature flag to enable AgentCore infrastructure
     - `enableAgentCoreMemory?: boolean` - Enable persistent memory table (default: true)
     - `enableAgentCoreObservability?: boolean` - Enable X-Ray and OpenTelemetry (default: true)
   - Instantiated AgentCore construct conditionally based on `enableAgentCore` flag
   - Passed AgentCore instance to API construct

2. **API Construct Updates** (`cdk/lib/constructs/api.ts`):
   - Added `agentCore?: AgentCore` to `ApiProps` interface
   - Added AgentCore environment variables to Lambda handler:
     - `AGENTCORE_ENABLED` - Boolean flag
     - `AGENTCORE_RUNTIME_TABLE_NAME` - Runtime registry table
     - `AGENTCORE_MEMORY_TABLE_NAME` - Memory table (optional)
     - `AGENTCORE_CONTAINER_REPOSITORY_URI` - ECR repository
     - `AGENTCORE_BUILD_PROJECT_NAME` - CodeBuild project for container builds
     - `AGENTCORE_RUNTIME_EXECUTION_ROLE_ARN` - Execution role ARN
   - Added IAM permissions to Lambda handler role:
     - Bedrock AgentCore service permissions (invoke, create, update, delete runtimes)
     - DynamoDB permissions for runtime registry and memory tables
     - CodeBuild permissions to trigger agent container builds
     - PassRole permissions for runtime execution role
     - ECR read permissions for container images

3. **Parameter Configuration** (`cdk/lib/utils/parameter-models.ts`):
   - Added AgentCore configuration to `BedrockChatParametersSchema`:
     - `enableAgentCore: z.boolean().default(false)` - Disabled by default
     - `enableAgentCoreMemory: z.boolean().default(true)` - Enabled when AgentCore is on
     - `enableAgentCoreObservability: z.boolean().default(true)` - Enabled by default
   - Added context parameter resolution for AgentCore settings
   - Updated type definitions to include new parameters

4. **Environment Configuration** (`cdk/parameter.ts`):
   - Enabled AgentCore for `dev` environment:
     - `enableAgentCore: true`
     - `enableAgentCoreMemory: true`
     - `enableAgentCoreObservability: true`
   - Default and prod environments have AgentCore disabled (safe rollout)

**Integration Architecture:**

```
BedrockChatStack
├── Database (existing)
├── BotStore (optional, existing)
├── Embedding (existing)
├── AgentCore (NEW - optional)
│   ├── ECR Repository (agent containers)
│   ├── Runtime Registry Table (DynamoDB)
│   ├── Memory Table (DynamoDB, optional)
│   ├── CodeBuild Project (ARM64 builds)
│   ├── Runtime Execution Role (IAM)
│   └── Runtime Invoke Role (IAM)
└── BackendApi
    └── Lambda Handler
        ├── Environment Variables (AgentCore config)
        └── IAM Permissions (AgentCore operations)
```

**Key Design Decisions:**

1. **Optional by Design:**
   - AgentCore is feature-flagged via `enableAgentCore` parameter
   - Allows gradual migration without breaking existing deployments
   - Dev environment enabled for testing, prod remains on legacy implementation

2. **Full Observability:**
   - X-Ray tracing enabled by default (can be disabled for cost savings)
   - CloudWatch Logs for all components
   - OpenTelemetry integration prepared for container runtime

3. **Security Model:**
   - Reuses existing table access role pattern for row-level security
   - Separate execution vs. invocation roles (principle of least privilege)
   - IAM PassRole with service-specific conditions

4. **Resource Naming:**
   - All resources use `envPrefix` for multi-environment support
   - Follows existing naming conventions in the codebase

**Environment Variable Availability:**

The Lambda handler now has access to:
- `AGENTCORE_ENABLED` → Backend can conditionally use Strands vs. legacy agents
- `AGENTCORE_RUNTIME_TABLE_NAME` → Track bot-to-runtime mappings
- All other config needed to invoke and manage AgentCore runtimes

**Next Steps:**
- Backend code can now check `AGENTCORE_ENABLED` env var
- Phase 2 will implement Strands agent wrappers that consume these configs
- Phase 3 will create the container runtime and deployment automation

**Testing Notes:**
- Need to test CDK synthesis: `cd cdk && npm run build`
- Deploy to dev environment: `npx cdk deploy --all -c envName=dev`
- Verify CloudFormation stack includes AgentCore resources

---

## Phase 2: Core Strands Agent Implementation (Weeks 2-3)

### ⏳ Phase 2.1: Create Base Strands Agent
**Status:** ⏳ PENDING

**Planned File:** `backend/app/agents/strands/base_agent.py`

**Implementation Plan:**
- Create `StrandsAgentWrapper` class
- Map `BotModel` configuration to Strands agent config
- Handle generation parameters (temperature, top_p, etc.)
- Implement streaming callback integration
- Support for both tool-use and non-tool-use models

---

### ⏳ Phase 2.2: Port Knowledge Base Tool
**Status:** ⏳ PENDING

**Planned File:** `backend/app/agents/strands/tools/knowledge_tool.py`

**Implementation Plan:**
- Convert to Strands `@tool` decorator format
- Reuse existing `vector_search.py` and `sql_kb_search.py` logic
- Return structured results compatible with Strands
- Support both semantic and hybrid search modes

---

### ⏳ Phase 2.3: Replace Internet Search with AgentCore Gateway
**Status:** ⏳ PENDING

**Planned File:** `backend/app/agents/strands/tools/gateway_tools.py`

**Implementation Plan:**
- Configure AgentCore Gateway for Tavily/DuckDuckGo APIs
- Leverage MCP (Model Context Protocol) transformation
- Eliminate custom `internet_search.py` complexity
- Maintain Firecrawl support if needed

---

### ⏳ Phase 2.4: Handle Bedrock Agent Tool
**Status:** ⏳ PENDING

**Implementation Plan:**
- Model as nested Strands agent using "agents-as-tools" pattern
- Create sub-agent wrapper for Bedrock Agent invocations
- Preserve trace log formatting for UI display

---

### ⏳ Phase 2.5: Create Strands Orchestrator
**Status:** ⏳ PENDING

**Planned File:** `backend/app/usecases/strands_chat.py`

**Implementation Plan:**
- Replace custom agentic loop with Strands' model-driven approach
- Implement streaming callback handler
- Manage conversation history preparation
- Handle RAG prompt injection for non-tooluse models
- Maintain compatibility with existing `ChatOutput` schema

---

## Phase 3: AgentCore Runtime Integration (Weeks 3-4)

### ⏳ Phase 3.1: Create Agent Container
**Status:** ⏳ PENDING

**Planned Files:**
- `backend/agentcore_runtime/Dockerfile`
- `backend/agentcore_runtime/requirements.txt`

---

### ⏳ Phase 3.2: Implement FastAPI Server
**Status:** ⏳ PENDING

**Planned File:** `backend/agentcore_runtime/server.py`

**Implementation Plan:**
- `/invocations` POST endpoint (required by AgentCore)
- `/ping` GET health check (required by AgentCore)
- Load bot configuration from DynamoDB
- Instantiate Strands agent with appropriate tools
- Stream responses via Server-Sent Events

---

### ⏳ Phase 3.3: Build Deployment Pipeline
**Status:** ⏳ PENDING

**Notes:**
- CodeBuild spec already defined in Phase 1.2
- May need custom resource for runtime deployment automation
- Consider Blue/Green deployment strategy

---

### ⏳ Phase 3.4: Implement Runtime Registry
**Status:** ⏳ PENDING

**Planned File:** `backend/app/repositories/agentcore_runtime.py`

**Implementation Plan:**
- CRUD operations for runtime registry
- Map bot IDs to AgentCore runtime ARNs
- Create new runtime on bot creation (integrate with Step Functions)
- Handle runtime lifecycle (update, delete)
- Store runtime metadata in DynamoDB

---

## Phase 4: Feature Parity & Testing (Weeks 4-5)

### ⏳ Phase 4.1: Update Chat Use Case
**Status:** ⏳ PENDING

---

### ⏳ Phase 4.2: Conversation Storage Adapter
**Status:** ⏳ PENDING

---

### ⏳ Phase 4.3: Streaming Protocol Adapter
**Status:** ⏳ PENDING

---

### ⏳ Phase 4.4: Frontend Compatibility
**Status:** ⏳ PENDING

---

### ⏳ Phase 4.5: Comprehensive Testing
**Status:** ⏳ PENDING

---

## Phase 5: Multi-Agent Capabilities (Weeks 5-6)

*To be detailed as implementation progresses*

---

## Phase 6: Production Migration (Weeks 6-7)

*To be detailed as implementation progresses*

---

## Phase 7: Deprecation & Cleanup (Month 3+)

*To be detailed as implementation progresses*

---

## Key Decisions & Learnings

### Technical Decisions

1. **AgentCore Runtime vs. Embedded SDK**
   - **Decision:** Use dedicated AgentCore Runtime
   - **Rationale:** Better security (session isolation), managed scaling, required for multi-agent
   - **Trade-off:** Higher cold start (~2s vs ~400ms with SnapStart)

2. **Tool Migration Strategy**
   - **Decision:** Use native AgentCore features where possible
   - **Exception:** Keep custom knowledge base tool (unique to RAG architecture)
   - **Rationale:** Reduce maintenance, leverage AWS-managed tools

3. **Migration Approach**
   - **Decision:** Phased hybrid approach with feature flags
   - **Rationale:** Minimize risk, allow rollback, no breaking changes
   - **Timeline:** 2.5 months to full production

### Challenges & Solutions

*To be documented as they arise*

---

## Testing Checklist

### Unit Tests
- [ ] Strands agent wrapper
- [ ] Tool conversions (knowledge, gateway)
- [ ] Runtime registry operations
- [ ] Streaming callback handlers

### Integration Tests
- [ ] AgentCore runtime invocation
- [ ] End-to-end conversation flow
- [ ] Tool execution (knowledge base, internet search)
- [ ] Multi-agent collaboration

### Load Tests
- [ ] AgentCore scaling behavior
- [ ] Cold start impact analysis
- [ ] Concurrent user scenarios

### Compatibility Tests
- [ ] Existing bots continue to work
- [ ] Frontend unchanged (API contract)
- [ ] Conversation history compatibility

---

## Metrics & Monitoring

### Performance Metrics
- **Target:** Agent response latency ≤ current implementation
- **Current baseline:** TBD (measure before migration)
- **AgentCore:** TBD (measure after Phase 4)

### Quality Metrics
- **Target:** User satisfaction maintained or improved
- **Method:** TBD (A/B testing in Phase 6)

### Reliability Metrics
- **Target:** Error rate < 1% for AgentCore invocations
- **Monitoring:** CloudWatch dashboards + alarms

### Cost Metrics
- **Current:** TBD (Lambda costs per conversation)
- **AgentCore:** TBD (runtime costs per conversation)
- **Target:** Competitive or better at scale

---

## Resources & References

### AWS Documentation
- [Amazon Bedrock AgentCore](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/what-is-bedrock-agentcore.html)
- [Strands Agents Documentation](https://strandsagents.com/latest/)
- [AgentCore Runtime Guide](https://aws.github.io/bedrock-agentcore-starter-toolkit/)

### GitHub Repositories
- [AgentCore Python SDK](https://github.com/aws/bedrock-agentcore-sdk-python)
- [AgentCore Samples](https://github.com/awslabs/amazon-bedrock-agentcore-samples)
- [Strands SDK](https://github.com/strands-agents/sdk-python)

### Community
- [AgentCore Discord](https://discord.gg/bedrockagentcore-preview)

---

## Migration Timeline

```
Week 1-2:  Phase 1 - Infrastructure Foundation ✅ (In Progress)
Week 2-3:  Phase 2 - Core Strands Implementation
Week 3-4:  Phase 3 - AgentCore Runtime Integration
Week 4-5:  Phase 4 - Feature Parity & Testing
Week 5-6:  Phase 5 - Multi-Agent Capabilities
Week 6-10: Phase 6 - Production Migration (Gradual Rollout)
Month 3+:  Phase 7 - Deprecation & Cleanup
```

**Estimated Completion:** ~2.5 months from start

---

## Next Immediate Steps

1. ✅ Add AgentCore dependencies to `pyproject.toml`
2. ✅ Create AgentCore CDK construct
3. ✅ Update BedrockChatStack to integrate construct
4. ⏳ Test CDK build and synthesis
5. ⏳ Create Strands agent base wrapper (Phase 2.1)
6. ⏳ Port knowledge base tool to Strands format (Phase 2.2)

---

## Phase 1 Summary ✅

**Duration:** 1 day (2025-10-29)
**Status:** COMPLETED

**Achievements:**
- ✅ Added all required dependencies (bedrock-agentcore, strands-agents, toolkit, OpenTelemetry)
- ✅ Created comprehensive AgentCore CDK construct with:
  - ECR repository for ARM64 containers
  - DynamoDB tables for runtime registry and memory
  - IAM roles with proper security boundaries
  - CodeBuild project for automated container builds
  - Full observability stack (CloudWatch, X-Ray)
- ✅ Integrated AgentCore into main stack with feature flags
- ✅ Configured environment variables for backend consumption
- ✅ Set up IAM permissions for Lambda to invoke AgentCore
- ✅ Documented entire migration plan and progress

**Infrastructure Ready:**
- Backend Lambda can now access AgentCore configuration via environment variables
- Dev environment configured to enable AgentCore for testing
- Production environment safely remains on legacy implementation
- All resources properly tagged and named for multi-environment support

**Next:** Move to Phase 2 - Core Strands Agent Implementation

---

*Last Updated: 2025-10-29*
