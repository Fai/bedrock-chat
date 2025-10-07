# Knowledge Base UI Settings Refactor Plan

## Overview

The current bot settings UI (`BotKbEditPage.tsx`) was designed primarily for OpenSearch Serverless vector stores. With the addition of S3 Vector Store and SQL Knowledge Base support, many UI settings are now incorrectly shown for knowledge base types where they don't apply.

This document outlines a plan to refactor the UI to conditionally show/hide settings based on the selected knowledge base type.

## Problem Statement

### Current Issues

1. **OpenSearch Analyzer Settings** - Shown for S3 Vector and SQL KBs, but only applicable to OpenSearch Serverless
2. **Chunking Configuration** - Shown for SQL KBs, but SQL KBs don't use chunking (they query structured data)
3. **Parsing Model Settings** - Shown for SQL KBs, but not applicable to structured data queries
4. **File Upload / URL Inputs** - Shown for SQL KBs, which connect to existing databases instead
5. **S3 Vector 500 Token Limit** - Not enforced in UI validation despite being a hard constraint
6. **Search Type Options** - Already partially fixed: hybrid search hidden for S3 Vector (line 391-401)

### Knowledge Base Type Comparison

| Feature | OpenSearch Serverless | S3 Vector Store | SQL Knowledge Base |
|---------|----------------------|-----------------|-------------------|
| **Chunking Strategies** | All (default, fixed_size, hierarchical, semantic, none) | All (default, fixed_size, hierarchical, semantic, none) | ❌ Not applicable |
| **Max Chunk Tokens** | 8192 (titan_v2) / 512 (cohere) | ⚠️ **500 tokens max** | ❌ Not applicable |
| **Search Types** | Hybrid + Semantic | ⚠️ **Semantic only** | Hybrid + Semantic |
| **OpenSearch Analyzer** | ✅ Required | ❌ Not applicable | ❌ Not applicable |
| **Parsing Models** | ✅ Claude Sonnet/Haiku | ✅ Claude Sonnet/Haiku | ❌ Not applicable |
| **Web Crawling** | ✅ URLs, filters, scope | ✅ URLs, filters, scope | ❌ Not applicable |
| **File Upload** | ✅ Documents, S3 URLs | ✅ Documents, S3 URLs | ❌ Not applicable |
| **Data Source** | Files/URLs/S3 | Files/URLs/S3 | ⚠️ **Database connection** |
| **Embedding Model** | titan_v2, cohere_multilingual_v3 | titan_v2, cohere_multilingual_v3 | Via ARN configuration |

## Proposed Solution

### Phase 1: Conditional UI Rendering (High Priority)

#### 1.1 Hide OpenSearch Analyzer for S3 Vector and SQL KBs

**Location:** `BotKbEditPage.tsx` lines 2375-2440

**Change:**
```tsx
{/* OpenSearch Analyzer - Only for OpenSearch Serverless */}
{storageType === 'OPENSEARCH_SERVERLESS' && (
  <div className="mt-3 grid gap-1">
    {isNewBot && (
      <Select
        label={t('knowledgeBaseSettings.opensearchAnalyzer.label')}
        value={analyzer}
        options={analyzerOptions}
        onChange={(val) => {
          setAnalyzer(val);
          setOpenSearchParams(OPENSEARCH_ANALYZER[val]);
        }}
        className="mt-2"
      />
    )}
    {/* ... existing OpenSearch analyzer display code ... */}
  </div>
)}
```

**Impact:** Prevents confusion when users select S3 or SQL storage types

#### 1.2 Enforce S3 Vector 500 Token Limit

**Location:** `frontend/src/features/knowledgeBase/constants/index.ts`

**Change:**
```typescript
// Add S3-specific constraints
export const S3_VECTOR_CHUNK_LIMITS = {
  FIXED_SIZE: {
    maxTokens: {
      MAX: 500,  // S3 Vector hard limit
      MIN: 1,
      STEP: 1,
    },
  },
  HIERARCHICAL: {
    maxParentTokenSize: {
      MAX: 500,
      MIN: 1,
      STEP: 1,
    },
    maxChildTokenSize: {
      MAX: 500,
      MIN: 1,
      STEP: 1,
    },
  },
  SEMANTIC: {
    maxTokens: {
      MAX: 500,
      MIN: 1,
      STEP: 1,
    },
  },
};
```

