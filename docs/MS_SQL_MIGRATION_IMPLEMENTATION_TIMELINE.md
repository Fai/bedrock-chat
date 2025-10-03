# MS SQL to Bedrock SQL KB - Implementation Timeline & Man-Day Estimate

## Executive Summary

**Total Implementation Time**: 8-10 weeks
**Total Man-Days**: 85-110 days
**Team Size**: 3-4 engineers

---

## Team Composition & Rates

| Role | Quantity | Day Rate (Example) | Responsibilities |
|------|----------|-------------------|------------------|
| **Senior Cloud Architect** | 1 | $1,200/day | AWS infrastructure, DMS, Redshift design |
| **Senior Backend Engineer** | 1 | $1,000/day | Python/FastAPI, Bedrock KB integration |
| **Senior Frontend Engineer** | 1 | $900/day | React/TypeScript, migration UI |
| **DevOps Engineer** | 0.5 (part-time) | $1,000/day | Network setup, VPN, monitoring |

**Blended Rate**: ~$1,025/day

---

## Phase Breakdown - Code Implementation Only

### **Phase 0: Discovery & Planning (Customer-Led)**
**Duration**: 1-2 weeks
**Man-Days**: 0 (Customer questionnaire completion)

**Note**: This phase is customer-driven. No coding required. Sales team facilitates questionnaire and technical review call.

---

### **Phase 1: Infrastructure Development**
**Duration**: 2 weeks
**Man-Days**: 20 days

#### 1.1 Network & VPN Setup (5 days)
**Engineer**: DevOps Engineer (0.5 FTE)

| Task | Time | Files to Create/Modify |
|------|------|------------------------|
| CDK construct for VPN connection | 2 days | `cdk/lib/constructs/migration-network.ts` |
| Security groups for DMS | 1 day | Update `migration-network.ts` |
| VPC endpoint configuration | 1 day | Update `bedrock-chat-stack.ts` |
| Network connectivity testing | 1 day | Test scripts |

**Deliverables**:
- VPN tunnel operational
- Firewall rules configured
- Network connectivity validated

#### 1.2 AWS DMS Infrastructure (8 days)
**Engineer**: Senior Cloud Architect

| Task | Time | Files to Create/Modify |
|------|------|------------------------|
| DMS replication instance CDK | 2 days | `cdk/lib/constructs/database-migration.ts` |
| Source endpoint (MS SQL) | 1 day | Update `database-migration.ts` |
| Target endpoint (Redshift) | 1 day | Update `database-migration.ts` |
| Secrets Manager integration | 1 day | `cdk/lib/constructs/secrets.ts` |
| DMS task configuration | 2 days | Migration task with table mappings |
| CloudWatch monitoring setup | 1 day | `cdk/lib/constructs/migration-monitoring.ts` |

**Deliverables**:
- DMS infrastructure deployed
- Endpoints configured and tested
- Monitoring dashboards ready

#### 1.3 Redshift Serverless for SQL KB (7 days)
**Engineer**: Senior Cloud Architect

| Task | Time | Files to Create/Modify |
|------|------|------------------------|
| Redshift namespace & workgroup | 2 days | `cdk/lib/constructs/sql-knowledge-base.ts` |
| IAM roles for Bedrock KB | 2 days | Update `sql-knowledge-base.ts` |
| Cost optimization config (auto-pause) | 1 day | Update workgroup settings |
| S3 staging bucket for data | 1 day | `cdk/lib/constructs/staging-bucket.ts` |
| Unit tests for CDK constructs | 1 day | `cdk/test/sql-kb.test.ts` |

**Deliverables**:
- Redshift Serverless deployed (8 RPU base)
- Auto-pause configured (10 min idle)
- Budget alerts configured
- CDK tests passing

---

### **Phase 2: Migration Execution (Customer-Dependent)**
**Duration**: 1-2 weeks
**Man-Days**: 10 days (monitoring & support)

#### 2.1 Schema Conversion (3 days)
**Engineer**: Senior Cloud Architect + Senior Backend Engineer

| Task | Time | Responsibility |
|------|------|---------------|
| AWS SCT installation & setup | 0.5 day | Cloud Architect |
| Schema conversion (MS SQL → Redshift) | 1 day | Cloud Architect |
| Data type mapping review | 1 day | Backend Engineer |
| Apply schema to Redshift | 0.5 day | Cloud Architect |

**Tools Used**: AWS Schema Conversion Tool (SCT)

