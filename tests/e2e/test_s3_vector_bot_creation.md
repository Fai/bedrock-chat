# E2E Test Scenarios: S3 Vector Knowledge Base Bot Creation

## Overview

End-to-end test scenarios for S3 Vector Knowledge Base feature, covering the complete user journey from bot creation through querying and deletion.

## Test Environment Setup

### Prerequisites

1. **AWS Environment**:
   - Bedrock region: us-east-1, us-east-2, us-west-2, eu-central-1, or ap-southeast-2
   - S3 bucket for document storage
   - IAM role with Bedrock and S3 permissions (`BEDROCK_KB_ROLE_ARN`)
   - Cognito user pool configured

2. **Application Deployment**:
   - Frontend deployed and accessible
   - Backend API deployed
   - CloudFront distribution active
   - All CDK stacks deployed successfully

3. **Test User**:
   - Cognito user with `CreatingBotAllowed` group membership
   - Valid authentication credentials

4. **Test Data**:
   - Sample PDF documents (2-3 files, <5MB each)
   - Test queries related to document content

### Environment Variables

```bash
export BEDROCK_KB_ROLE_ARN=arn:aws:iam::123456789012:role/BedrockKnowledgeBaseRole
export DEFAULT_MODEL_ARN=arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-5-sonnet-20241022-v2:0
export BEDROCK_REGION=us-east-1
export TEST_DOCUMENT_BUCKET=test-documents-bucket
export FRONTEND_URL=https://d1234567890.cloudfront.net
export API_ENDPOINT=https://api.example.com
```

---

## Test Scenario 1: Create Bot with S3 Vector KB (Happy Path)

### Objective
Verify that a user can successfully create a bot with S3 Vector Knowledge Base in a supported region.

### Pre-conditions
- User is logged in
- Browser is on the bot creation page
- Bedrock region is us-east-1 (supported)

### Test Steps

1. **Navigate to Bot Creation**
   - Click "Create Bot" button
   - Verify bot creation wizard appears

2. **Enter Bot Details**
   - Bot Name: "E2E Test S3 Vector Bot"
   - Description: "Testing S3 Vector storage with cost savings"
   - Instruction: "You are a helpful assistant with knowledge from uploaded documents"
   - Model: Select "Claude 3.5 Sonnet"

3. **Configure Knowledge Base**
   - Enable "Knowledge Base" toggle
   - Select "Vector Knowledge Base" (not SQL)

4. **Select S3 Vector Storage Type**
   - Verify **two storage options appear**: "OpenSearch Serverless" and "S3 Vectors"
   - Verify S3 Vectors card shows:
     - ✅ "PREVIEW" badge
     - ✅ Cost: "~$0.13/month per 1M vectors"
     - ✅ Features: "99% cost savings", "Quick Create", etc.
   - Verify S3 Vectors card is **enabled** (not disabled)
   - Click **"S3 Vectors"** card

5. **Verify Warning Banner Appears**
   - Verify yellow warning banner appears below storage selector
   - Verify banner contains:
     - ✅ "Preview Feature" section
     - ✅ "Key Limitations" section (4 limitations)
     - ✅ "Best For" section with recommendations

6. **Configure Embeddings & Chunking**
   - Embeddings Model: Select "Titan Text Embeddings V2" (default)
   - Chunking Strategy: "Default" (hierarchical)
   - Max chunk tokens: Leave default (should be ≤500 for S3 Vectors)

7. **Upload Documents**
   - Click "Upload Documents" button
   - Select 2-3 PDF files
   - Verify upload progress
   - Verify files appear in document list

8. **Configure Search Parameters**
   - Search Type: Verify only **"Semantic"** is available (no "Hybrid" option for S3 Vectors)
   - Max Results: 5 (default)

9. **Create Bot**
   - Click "Create" button
   - Verify loading state
   - Wait for bot creation (may take 30-60 seconds)

### Expected Results

1. ✅ Bot created successfully
2. ✅ Success message appears: "Bot created successfully"
3. ✅ Redirected to bot details page
4. ✅ Bot status shows "Available" or "Syncing"
5. ✅ Knowledge Base section shows:
   - Storage Type: "S3 Vectors"
   - Embeddings Model: "Titan V2"
   - Chunking Strategy: "Default"
   - Search Type: "Semantic"
6. ✅ AWS Console verification:
   - Bedrock Knowledge Base created with S3_VECTORS storage type
   - S3 vector bucket auto-created (name: `bedrock-kb-vectors-<account>-<region>-<kb-id>`)
   - Data source connected to document bucket

