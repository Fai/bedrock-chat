import React from 'react';
import { twMerge } from 'tailwind-merge';
import {
  PiCheckCircleFill,
  PiHourglassHighFill,
  PiSpinnerGapBold,
  PiWarningCircleFill,
  PiXCircleFill,
} from 'react-icons/pi';
import { KnowledgeBaseStatus, IngestionJobStatus } from '../types';

type Props = {
  status: KnowledgeBaseStatus;
  ingestionJobStatus?: IngestionJobStatus | null;
  errorMessage?: string;
  className?: string;
};

const KnowledgeBaseStatusBadge: React.FC<Props> = ({
  status,
  ingestionJobStatus,
  errorMessage,
  className,
}) => {
  const getStatusConfig = () => {
    // If there's an error, show failed status
    if (errorMessage) {
      return {
        icon: <PiXCircleFill className="animate-none" />,
        text: 'Failed',
        bgColor: 'bg-red/10',
        textColor: 'text-red',
        borderColor: 'border-red/30',
      };
    }

    // Check ingestion job status first (more granular)
    if (ingestionJobStatus) {
      switch (ingestionJobStatus) {
        case 'STARTING':
          return {
            icon: <PiHourglassHighFill className="animate-pulse" />,
            text: 'Starting Ingestion',
            bgColor: 'bg-blue/10',
            textColor: 'text-blue',
            borderColor: 'border-blue/30',
          };
        case 'IN_PROGRESS':
          return {
            icon: <PiSpinnerGapBold className="animate-spin" />,
            text: 'Ingesting Data',
            bgColor: 'bg-blue/10',
            textColor: 'text-blue',
            borderColor: 'border-blue/30',
          };
        case 'COMPLETE':
          return {
            icon: <PiCheckCircleFill className="animate-none" />,
            text: 'Ready',
            bgColor: 'bg-green/10',
            textColor: 'text-green',
            borderColor: 'border-green/30',
          };
        case 'FAILED':
          return {
            icon: <PiXCircleFill className="animate-none" />,
            text: 'Ingestion Failed',
            bgColor: 'bg-red/10',
            textColor: 'text-red',
            borderColor: 'border-red/30',
          };
      }
    }

    // Fall back to KB status
    switch (status) {
      case 'CREATING':
        return {
          icon: <PiSpinnerGapBold className="animate-spin" />,
          text: 'Creating',
          bgColor: 'bg-blue/10',
          textColor: 'text-blue',
          borderColor: 'border-blue/30',
        };
      case 'ACTIVE':
        return {
          icon: <PiCheckCircleFill className="animate-none" />,
          text: 'Active',
          bgColor: 'bg-green/10',
          textColor: 'text-green',
          borderColor: 'border-green/30',
        };
      case 'UPDATING':
        return {
          icon: <PiSpinnerGapBold className="animate-spin" />,
          text: 'Updating',
          bgColor: 'bg-blue/10',
          textColor: 'text-blue',
          borderColor: 'border-blue/30',
        };
      case 'DELETING':
        return {
          icon: <PiSpinnerGapBold className="animate-spin" />,
          text: 'Deleting',
          bgColor: 'bg-gray/10',
          textColor: 'text-gray',
          borderColor: 'border-gray/30',
        };
      case 'FAILED':
        return {
          icon: <PiXCircleFill className="animate-none" />,
          text: 'Failed',
          bgColor: 'bg-red/10',
          textColor: 'text-red',
          borderColor: 'border-red/30',
        };
      case 'NOT_STARTED':
        return {
          icon: <PiWarningCircleFill className="animate-none" />,
          text: 'Not Started',
          bgColor: 'bg-yellow/10',
          textColor: 'text-yellow',
          borderColor: 'border-yellow/30',
        };
      case 'UNKNOWN':
      default:
        return {
          icon: <PiWarningCircleFill className="animate-none" />,
          text: 'Unknown',
          bgColor: 'bg-gray/10',
          textColor: 'text-gray',
          borderColor: 'border-gray/30',
        };
    }
  };

  const config = getStatusConfig();

  return (
    <div
      className={twMerge(
        'inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-sm font-medium',
        config.bgColor,
        config.textColor,
        config.borderColor,
        className
      )}
      title={errorMessage || undefined}>
      {config.icon}
      <span>{config.text}</span>
    </div>
  );
};

export default KnowledgeBaseStatusBadge;
