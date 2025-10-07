import React, { useMemo } from 'react';
import StorageTypeCard from './StorageTypeCard';
import S3VectorWarningBanner from './S3VectorWarningBanner';
import { VectorStorageType } from '../types';
import { S3_VECTOR_SUPPORTED_REGIONS } from '../constants';

type Props = {
  selectedStorageType: VectorStorageType;
  onStorageTypeChange: (storageType: VectorStorageType) => void;
  bedrockRegion?: string;
  className?: string;
};

const StorageTypeSelector: React.FC<Props> = ({
  selectedStorageType,
  onStorageTypeChange,
  bedrockRegion,
  className,
}) => {
  // Check if S3 Vector is available in the current region
  const isS3VectorAvailable = useMemo(() => {
    if (!bedrockRegion) return false;
    return S3_VECTOR_SUPPORTED_REGIONS.includes(
      bedrockRegion as (typeof S3_VECTOR_SUPPORTED_REGIONS)[number]
    );
  }, [bedrockRegion]);

  return (
    <div className={`flex flex-col gap-4 ${className || ''}`}>
      {/* Title */}
      <div>
        <h3 className="text-base font-semibold text-dark-gray dark:text-light-gray">
          Vector Storage Type
        </h3>
        <p className="mt-1 text-sm text-gray dark:text-aws-font-color-dark">
          Choose the backend storage for your vector embeddings. This cannot be
          changed after creating the bot.
        </p>
      </div>

      {/* Storage Type Cards */}
      <div className="grid grid-cols-1 gap-3 lg:grid-cols-2">
        {/* OpenSearch Serverless (Default) */}
        <StorageTypeCard
          type="OPENSEARCH_SERVERLESS"
          title="OpenSearch Serverless"
          description="Production-ready vector search with sub-millisecond latency"
          costLevel="~$88/month per 1M vectors"
          features={[
            'Sub-millisecond query latency',
            'Hybrid search (semantic + keyword)',
            'Up to 8192 token chunks',
            'Production-ready with SLA',
            'Full metadata support',
          ]}
          isSelected={selectedStorageType === 'OPENSEARCH_SERVERLESS'}
          onClick={() => onStorageTypeChange('OPENSEARCH_SERVERLESS')}
        />

        {/* S3 Vectors (Preview) */}
        <StorageTypeCard
          type="S3_VECTOR"
          title="S3 Vectors"
          description="Cost-optimized vector storage for large datasets"
          costLevel="~$0.13/month per 1M vectors"
          features={[
            '99% cost savings vs OpenSearch',
            'Ideal for large datasets',
            'Good for dev/test workloads',
            'Quick Create auto-provisioning',
          ]}
          limitations={[
            'Preview feature - subject to change',
            'Semantic search only (no hybrid)',
            'Max 500 tokens per chunk',
            'Sub-second latency (not sub-millisecond)',
          ]}
          isSelected={selectedStorageType === 'S3_VECTOR'}
          isPreview={true}
          isDisabled={!isS3VectorAvailable}
          disabledReason={
            !isS3VectorAvailable
              ? `S3 Vectors not available in ${bedrockRegion || 'this region'}. Supported regions: ${S3_VECTOR_SUPPORTED_REGIONS.join(', ')}`
              : undefined
          }
          onClick={() => onStorageTypeChange('S3_VECTOR')}
        />
      </div>

      {/* S3 Vector Warning Banner (show when S3_VECTOR selected) */}
      {selectedStorageType === 'S3_VECTOR' && (
        <S3VectorWarningBanner className="mt-2" />
      )}

      {/* Regional Availability Info */}
      {!isS3VectorAvailable && (
        <div className="rounded-lg border border-blue/30 bg-blue/5 p-3 dark:border-blue/40 dark:bg-blue/10">
          <p className="text-xs text-blue-600 dark:text-blue-400">
            <strong>Note:</strong> S3 Vectors is only available in:{' '}
            {S3_VECTOR_SUPPORTED_REGIONS.join(', ')}. 
            {bedrockRegion ? (
              <>Your current Bedrock region is <strong>{bedrockRegion}</strong>.</>
            ) : (
              <>Contact your administrator to configure S3 Vector support.</>
            )}
          </p>
        </div>
      )}

      {/* Cost Comparison */}
      <div className="rounded-lg border border-gray/20 bg-gray/5 p-4 dark:border-aws-font-color-dark/20 dark:bg-aws-squid-ink/50">
        <div className="mb-2 text-sm font-semibold text-dark-gray dark:text-light-gray">
          Storage Cost Comparison (1M vectors @ 1024 dimensions)
        </div>
        <div className="space-y-2 text-xs text-gray dark:text-aws-font-color-dark">
          <div className="flex items-center justify-between">
            <span>OpenSearch Serverless:</span>
            <span className="font-mono font-medium">~$88/month</span>
          </div>
          <div className="flex items-center justify-between">
            <span>S3 Vectors:</span>
            <span className="font-mono font-medium text-green">
              ~$0.13/month
            </span>
          </div>
          <div className="mt-2 border-t pt-2 dark:border-aws-font-color-dark/20">
            <span className="text-green">
              💰 S3 Vectors saves 99.85% on storage costs
            </span>
          </div>
        </div>
        <div className="mt-3 text-xs text-gray dark:text-aws-font-color-dark">
          Note: OpenSearch has additional compute costs (OCU) for indexing and
          queries. S3 Vectors has additional costs for query requests. Actual
          costs depend on usage patterns.
        </div>
      </div>
    </div>
  );
};

export default StorageTypeSelector;
