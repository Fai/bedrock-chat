# Frontend Multi-Storage Knowledge Base Design Proposal

## Session: 2025-10-06 12:15 UTC

### Current State Analysis

**Existing Implementation**:
- Frontend currently supports **OpenSearch Serverless only** for VECTOR knowledge bases
- SQL KB types added but **no UI for selection**
- S3 Vector storage type **not yet integrated in frontend**

**Current Type Structure**:
```typescript
// frontend/src/features/knowledgeBase/types/index.d.ts

// Existing VECTOR KB (OpenSearch only)
type BedrockKnowledgeBase = {
  knowledgeBaseId: string | null;
  embeddingsModel: EmbeddingsModel;
  chunkingConfiguration: ChunkingConfiguration;
  openSearch: OpenSearchParams;  // ALWAYS required (OpenSearch-specific)
  searchParams: SearchParams;
  // ...
};

// SQL KB (separate type)
type SqlKnowledgeBase = {
  knowledgeBaseType: 'SQL';
  databaseConfig: SqlDatabaseConfig;
  // ...
};

// Resource type enum
type KnowledgeBaseResourceType = 'VECTOR' | 'SQL';
```

**Problem**: No concept of "storage type" for VECTOR KBs (OpenSearch vs S3 Vectors)

---

## Design Proposal

### 1. Architecture Changes

#### 1.1 Add Storage Type to Type System

```typescript
// NEW: Storage type for VECTOR knowledge bases
export type VectorStorageType = 'OPENSEARCH_SERVERLESS' | 'S3_VECTOR';

// UPDATED: BedrockKnowledgeBase with optional storage type
export type BedrockKnowledgeBase = {
  knowledgeBaseId: string | null;
  existKnowledgeBaseId: string | null;
  dataSourceIds?: string[];

  // NEW: Storage type selection
  storageType?: VectorStorageType;  // Defaults to OPENSEARCH_SERVERLESS

  embeddingsModel: EmbeddingsModel;
  chunkingConfiguration: ChunkingConfiguration;

  // UPDATED: Optional for S3 Vectors
  openSearch?: OpenSearchParams | null;  // Only for OpenSearch

  searchParams: SearchParams;
  parsingModel?: ParsingModel;
  webCrawlingScope?: WebCrawlingScope;
  webCrawlingFilters?: WebCrawlingFilters;
};

// Unified KB type (VECTOR or SQL)
export type KnowledgeBaseConfig = BedrockKnowledgeBase | SqlKnowledgeBase;
```

#### 1.2 Create Storage Type Selector Component

**Component**: `StorageTypeSelector.tsx`

```typescript
type StorageTypeOption = {
  type: 'OPENSEARCH_SERVERLESS' | 'S3_VECTOR' | 'SQL';
  name: string;
  description: string;
  icon: IconType;
  badge?: 'Preview' | 'Production';
  costLevel: 'High' | 'Medium' | 'Low';
  latency: 'Sub-ms' | 'Sub-second' | 'N/A';
  features: string[];
  limitations?: string[];
};

const STORAGE_OPTIONS: StorageTypeOption[] = [
  {
    type: 'OPENSEARCH_SERVERLESS',
    name: 'OpenSearch Serverless',
    description: 'Production-ready vector search with low latency',
    icon: PiDatabase,
    badge: 'Production',
    costLevel: 'High',
    latency: 'Sub-ms',
    features: [
      'Hybrid search (semantic + keyword)',
      'Sub-millisecond query latency',
      'Auto-scaling',
      'Advanced analytics'
    ],
    limitations: []
  },
  {
    type: 'S3_VECTOR',
    name: 'S3 Vectors',
    description: 'Cost-effective vector storage for large datasets',
    icon: PiCloudArrowDown,
    badge: 'Preview',
    costLevel: 'Low',
    latency: 'Sub-second',
    features: [
      '99% cost savings vs OpenSearch',
      'Unlimited storage capacity',
      'Quick Create auto-setup',
      'Best for dev/test'
    ],
    limitations: [
      'Semantic search only (no hybrid)',
      'Preview feature (subject to change)',
      'Sub-second latency'
    ]
  },
  {
    type: 'SQL',
    name: 'SQL Database',
    description: 'Natural language queries to structured data',
    icon: PiTable,
    costLevel: 'Medium',
    latency: 'N/A',
    features: [
      'Text-to-SQL conversion',
      'Redshift Serverless',
      'Structured data queries',
      'Schema sync'
    ],
    limitations: []
  }
];
```

