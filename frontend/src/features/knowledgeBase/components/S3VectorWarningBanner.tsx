import React from 'react';
import { PiWarningCircleFill, PiInfoFill } from 'react-icons/pi';

type Props = {
  className?: string;
};

const S3VectorWarningBanner: React.FC<Props> = ({ className }) => {
  return (
    <div
      className={`flex flex-col gap-3 rounded-lg border border-yellow/30 bg-yellow/10 p-4 dark:border-yellow/40 dark:bg-yellow/5 ${className || ''}`}>
      {/* Preview Warning */}
      <div className="flex items-start gap-3">
        <PiWarningCircleFill className="mt-0.5 h-5 w-5 flex-shrink-0 text-yellow-600 dark:text-yellow-400" />
        <div className="flex-1">
          <div className="text-sm font-semibold text-yellow-700 dark:text-yellow-300">
            Preview Feature
          </div>
          <div className="mt-1 text-xs text-yellow-600 dark:text-yellow-400">
            S3 Vectors is currently in preview. While suitable for development
            and testing, it may experience changes and is not recommended for
            production workloads requiring guaranteed SLAs.
          </div>
        </div>
      </div>

      {/* Key Limitations */}
      <div className="flex items-start gap-3 border-t border-yellow/20 pt-3 dark:border-yellow/30">
        <PiInfoFill className="mt-0.5 h-5 w-5 flex-shrink-0 text-yellow-600 dark:text-yellow-400" />
        <div className="flex-1">
          <div className="text-sm font-semibold text-yellow-700 dark:text-yellow-300">
            Key Limitations
          </div>
          <ul className="mt-2 space-y-1 text-xs text-yellow-600 dark:text-yellow-400">
            <li className="flex items-start gap-2">
              <span className="mt-1 h-1 w-1 flex-shrink-0 rounded-full bg-yellow-600 dark:bg-yellow-400" />
              <span>
                <strong>Regional Availability:</strong> Only available in
                us-east-1, us-east-2, us-west-2, eu-central-1, ap-southeast-2
              </span>
            </li>
            <li className="flex items-start gap-2">
              <span className="mt-1 h-1 w-1 flex-shrink-0 rounded-full bg-yellow-600 dark:bg-yellow-400" />
              <span>
                <strong>Search Type:</strong> Semantic search only (no hybrid
                search)
              </span>
            </li>
            <li className="flex items-start gap-2">
              <span className="mt-1 h-1 w-1 flex-shrink-0 rounded-full bg-yellow-600 dark:bg-yellow-400" />
              <span>
                <strong>Chunking Limit:</strong> Maximum 500 tokens per chunk
                (vs 8192 for OpenSearch)
              </span>
            </li>
            <li className="flex items-start gap-2">
              <span className="mt-1 h-1 w-1 flex-shrink-0 rounded-full bg-yellow-600 dark:bg-yellow-400" />
              <span>
                <strong>Query Latency:</strong> Sub-second response time (vs
                sub-millisecond for OpenSearch)
              </span>
            </li>
          </ul>
        </div>
      </div>

      {/* Best For */}
      <div className="flex items-start gap-3 border-t border-yellow/20 pt-3 dark:border-yellow/30">
        <PiInfoFill className="mt-0.5 h-5 w-5 flex-shrink-0 text-yellow-600 dark:text-yellow-400" />
        <div className="flex-1">
          <div className="text-sm font-semibold text-yellow-700 dark:text-yellow-300">
            Best For
          </div>
          <div className="mt-1 text-xs text-yellow-600 dark:text-yellow-400">
            Development, testing, cost-sensitive workloads with large datasets
            and low query volumes. For production workloads requiring low
            latency and hybrid search, consider OpenSearch Serverless.
          </div>
        </div>
      </div>
    </div>
  );
};

export default S3VectorWarningBanner;
