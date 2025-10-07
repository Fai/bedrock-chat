import {
  BedrockKnowledgeBase,
  OpenSearchParams,
  SearchParams,
  FixedSizeParams,
  HierarchicalParams,
  SemanticParams,
} from '../types';

export const OPENSEARCH_ANALYZER: {
  [key: string]: OpenSearchParams;
} = {
  icu: {
    analyzer: {
      characterFilters: ['icu_normalizer'],
      tokenizer: 'icu_tokenizer',
      tokenFilters: ['icu_folding'],
    },
  } as OpenSearchParams,
  kuromoji: {
    analyzer: {
      characterFilters: ['icu_normalizer'],
      tokenizer: 'kuromoji_tokenizer',
      tokenFilters: [
        'kuromoji_baseform',
        'kuromoji_part_of_speech',
        'kuromoji_stemmer',
        'cjk_width',
        'ja_stop',
        'lowercase',
        'icu_folding',
      ],
    },
  } as OpenSearchParams,
  none: {
    // as fallback
    analyzer: null,
  },
} as const;

export const DEFAULT_OPENSEARCH_ANALYZER: {
  [key: string]: string;
} = {
  ja: 'kuromoji',
  ko: 'icu',
  zhhans: 'icu',
  zhhant: 'icu',
} as const;

// S3 Vectors supported regions (preview)
export const S3_VECTOR_SUPPORTED_REGIONS = [
  'us-east-1',
  'us-east-2',
  'us-west-2',
  'eu-central-1',
  'ap-southeast-2',
] as const;

// S3 Vectors constraints
export const S3_VECTOR_CONSTRAINTS = {
  MAX_CHUNK_TOKENS: 500,  // S3 Vectors chunking limitation
  SEARCH_TYPE: 'semantic' as const,  // Only semantic search supported
  METADATA_SIZE_LIMIT: 40 * 1024,  // 40KB max metadata per vector
  FILTERABLE_METADATA_LIMIT: 2 * 1024,  // 2KB filterable metadata
} as const;

// S3 Vector specific chunk limits (500 token max)
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
} as const;

// Default OpenSearch KB (backward compatible - default storage type)
export const DEFAULT_BEDROCK_KNOWLEDGEBASE: BedrockKnowledgeBase = {
  knowledgeBaseId: null,
  existKnowledgeBaseId: null,
  storageType: 'OPENSEARCH_SERVERLESS',  // Default to OpenSearch
  embeddingsModel: 'cohere_multilingual_v3',
  openSearch: OPENSEARCH_ANALYZER['none'],
  chunkingConfiguration: {
    chunkingStrategy: 'default'
  },
  searchParams: {
    maxResults: 20,
    searchType: 'hybrid',
  },
};

// S3 Vector KB defaults
export const DEFAULT_S3_VECTOR_KNOWLEDGEBASE: BedrockKnowledgeBase = {
  knowledgeBaseId: null,
  existKnowledgeBaseId: null,
  storageType: 'S3_VECTOR',
  embeddingsModel: 'titan_v2',  // Titan V2 recommended for S3 Vectors
  openSearch: null,  // No OpenSearch for S3 Vectors
  chunkingConfiguration: {
    chunkingStrategy: 'default'
  },
  searchParams: {
    maxResults: 5,
    searchType: 'semantic',  // S3 Vectors only support semantic
  },
};

export const DEFAULT_FIXED_CHUNK_PARAMS: FixedSizeParams = {
  chunkingStrategy: 'fixed_size',
  maxTokens: 300,
  overlapPercentage: 20,
};

// Fixed size chunking valid range
// Ref: https://docs.aws.amazon.com/bedrock/latest/APIReference/API_agent_FixedSizeChunkingConfiguration.html 
export const EDGE_FIXED_CHUNK_PARAMS = {
  maxTokens: {
    MAX: {
      titan_v2: 8192,
      cohere_multilingual_v3: 512,
    },
    MIN: 1,
    STEP: 1,
  },
  overlapPercentage: {
    MAX: 99,
    MIN: 1,
    STEP: 1,
  },
};

export const DEFAULT_HIERARCHICAL_CHUNK_PARAMS: HierarchicalParams = {
  chunkingStrategy: 'hierarchical',
  overlapTokens: 60,
  maxParentTokenSize: 1500,
  maxChildTokenSize: 300,
};

// Hierarchical chunking valid range
// Ref: https://docs.aws.amazon.com/bedrock/latest/APIReference/API_agent_HierarchicalChunkingConfiguration.html
export const EDGE_HIERARCHICAL_CHUNK_PARAMS = {
  overlapTokens: {
    MIN: 1,
    STEP: 1,
  },
  maxParentTokenSize: {
    MAX: {
      titan_v2: 8192,
      cohere_multilingual_v3: 512,
    },
    MIN: 1,
    STEP: 1,
  },
  maxChildTokenSize: {
    MAX: {
      titan_v2: 8192,
      cohere_multilingual_v3: 512,
    },
    MIN: 1,
    STEP: 1,
  },
};

export const DEFAULT_SEMANTIC_CHUNK_PARAMS: SemanticParams = {
  chunkingStrategy: 'semantic',
  maxTokens: 300,
  bufferSize: 0,
  breakpointPercentileThreshold: 95,
};

// Semantic chunking valid range
// Ref: https://docs.aws.amazon.com/bedrock/latest/APIReference/API_agent_SemanticChunkingConfiguration.html
export const EDGE_SEMANTIC_CHUNK_PARAMS = {
  maxTokens: {
    MAX: {
      titan_v2: 8192,
      cohere_multilingual_v3: 512,
    },
    MIN: 1,
    STEP: 1,
  },
  bufferSize: {
    MAX: 1,
    MIN: 0,
    STEP: 1,
  },
  breakpointPercentileThreshold: {
    MAX: 99,
    MIN: 50,
    STEP: 1,
  },
};

export const EDGE_SEARCH_PARAMS = {
  maxResults: {
    MAX: 100,
    MIN: 1,
    STEP: 1,
  },
};

export const DEFAULT_SEARCH_CONFIG: SearchParams = {
  maxResults: 5,
  searchType: 'hybrid',
};