### Post-conditions
- Bot exists in bot list
- Knowledge Base is in ACTIVE status
- Documents are indexed (may take a few minutes)

---

## Test Scenario 2: Query Bot with S3 Vector KB

### Objective
Verify that queries return relevant results from S3 Vector storage.

### Pre-conditions
- Bot from Scenario 1 exists
- Knowledge Base status is "Available"
- Documents are fully indexed

### Test Steps

1. **Navigate to Chat**
   - Open bot from Scenario 1
   - Click "Chat" or navigate to chat interface

2. **Send Test Query**
   - Query: "What is the main topic discussed in the uploaded documents?"
   - Click "Send"

3. **Verify Response**
   - Wait for response (latency should be <5 seconds, sub-second for S3 Vectors)
   - Verify response contains relevant information from documents
   - Verify response quality is reasonable

4. **Verify Citations**
   - Check if citations/sources are displayed
   - Verify citations reference the uploaded documents

5. **Send Follow-up Query**
   - Query: "Can you provide more details about [specific topic from documents]?"
   - Verify response uses context from previous query

### Expected Results

1. ✅ Query processed successfully
2. ✅ Response generated in <5 seconds
3. ✅ Response is relevant to document content
4. ✅ Citations/sources displayed (if implemented)
5. ✅ Conversation context maintained across queries

---

## Test Scenario 3: Regional Validation (S3 Vector Unavailable)

### Objective
Verify that S3 Vector option is disabled in unsupported regions with proper user feedback.

### Pre-conditions
- User is logged in
- Bedrock region is set to **ap-south-1** (unsupported)

### Test Steps

1. **Navigate to Bot Creation**
   - Click "Create Bot"
   - Enter bot details

2. **Configure Knowledge Base**
   - Enable "Knowledge Base" toggle
   - Observe storage type selector

3. **Verify S3 Vector is Disabled**
   - Verify "S3 Vectors" card appears but is **disabled** (grayed out)
   - Verify disabled card has opacity and cursor-not-allowed styling
   - Hover over S3 Vectors card

4. **Check Tooltip**
   - Verify tooltip appears with message:
     - "S3 Vectors not available in this region. Supported regions: us-east-1, us-east-2, us-west-2, eu-central-1, ap-southeast-2"

5. **Check Regional Warning Banner**
   - Verify yellow info banner appears below selector
   - Verify banner text: "S3 Vectors is only available in: us-east-1, us-east-2, us-west-2, eu-central-1, ap-southeast-2. Your current region: ap-south-1"

6. **Attempt to Click Disabled Card**
   - Try clicking S3 Vectors card
   - Verify nothing happens (no selection change)

7. **Verify OpenSearch Still Available**
   - Verify "OpenSearch Serverless" card is enabled
   - Click OpenSearch card
   - Verify selection works normally

### Expected Results

1. ✅ S3 Vectors option is visually disabled
2. ✅ Helpful tooltip explains region restriction
3. ✅ Regional warning banner displayed
4. ✅ Current region (ap-south-1) shown in warning
5. ✅ Clicking disabled card does nothing
6. ✅ OpenSearch Serverless remains functional
7. ✅ User can still create bot with OpenSearch

---

## Test Scenario 4: Storage Type Immutability

### Objective
Verify that storage type cannot be changed after bot creation.

### Pre-conditions
- Bot with S3 Vector KB exists (from Scenario 1)

### Test Steps

1. **Navigate to Bot Edit Page**
   - Open bot from Scenario 1
   - Click "Edit" button

2. **Verify Storage Selector Hidden**
   - Scroll to Knowledge Base section
   - Verify storage type selector **does not appear** (only shown for new bots)

3. **Verify Storage Type Displayed**
   - Verify static text showing: "Storage Type: S3 Vectors"
   - Verify user cannot change this field

4. **Verify Other Settings Editable**
   - Verify bot name, description, instructions are editable
   - Verify documents can be added/removed
   - Verify chunking/search params cannot be changed (KB immutable)

### Expected Results

1. ✅ Storage type selector not visible on edit page
2. ✅ Current storage type displayed as read-only
3. ✅ User informed that storage type is immutable
4. ✅ Other bot settings remain editable

---

## Test Scenario 5: Cost Comparison Display

### Objective
Verify accurate cost comparison information is displayed to users.

### Pre-conditions
- User on bot creation page
- Bedrock region: us-east-1 (supported)

### Test Steps