**Visual Design**:
```
┌─────────────────────────────────────────────────────────────┐
│  Select Knowledge Base Storage Type                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────┐  ┌──────────────────┐  ┌────────────┐│
│  │ [Database Icon]  │  │ [Cloud Icon]     │  │ [SQL Icon] ││
│  │ OpenSearch       │  │ S3 Vectors       │  │ SQL DB     ││
│  │ Serverless       │  │ [PREVIEW]        │  │            ││
│  ├──────────────────┤  ├──────────────────┤  ├────────────┤│
│  │ Production-ready │  │ Cost-effective   │  │ Structured ││
│  │ Low latency      │  │ Large datasets   │  │ Text-to-SQL││
│  ├──────────────────┤  ├──────────────────┤  ├────────────┤│
│  │ ✓ Hybrid search  │  │ ✓ 99% cheaper    │  │ ✓ Redshift ││
│  │ ✓ Sub-ms latency │  │ ✓ Quick Create   │  │ ✓ Schema   ││
│  │ ✓ Auto-scaling   │  │ ⚠ Semantic only  │  │   sync     ││
│  │                  │  │ ⚠ Preview        │  │            ││
│  ├──────────────────┤  ├──────────────────┤  ├────────────┤│
│  │ Cost: $$$ High   │  │ Cost: $ Low      │  │ Cost: $$   ││
│  │ [Selected ✓]     │  │ [Select]         │  │ [Select]   ││
│  └──────────────────┘  └──────────────────┘  └────────────┘│
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

### 2. UI Flow Changes

#### 2.1 Bot Creation/Edit Flow

**Current Flow**:
```
1. Bot Details (name, description)
2. Knowledge Base Config
   - File upload
   - URL crawling
   - OpenSearch analyzer (always shown)
   - Chunking config
   - Search params
```

**Proposed New Flow**:
```
1. Bot Details (name, description)

2. Knowledge Base Type Selection
   ┌────────────────────────────────────┐
   │ Select Knowledge Base Type         │
   │ ○ Document Search (VECTOR)         │
   │ ○ SQL Database (SQL)               │
   └────────────────────────────────────┘

3a. IF VECTOR Selected:
   ┌────────────────────────────────────┐
   │ Select Storage Type                │
   │ [OpenSearch] [S3 Vector] [Both]    │
   └────────────────────────────────────┘

   3a1. IF OpenSearch:
      - File upload / URL crawling
      - OpenSearch analyzer config
      - Chunking config
      - Search params (hybrid/semantic)

   3a2. IF S3 Vector:
      - File upload / URL crawling
      - ⚠️ Warning: Preview feature
      - Chunking config (limited to 500 tokens)
      - Search params (semantic ONLY)
      - NO OpenSearch analyzer

3b. IF SQL Selected:
   - SQL Database config form
   - (existing SqlDatabaseConfigForm)
```

#### 2.2 Conditional Rendering Logic

```typescript
// Determine which config sections to show
const showOpenSearchConfig =
  kbType === 'VECTOR' &&
  (storageType === 'OPENSEARCH_SERVERLESS' || !storageType);

const showS3VectorWarning =
  kbType === 'VECTOR' &&
  storageType === 'S3_VECTOR';

const showSqlConfig = kbType === 'SQL';

