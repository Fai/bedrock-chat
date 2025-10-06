/**
 * Integration tests for StorageTypeSelector component.
 *
 * These tests verify the interaction between StorageTypeSelector and its child components,
 * as well as proper state management and regional validation logic.
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import StorageTypeSelector from '../components/StorageTypeSelector';

describe('StorageTypeSelector Integration Tests', () => {
  describe('Regional Validation Integration', () => {
    it('should disable S3 Vector and show availability info when region is unsupported', () => {
      const onChange = vi.fn();

      render(
        <StorageTypeSelector
          selectedStorageType="OPENSEARCH_SERVERLESS"
          onStorageTypeChange={onChange}
          bedrockRegion="ap-south-1" // Unsupported region
        />
      );

      // S3 Vector card should be disabled
      const s3Button = screen.getByText('S3 Vectors').closest('button');
      expect(s3Button).toHaveAttribute('disabled');

      // Should show regional availability warning
      expect(
        screen.getByText(/S3 Vectors is only available in:/)
      ).toBeInTheDocument();
      expect(screen.getByText(/ap-south-1/)).toBeInTheDocument();

      // Should not be clickable
      if (s3Button) {
        fireEvent.click(s3Button);
      }
      expect(onChange).not.toHaveBeenCalled();
    });

    it('should enable S3 Vector for all supported regions', () => {
      const supportedRegions = [
        'us-east-1',
        'us-east-2',
        'us-west-2',
        'eu-central-1',
        'ap-southeast-2',
      ];

      supportedRegions.forEach((region) => {
        const { unmount } = render(
          <StorageTypeSelector
            selectedStorageType="OPENSEARCH_SERVERLESS"
            onStorageTypeChange={vi.fn()}
            bedrockRegion={region}
          />
        );

        const s3Button = screen.getByText('S3 Vectors').closest('button');
        expect(s3Button).not.toHaveAttribute('disabled');

        // Should not show regional availability warning for supported regions
        expect(
          screen.queryByText(/S3 Vectors is only available in:/)
        ).not.toBeInTheDocument();

        unmount();
      });
    });
  });

  describe('Storage Type Selection Flow', () => {
    it('should complete full selection flow from OpenSearch to S3 Vector', async () => {
      const onChange = vi.fn();

      const { rerender } = render(
        <StorageTypeSelector
          selectedStorageType="OPENSEARCH_SERVERLESS"
          onStorageTypeChange={onChange}
          bedrockRegion="us-east-1"
        />
      );

      // Initial state: OpenSearch selected
      const openSearchCard = screen
        .getByText('OpenSearch Serverless')
        .closest('button');
      expect(openSearchCard?.querySelector('svg')).toBeInTheDocument(); // Checkmark

      // Should not show warning banner initially
      expect(screen.queryByText('Preview Feature')).not.toBeInTheDocument();

      // Click S3 Vector card
      const s3Card = screen.getByText('S3 Vectors').closest('button');
      if (s3Card) {
        fireEvent.click(s3Card);
      }

      // Verify callback was called with correct value
      expect(onChange).toHaveBeenCalledWith('S3_VECTOR');
      expect(onChange).toHaveBeenCalledTimes(1);

      // Simulate parent component updating state
      rerender(
        <StorageTypeSelector
          selectedStorageType="S3_VECTOR"
          onStorageTypeChange={onChange}
          bedrockRegion="us-east-1"
        />
      );

      // Now S3 Vector should be selected
      const s3CardAfter = screen.getByText('S3 Vectors').closest('button');
      expect(s3CardAfter?.querySelector('svg')).toBeInTheDocument(); // Checkmark

      // Warning banner should appear
      await waitFor(() => {
        expect(screen.getByText('Preview Feature')).toBeInTheDocument();
        expect(screen.getByText('Key Limitations')).toBeInTheDocument();
      });
    });

    it('should switch back from S3 Vector to OpenSearch', () => {
      const onChange = vi.fn();

      const { rerender } = render(
        <StorageTypeSelector
          selectedStorageType="S3_VECTOR"
          onStorageTypeChange={onChange}
          bedrockRegion="us-east-1"
        />
      );

      // Warning banner should be visible
      expect(screen.getByText('Preview Feature')).toBeInTheDocument();

      // Click OpenSearch card
      const openSearchCard = screen
        .getByText('OpenSearch Serverless')
        .closest('button');
      if (openSearchCard) {
        fireEvent.click(openSearchCard);
      }

      expect(onChange).toHaveBeenCalledWith('OPENSEARCH_SERVERLESS');

      // Simulate state update
      rerender(
        <StorageTypeSelector
          selectedStorageType="OPENSEARCH_SERVERLESS"
          onStorageTypeChange={onChange}
          bedrockRegion="us-east-1"
        />
      );

      // Warning banner should disappear
      expect(screen.queryByText('Preview Feature')).not.toBeInTheDocument();
    });
  });

  describe('Warning Banner Integration', () => {
    it('should show comprehensive warning information when S3 Vector is selected', () => {
      render(
        <StorageTypeSelector
          selectedStorageType="S3_VECTOR"
          onStorageTypeChange={vi.fn()}
          bedrockRegion="us-east-1"
        />
      );

      // Preview warning
      expect(screen.getByText('Preview Feature')).toBeInTheDocument();
      expect(
        screen.getByText(/S3 Vectors is currently in preview/)
      ).toBeInTheDocument();

      // Key limitations
      expect(screen.getByText('Key Limitations')).toBeInTheDocument();
      expect(screen.getByText(/Regional Availability:/)).toBeInTheDocument();
      expect(screen.getByText(/Search Type:/)).toBeInTheDocument();
      expect(screen.getByText(/Chunking Limit:/)).toBeInTheDocument();
      expect(screen.getByText(/Query Latency:/)).toBeInTheDocument();

      // Best for section
      expect(screen.getByText('Best For')).toBeInTheDocument();
      expect(
        screen.getByText(/Development, testing, cost-sensitive workloads/)
      ).toBeInTheDocument();
    });
  });

  describe('Cost Comparison Display', () => {
    it('should display cost information for both storage types', () => {
      render(
        <StorageTypeSelector
          selectedStorageType="OPENSEARCH_SERVERLESS"
          onStorageTypeChange={vi.fn()}
          bedrockRegion="us-east-1"
        />
      );

      // Cost comparison section
      expect(
        screen.getByText(/Storage Cost Comparison/)
      ).toBeInTheDocument();

      // OpenSearch cost (appears in both card and comparison)
      expect(screen.getAllByText(/~\$88\/month/).length).toBeGreaterThan(0);

      // S3 Vector cost (appears in both card and comparison)
      expect(screen.getAllByText(/~\$0\.13\/month/).length).toBeGreaterThan(0);

      // Cost savings
      expect(
        screen.getByText(/S3 Vectors saves 99\.85% on storage costs/)
      ).toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('should handle missing bedrockRegion gracefully', () => {
      const onChange = vi.fn();

      render(
        <StorageTypeSelector
          selectedStorageType="OPENSEARCH_SERVERLESS"
          onStorageTypeChange={onChange}
        />
      );

      // S3 Vector should be disabled when region is missing
      const s3Button = screen.getByText('S3 Vectors').closest('button');
      expect(s3Button).toHaveAttribute('disabled');

      // Should show availability info
      expect(
        screen.getByText(/S3 Vectors is only available in:/)
      ).toBeInTheDocument();
    });

    it('should handle rapid selection changes', () => {
      const onChange = vi.fn();

      render(
        <StorageTypeSelector
          selectedStorageType="OPENSEARCH_SERVERLESS"
          onStorageTypeChange={onChange}
          bedrockRegion="us-east-1"
        />
      );

      const s3Button = screen.getByText('S3 Vectors').closest('button');
      const openSearchButton = screen
        .getByText('OpenSearch Serverless')
        .closest('button');

      // Rapid clicks
      if (s3Button) fireEvent.click(s3Button);
      if (openSearchButton) fireEvent.click(openSearchButton);
      if (s3Button) fireEvent.click(s3Button);

      // Should have been called 3 times
      expect(onChange).toHaveBeenCalledTimes(3);
      expect(onChange).toHaveBeenNthCalledWith(1, 'S3_VECTOR');
      expect(onChange).toHaveBeenNthCalledWith(2, 'OPENSEARCH_SERVERLESS');
      expect(onChange).toHaveBeenNthCalledWith(3, 'S3_VECTOR');
    });

    it('should maintain selection when region changes to supported region', () => {
      const onChange = vi.fn();

      const { rerender } = render(
        <StorageTypeSelector
          selectedStorageType="S3_VECTOR"
          onStorageTypeChange={onChange}
          bedrockRegion="us-east-1"
        />
      );

      // S3 Vector should be enabled
      let s3Button = screen.getByText('S3 Vectors').closest('button');
      expect(s3Button).not.toHaveAttribute('disabled');

      // Change to another supported region
      rerender(
        <StorageTypeSelector
          selectedStorageType="S3_VECTOR"
          onStorageTypeChange={onChange}
          bedrockRegion="eu-central-1"
        />
      );

      // Should still be enabled
      s3Button = screen.getByText('S3 Vectors').closest('button');
      expect(s3Button).not.toHaveAttribute('disabled');

      // Selection should remain (onChange not called)
      expect(onChange).not.toHaveBeenCalled();
    });

    it('should show disabled state when region changes to unsupported', () => {
      const { rerender } = render(
        <StorageTypeSelector
          selectedStorageType="S3_VECTOR"
          onStorageTypeChange={vi.fn()}
          bedrockRegion="us-east-1"
        />
      );

      // Initially enabled
      let s3Button = screen.getByText('S3 Vectors').closest('button');
      expect(s3Button).not.toHaveAttribute('disabled');

      // Change to unsupported region
      rerender(
        <StorageTypeSelector
          selectedStorageType="S3_VECTOR"
          onStorageTypeChange={vi.fn()}
          bedrockRegion="ap-south-1"
        />
      );

      // Should now be disabled
      s3Button = screen.getByText('S3 Vectors').closest('button');
      expect(s3Button).toHaveAttribute('disabled');

      // Should show regional warning
      expect(
        screen.getByText(/S3 Vectors is only available in:/)
      ).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('should have proper button roles and accessibility attributes', () => {
      render(
        <StorageTypeSelector
          selectedStorageType="OPENSEARCH_SERVERLESS"
          onStorageTypeChange={vi.fn()}
          bedrockRegion="us-east-1"
        />
      );

      const buttons = screen.getAllByRole('button');
      expect(buttons.length).toBeGreaterThanOrEqual(2);

      buttons.forEach((button) => {
        expect(button).toHaveAttribute('type', 'button');
      });
    });

    it('should provide descriptive title for disabled S3 Vector option', () => {
      render(
        <StorageTypeSelector
          selectedStorageType="OPENSEARCH_SERVERLESS"
          onStorageTypeChange={vi.fn()}
          bedrockRegion="ap-south-1"
        />
      );

      const s3Button = screen.getByText('S3 Vectors').closest('button');
      const title = s3Button?.getAttribute('title');

      expect(title).toContain('ap-south-1');
      expect(title).toContain('Supported regions:');
      expect(title).toContain('us-east-1');
    });
  });
});