1. **View Storage Type Selector**
   - Navigate to bot creation
   - Enable Knowledge Base
   - Observe storage type cards

2. **Verify OpenSearch Cost Info**
   - OpenSearch card shows: "~$88/month per 1M vectors"
   - Verify features listed (hybrid search, low latency, etc.)

3. **Verify S3 Vector Cost Info**
   - S3 Vectors card shows: "~$0.13/month per 1M vectors"
   - Verify features listed (99% cost savings, Quick Create, etc.)

4. **Scroll to Cost Comparison Section**
   - Scroll down below storage cards
   - Verify "Storage Cost Comparison" section appears

5. **Verify Cost Table**
   - Table shows both options with costs
   - OpenSearch: ~$88/month
   - S3 Vectors: ~$0.13/month
   - Savings calculation: "S3 Vectors saves 99.85% on storage costs"

6. **Verify Cost Note**
   - Verify note explaining: "Based on 1M vectors, 1024 dimensions, 4GB storage"
   - Verify disclaimer: "Actual costs may vary based on usage"

### Expected Results

1. ✅ Cost displayed accurately on cards
2. ✅ Cost comparison table visible
3. ✅ Savings percentage calculated correctly (99.85%)
4. ✅ Cost basis explained clearly
5. ✅ User can make informed decision based on cost

---

## Test Scenario 6: Delete Bot with S3 Vector KB

### Objective
Verify complete cleanup when deleting a bot with S3 Vector Knowledge Base.

### Pre-conditions
- Bot with S3 Vector KB exists (from Scenario 1)

### Test Steps

1. **Navigate to Bot List**
   - View "My Bots" page
   - Locate test bot created in Scenario 1

2. **Delete Bot**
   - Click "Delete" button on bot
   - Verify confirmation dialog appears
   - Confirm deletion

3. **Verify Bot Removed**
   - Verify bot no longer appears in bot list
   - Verify success message: "Bot deleted successfully"

4. **AWS Console Verification**
   - Check Bedrock Knowledge Bases console
   - Verify Knowledge Base is deleted
   - Check S3 console
   - Verify vector bucket cleaned up (or deletion in progress)
   - Check DynamoDB
   - Verify bot record removed

### Expected Results

1. ✅ Bot deleted from UI
2. ✅ Knowledge Base deleted from Bedrock
3. ✅ S3 vector bucket deleted (or marked for deletion)
4. ✅ All associated resources cleaned up
5. ✅ No orphaned resources remain

---

## Test Scenario 7: Chunking Limit Validation (500 Tokens)

### Objective
Verify that S3 Vectors enforces the 500 token chunking limit.

### Pre-conditions
- User on bot creation page
- S3 Vector storage type selected
- Bedrock region: us-east-1

### Test Steps

1. **Select Fixed Size Chunking**
   - Storage Type: S3 Vectors
   - Chunking Strategy: "Fixed Size"

2. **Attempt to Set 600 Tokens**
   - Max Tokens field: Enter "600"
   - Try to proceed with bot creation

3. **Verify Validation Error**
   - Verify error message appears: "S3 Vectors supports maximum 500 tokens per chunk"
   - Verify "Create" button is disabled or shows error

4. **Correct to 500 Tokens**
   - Change Max Tokens to "500"
   - Verify error clears
   - Verify "Create" button enabled

5. **Create Bot Successfully**
   - Complete bot creation with 500 token chunks
   - Verify bot created successfully

### Expected Results

1. ✅ Frontend validates chunk size ≤500 for S3 Vectors
2. ✅ Clear error message displayed for invalid input
3. ✅ Bot creation blocked until corrected
4. ✅ Valid configuration (≤500 tokens) accepted
5. ✅ Backend also validates (double validation)

---

## Test Scenario 8: Hybrid Search Not Available

### Objective
Verify that hybrid search is not available for S3 Vector storage (semantic only).

### Pre-conditions
- User on bot creation page
- S3 Vector storage type selected
- Bedrock region: us-east-1

### Test Steps

1. **Select S3 Vector Storage**
   - Choose "S3 Vectors" card
   - Proceed to search configuration

2. **Check Search Type Options**
   - Observe "Search Type" dropdown/selector
   - Verify only "Semantic" option available
   - Verify "Hybrid" option is NOT available or is disabled

3. **Verify Info Text**
   - Check for info/tooltip explaining:
     - "S3 Vectors supports semantic search only"
     - "Hybrid search is only available with OpenSearch Serverless"

