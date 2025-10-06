import React from 'react';
import { twMerge } from 'tailwind-merge';
import { PiCheckCircleFill } from 'react-icons/pi';
import { VectorStorageType } from '../types';

type Props = {
  type: VectorStorageType | 'SQL';
  title: string;
  description: string;
  costLevel: string;
  features: string[];
  limitations?: string[];
  isSelected: boolean;
  isPreview?: boolean;
  isDisabled?: boolean;
  disabledReason?: string;
  onClick: () => void;
  className?: string;
};

const StorageTypeCard: React.FC<Props> = ({
  type,
  title,
  description,
  costLevel,
  features,
  limitations = [],
  isSelected,
  isPreview = false,
  isDisabled = false,
  disabledReason,
  onClick,
  className,
}) => {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={isDisabled}
      className={twMerge(
        'relative flex w-full flex-col gap-3 rounded-lg border-2 p-4 text-left transition-all',
        isSelected
          ? 'border-aws-sea-blue bg-aws-sea-blue/5 dark:border-aws-sea-blue dark:bg-aws-sea-blue/10'
          : 'border-gray/30 bg-white hover:border-aws-sea-blue/50 dark:border-aws-font-color-dark/30 dark:bg-aws-squid-ink dark:hover:border-aws-sea-blue/50',
        isDisabled &&
          'cursor-not-allowed opacity-50 hover:border-gray/30 dark:hover:border-aws-font-color-dark/30',
        className
      )}
      title={isDisabled ? disabledReason : undefined}>
      {/* Header */}
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <h3 className="text-base font-semibold text-dark-gray dark:text-light-gray">
              {title}
            </h3>
            {isPreview && (
              <span className="rounded bg-yellow/20 px-2 py-0.5 text-xs font-medium text-yellow-600 dark:bg-yellow/30 dark:text-yellow-400">
                PREVIEW
              </span>
            )}
          </div>
          <p className="mt-1 text-sm text-gray dark:text-aws-font-color-dark">
            {description}
          </p>
        </div>
        {isSelected && (
          <PiCheckCircleFill className="h-6 w-6 flex-shrink-0 text-aws-sea-blue" />
        )}
      </div>

      {/* Cost Level */}
      <div className="flex items-center gap-2">
        <span className="text-xs font-medium text-gray dark:text-aws-font-color-dark">
          Cost:
        </span>
        <span className="text-sm font-semibold text-dark-gray dark:text-light-gray">
          {costLevel}
        </span>
      </div>

      {/* Features */}
      <div className="space-y-1">
        {features.map((feature, index) => (
          <div key={index} className="flex items-start gap-2">
            <span className="mt-1 h-1.5 w-1.5 flex-shrink-0 rounded-full bg-green" />
            <span className="text-xs text-dark-gray dark:text-light-gray">
              {feature}
            </span>
          </div>
        ))}
      </div>

      {/* Limitations (if any) */}
      {limitations.length > 0 && (
        <div className="space-y-1 border-t pt-2 dark:border-aws-font-color-dark/30">
          <div className="text-xs font-medium text-gray dark:text-aws-font-color-dark">
            Limitations:
          </div>
          {limitations.map((limitation, index) => (
            <div key={index} className="flex items-start gap-2">
              <span className="mt-1 h-1.5 w-1.5 flex-shrink-0 rounded-full bg-yellow" />
              <span className="text-xs text-gray dark:text-aws-font-color-dark">
                {limitation}
              </span>
            </div>
          ))}
        </div>
      )}
    </button>
  );
};

export default StorageTypeCard;