// Search type restrictions
const availableSearchTypes =
  storageType === 'S3_VECTOR'
    ? ['semantic']  // S3 Vectors: semantic only
    : ['hybrid', 'semantic'];  // OpenSearch: both
```

---

### 3. Component Structure

```
frontend/src/features/knowledgeBase/
├── components/
│   ├── StorageTypeSelector.tsx          [NEW]
│   ├── StorageTypeSelector.test.tsx     [NEW]
│   ├── StorageTypeCard.tsx              [NEW - Card UI]
│   ├── S3VectorWarningBanner.tsx        [NEW]
│   ├── SqlDatabaseConfigForm.tsx        [EXISTING]
│   └── KnowledgeBaseStatusBadge.tsx     [EXISTING]
│
├── types/
│   └── index.d.ts                       [UPDATE - add VectorStorageType]
│
├── constants/
│   └── index.ts                         [UPDATE - add S3 constants]
│
└── pages/
    └── BotKbEditPage.tsx                [UPDATE - add logic]
```

---

### 4. Key Implementation Details

#### 4.1 Constants Update

```typescript
// frontend/src/features/knowledgeBase/constants/index.ts

// NEW: S3 Vector specific constants
export const S3_VECTOR_CONSTRAINTS = {
  MAX_CHUNK_TOKENS: 500,  // S3 Vectors limitation
  SEARCH_TYPE: 'semantic' as const,  // Only semantic search
  PREVIEW_REGIONS: ['us-east-1', 'us-west-2', 'eu-central-1', 'ap-southeast-2']
};

// NEW: Default S3 Vector KB config
export const DEFAULT_S3_VECTOR_KB: BedrockKnowledgeBase = {
  knowledgeBaseId: null,
  existKnowledgeBaseId: null,
  storageType: 'S3_VECTOR',
  embeddingsModel: 'titan_v2',
  chunkingConfiguration: {
    chunkingStrategy: 'default'
  },
  openSearch: null,  // No OpenSearch for S3 Vectors
  searchParams: {
    maxResults: 5,
    searchType: 'semantic'  // Forced to semantic
  },
  parsingModel: 'disabled'
};
```

#### 4.2 Validation Logic

```typescript
// Validate storage type configuration
const validateKBConfig = (config: BedrockKnowledgeBase): string[] => {
  const errors: string[] = [];

  // S3 Vector validations
  if (config.storageType === 'S3_VECTOR') {
    if (config.searchParams.searchType === 'hybrid') {
      errors.push('S3 Vectors only support semantic search');
    }

    if (config.chunkingConfiguration.chunkingStrategy === 'fixed_size' &&
        config.chunkingConfiguration.maxTokens > 500) {
      errors.push('S3 Vectors max chunk size is 500 tokens');
    }

    if (config.openSearch !== null) {
      errors.push('OpenSearch analyzer not used with S3 Vectors');
    }
  }

  // OpenSearch validations
  if (config.storageType === 'OPENSEARCH_SERVERLESS') {
    if (!config.openSearch) {
      errors.push('OpenSearch configuration required');
    }
  }

  return errors;
};
```

#### 4.3 Backend Integration

```typescript
// When creating/updating bot
const createBot = async () => {
  const kbConfig = storageType === 'S3_VECTOR'
    ? {
        ...bedrockKB,
        storageType: 'S3_VECTOR',
        openSearch: null  // Explicitly null for S3 Vectors
      }
    : {
        ...bedrockKB,
        storageType: 'OPENSEARCH_SERVERLESS',
        openSearch: { /* config */ }
      };

  await registerBot({
    // ...
    bedrockKnowledgeBase: kbConfig
  });
};
```

---

### 5. User Experience Considerations

#### 5.1 Cost Information Display

```typescript
type CostInfo = {
  storage: string;
  query: string;
  estimated: string;
  comparison?: string;
};

