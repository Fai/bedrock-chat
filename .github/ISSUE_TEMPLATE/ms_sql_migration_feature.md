---
name: MS SQL Migration to Bedrock SQL Knowledge Base
about: Implement MS SQL Server database migration and Bedrock SQL KB integration
title: "[Feature Request] MS SQL Database Migration & Bedrock SQL Knowledge Base Support"
labels: "enhancement, sql-kb, migration"
assignees: ""
---

## Describe the solution you'd like

Implement end-to-end support for migrating external MS SQL Server databases to AWS and integrating them with Amazon Bedrock Knowledge Bases (SQL type) to enable natural language querying through the Bedrock Chat application.

### High-Level Architecture

```
External MS SQL Server → AWS DMS → Amazon Redshift Serverless → Bedrock Knowledge Base (SQL)
                                                                          ↓
                                                            Bedrock Chat Bot (Query & Chat)
```

### Key Capabilities

1. **Database Migration**:
   - Migrate MS SQL Server databases to AWS using AWS Database Migration Service (DMS)
   - Support both one-time migration and continuous replication (CDC)
   - Handle schema conversion (MS SQL → Redshift) using AWS Schema Conversion Tool

2. **Bedrock SQL Knowledge Base Integration**:
   - Create Bedrock Knowledge Bases with Redshift Serverless as data source
   - Configure field mapping for semantic search (id, content, metadata)
   - Enable natural language to SQL query conversion via Bedrock

3. **User Interface**:
   - Migration progress monitoring dashboard
   - Database schema upload and validation UI
   - SQL KB configuration wizard in bot creation flow
   - Query transparency (show generated SQL in chat)

4. **Infrastructure as Code**:
   - CDK constructs for VPN/Direct Connect connectivity
   - DMS replication instance and endpoints
   - Redshift Serverless with cost optimization (auto-pause, RPU scaling)
   - Secrets Manager for credential management
   - CloudWatch monitoring and budget alerts

## Why the solution is needed

### Business Problem

Our customers have valuable structured data in external MS SQL Server databases (on-premises or other clouds) that they want to query using natural language through AI-powered chatbots. Current Bedrock Chat only supports:
- Vector-based knowledge bases (documents in S3)
- Kendra search (deprecated focus)

There is **no support for structured SQL databases**, which represent a significant portion of enterprise data.

### Customer Use Cases

1. **Customer Order History Queries**:
   - User asks: _"Show me all orders from customer ABC in Q1 2024"_
   - Bot converts to SQL, queries Redshift, returns natural language answer

2. **Product Inventory Lookups**:
   - User asks: _"What's the current stock level for product XYZ?"_
   - Bot retrieves real-time inventory data from migrated database

3. **Sales Analytics**:
   - User asks: _"What were our top-selling products last month?"_
   - Bot performs aggregation queries and presents insights

4. **Financial Reporting**:
   - User asks: _"Calculate total revenue by region for 2024"_
   - Bot generates complex analytical queries with joins and aggregations

### Why Migrate to AWS?

- **Bedrock Requirement**: Bedrock Knowledge Bases (SQL type) only supports Amazon Redshift Serverless
- **Scalability**: Redshift Serverless auto-scales based on workload (8-512 RPU)
- **Cost Optimization**: Pay-per-use with auto-pause (no idle costs)
- **Security**: AWS KMS encryption, VPC isolation, IAM-based access control
- **Integration**: Native integration with Bedrock, S3, and other AWS services

## Additional context

### Current State

- **Type Definition Exists**: `type_kb_resource_type = Literal["VECTOR", "KENDRA", "SQL"]` is already defined in codebase
- **No Implementation**: SQL type defined but not implemented in UI or backend
- **Architecture Gap**: No infrastructure for SQL database connectivity or migration

### Technical Specifications

#### Infrastructure Components

1. **Network Connectivity**:
   - Site-to-Site VPN or AWS Direct Connect
   - Security groups for DMS and Redshift access
   - VPC endpoints for Bedrock service (optional)

2. **AWS Database Migration Service (DMS)**:
   - Replication instance (t3.medium start, scale as needed)
   - Source endpoint: Customer MS SQL Server
   - Target endpoint: Redshift Serverless
   - Migration task with table mappings and transformations

3. **Amazon Redshift Serverless**:
   - Base capacity: 8 RPU (cost-optimized)
   - Max capacity: 128 RPU (migration spikes)
   - Auto-pause: 10 minutes idle time
   - Encryption: AWS KMS at rest + TLS in transit

4. **Amazon Bedrock Knowledge Base (SQL)**:
   - Data source type: `REDSHIFT`
   - Field mapping: `{primaryKeyField, textField, metadataField}`
   - Embedding model: Titan v2 or Cohere Multilingual v3