**Location:** `BotKbEditPage.tsx` validation logic (lines ~1100-1180)

**Change:**
```typescript
// Update validation to use S3-specific limits when applicable
const maxEdgeFixed = storageType === 'S3_VECTOR'
  ? S3_VECTOR_CHUNK_LIMITS.FIXED_SIZE.maxTokens.MAX
  : EDGE_FIXED_CHUNK_PARAMS.maxTokens.MAX[embeddingsModel];

const maxEdgeHierarchical = storageType === 'S3_VECTOR'
  ? S3_VECTOR_CHUNK_LIMITS.HIERARCHICAL.maxParentTokenSize.MAX
  : EDGE_HIERARCHICAL_CHUNK_PARAMS.maxParentTokenSize.MAX[embeddingsModel];

const maxEdgeSemantic = storageType === 'S3_VECTOR'
  ? S3_VECTOR_CHUNK_LIMITS.SEMANTIC.maxTokens.MAX
  : EDGE_SEMANTIC_CHUNK_PARAMS.maxTokens.MAX[embeddingsModel];
```

**Impact:** Prevents validation errors during KB creation

#### 1.3 Conditionally Render Chunking Settings

**Location:** `BotKbEditPage.tsx` chunking configuration section (lines ~2180-2373)

**Change:**
```tsx
{/* Chunking Configuration - Not applicable for SQL KBs */}
{knowledgeBaseType !== 'SQL' && (
  <ExpandableDrawerGroup
    isDefaultShow={true}
    label={t('knowledgeBaseSettings.chunkingStrategy.label')}
    className="py-2">
    {/* ... existing chunking strategy selection ... */}

    {/* Add S3 Vector warning */}
    {storageType === 'S3_VECTOR' && (
      <Alert severity="info" className="mt-2">
        <Trans i18nKey="knowledgeBaseSettings.s3VectorLimitation">
          S3 Vector Store has a maximum chunk size of 500 tokens and supports semantic search only.
        </Trans>
      </Alert>
    )}

    {/* ... rest of chunking configuration ... */}
  </ExpandableDrawerGroup>
)}
```

**Impact:** Hides irrelevant settings for SQL KBs

#### 1.4 Conditionally Render Parsing Model Settings

**Location:** `BotKbEditPage.tsx` parsing model section

**Change:**
```tsx
{/* Parsing Model - Not applicable for SQL KBs */}
{knowledgeBaseType !== 'SQL' && (
  <ExpandableDrawerGroup
    isDefaultShow={false}
    label={t('knowledgeBaseSettings.parsingModel.label')}
    className="py-2">
    {/* ... existing parsing model configuration ... */}
  </ExpandableDrawerGroup>
)}
```

**Impact:** Removes confusion about parsing in SQL context

#### 1.5 Conditional Data Source Inputs

**Location:** `BotKbEditPage.tsx` knowledge section (file upload, URLs, S3 URLs)

