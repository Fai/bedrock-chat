import React, { useMemo } from 'react';
import { twMerge } from 'tailwind-merge';

type Props = {
  results: Array<Record<string, unknown>>;
  sqlQuery?: string | null;
  maxRows?: number;
  className?: string;
};

const SqlResultsTable: React.FC<Props> = ({
  results,
  sqlQuery,
  maxRows = 100,
  className,
}) => {
  // Extract column headers from the first result
  const columns = useMemo(() => {
    if (!results || results.length === 0) {
      return [];
    }
    return Object.keys(results[0]);
  }, [results]);

  // Limit rows for display
  const displayResults = useMemo(() => {
    return results.slice(0, maxRows);
  }, [results, maxRows]);

  const isTruncated = results.length > maxRows;

  if (!results || results.length === 0) {
    return (
      <div className="rounded border border-gray/30 bg-gray/5 p-4 text-center text-sm text-gray dark:border-aws-font-color-dark/30 dark:bg-aws-ui-color-dark/50">
        No results returned from query
      </div>
    );
  }

  return (
    <div className={twMerge('flex flex-col gap-2', className)}>
      {sqlQuery && (
        <details className="group rounded border border-blue/30 bg-blue/5 dark:border-blue/50 dark:bg-blue/10">
          <summary className="cursor-pointer px-3 py-2 text-sm font-mono text-blue hover:bg-blue/10 dark:hover:bg-blue/20">
            <span className="select-none group-open:hidden">▶ Show SQL Query</span>
            <span className="select-none group-open:inline hidden">▼ Hide SQL Query</span>
          </summary>
          <pre className="overflow-x-auto border-t border-blue/30 bg-blue/5 px-3 py-2 text-xs font-mono dark:border-blue/50 dark:bg-aws-ui-color-dark">
            {sqlQuery}
          </pre>
        </details>
      )}

      <div className="overflow-x-auto rounded border dark:border-aws-font-color-dark/30">
        <table className="min-w-full divide-y divide-gray/20 dark:divide-aws-font-color-dark/20">
          <thead className="bg-gray/10 dark:bg-aws-ui-color-dark/50">
            <tr>
              {columns.map((column) => (
                <th
                  key={column}
                  scope="col"
                  className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wider text-dark-gray dark:text-light-gray">
                  {column}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray/10 bg-white dark:divide-aws-font-color-dark/10 dark:bg-aws-ui-color-dark">
            {displayResults.map((row, rowIndex) => (
              <tr
                key={rowIndex}
                className="hover:bg-gray/5 dark:hover:bg-aws-ui-color-dark/30">
                {columns.map((column) => (
                  <td
                    key={`${rowIndex}-${column}`}
                    className="whitespace-nowrap px-3 py-2 text-sm text-aws-font-color-light dark:text-aws-font-color-dark">
                    {formatCellValue(row[column])}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {isTruncated && (
        <div className="text-center text-xs text-gray dark:text-aws-font-color-dark">
          Showing {maxRows} of {results.length} results
        </div>
      )}

      <div className="text-xs text-gray dark:text-aws-font-color-dark">
        {results.length} row{results.length !== 1 ? 's' : ''} returned
      </div>
    </div>
  );
};

/**
 * Format cell value for display
 */
function formatCellValue(value: unknown): string {
  if (value === null || value === undefined) {
    return '-';
  }

  if (typeof value === 'object') {
    try {
      return JSON.stringify(value);
    } catch {
      return String(value);
    }
  }

  if (typeof value === 'boolean') {
    return value ? 'true' : 'false';
  }

  if (typeof value === 'number') {
    // Format numbers with commas for readability
    return value.toLocaleString();
  }

  return String(value);
}

export default SqlResultsTable;