#### 2.2 DMS Migration Task Execution (5 days)
**Engineer**: Senior Cloud Architect (monitoring)

| Task | Time | Files to Create/Modify |
|------|------|------------------------|
| Table mappings configuration | 1 day | JSON table mapping rules |
| Start DMS migration task | 0.5 day | AWS Console/CLI |
| Migration monitoring | 2 days | Real-time monitoring |
| Data validation (row counts) | 1 day | SQL scripts |
| Migration troubleshooting | 0.5 day | Issue resolution |

**Deliverables**:
- All tables migrated successfully
- Data validation report
- Migration metrics documented

#### 2.3 Post-Migration Validation (2 days)
**Engineer**: Senior Backend Engineer

| Task | Time | Files to Create/Modify |
|------|------|------------------------|
| Row count validation scripts | 0.5 day | `scripts/validate_migration.sql` |
| Data quality checks | 1 day | Python validation scripts |
| NULL value analysis | 0.5 day | SQL queries |

**Deliverables**:
- Migration validation report
- Data quality assessment

---

### **Phase 3: Bedrock SQL KB Integration**
**Duration**: 2 weeks
**Man-Days**: 20 days

#### 3.1 Backend API Development (12 days)
**Engineer**: Senior Backend Engineer

| Task | Time | Files to Create/Modify |
|------|------|------------------------|
| Extend data models for SQL KB | 2 days | `backend/app/routes/schemas/bot_kb.py`<br/>`backend/app/repositories/models/custom_bot_kb.py` |
| Redshift query repository | 3 days | `backend/app/repositories/redshift_kb.py` |
| Bedrock KB creation API | 3 days | `backend/app/repositories/knowledge_base.py`<br/>Function: `create_sql_knowledge_base()` |
| Data transformation for KB | 2 days | Create views in Redshift for Bedrock KB |
| API endpoints for SQL KB | 2 days | `backend/app/routes/bot.py`<br/>- POST `/bots/{id}/sql-kb`<br/>- GET `/bots/{id}/sql-kb/schema`<br/>- POST `/bots/{id}/sql-kb/query` |

**Key Implementation**:
```python
# backend/app/repositories/knowledge_base.py
def create_sql_knowledge_base(bot_id: str, redshift_config: dict) -> str:
    # 1. Create Bedrock KB with Redshift data source
    # 2. Configure field mapping (id, content, metadata)
    # 3. Start ingestion job
    # 4. Store KB ID in DynamoDB
    pass
```

#### 3.2 Backend Testing (5 days)
**Engineer**: Senior Backend Engineer

| Task | Time | Files to Create/Modify |
|------|------|------------------------|
| Unit tests for KB repository | 2 days | `backend/tests/test_repositories/test_redshift_kb.py` |
| Integration tests (Bedrock KB) | 2 days | `backend/tests/test_integration/test_sql_kb.py` |
| API endpoint tests | 1 day | `backend/tests/test_routes/test_sql_bot.py` |

**Target**: >80% code coverage

#### 3.3 Query Optimization (3 days)
**Engineer**: Senior Cloud Architect

| Task | Time | Files to Create/Modify |
|------|------|------------------------|
| Redshift query performance tuning | 1 day | Optimize views, add indexes |
| Bedrock KB field mapping optimization | 1 day | Text field concatenation strategies |
| Query result caching strategy | 1 day | Redis/CloudFront caching (optional) |

**Deliverables**:
- Backend APIs functional
- Tests passing (>80% coverage)
- Query latency < 2 seconds

---

### **Phase 4: Frontend Development**
**Duration**: 2 weeks
**Man-Days**: 20 days

#### 4.1 Migration UI Components (8 days)
**Engineer**: Senior Frontend Engineer

| Task | Time | Files to Create/Modify |
|------|------|------------------------|
| Type definitions for SQL KB | 1 day | `frontend/src/features/knowledgeBase/types/index.d.ts` |
| Migration progress component | 2 days | `frontend/src/features/migration/MigrationProgress.tsx` |
| Database schema upload UI | 2 days | `frontend/src/features/migration/SchemaUpload.tsx` |
| Table preview component | 2 days | `frontend/src/features/migration/TablePreview.tsx` |
| Migration status dashboard | 1 day | `frontend/src/features/migration/Dashboard.tsx` |

#### 4.2 SQL KB Configuration UI (7 days)
**Engineer**: Senior Frontend Engineer