**Change:**
```tsx
{/* Vector KB Data Sources (Files, URLs, S3) */}
{knowledgeBaseType !== 'SQL' && (
  <>
    {/* File Upload */}
    <KnowledgeFileUploader
      files={files}
      // ... props ...
    />

    {/* URLs */}
    <div className="mt-4">
      {/* ... URL input fields ... */}
    </div>

    {/* S3 URLs */}
    <div className="mt-4">
      {/* ... S3 URL input fields ... */}
    </div>

    {/* Web Crawling Settings */}
    <ExpandableDrawerGroup>
      {/* ... web crawling config ... */}
    </ExpandableDrawerGroup>
  </>
)}

{/* SQL KB Data Source (Database Connection) */}
{knowledgeBaseType === 'SQL' && (
  <div className="mt-4">
    <Alert severity="info">
      <Trans i18nKey="sqlKnowledgeBase.connectionInfo">
        SQL Knowledge Bases connect to your Amazon Redshift Serverless database.
        Configure the connection details below.
      </Trans>
    </Alert>

    {/* Database Connection Form */}
    <div className="mt-4 grid gap-4">
      <InputText
        label={t('sqlKnowledgeBase.workgroupName')}
        value={sqlConfig.workgroupName}
        onChange={(val) => setSqlConfig({...sqlConfig, workgroupName: val})}
        hint={t('sqlKnowledgeBase.workgroupNameHint')}
      />

      <InputText
        label={t('sqlKnowledgeBase.workgroupArn')}
        value={sqlConfig.workgroupArn}
        onChange={(val) => setSqlConfig({...sqlConfig, workgroupArn: val})}
        hint={t('sqlKnowledgeBase.workgroupArnHint')}
      />

      <InputText
        label={t('sqlKnowledgeBase.databaseName')}
        value={sqlConfig.databaseName}
        onChange={(val) => setSqlConfig({...sqlConfig, databaseName: val})}
      />

      <InputText
        label={t('sqlKnowledgeBase.tableName')}
        value={sqlConfig.tableName}
        onChange={(val) => setSqlConfig({...sqlConfig, tableName: val})}
      />

      <InputText
        label={t('sqlKnowledgeBase.secretArn')}
        value={sqlConfig.secretArn}
        onChange={(val) => setSqlConfig({...sqlConfig, secretArn: val})}
        hint={t('sqlKnowledgeBase.secretArnHint')}
      />

      {/* Field Mapping */}
      <div className="mt-2">
        <div className="text-sm font-semibold">
          {t('sqlKnowledgeBase.fieldMapping.title')}
        </div>
        <div className="mt-2 grid gap-2">
          <InputText
            label={t('sqlKnowledgeBase.fieldMapping.idColumn')}
            value={sqlConfig.fieldMapping.id}
            onChange={(val) => setSqlConfig({
              ...sqlConfig,
              fieldMapping: {...sqlConfig.fieldMapping, id: val}
            })}
          />
          <InputText
            label={t('sqlKnowledgeBase.fieldMapping.contentColumn')}
            value={sqlConfig.fieldMapping.content}
            onChange={(val) => setSqlConfig({
              ...sqlConfig,
              fieldMapping: {...sqlConfig.fieldMapping, content: val}
            })}
          />
          <InputText
            label={t('sqlKnowledgeBase.fieldMapping.metadataColumn')}
            value={sqlConfig.fieldMapping.metadata}
            onChange={(val) => setSqlConfig({
              ...sqlConfig,
              fieldMapping: {...sqlConfig.fieldMapping, metadata: val}
            })}
          />
        </div>
      </div>
    </div>
  </div>
)}
```

**Note:** This assumes SQL KB configuration state is added. If not implemented yet, this section should be planned separately.

**Impact:** Shows appropriate data source configuration based on KB type

### Phase 2: Enhanced User Experience (Medium Priority)

#### 2.1 Storage Type Selector with Warnings

**Location:** `frontend/src/features/knowledgeBase/components/StorageTypeSelector.tsx`

**Enhancement:**
```tsx
<div className="grid gap-4">
  {/* OpenSearch Serverless */}
  <RadioButton
    value={storageType === 'OPENSEARCH_SERVERLESS'}
    label={
      <div>
        <div className="font-semibold">OpenSearch Serverless</div>
        <div className="text-xs text-gray-600">
          ✅ Hybrid search • ✅ Full analyzer control • ✅ No chunk limits
        </div>
      </div>
    }
    onChange={() => setStorageType('OPENSEARCH_SERVERLESS')}
  />

  {/* S3 Vector Store */}
  <RadioButton
    value={storageType === 'S3_VECTOR'}
    label={
      <div>
        <div className="font-semibold">S3 Vector Store</div>
        <div className="text-xs text-gray-600">
          ⚠️ Semantic only • ⚠️ 500 token chunk limit • ✅ Lower cost
        </div>
      </div>
    }
    onChange={() => setStorageType('S3_VECTOR')}
  />

  {/* Note about SQL KB being separate */}
  <Alert severity="info">
    <Trans i18nKey="storageTypeSelector.sqlKbNote">
      For SQL Knowledge Bases (Amazon Redshift), use the dedicated SQL KB creation flow.
    </Trans>
  </Alert>
</div>
```

