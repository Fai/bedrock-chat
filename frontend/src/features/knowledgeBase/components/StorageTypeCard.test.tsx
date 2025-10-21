import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import StorageTypeCard from './StorageTypeCard';

describe('StorageTypeCard', () => {
  const defaultProps = {
    type: 'OPENSEARCH_SERVERLESS' as const,
    title: 'OpenSearch Serverless',
    description: 'Production-ready vector search',
    costLevel: '~$88/month',
    features: ['Low latency', 'Hybrid search'],
    isSelected: false,
    onClick: vi.fn(),
  };

  it('renders title and description correctly', () => {
    render(<StorageTypeCard {...defaultProps} />);
    expect(screen.getByText('OpenSearch Serverless')).toBeInTheDocument();
    expect(screen.getByText('Production-ready vector search')).toBeInTheDocument();
  });

  it('renders cost level correctly', () => {
    render(<StorageTypeCard {...defaultProps} />);
    expect(screen.getByText('~$88/month')).toBeInTheDocument();
  });

  it('renders all features', () => {
    render(<StorageTypeCard {...defaultProps} />);
    expect(screen.getByText('Low latency')).toBeInTheDocument();
    expect(screen.getByText('Hybrid search')).toBeInTheDocument();
  });

  it('renders limitations when provided', () => {
    render(
      <StorageTypeCard
        {...defaultProps}
        limitations={['Preview only', 'Limited regions']}
      />
    );
    expect(screen.getByText('Limitations:')).toBeInTheDocument();
    expect(screen.getByText('Preview only')).toBeInTheDocument();
    expect(screen.getByText('Limited regions')).toBeInTheDocument();
  });

  it('shows checkmark when selected', () => {
    const { container } = render(
      <StorageTypeCard {...defaultProps} isSelected={true} />
    );
    // Check for SVG checkmark icon
    const checkIcon = container.querySelector('svg');
    expect(checkIcon).toBeInTheDocument();
  });

  it('does not show checkmark when not selected', () => {
    const { container } = render(
      <StorageTypeCard {...defaultProps} isSelected={false} />
    );
    // Should not have checkmark when not selected
    const checkIcon = container.querySelector('svg');
    expect(checkIcon).not.toBeInTheDocument();
  });

  it('shows preview badge when isPreview is true', () => {
    render(<StorageTypeCard {...defaultProps} isPreview={true} />);
    expect(screen.getByText('PREVIEW')).toBeInTheDocument();
  });

  it('does not show preview badge when isPreview is false', () => {
    render(<StorageTypeCard {...defaultProps} isPreview={false} />);
    expect(screen.queryByText('PREVIEW')).not.toBeInTheDocument();
  });

  it('calls onClick when clicked', () => {
    const onClick = vi.fn();
    render(<StorageTypeCard {...defaultProps} onClick={onClick} />);

    const button = screen.getByRole('button');
    fireEvent.click(button);

    expect(onClick).toHaveBeenCalledTimes(1);
  });

  it('does not call onClick when disabled', () => {
    const onClick = vi.fn();
    render(
      <StorageTypeCard
        {...defaultProps}
        onClick={onClick}
        isDisabled={true}
        disabledReason="Not available in this region"
      />
    );

    const button = screen.getByRole('button');
    fireEvent.click(button);

    expect(onClick).not.toHaveBeenCalled();
  });

  it('shows disabled reason in title attribute when disabled', () => {
    const { container } = render(
      <StorageTypeCard
        {...defaultProps}
        isDisabled={true}
        disabledReason="Not available in this region"
      />
    );

    const button = container.querySelector('[title="Not available in this region"]');
    expect(button).toBeInTheDocument();
  });

  it('applies custom className', () => {
    const { container } = render(
      <StorageTypeCard {...defaultProps} className="custom-class" />
    );

    const button = container.querySelector('.custom-class');
    expect(button).toBeInTheDocument();
  });

  it('applies selected styles when isSelected is true', () => {
    const { container } = render(
      <StorageTypeCard {...defaultProps} isSelected={true} />
    );

    const button = container.querySelector('button');
    expect(button?.className).toContain('border-aws-sea-blue');
  });

  it('applies disabled styles when isDisabled is true', () => {
    const { container } = render(
      <StorageTypeCard {...defaultProps} isDisabled={true} />
    );

    const button = container.querySelector('button');
    expect(button?.className).toContain('cursor-not-allowed');
    expect(button?.className).toContain('opacity-50');
  });
});