| Task | Time | Files to Create/Modify |
|------|------|------------------------|
| SQL KB setup wizard | 3 days | `frontend/src/features/knowledgeBase/SqlKbWizard.tsx` |
| Field mapping interface | 2 days | `frontend/src/features/knowledgeBase/FieldMapper.tsx` |
| Integration with bot creation | 2 days | Update `frontend/src/pages/BotCreate.tsx` |

#### 4.3 Chat Interface Enhancement (3 days)
**Engineer**: Senior Frontend Engineer

| Task | Time | Files to Create/Modify |
|------|------|------------------------|
| SQL query display in chat | 1 day | Update `frontend/src/features/chat/ChatMessage.tsx` |
| Structured result table view | 1 day | `frontend/src/features/chat/SqlResultTable.tsx` |
| Query transparency toggle | 1 day | Show/hide generated SQL option |

#### 4.4 Frontend Testing (2 days)
**Engineer**: Senior Frontend Engineer

| Task | Time | Files to Create/Modify |
|------|------|------------------------|
| Component tests (Vitest) | 1 day | `*.test.tsx` for all new components |
| Ladle stories for components | 1 day | `*.stories.tsx` for component gallery |

**Deliverables**:
- Migration UI functional
- SQL KB configuration wizard complete
- All components tested and documented in Ladle

---

### **Phase 5: Integration & Hardening**
**Duration**: 1-2 weeks
**Man-Days**: 15-20 days

#### 5.1 End-to-End Testing (5 days)
**Engineers**: All team members

| Task | Time | Responsibility |
|------|------|---------------|
| E2E test scenarios | 2 days | Backend + Frontend Engineers |
| Performance testing (load test) | 1 day | Cloud Architect |
| Security testing | 1 day | DevOps Engineer |
| UAT with customer | 1 day | All team + Customer |

#### 5.2 Documentation (5 days)
**Engineers**: Senior Backend + Frontend Engineers

| Task | Time | Files to Create/Modify |
|------|------|------------------------|
| User guide for SQL KB | 2 days | `docs/SQL_KNOWLEDGE_BASE_USER_GUIDE.md` |
| Administrator deployment guide | 1 day | `docs/SQL_KB_DEPLOYMENT.md` |
| API documentation updates | 1 day | FastAPI auto-docs + README updates |
| Troubleshooting guide | 1 day | `docs/SQL_KB_TROUBLESHOOTING.md` |

#### 5.3 Production Preparation (5-10 days)
**Engineer**: Senior Cloud Architect + DevOps

| Task | Time | Files to Create/Modify |
|------|------|------------------------|
| Production CDK deployment | 2 days | Deploy to prod environment |
| Monitoring & alerting setup | 2 days | CloudWatch dashboards, alarms |
| Backup & recovery testing | 1 day | Redshift snapshot, restore test |
| Runbook creation | 1 day | `docs/SQL_KB_RUNBOOK.md` |
| Customer training session | 2-4 days | On-site/remote training |

**Deliverables**:
- Production-ready deployment
- Complete documentation
- Customer trained

---

## Total Man-Day Summary

| Phase | Duration | Man-Days | Cost Estimate ($1,025/day) |
|-------|----------|----------|----------------------------|
| **Phase 0**: Discovery | 1-2 weeks | 0 | $0 (customer-led) |
| **Phase 1**: Infrastructure | 2 weeks | 20 | $20,500 |
| **Phase 2**: Migration | 1-2 weeks | 10 | $10,250 |
| **Phase 3**: Bedrock KB | 2 weeks | 20 | $20,500 |
| **Phase 4**: Frontend | 2 weeks | 20 | $20,500 |
| **Phase 5**: Hardening | 1-2 weeks | 15-20 | $15,375 - $20,500 |
| | | | |
| **Total (Minimum)** | **8 weeks** | **85 days** | **$87,125** |
| **Total (Maximum)** | **10 weeks** | **110 days** | **$112,750** |

---

## Pricing Models for Sales Quotes

### Option 1: Fixed Price (Recommended)
**Price**: $95,000 - $115,000
**Includes**:
- All development work (85-110 man-days)
- AWS infrastructure setup
- 2 weeks of post-launch support
- Documentation and training

**Excludes**:
- AWS infrastructure costs (billed separately)
- Customer network setup (VPN/Direct Connect)
- Ongoing AWS operational costs

### Option 2: Time & Materials
**Hourly Rate**: $125-$150/hour (based on role)
**Estimated Hours**: 680-880 hours (85-110 days × 8 hrs)
**Estimated Total**: $85,000 - $132,000