**Impact:** Users understand limitations before configuration

#### 2.2 Dynamic Chunk Size Slider Ranges

**Location:** `BotKbEditPage.tsx` slider configurations

**Enhancement:**
```tsx
// Dynamically adjust slider max based on storage type
const getMaxTokens = () => {
  if (storageType === 'S3_VECTOR') {
    return 500;
  }
  return EDGE_FIXED_CHUNK_PARAMS.maxTokens.MAX[embeddingsModel];
};

<Slider
  value={fixedSizeParams.maxTokens}
  range={{
    min: EDGE_FIXED_CHUNK_PARAMS.maxTokens.MIN,
    max: getMaxTokens(),
    step: EDGE_FIXED_CHUNK_PARAMS.maxTokens.STEP,
  }}
  // ... other props
/>
```

**Impact:** Slider physically prevents invalid values

#### 2.3 Help Text Updates

**Location:** All translation files (`frontend/src/i18n/*/index.ts`)

**New Translation Keys:**
```typescript
knowledgeBaseSettings: {
  s3VectorLimitation: 'S3 Vector Store has a maximum chunk size of 500 tokens and supports semantic search only.',
  opensearchAnalyzer: {
    label: 'OpenSearch Analyzer (OpenSearch Serverless only)',
    hint: 'Text analysis configuration for OpenSearch indexing. Not applicable to S3 Vector or SQL Knowledge Bases.',
    // ... existing keys
  },
  chunkingStrategy: {
    label: 'Chunking Strategy (Vector KBs only)',
    hint: 'How documents are split into chunks for embedding. Not applicable to SQL Knowledge Bases.',
    // ... existing keys
  },
  parsingModel: {
    label: 'Parsing Model (Vector KBs only)',
    hint: 'Foundation model for advanced document parsing. Not applicable to SQL Knowledge Bases.',
    // ... existing keys
  },
},
storageTypeSelector: {
  sqlKbNote: 'For SQL Knowledge Bases (Amazon Redshift), use the dedicated SQL KB creation flow or API.',
},
sqlKnowledgeBase: {
  connectionInfo: 'SQL Knowledge Bases connect to your Amazon Redshift Serverless database. Configure the connection details below.',
  workgroupName: 'Redshift Workgroup Name',
  workgroupNameHint: 'The name of your Redshift Serverless workgroup',
  workgroupArn: 'Workgroup ARN',
  workgroupArnHint: 'Full ARN of the Redshift Serverless workgroup',
  databaseName: 'Database Name',
  tableName: 'Table/View Name',
  secretArn: 'Secrets Manager Secret ARN',
  secretArnHint: 'ARN of the secret containing database credentials',
  fieldMapping: {
    title: 'Field Mapping',
    idColumn: 'ID Column',
    contentColumn: 'Content Column',
    metadataColumn: 'Metadata Column',
  },
},
```

**Impact:** Clear communication about type-specific features

### Phase 3: SQL KB Integration (If Needed)

#### 3.1 Type Discriminator in State

**Location:** `BotKbEditPage.tsx` state management

**Addition:**
```typescript
// Add knowledge base type discriminator
type KnowledgeBaseKind = 'VECTOR' | 'SQL';

const [knowledgeBaseKind, setKnowledgeBaseKind] = useState<KnowledgeBaseKind>('VECTOR');

// SQL KB specific state
const [sqlConfig, setSqlConfig] = useState<{
  workgroupName: string;
  workgroupArn: string;
  databaseName: string;
  tableName: string;
  secretArn: string;
  fieldMapping: {
    id: string;
    content: string;
    metadata: string;
  };
}>({
  workgroupName: '',
  workgroupArn: '',
  databaseName: '',
  tableName: '',
  secretArn: '',
  fieldMapping: {
    id: 'id',
    content: 'content',
    metadata: 'metadata',
  },
});
```

