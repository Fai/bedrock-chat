import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import KnowledgeBaseStatusBadge from './KnowledgeBaseStatusBadge';

describe('KnowledgeBaseStatusBadge', () => {
  it('renders creating status correctly', () => {
    render(<KnowledgeBaseStatusBadge status="CREATING" />);
    expect(screen.getByText('Creating')).toBeInTheDocument();
  });

  it('renders active status correctly', () => {
    render(<KnowledgeBaseStatusBadge status="ACTIVE" />);
    expect(screen.getByText('Active')).toBeInTheDocument();
  });

  it('renders failed status correctly', () => {
    render(<KnowledgeBaseStatusBadge status="FAILED" />);
    expect(screen.getByText('Failed')).toBeInTheDocument();
  });

  it('renders ingestion starting status', () => {
    render(
      <KnowledgeBaseStatusBadge
        status="ACTIVE"
        ingestionJobStatus="STARTING"
      />
    );
    expect(screen.getByText('Starting Ingestion')).toBeInTheDocument();
  });

  it('renders ingestion in progress status', () => {
    render(
      <KnowledgeBaseStatusBadge
        status="ACTIVE"
        ingestionJobStatus="IN_PROGRESS"
      />
    );
    expect(screen.getByText('Ingesting Data')).toBeInTheDocument();
  });

  it('renders ingestion complete status as ready', () => {
    render(
      <KnowledgeBaseStatusBadge
        status="ACTIVE"
        ingestionJobStatus="COMPLETE"
      />
    );
    expect(screen.getByText('Ready')).toBeInTheDocument();
  });

  it('renders ingestion failed status', () => {
    render(
      <KnowledgeBaseStatusBadge status="ACTIVE" ingestionJobStatus="FAILED" />
    );
    expect(screen.getByText('Ingestion Failed')).toBeInTheDocument();
  });

  it('prioritizes ingestion status over KB status', () => {
    render(
      <KnowledgeBaseStatusBadge
        status="CREATING"
        ingestionJobStatus="COMPLETE"
      />
    );
    // Should show "Ready" from ingestion status, not "Creating" from KB status
    expect(screen.getByText('Ready')).toBeInTheDocument();
    expect(screen.queryByText('Creating')).not.toBeInTheDocument();
  });

  it('shows error message in title attribute when provided', () => {
    const { container } = render(
      <KnowledgeBaseStatusBadge
        status="FAILED"
        errorMessage="Connection timeout"
      />
    );
    const badge = container.querySelector('[title="Connection timeout"]');
    expect(badge).toBeInTheDocument();
  });

  it('renders failed status when error message is present', () => {
    render(
      <KnowledgeBaseStatusBadge
        status="ACTIVE"
        errorMessage="Something went wrong"
      />
    );
    // Error message should override active status
    expect(screen.getByText('Failed')).toBeInTheDocument();
  });

  it('renders not started status', () => {
    render(<KnowledgeBaseStatusBadge status="NOT_STARTED" />);
    expect(screen.getByText('Not Started')).toBeInTheDocument();
  });

  it('renders unknown status', () => {
    render(<KnowledgeBaseStatusBadge status="UNKNOWN" />);
    expect(screen.getByText('Unknown')).toBeInTheDocument();
  });

  it('renders updating status correctly', () => {
    render(<KnowledgeBaseStatusBadge status="UPDATING" />);
    expect(screen.getByText('Updating')).toBeInTheDocument();
  });

  it('renders deleting status correctly', () => {
    render(<KnowledgeBaseStatusBadge status="DELETING" />);
    expect(screen.getByText('Deleting')).toBeInTheDocument();
  });

  it('applies custom className', () => {
    const { container } = render(
      <KnowledgeBaseStatusBadge status="ACTIVE" className="custom-class" />
    );
    const badge = container.querySelector('.custom-class');
    expect(badge).toBeInTheDocument();
  });
});
