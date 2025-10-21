# E2E Testing Guide for Bedrock Chat

## Overview

This guide covers end-to-end testing for Bedrock Chat, including the new S3 Vector and SQL Knowledge Base features.

## Prerequisites

### Infrastructure Requirements
- AWS Account with appropriate permissions
- Bedrock models enabled in target region
- CDK deployment completed successfully

### Required Environment Variables
```bash
# Core Bedrock Chat
export CONVERSATION_TABLE_NAME=BedrockChatStack-DatabaseConversationTablexxxx
export BOT_TABLE_NAME=BedrockChatStack-DatabaseBotTablexxxx
export DOCUMENT_BUCKET=bedrockregionresourcessta-useast1documentbucket038-xxx
export LARGE_MESSAGE_BUCKET=bedrockchatstack-largemessagebucketxxx
export USER_POOL_ID=xxxxxxxxx
export CLIENT_ID=xxxxxxxxx
export OPENSEARCH_DOMAIN_ENDPOINT=https://xxx.aa-region-1.aoss.amazonaws.com

# New Features
export BEDROCK_KB_ROLE_ARN=arn:aws:iam::ACCOUNT:role/BedrockKnowledgeBaseRole
export DEFAULT_MODEL_ARN=arn:aws:bedrock:REGION::foundation-model/anthropic.claude-3-5-sonnet-20241022-v2:0
export BEDROCK_REGION=us-east-1
```

## Test Scenarios

### 1. S3 Vector Knowledge Base E2E

**Prerequisites**:
- Region: us-east-1, us-east-2, us-west-2, eu-central-1, or ap-southeast-2
- Titan Embed Text v2 model enabled

**Test Steps**:
1. Create bot with S3 Vector storage type
2. Upload test documents
3. Verify vector bucket creation
4. Test document ingestion
5. Test chat with RAG retrieval
6. Verify cost efficiency vs OpenSearch

**Expected Results**:
- S3 vector bucket auto-created: `bedrock-kb-vectors-ACCOUNT-REGION-KB_ID`
- Documents vectorized and stored
- Chat responses include relevant citations
- ~99% cost savings vs OpenSearch Serverless

### 2. SQL Knowledge Base E2E

**Prerequisites**:
- Redshift Serverless workgroup deployed
- Test database with sample data
- Secrets Manager secret for DB credentials

**Test Steps**:
1. Create bot with SQL KB configuration
2. Configure database connection
3. Test natural language to SQL conversion
4. Verify structured results display
5. Test complex queries

**Expected Results**:
- Bedrock KB created with Redshift data source
- Natural language queries converted to SQL
- Results displayed in structured table format
- Query execution within acceptable latency

### 3. Frontend Storage Type Selection

**Test Steps**:
1. Access bot creation UI
2. Verify storage type selector displays
3. Test regional validation
4. Test cost comparison display
5. Complete bot creation flow

**Expected Results**:
- OpenSearch Serverless selected by default
- S3 Vector option shows preview badge
- Regional validation works correctly
- Cost comparison accurate (99% savings)

## Running Tests

### Unit Tests
```bash
# Backend
cd backend && source .venv/bin/activate
python3 -m pytest tests/test_repositories/test_s3_vector_kb.py -v
python3 -m pytest tests/test_repositories/test_sql_knowledge_base.py -v

# Frontend
cd frontend
npm test -- --run StorageTypeSelector
```

### Integration Tests
```bash
# S3 Vector Integration
cd backend && source .venv/bin/activate
python3 -m pytest tests/integration/test_s3_vector_integration.py -v
```

### Manual E2E Testing
1. Deploy infrastructure: `cd cdk && npx cdk deploy --all`
2. Set environment variables from CDK outputs
3. Test API endpoints with curl/Postman
4. Test frontend UI flows
5. Validate AWS resource creation

## Test Data

### Sample Documents for S3 Vector KB
```bash
mkdir -p test-documents
echo "Amazon Bedrock provides foundation models via API." > test-documents/bedrock.txt
echo "AWS Lambda is a serverless compute service." > test-documents/lambda.txt
```

### Sample SQL Data for SQL KB
```sql
CREATE TABLE products (
    product_id INT PRIMARY KEY,
    description TEXT,
    category VARCHAR(50),
    price DECIMAL(10,2)
);

INSERT INTO products VALUES 
(1, 'Wireless headphones with noise cancellation', 'Electronics', 299.99),
(2, 'Ergonomic office chair with lumbar support', 'Furniture', 449.99);
```

## Validation Checklist

### S3 Vector KB
- [ ] Bot creation with S3_VECTOR storage type
- [ ] S3 vector bucket auto-creation
- [ ] Document upload and ingestion
- [ ] Vector search functionality
- [ ] Cost efficiency vs OpenSearch
- [ ] Regional availability validation

### SQL KB
- [ ] Bot creation with SQL configuration
- [ ] Redshift data source connection
- [ ] Natural language to SQL conversion
- [ ] Structured results display
- [ ] Query performance acceptable

### Frontend
- [ ] Storage type selector renders
- [ ] Regional validation works
- [ ] Cost comparison displays
- [ ] Preview badges show correctly
- [ ] Bot creation completes successfully

## Troubleshooting

### Common Issues
1. **CDK Deployment Fails**: Check CloudBuild logs for frontend build errors
2. **Missing Environment Variables**: Verify all required vars set from CDK outputs
3. **S3 Vector Unavailable**: Ensure region supports S3 Vectors feature
4. **SQL KB Connection Fails**: Verify Redshift workgroup and secret configuration
5. **Frontend Build Issues**: Check Node.js version and npm dependencies

### Debug Commands
```bash
# Check CDK outputs
aws cloudformation describe-stacks --stack-name BedrockChatStack

# Verify Bedrock models
aws bedrock list-foundation-models --region us-east-1

# Check S3 vector buckets
aws s3 ls | grep bedrock-kb-vectors

# Test API endpoints
curl -X GET http://localhost:8000/health
```

## Performance Benchmarks

### Expected Latencies
- S3 Vector KB creation: 2-3 minutes
- Document ingestion: 30 seconds - 2 minutes
- Vector search: <1 second
- SQL query execution: <3 seconds
- Frontend page load: <2 seconds

### Cost Comparisons
- S3 Vector: ~$0.13/month (1M vectors)
- OpenSearch Serverless: ~$88/month (1M vectors)
- SQL KB: Variable based on Redshift usage

## Maintenance

### Regular Testing Schedule
- **Daily**: Unit tests in CI/CD
- **Weekly**: Integration tests
- **Monthly**: Full E2E validation
- **Release**: Complete test suite

### Test Data Refresh
- Update sample documents quarterly
- Refresh SQL test data monthly
- Validate regional availability changes

---

**Last Updated**: October 6, 2025
**Version**: 1.0
**Maintainer**: Development Team