#### 3.2 Separate SQL KB Route (Optional)

**Alternative Approach:** Create dedicated page for SQL KB

**Location:** New file `frontend/src/features/knowledgeBase/pages/BotSqlKbEditPage.tsx`

**Benefits:**
- Cleaner separation of concerns
- Simpler logic without conditionals
- Better user experience (wizard-style flow)
- Easier to maintain

**Routing:**
```typescript
// frontend/src/routes/index.tsx
<Route path="/bot/:botId/kb/sql" element={<BotSqlKbEditPage />} />
<Route path="/bot/new/sql" element={<BotSqlKbEditPage />} />
```

**Impact:** May be overkill if SQL KB is rarely used; keeps existing page simpler

## Implementation Checklist

### High Priority (Phase 1)

- [ ] Hide OpenSearch Analyzer for S3 Vector and SQL KBs
- [ ] Add S3 Vector 500 token limit constants
- [ ] Enforce S3 Vector limits in validation logic
- [ ] Update chunk size sliders to use dynamic max values
- [ ] Add S3 Vector limitation warning alert
- [ ] Conditionally render chunking settings (hide for SQL)
- [ ] Conditionally render parsing model settings (hide for SQL)
- [ ] Conditionally render data source inputs (vector vs SQL)
- [ ] Add SQL KB connection form (if not exists)
- [ ] Update validation to handle SQL KB configuration
- [ ] Test all three KB types end-to-end

### Medium Priority (Phase 2)

- [ ] Enhance StorageTypeSelector with feature comparison
- [ ] Add info badges/tags to section headers ("OpenSearch only", etc.)
- [ ] Update all help text to mention type applicability
- [ ] Add tooltips explaining why settings are hidden
- [ ] Improve error messages with type-specific guidance
- [ ] Add AWS documentation links per KB type
- [ ] Update translation files (all languages)

### Low Priority (Phase 3)

- [ ] Consider dedicated SQL KB creation page
- [ ] Add KB type selection wizard for new bots
- [ ] Implement "switch KB type" functionality with migration
- [ ] Add KB type comparison page in documentation
- [ ] Create visual flowcharts for each KB type setup

## Testing Strategy

### Unit Tests

**Location:** `frontend/src/features/knowledgeBase/pages/BotKbEditPage.test.tsx`

```typescript
describe('BotKbEditPage - Storage Type Conditionals', () => {
  it('should hide OpenSearch Analyzer for S3 Vector', () => {
    render(<BotKbEditPage storageType="S3_VECTOR" />);
    expect(screen.queryByText('OpenSearch Analyzer')).not.toBeInTheDocument();
  });

  it('should hide chunking for SQL KB', () => {
    render(<BotKbEditPage knowledgeBaseKind="SQL" />);
    expect(screen.queryByText('Chunking Strategy')).not.toBeInTheDocument();
  });

  it('should enforce 500 token limit for S3 Vector', () => {
    const { getByLabelText } = render(<BotKbEditPage storageType="S3_VECTOR" />);
    const slider = getByLabelText('Max Tokens');
    expect(slider).toHaveAttribute('max', '500');
  });

  it('should show SQL connection form for SQL KB', () => {
    render(<BotKbEditPage knowledgeBaseKind="SQL" />);
    expect(screen.getByText('Workgroup ARN')).toBeInTheDocument();
  });
});
```

### Integration Tests

1. **OpenSearch KB Creation:** Verify all settings apply correctly
2. **S3 Vector KB Creation:** Verify 500 token limit enforced, semantic-only search
3. **SQL KB Creation:** Verify connection form validation, database connection test
4. **KB Type Switching:** Verify settings reset appropriately when changing types
5. **Edit Existing KB:** Verify correct settings shown based on existing KB type

