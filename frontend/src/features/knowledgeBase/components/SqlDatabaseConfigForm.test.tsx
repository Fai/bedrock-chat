import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import SqlDatabaseConfigForm from './SqlDatabaseConfigForm';
import { SqlDatabaseConfig } from '../types';

describe('SqlDatabaseConfigForm', () => {
  const mockConfig: SqlDatabaseConfig = {
    workgroupName: 'test-workgroup',
    workgroupArn:
      'arn:aws:redshift-serverless:us-east-1:123456789012:workgroup/test-workgroup',
    databaseName: 'test_database',
    tableName: 'test_table',
    fieldMapping: {
      id: 'id',
      content: 'content',
      metadata: 'metadata',
    },
    secretArn:
      'arn:aws:secretsmanager:us-east-1:123456789012:secret:test-secret',
  };

  it('renders all form fields with correct values', () => {
    const onChange = vi.fn();
    render(<SqlDatabaseConfigForm config={mockConfig} onChange={onChange} />);

    expect(screen.getByDisplayValue('test-workgroup')).toBeInTheDocument();
    expect(
      screen.getByDisplayValue(
        'arn:aws:redshift-serverless:us-east-1:123456789012:workgroup/test-workgroup'
      )
    ).toBeInTheDocument();
    expect(screen.getByDisplayValue('test_database')).toBeInTheDocument();
    expect(screen.getByDisplayValue('test_table')).toBeInTheDocument();
    expect(
      screen.getByDisplayValue(
        'arn:aws:secretsmanager:us-east-1:123456789012:secret:test-secret'
      )
    ).toBeInTheDocument();
  });

  it('calls onChange when workgroup name changes', () => {
    const onChange = vi.fn();
    render(<SqlDatabaseConfigForm config={mockConfig} onChange={onChange} />);

    const input = screen.getByDisplayValue('test-workgroup');
    fireEvent.change(input, { target: { value: 'new-workgroup' } });

    expect(onChange).toHaveBeenCalledWith({
      ...mockConfig,
      workgroupName: 'new-workgroup',
    });
  });

  it('calls onChange when database name changes', () => {
    const onChange = vi.fn();
    render(<SqlDatabaseConfigForm config={mockConfig} onChange={onChange} />);

    const input = screen.getByDisplayValue('test_database');
    fireEvent.change(input, { target: { value: 'new_database' } });

    expect(onChange).toHaveBeenCalledWith({
      ...mockConfig,
      databaseName: 'new_database',
    });
  });

  it('calls onChange when field mapping changes', () => {
    const onChange = vi.fn();
    render(<SqlDatabaseConfigForm config={mockConfig} onChange={onChange} />);

    // Find the ID field mapping input (there are 3 inputs with "id" - need the right one)
    const inputs = screen.getAllByDisplayValue('id');
    const idInput = inputs[0]; // First one is the ID column mapping

    fireEvent.change(idInput, { target: { value: 'user_id' } });

    expect(onChange).toHaveBeenCalledWith({
      ...mockConfig,
      fieldMapping: {
        ...mockConfig.fieldMapping,
        id: 'user_id',
      },
    });
  });

  it('displays error messages when provided', () => {
    const onChange = vi.fn();
    const errors = {
      workgroupName: 'Workgroup name is required',
      databaseName: 'Database name is required',
    };

    render(
      <SqlDatabaseConfigForm
        config={mockConfig}
        onChange={onChange}
        errors={errors}
      />
    );

    expect(screen.getByText('Workgroup name is required')).toBeInTheDocument();
    expect(screen.getByText('Database name is required')).toBeInTheDocument();
  });

  it('displays validation hint for invalid workgroup ARN', () => {
    const onChange = vi.fn();
    const invalidConfig = {
      ...mockConfig,
      workgroupArn: 'invalid-arn',
    };

    render(
      <SqlDatabaseConfigForm config={invalidConfig} onChange={onChange} />
    );

    expect(
      screen.getByText(/Expected format: arn:aws:redshift-serverless/)
    ).toBeInTheDocument();
  });

  it('displays validation hint for invalid secret ARN', () => {
    const onChange = vi.fn();
    const invalidConfig = {
      ...mockConfig,
      secretArn: 'invalid-secret-arn',
    };

    render(
      <SqlDatabaseConfigForm config={invalidConfig} onChange={onChange} />
    );

    expect(
      screen.getByText(/Expected format: arn:aws:secretsmanager/)
    ).toBeInTheDocument();
  });

  it('renders field mapping section with correct labels', () => {
    const onChange = vi.fn();
    render(<SqlDatabaseConfigForm config={mockConfig} onChange={onChange} />);

    expect(screen.getByText('Field Mapping *')).toBeInTheDocument();
    expect(screen.getByText('ID Column')).toBeInTheDocument();
    expect(screen.getByText('Content Column')).toBeInTheDocument();
    expect(screen.getByText('Metadata Column')).toBeInTheDocument();
  });

  it('displays helpful hints for each field', () => {
    const onChange = vi.fn();
    const validConfig = mockConfig;

    render(
      <SqlDatabaseConfigForm config={validConfig} onChange={onChange} />
    );

    expect(
      screen.getByText('The name of your Redshift Serverless workgroup')
    ).toBeInTheDocument();
    expect(
      screen.getByText('The name of the database containing your data')
    ).toBeInTheDocument();
    expect(
      screen.getByText('Column containing unique identifiers (primary key)')
    ).toBeInTheDocument();
  });
});