#### Backend Implementation

**Files to Create**:
- `backend/app/repositories/redshift_kb.py` - Redshift query repository
- `backend/app/routes/migration.py` - Migration monitoring APIs
- `backend/app/routes/schemas/sql_kb.py` - SQL KB data models

**Files to Modify**:
- `backend/app/repositories/knowledge_base.py` - Add `create_sql_knowledge_base()`
- `backend/app/routes/bot.py` - Add SQL KB endpoints

**Key Functions**:
```python
def create_sql_knowledge_base(bot_id: str, redshift_config: dict) -> str:
    """Create Bedrock KB with Redshift data source"""

def get_migration_status(task_arn: str) -> dict:
    """Monitor DMS migration progress"""

def validate_redshift_schema(workgroup: str, database: str) -> bool:
    """Validate schema for Bedrock KB compatibility"""
```

#### Frontend Implementation

**Files to Create**:
- `frontend/src/features/migration/MigrationProgress.tsx` - Migration dashboard
- `frontend/src/features/migration/SchemaUpload.tsx` - Schema upload UI
- `frontend/src/features/knowledgeBase/SqlKbWizard.tsx` - SQL KB configuration
- `frontend/src/features/chat/SqlResultTable.tsx` - Structured result display

**Files to Modify**:
- `frontend/src/features/knowledgeBase/types/index.d.ts` - Add SQL KB types
- `frontend/src/pages/BotCreate.tsx` - Integrate SQL KB wizard

#### CDK Infrastructure

**Files to Create**:
- `cdk/lib/constructs/migration-network.ts` - VPN and security groups
- `cdk/lib/constructs/database-migration.ts` - DMS infrastructure
- `cdk/lib/constructs/sql-knowledge-base.ts` - Redshift Serverless
- `cdk/lib/constructs/secrets.ts` - Secrets Manager for credentials

**Configuration** (`cdk/parameter.ts`):
```typescript
sqlKnowledgeBaseConfig: {
  redshiftBaseCapacity: 8,
  redshiftMaxCapacity: 128,
  autoPauseMinutes: 10,
  monthlyBudgetUSD: 1000,
  enableContinuousReplication: false, // One-time migration by default
}
```

### Cost Estimate

#### One-Time Migration Costs (1TB database example):
- DMS replication instance (24 hrs): $100
- Data transfer out: $90
- Redshift migration spike (128 RPU × 24 hrs): $1,152
- **Total**: ~$1,350

#### Monthly Operational Costs:
- Redshift Serverless (8 RPU, 50% utilization): $750 - $1,500
- VPN Connection: $36
- Secrets Manager: $0.40
- CloudWatch & S3: $25 - $70
- **Total**: ~$800 - $1,600/month

With auto-pause and optimization: **$500 - $1,000/month** for typical usage.

### Security Considerations

- **Encryption**: TLS 1.2+ in transit, AWS KMS at rest
- **Authentication**: IAM-based for Redshift Data API (no credentials in code)
- **Secrets Management**: AWS Secrets Manager with auto-rotation
- **Network Isolation**: VPC private subnets, no public exposure
- **Compliance**: HIPAA, PCI DSS, SOC 2 compatible infrastructure

### Migration Strategy Options

1. **One-Time Migration** (Recommended):
   - Historical data snapshot
   - Lower cost (DMS instance stopped after migration)
   - Suitable for: Archival data, reporting databases

2. **Continuous Replication (CDC)**:
   - Real-time sync with source database
   - Higher cost (DMS running 24/7)
   - Suitable for: Operational databases requiring fresh data

### Performance Requirements

- Query response time: < 2 seconds (typical)
- Database size support: Up to 100GB (initial), scalable to TB+
- Concurrent users: 50-100 simultaneous queries
- Migration throughput: 100-500 GB/hour (depends on network)

## Implementation feasibility

- [x] **Yes, we are able to implement the feature and create a pull request.**

### Implementation Timeline

**Total Duration**: 8-10 weeks
**Man-Days**: 85-110 days
**Team**: 3-4 engineers (Cloud Architect, Backend, Frontend, DevOps)

#### Phase Breakdown:

| Phase | Duration | Man-Days | Key Deliverables |
|-------|----------|----------|------------------|
| 0. Discovery (Customer) | 1-2 weeks | 0 | Questionnaire, network plan |
| 1. Infrastructure | 2 weeks | 20 | VPN, DMS, Redshift CDK |
| 2. Migration | 1-2 weeks | 10 | Schema conversion, data load |
| 3. Bedrock KB Backend | 2 weeks | 20 | APIs, KB integration, tests |
| 4. Frontend UI | 2 weeks | 20 | Migration dashboard, SQL KB wizard |
| 5. Integration & Hardening | 1-2 weeks | 15-20 | E2E testing, docs, training |

