import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import S3VectorWarningBanner from './S3VectorWarningBanner';

describe('S3VectorWarningBanner', () => {
  it('renders preview warning section', () => {
    render(<S3VectorWarningBanner />);
    expect(screen.getByText('Preview Feature')).toBeInTheDocument();
    expect(
      screen.getByText(/S3 Vectors is currently in preview/)
    ).toBeInTheDocument();
  });

  it('renders key limitations section', () => {
    render(<S3VectorWarningBanner />);
    expect(screen.getByText('Key Limitations')).toBeInTheDocument();
  });

  it('renders regional availability limitation', () => {
    render(<S3VectorWarningBanner />);
    expect(screen.getByText(/Regional Availability:/)).toBeInTheDocument();
    expect(screen.getByText(/Only available in us-east-1/)).toBeInTheDocument();
  });

  it('renders search type limitation', () => {
    render(<S3VectorWarningBanner />);
    expect(screen.getByText(/Search Type:/)).toBeInTheDocument();
    expect(screen.getByText(/Semantic search only/)).toBeInTheDocument();
  });

  it('renders chunking limit limitation', () => {
    render(<S3VectorWarningBanner />);
    expect(screen.getByText(/Chunking Limit:/)).toBeInTheDocument();
    expect(screen.getByText(/Maximum 500 tokens/)).toBeInTheDocument();
  });

  it('renders query latency limitation', () => {
    render(<S3VectorWarningBanner />);
    expect(screen.getByText(/Query Latency:/)).toBeInTheDocument();
    expect(screen.getByText(/Sub-second response time/)).toBeInTheDocument();
  });

  it('renders best for section', () => {
    render(<S3VectorWarningBanner />);
    expect(screen.getByText('Best For')).toBeInTheDocument();
    expect(
      screen.getByText(/Development, testing, cost-sensitive workloads/)
    ).toBeInTheDocument();
  });

  it('recommends OpenSearch for production', () => {
    render(<S3VectorWarningBanner />);
    expect(
      screen.getByText(/consider OpenSearch Serverless/)
    ).toBeInTheDocument();
  });

  it('applies custom className', () => {
    const { container } = render(
      <S3VectorWarningBanner className="custom-class" />
    );
    const banner = container.querySelector('.custom-class');
    expect(banner).toBeInTheDocument();
  });

  it('displays warning and info icons', () => {
    const { container } = render(<S3VectorWarningBanner />);
    const icons = container.querySelectorAll('svg');
    // Should have multiple icons (warning and info)
    expect(icons.length).toBeGreaterThan(0);
  });

  it('lists all supported regions', () => {
    render(<S3VectorWarningBanner />);
    const supportedRegions = [
      'us-east-1',
      'us-east-2',
      'us-west-2',
      'eu-central-1',
      'ap-southeast-2',
    ];

    // Check each region appears in the document
    supportedRegions.forEach((region) => {
      expect(screen.getByText(new RegExp(region))).toBeInTheDocument();
    });
  });
});
