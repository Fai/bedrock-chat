import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import SqlResultsTable from './SqlResultsTable';

describe('SqlResultsTable', () => {
  const mockResults = [
    { id: 1, name: 'Alice', age: 30, email: 'alice@example.com' },
    { id: 2, name: 'Bob', age: 25, email: 'bob@example.com' },
    { id: 3, name: 'Charlie', age: 35, email: 'charlie@example.com' },
  ];

  const mockSqlQuery =
    'SELECT id, name, age, email FROM users WHERE age > 20';

  it('renders table with correct data', () => {
    render(<SqlResultsTable results={mockResults} />);

    // Check headers (rendered as lowercase but styled as uppercase)
    expect(screen.getByText('id')).toBeInTheDocument();
    expect(screen.getByText('name')).toBeInTheDocument();
    expect(screen.getByText('age')).toBeInTheDocument();
    expect(screen.getByText('email')).toBeInTheDocument();

    // Check data
    expect(screen.getByText('Alice')).toBeInTheDocument();
    expect(screen.getByText('Bob')).toBeInTheDocument();
    expect(screen.getByText('Charlie')).toBeInTheDocument();
    expect(screen.getByText('alice@example.com')).toBeInTheDocument();
  });

  it('displays SQL query in collapsible section', () => {
    render(<SqlResultsTable results={mockResults} sqlQuery={mockSqlQuery} />);

    expect(screen.getByText('▶ Show SQL Query')).toBeInTheDocument();
    expect(screen.getByText(mockSqlQuery)).toBeInTheDocument();
  });

  it('shows row count', () => {
    render(<SqlResultsTable results={mockResults} />);
    expect(screen.getByText('3 rows returned')).toBeInTheDocument();
  });

  it('shows singular row text for single row', () => {
    const singleResult = [mockResults[0]];
    render(<SqlResultsTable results={singleResult} />);
    expect(screen.getByText('1 row returned')).toBeInTheDocument();
  });

  it('renders empty state when no results', () => {
    render(<SqlResultsTable results={[]} />);
    expect(
      screen.getByText('No results returned from query')
    ).toBeInTheDocument();
  });

  it('truncates results when maxRows is exceeded', () => {
    const manyResults = Array.from({ length: 150 }, (_, i) => ({
      id: i + 1,
      name: `User ${i + 1}`,
    }));

    render(<SqlResultsTable results={manyResults} maxRows={100} />);

    expect(screen.getByText('Showing 100 of 150 results')).toBeInTheDocument();
    expect(screen.getByText('User 1')).toBeInTheDocument();
    expect(screen.getByText('User 100')).toBeInTheDocument();
    expect(screen.queryByText('User 101')).not.toBeInTheDocument();
  });

  it('does not show truncation message when under maxRows', () => {
    render(<SqlResultsTable results={mockResults} maxRows={100} />);
    expect(
      screen.queryByText(/Showing \d+ of \d+ results/)
    ).not.toBeInTheDocument();
  });

  it('formats null values as dash', () => {
    const resultsWithNull = [{ id: 1, name: 'Test', value: null }];
    render(<SqlResultsTable results={resultsWithNull} />);

    const cells = screen.getAllByText('-');
    expect(cells.length).toBeGreaterThan(0);
  });

  it('formats boolean values correctly', () => {
    const resultsWithBoolean = [
      { id: 1, active: true, verified: false },
    ];
    render(<SqlResultsTable results={resultsWithBoolean} />);

    expect(screen.getByText('true')).toBeInTheDocument();
    expect(screen.getByText('false')).toBeInTheDocument();
  });

  it('formats numbers with locale formatting', () => {
    const resultsWithNumbers = [{ id: 1, revenue: 1234567.89 }];
    render(<SqlResultsTable results={resultsWithNumbers} />);

    // Number should be formatted with commas
    expect(screen.getByText(/1,234,567/)).toBeInTheDocument();
  });

  it('formats object values as JSON', () => {
    const resultsWithObject = [
      { id: 1, metadata: { key: 'value', nested: { data: 123 } } },
    ];
    render(<SqlResultsTable results={resultsWithObject} />);

    expect(screen.getByText(/"key":"value"/)).toBeInTheDocument();
  });

  it('applies custom className', () => {
    const { container } = render(
      <SqlResultsTable results={mockResults} className="custom-table" />
    );

    expect(container.querySelector('.custom-table')).toBeInTheDocument();
  });

  it('renders without SQL query section when sqlQuery is not provided', () => {
    render(<SqlResultsTable results={mockResults} />);

    expect(screen.queryByText('Show SQL Query')).not.toBeInTheDocument();
  });

  it('handles undefined values gracefully', () => {
    const resultsWithUndefined = [{ id: 1, name: undefined }];
    render(<SqlResultsTable results={resultsWithUndefined} />);

    // Should render dash for undefined
    expect(screen.getAllByText('-').length).toBeGreaterThan(0);
  });

  it('extracts columns from first result object', () => {
    const customResults = [
      { customCol1: 'A', customCol2: 'B' },
      { customCol1: 'C', customCol2: 'D', extraCol: 'E' }, // Extra column in second row
    ];
    render(<SqlResultsTable results={customResults} />);

    // Should only show columns from first row
    expect(screen.getByText('customCol1')).toBeInTheDocument();
    expect(screen.getByText('customCol2')).toBeInTheDocument();
    expect(screen.queryByText('extraCol')).not.toBeInTheDocument();
  });
});