**Detailed Timeline**: See `/docs/MS_SQL_MIGRATION_IMPLEMENTATION_TIMELINE.md`

### Prerequisites

**Customer Requirements**:
- [ ] MS SQL Server version 2008 or later
- [ ] Network connectivity (VPN or Direct Connect)
- [ ] Read-only database user credentials
- [ ] Firewall access for AWS IP ranges
- [ ] Completed discovery questionnaire

**AWS Prerequisites**:
- [ ] Redshift Serverless available in target region
- [ ] Bedrock KB SQL type support confirmed
- [ ] Budget approval (~$100K implementation + $1-2K/month operations)

### Dependencies

**External**:
- AWS Database Migration Service (DMS)
- AWS Schema Conversion Tool (SCT)
- Amazon Redshift Serverless
- Amazon Bedrock Knowledge Bases (SQL connector)

**Internal**:
- Existing Bedrock Chat infrastructure
- Current CDK deployment pipeline
- Backend FastAPI framework
- Frontend React/TypeScript stack

### Testing Strategy

1. **Unit Tests**:
   - CDK construct tests (Jest)
   - Backend API tests (pytest, >80% coverage)
   - Frontend component tests (Vitest)

2. **Integration Tests**:
   - DMS migration with test MS SQL database
   - Bedrock KB creation and querying
   - End-to-end chat flow with SQL results

3. **Performance Tests**:
   - Query latency benchmarks
   - Concurrent user load testing
   - Migration throughput validation

4. **Security Tests**:
   - Secrets Manager credential rotation
   - VPC network isolation verification
   - Encryption at rest and in transit validation

### Rollback Plan

**Immediate Rollback**:
- Feature flag to disable SQL KB creation in UI
- Stop DMS replication instance
- Route users to VECTOR KB only

**Complete Rollback**:
- CDK stack deletion (preserve data in Redshift)
- Database snapshot before migration
- Frontend component hiding via feature toggle

### Monitoring & Observability

**Metrics**:
- DMS migration progress (tables loaded, rows/sec)
- Redshift query performance (latency, throughput)
- Bedrock KB ingestion status
- RPU utilization and auto-pause events
- Cost tracking per bot

**Alerts**:
- Migration failure (SNS notification)
- Query timeout > 5 seconds
- RPU usage > 80% of max capacity
- Monthly cost > budget threshold
- Failed KB creation attempts

### Documentation Required

**User Documentation**:
- [ ] SQL Knowledge Base User Guide
- [ ] Migration prerequisites checklist
- [ ] Query optimization best practices
- [ ] Troubleshooting guide

**Developer Documentation**:
- [ ] API endpoint documentation (FastAPI auto-docs)
- [ ] CDK construct reference
- [ ] Database schema requirements
- [ ] Deployment runbook

**Operator Documentation**:
- [ ] DMS migration playbook
- [ ] Redshift maintenance procedures
- [ ] Cost optimization guide
- [ ] Disaster recovery plan

## Related Issues

- #XXX - Original SQL KB type definition (if exists)
- #XXX - Bedrock Knowledge Bases enhancement request (if exists)

## References

**AWS Documentation**:
- [Amazon Bedrock Knowledge Bases - SQL Data Source](https://docs.aws.amazon.com/bedrock/latest/userguide/knowledge-base-ds-sql.html)
- [AWS Database Migration Service](https://docs.aws.amazon.com/dms/latest/userguide/)
- [Amazon Redshift Serverless](https://docs.aws.amazon.com/redshift/latest/mgmt/serverless-whatis.html)
- [AWS Schema Conversion Tool](https://docs.aws.amazon.com/SchemaConversionTool/latest/userguide/)

**Project Documentation**:
- `/docs/MS_SQL_MIGRATION_DISCOVERY_QUESTIONNAIRE.md` - Customer assessment
- `/docs/MS_SQL_MIGRATION_IMPLEMENTATION_TIMELINE.md` - Detailed timeline & costs
- `/docs/SQL_KNOWLEDGE_BASE_IMPLEMENTATION.md` - Original technical plan

---

**Priority**: High
**Estimated Effort**: 85-110 man-days (8-10 weeks)
**Business Value**: Enable AI-powered querying of enterprise SQL databases
**Risk Level**: Medium (network complexity, cost management)

---

*Submitted by: [Your Name]*
*Date: 2025-10-02*
*Customer: [Customer Name - if applicable]*