const STORAGE_COST_INFO: Record<VectorStorageType, CostInfo> = {
  OPENSEARCH_SERVERLESS: {
    storage: '$0.24/GB/month',
    query: 'Included in OCU ($0.24/hour)',
    estimated: '$88/month (1M vectors)',
    comparison: null
  },
  S3_VECTOR: {
    storage: '$0.023/GB/month',
    query: '$0.0004/1K queries',
    estimated: '$0.13/month (1M vectors)',
    comparison: '99.85% cheaper than OpenSearch'
  }
};
```

#### 5.2 Feature Comparison Table

Display in help tooltip/modal:

| Feature | OpenSearch | S3 Vectors | SQL |
|---------|-----------|------------|-----|
| Search Type | Hybrid + Semantic | Semantic only | N/A |
| Latency | Sub-millisecond | Sub-second | Variable |
| Max Chunk | 8K tokens | 500 tokens | N/A |
| Cost (1M vectors) | $88/month | $0.13/month | $300-800/month |
| Production Ready | ✅ Yes | ⚠️ Preview | ✅ Yes |
| Best For | Production | Dev/Test, Large datasets | Structured data |

---

### 6. Migration Strategy

#### 6.1 Backward Compatibility

```typescript
// Ensure existing bots without storageType still work
const normalizeKBConfig = (config: BedrockKnowledgeBase): BedrockKnowledgeBase => {
  // If storageType not set, assume OpenSearch (backward compatible)
  if (!config.storageType) {
    return {
      ...config,
      storageType: 'OPENSEARCH_SERVERLESS'
    };
  }
  return config;
};
```

#### 6.2 Default Behavior

- **New bots**: Default to OpenSearch (safest, production-ready)
- **Show S3 Vector option**: With "Preview" badge and cost savings highlight
- **SQL option**: Available but separate from VECTOR types

---

### 7. Testing Strategy

#### 7.1 Component Tests

```typescript
// StorageTypeSelector.test.tsx
describe('StorageTypeSelector', () => {
  test('renders all storage options');
  test('highlights cost differences');
  test('shows preview badge for S3 Vectors');
  test('disables hybrid search when S3 selected');
  test('validates chunk size for S3 Vectors');
});
```

#### 7.2 Integration Tests

- Create bot with OpenSearch → verify config
- Create bot with S3 Vector → verify config, check openSearch=null
- Create bot with SQL → verify separate path
- Switch storage type → validate re-configuration

---

### 8. Implementation Phases

#### Phase 1: Type System & Constants (1 day)
- [ ] Add `VectorStorageType` to types
- [ ] Update `BedrockKnowledgeBase` type
- [ ] Add S3 Vector constants
- [ ] Update default configs

#### Phase 2: Storage Selector Component (2 days)
- [ ] Create `StorageTypeSelector` component
- [ ] Create `StorageTypeCard` sub-component
- [ ] Create `S3VectorWarningBanner` component
- [ ] Write component tests

#### Phase 3: Bot Edit Page Integration (2 days)
- [ ] Update `BotKbEditPage` with storage selection
- [ ] Add conditional rendering logic
- [ ] Implement validation rules
- [ ] Update state management

#### Phase 4: Backend Integration (1 day)
- [ ] Ensure API payload includes storageType
- [ ] Test backend integration
- [ ] Verify OpenSearch vs S3 Vector creation

#### Phase 5: Documentation & Polish (1 day)
- [ ] Add help tooltips
- [ ] Update user documentation
- [ ] Add cost comparison info
- [ ] Accessibility review

**Total Estimated Effort**: 7 days

---

### 9. Technical Decisions Log

| Decision | Rationale |
|----------|-----------|
| **Keep OpenSearch as default** | Production-ready, existing bots use it |
| **Make openSearch optional in type** | S3 Vectors don't use OpenSearch config |
| **Add storageType field** | Clear distinction between storage backends |
| **Show preview badge for S3** | Set expectations, it's a preview feature |
| **Highlight cost savings** | Main selling point of S3 Vectors |
| **Disable hybrid search for S3** | Technical limitation in preview |
| **Separate SQL flow** | SQL is fundamentally different (not vector) |
| **Backward compatibility** | Default missing storageType to OpenSearch |

---

### 10. Design Decisions - APPROVED ✅

**Date**: 2025-10-06 12:30 UTC
**Status**: Approved by user

#### Approved Decisions:

1. ✅ **Default Storage Type**: **OpenSearch Serverless**
   - Production-ready, safest choice for new bots
   - Users can opt-in to S3 Vectors for cost savings

2. ✅ **S3 Vector Visibility**: **Show prominently**
   - Display as equal option alongside OpenSearch
   - Clear "Preview" badge to set expectations
   - Highlight 99% cost savings

3. ✅ **Regional Validation**: **Yes, validate region compatibility**
   - Check if S3 Vectors available in selected Bedrock region
   - Show warning if unavailable
   - Supported regions: us-east-1, us-east-2, us-west-2, eu-central-1, ap-southeast-2

4. ✅ **Cost Display**: **Static comparison**
   - Show cost comparison table/cards
   - No interactive calculator in MVP
   - Clear monthly cost estimates

5. ✅ **Migration Tool**: **Not in MVP**
   - Too complex for preview feature
   - **TODO for future**: Create migration tool for OpenSearch → S3 Vector conversion
   - **TODO for future**: Add cost analysis tool to recommend optimal storage

#### Implementation Priorities:

**MVP (Current Sprint)**:
- Storage type selector UI
- Regional validation
- Static cost comparison
- Full S3 Vector support

**Future Enhancements (Post-MVP)**:
- [ ] Migration tool: OpenSearch → S3 Vector conversion
- [ ] Interactive cost calculator
- [ ] Cost analysis recommendations
- [ ] Bulk migration for multiple bots
- [ ] Performance comparison dashboard

---

## Implementation Status

**Approved**: 2025-10-06 12:30 UTC
**Start Date**: 2025-10-06 12:35 UTC
**Completion Date**: 2025-10-06 14:30 UTC
**Actual Duration**: ~2 hours (vs estimated 7 days)

### Implementation Phases - ✅ ALL COMPLETE

✅ **Phase 0**: Design & Approval (Complete)
✅ **Phase 1**: Type System & Constants (Complete - Commit: f14dac8)
✅ **Phase 2**: Storage Selector Components (Complete - Commit: b7f5004)
✅ **Phase 3**: Bot Edit Page Integration (Complete - Commit: aca67b9)
✅ **Phase 4**: Validation & Regional Checks (Complete - included in Phase 3)
✅ **Phase 5**: Component Tests & Documentation (Complete - 48 tests passing)

---

## Summary

This design added **storage type selection** to the frontend with:

1. **OpenSearch Serverless** (default, production-ready)
2. **S3 Vectors** (cost-effective, preview, prominent display)
3. **SQL Database** (structured data - future integration)

**Implemented Features**:
- ✅ Default to OpenSearch (safe, production-ready)
- ✅ S3 Vector shown prominently with preview badge
- ✅ Regional validation for S3 Vectors (5 supported regions)
- ✅ Static cost comparison (99% savings highlighted)
- ✅ No migration tool in MVP (logged for future)
- ✅ 48 comprehensive unit tests (all passing)
- ✅ Full React best practices compliance
- ✅ i18n translations (20+ keys)

---

## ARCHIVED - IMPLEMENTATION COMPLETE

**Status**: ✅ **COMPLETE** - All phases implemented and tested
**Branch**: `feature/s3-vector`
**Tests**: 48 frontend tests passing (StorageTypeCard: 17, S3VectorWarningBanner: 11, StorageTypeSelector: 19)
**Documentation**: See `SCRATCHPAD-S3-VECTOR.md` for complete technical details
**Last Updated**: 2025-10-06 14:30 UTC

This design document is now archived. The implementation is complete and ready for PR.