4. **Compare with OpenSearch**
   - Switch back to "OpenSearch Serverless"
   - Verify both "Semantic" and "Hybrid" options available

5. **Switch Back to S3 Vector**
   - Select "S3 Vectors" again
   - Verify "Hybrid" option removed again
   - Verify search type auto-reset to "Semantic"

### Expected Results

1. ✅ Only "Semantic" search available for S3 Vectors
2. ✅ "Hybrid" option hidden or disabled
3. ✅ Info text explains limitation
4. ✅ OpenSearch still offers both options
5. ✅ Switching storage types updates search options dynamically

---

## Performance Benchmarks

### Expected Performance Metrics

| Metric | Target | Acceptance Criteria |
|--------|--------|---------------------|
| **KB Creation Time** | <60s | S3 Vector Quick Create |
| **Query Latency** | <3s | Sub-second for S3 Vectors |
| **Document Ingestion** | <5 min | For 3 PDFs (<5MB each) |
| **Page Load Time** | <2s | Storage selector page |
| **Storage Type Switch** | <100ms | UI update responsive |

---

## Regression Tests

### Verify Existing Features Still Work

1. **OpenSearch Serverless (Default)**
   - Create bot with OpenSearch (ensure not broken)
   - Verify hybrid search still works
   - Verify custom analyzers functional

2. **SQL Knowledge Base**
   - SQL KB creation unaffected
   - SQL KB type selector still works

3. **Backward Compatibility**
   - Existing bots without `storageType` field default to OpenSearch
   - Existing bots still queryable
   - No migration required

---

## Error Scenarios

### Test Error Handling

1. **API Failure During KB Creation**
   - Mock Bedrock API failure
   - Verify error message shown to user
   - Verify bot marked as "Failed" with reason

2. **Insufficient IAM Permissions**
   - Missing S3 permissions in KB role
   - Verify helpful error message
   - Verify rollback behavior

3. **Invalid Region Configuration**
   - Backend region doesn't match frontend
   - Verify validation error
   - Verify user guided to correct region

4. **Network Timeout**
   - Slow network during KB creation
   - Verify loading state displayed
   - Verify timeout handled gracefully

---

## Test Data Cleanup

After all E2E tests:

```bash
# List all test bots
aws dynamodb scan --table-name <BOT_TABLE> --filter-expression "contains(bot_id, :prefix)" --expression-attribute-values '{":prefix":{"S":"e2e-test"}}'

# Delete test bots
# (Use bot deletion API for each test bot)

# Verify Bedrock KBs cleaned up
aws bedrock-agent list-knowledge-bases --region us-east-1 | grep "e2e-test"

# Verify S3 buckets cleaned up
aws s3 ls | grep "bedrock-kb-vectors"
```

---

## Test Execution Checklist

- [ ] All pre-conditions met
- [ ] Test environment configured
- [ ] Test data prepared
- [ ] Run Scenario 1: Happy path bot creation
- [ ] Run Scenario 2: Query bot
- [ ] Run Scenario 3: Regional validation
- [ ] Run Scenario 4: Immutability check
- [ ] Run Scenario 5: Cost comparison
- [ ] Run Scenario 6: Bot deletion
- [ ] Run Scenario 7: Chunking validation
- [ ] Run Scenario 8: Hybrid search restriction
- [ ] Performance benchmarks met
- [ ] Regression tests passed
- [ ] Error scenarios handled
- [ ] Test data cleaned up
- [ ] Results documented

---

## Test Report Template

```markdown
# E2E Test Execution Report

**Date**: YYYY-MM-DD
**Tester**: [Name]
**Environment**: [dev/staging/prod]
**Region**: us-east-1

## Test Results Summary

| Scenario | Status | Duration | Notes |
|----------|--------|----------|-------|
| S1: Bot Creation | ✅ PASS | 45s | |
| S2: Query Bot | ✅ PASS | 3.2s | |
| S3: Regional Validation | ✅ PASS | - | |
| S4: Immutability | ✅ PASS | - | |
| S5: Cost Comparison | ✅ PASS | - | |
| S6: Bot Deletion | ✅ PASS | 8s | |
| S7: Chunking Validation | ✅ PASS | - | |
| S8: Hybrid Search | ✅ PASS | - | |

## Issues Found

1. [Issue description if any]

## Performance Metrics

- KB Creation: 42s (target: <60s) ✅
- Query Latency: 2.8s (target: <3s) ✅
- Page Load: 1.4s (target: <2s) ✅

## Recommendations

[Any recommendations for improvements]
```