**Best For**: Projects with uncertain scope or requirements

### Option 3: Phased Approach
Allow customer to approve each phase:

| Phase | Price Range |
|-------|-------------|
| Phase 1: Infrastructure | $20,000 - $25,000 |
| Phase 2: Migration | $10,000 - $12,000 |
| Phase 3: Bedrock Integration | $20,000 - $25,000 |
| Phase 4: Frontend | $20,000 - $25,000 |
| Phase 5: Hardening | $15,000 - $20,000 |

**Total**: $85,000 - $107,000

---

## AWS Infrastructure Costs (Monthly)

**To be quoted separately**:

| Component | Monthly Cost |
|-----------|--------------|
| Redshift Serverless (8 RPU, 50% utilization) | $750 - $1,500 |
| AWS DMS (stopped after migration) | $0 |
| VPN Connection | $36 |
| Secrets Manager | $0.40/secret |
| CloudWatch Logs & Metrics | $20 - $50 |
| S3 Storage (staging) | $5 - $20 |
| Data Transfer (ongoing) | $50 - $100 |
| | |
| **Total Monthly** | **$861 - $1,706** |

**One-Time Migration Costs**:
- DMS replication instance (24 hrs): $100
- Data transfer out (1TB example): $90
- Redshift migration spike (128 RPU, 24 hrs): $1,152

**Total One-Time**: ~$1,350 (for 1TB migration)

---

## Risk Contingency

Add 15-20% contingency for:
- Unexpected schema complexity
- Network connectivity issues
- Customer-side delays
- Scope creep

**Recommended Quote**: $100,000 - $120,000 (with contingency)

---

## Payment Milestones (Example)

1. **Contract Signing**: 25% ($25,000)
2. **Phase 1 Complete** (Infrastructure): 20% ($20,000)
3. **Phase 3 Complete** (Bedrock KB): 25% ($25,000)
4. **Phase 4 Complete** (Frontend): 20% ($20,000)
5. **Go-Live & Training**: 10% ($10,000)

---

## Assumptions & Exclusions

### Included in Quote:
- ✅ CDK infrastructure code development
- ✅ Backend API development (Python/FastAPI)
- ✅ Frontend UI development (React/TypeScript)
- ✅ Database schema conversion
- ✅ DMS migration configuration
- ✅ Bedrock KB integration
- ✅ Testing and documentation
- ✅ 2 weeks post-launch support

### Excluded from Quote:
- ❌ Customer VPN device configuration (customer responsibility)
- ❌ MS SQL Server licensing
- ❌ Direct Connect setup fees (if required)
- ❌ AWS infrastructure monthly costs (billed separately)
- ❌ Ongoing maintenance beyond 2 weeks
- ❌ Feature enhancements after go-live
- ❌ Training beyond initial 2-4 day session

### Customer Responsibilities:
- Complete discovery questionnaire within 1 week
- Provide database access credentials
- Configure firewall rules within 3 days
- Participate in UAT testing
- Approve each phase milestone
- Provide timely feedback on deliverables

---

## Fast-Track Option (+30% Premium)

**Timeline**: 6 weeks instead of 8-10 weeks
**Man-Days**: Same (85-110 days)
**Team Size**: 5-6 engineers (parallel work)
**Additional Cost**: +$30,000
**Total**: $130,000 - $150,000

**Trade-offs**:
- Reduced testing time
- Parallel development (higher coordination overhead)
- Limited customer feedback cycles

---

## Sales Quote Template

```
MS SQL to Bedrock SQL Knowledge Base - Implementation Services

Base Implementation: $95,000 - $115,000
- 8-10 week delivery timeline
- 3-4 engineer team
- Full-stack development (CDK, Backend, Frontend)
- Testing & documentation
- 2 weeks post-launch support

Optional Add-ons:
+ Fast-track delivery (6 weeks): +$30,000
+ Extended support (3 months): +$15,000/month
+ Custom feature development: T&M at $150/hour

AWS Infrastructure (Monthly):
$861 - $1,706/month (billed by AWS directly)

One-Time Migration Costs:
~$1,350 (for 1TB database migration)

Total Project Investment:
$95,000 - $115,000 (implementation)
+ $861-1,706/month (AWS infrastructure)
+ $1,350 (one-time migration)

Payment Terms:
Net 30 days, milestone-based (5 payments)
```

---

*Last Updated: 2025-10-02*
*Version: 1.0*
*Contact: [Sales Team Email]*
