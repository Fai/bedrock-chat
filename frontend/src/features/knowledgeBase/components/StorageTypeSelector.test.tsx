import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import StorageTypeSelector from './StorageTypeSelector';

describe('StorageTypeSelector', () => {
  const defaultProps = {
    selectedStorageType: 'OPENSEARCH_SERVERLESS' as const,
    onStorageTypeChange: vi.fn(),
  };

  it('renders title and description', () => {
    render(<StorageTypeSelector {...defaultProps} />);
    expect(screen.getByText('Vector Storage Type')).toBeInTheDocument();
    expect(
      screen.getByText(/Choose the backend storage for your vector embeddings/)
    ).toBeInTheDocument();
  });

  it('renders OpenSearch Serverless card', () => {
    render(<StorageTypeSelector {...defaultProps} />);
    expect(screen.getByText('OpenSearch Serverless')).toBeInTheDocument();
    expect(
      screen.getByText('Production-ready vector search with sub-millisecond latency')
    ).toBeInTheDocument();
  });

  it('renders S3 Vectors card', () => {
    render(<StorageTypeSelector {...defaultProps} />);
    expect(screen.getByText('S3 Vectors')).toBeInTheDocument();
    expect(
      screen.getByText('Cost-optimized vector storage for large datasets')
    ).toBeInTheDocument();
  });

  it('shows S3 Vectors as selected when selectedStorageType is S3_VECTOR', () => {
    const { container } = render(
      <StorageTypeSelector
        {...defaultProps}
        selectedStorageType="S3_VECTOR"
      />
    );

    // Check that S3_VECTOR card has selected styling (contains checkmark SVG)
    const buttons = container.querySelectorAll('button');
    const s3Button = Array.from(buttons).find((btn) =>
      btn.textContent?.includes('S3 Vectors')
    );

    expect(s3Button?.querySelector('svg')).toBeInTheDocument();
  });

  it('calls onStorageTypeChange when OpenSearch card is clicked', () => {
    const onChange = vi.fn();
    render(
      <StorageTypeSelector
        {...defaultProps}
        onStorageTypeChange={onChange}
      />
    );

    const openSearchButton = screen
      .getByText('OpenSearch Serverless')
      .closest('button');
    if (openSearchButton) {
      fireEvent.click(openSearchButton);
    }

    expect(onChange).toHaveBeenCalledWith('OPENSEARCH_SERVERLESS');
  });

  it('calls onStorageTypeChange when S3 Vector card is clicked and available', () => {
    const onChange = vi.fn();
    render(
      <StorageTypeSelector
        {...defaultProps}
        onStorageTypeChange={onChange}
        bedrockRegion="us-east-1"
      />
    );

    const s3Button = screen.getByText('S3 Vectors').closest('button');
    if (s3Button) {
      fireEvent.click(s3Button);
    }

    expect(onChange).toHaveBeenCalledWith('S3_VECTOR');
  });

  it('disables S3 Vector card when region is not supported', () => {
    render(
      <StorageTypeSelector {...defaultProps} bedrockRegion="us-west-1" />
    );

    const s3Button = screen.getByText('S3 Vectors').closest('button');
    expect(s3Button).toHaveAttribute('disabled');
  });

  it('enables S3 Vector card when region is us-east-1', () => {
    render(
      <StorageTypeSelector {...defaultProps} bedrockRegion="us-east-1" />
    );

    const s3Button = screen.getByText('S3 Vectors').closest('button');
    expect(s3Button).not.toHaveAttribute('disabled');
  });

  it('enables S3 Vector card when region is us-east-2', () => {
    render(
      <StorageTypeSelector {...defaultProps} bedrockRegion="us-east-2" />
    );

    const s3Button = screen.getByText('S3 Vectors').closest('button');
    expect(s3Button).not.toHaveAttribute('disabled');
  });

  it('enables S3 Vector card when region is eu-central-1', () => {
    render(
      <StorageTypeSelector {...defaultProps} bedrockRegion="eu-central-1" />
    );

    const s3Button = screen.getByText('S3 Vectors').closest('button');
    expect(s3Button).not.toHaveAttribute('disabled');
  });

  it('shows warning banner when S3_VECTOR is selected', () => {
    render(
      <StorageTypeSelector
        {...defaultProps}
        selectedStorageType="S3_VECTOR"
        bedrockRegion="us-east-1"
      />
    );

    expect(screen.getByText('Preview Feature')).toBeInTheDocument();
    expect(screen.getByText('Key Limitations')).toBeInTheDocument();
  });

  it('does not show warning banner when OPENSEARCH_SERVERLESS is selected', () => {
    render(
      <StorageTypeSelector
        {...defaultProps}
        selectedStorageType="OPENSEARCH_SERVERLESS"
      />
    );

    expect(screen.queryByText('Preview Feature')).not.toBeInTheDocument();
  });

  it('shows regional availability info when S3 Vector is not available', () => {
    render(
      <StorageTypeSelector {...defaultProps} bedrockRegion="ap-south-1" />
    );

    expect(
      screen.getByText(/S3 Vectors is only available in:/)
    ).toBeInTheDocument();
    expect(screen.getByText(/ap-south-1/)).toBeInTheDocument();
  });

  it('does not show regional availability info when S3 Vector is available', () => {
    render(
      <StorageTypeSelector {...defaultProps} bedrockRegion="us-east-1" />
    );

    expect(
      screen.queryByText(/S3 Vectors is only available in:/)
    ).not.toBeInTheDocument();
  });

  it('renders cost comparison section', () => {
    render(<StorageTypeSelector {...defaultProps} />);

    expect(
      screen.getByText(/Storage Cost Comparison/)
    ).toBeInTheDocument();
    expect(screen.getByText(/~\$88\/month/)).toBeInTheDocument();
    expect(screen.getByText(/~\$0\.13\/month/)).toBeInTheDocument();
  });

  it('shows cost savings percentage', () => {
    render(<StorageTypeSelector {...defaultProps} />);

    expect(
      screen.getByText(/S3 Vectors saves 99\.85% on storage costs/)
    ).toBeInTheDocument();
  });

  it('applies custom className', () => {
    const { container } = render(
      <StorageTypeSelector {...defaultProps} className="custom-class" />
    );

    const selector = container.querySelector('.custom-class');
    expect(selector).toBeInTheDocument();
  });

  it('handles missing bedrockRegion gracefully', () => {
    render(<StorageTypeSelector {...defaultProps} />);

    const s3Button = screen.getByText('S3 Vectors').closest('button');
    expect(s3Button).toHaveAttribute('disabled');
  });

  it('displays correct disabled reason for unsupported region', () => {
    const { container } = render(
      <StorageTypeSelector {...defaultProps} bedrockRegion="ap-south-1" />
    );

    const s3Button = screen.getByText('S3 Vectors').closest('button');
    expect(s3Button?.getAttribute('title')).toContain('ap-south-1');
    expect(s3Button?.getAttribute('title')).toContain('Supported regions:');
  });
});