### Manual Testing Checklist

- [ ] Create OpenSearch KB with all chunking strategies
- [ ] Create S3 Vector KB with >500 token chunks (should fail validation)
- [ ] Create S3 Vector KB with hybrid search (should force semantic)
- [ ] Verify OpenSearch Analyzer hidden for S3 Vector
- [ ] Create SQL KB with database connection
- [ ] Verify file upload hidden for SQL KB
- [ ] Edit existing OpenSearch KB (verify analyzer shown)
- [ ] Edit existing S3 Vector KB (verify analyzer hidden)
- [ ] Switch between storage types and verify UI updates

## Rollout Plan

### Step 1: Non-breaking Changes (Week 1)
- Add S3 Vector constraint constants
- Update validation logic (doesn't break existing functionality)
- Add translation keys (unused until referenced)

### Step 2: UI Conditionals (Week 2)
- Implement conditional rendering for OpenSearch Analyzer
- Implement conditional rendering for chunking/parsing
- Add warning alerts for S3 Vector limitations

### Step 3: SQL KB Support (Week 3, if needed)
- Add SQL KB connection form
- Implement SQL-specific validation
- Add SQL KB creation API integration

### Step 4: Polish & Testing (Week 4)
- Enhanced storage selector
- Updated help text and tooltips
- Comprehensive testing
- Documentation updates

## Success Metrics

- ✅ Zero OpenSearch-specific settings shown for S3 Vector or SQL KBs
- ✅ Zero chunking/parsing settings shown for SQL KBs
- ✅ 100% of S3 Vector KBs respect 500 token limit
- ✅ All existing OpenSearch KBs continue to work unchanged
- ✅ User confusion tickets reduced by 80%
- ✅ KB creation success rate improved by 20%

## Related Documentation

- [SQL KB User Guide](./SQL_KB_USER_GUIDE.md)
- [SQL KB Developer Guide](./SQL_KB_DEVELOPER_GUIDE.md)
- [E2E Testing Guide](./E2E_TESTING_GUIDE.md)
- [AWS Bedrock KB Documentation](https://docs.aws.amazon.com/bedrock/latest/userguide/knowledge-base.html)

## Questions & Decisions

### Decision Required: SQL KB UI Approach

**Option A:** Conditional rendering in existing `BotKbEditPage.tsx`
- ✅ Pros: Single source of truth, no routing changes
- ❌ Cons: More complex conditional logic, harder to maintain

**Option B:** Separate `BotSqlKbEditPage.tsx` component
- ✅ Pros: Clean separation, simpler logic, better UX
- ❌ Cons: Code duplication for common settings, new routes needed

**Recommendation:** Start with Option A for Phase 1-2, evaluate Option B if complexity grows

### Open Questions

1. Should S3 Vector be the default for new KBs (lower cost)?
2. Should we allow KB type migration (e.g., OpenSearch → S3 Vector)?
3. Should SQL KB be accessible from main KB creation flow or separate?
4. Do we need a KB type comparison matrix in the UI?

## Appendix: Current Code References

### Key Files
- `frontend/src/features/knowledgeBase/pages/BotKbEditPage.tsx` (main page)
- `frontend/src/features/knowledgeBase/types/index.d.ts` (type definitions)
- `frontend/src/features/knowledgeBase/constants/index.ts` (constants)
- `frontend/src/features/knowledgeBase/components/StorageTypeSelector.tsx` (selector component)
- `backend/app/repositories/sql_knowledge_base.py` (SQL KB backend)
- `backend/app/repositories/s3_vector_kb.py` (S3 Vector backend)

### Key Line References (BotKbEditPage.tsx)
- Lines 152-154: Storage type state
- Lines 391-401: Search type options (already conditional) ✅
- Lines 404-411: Force semantic for S3 Vector ✅
- Lines 2180-2373: Chunking configuration (needs conditional)
- Lines 2375-2440: OpenSearch Analyzer (needs conditional)
- Lines ~1100-1180: Validation logic (needs S3 limits)
