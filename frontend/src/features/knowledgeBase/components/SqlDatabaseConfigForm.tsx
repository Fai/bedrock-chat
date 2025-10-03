import React, { useMemo } from 'react';
import InputText from '../../../components/InputText';
import { SqlDatabaseConfig } from '../types';

type Props = {
  config: SqlDatabaseConfig;
  onChange: (config: SqlDatabaseConfig) => void;
  errors?: Partial<Record<keyof SqlDatabaseConfig | 'fieldMapping', string>>;
};

const SqlDatabaseConfigForm: React.FC<Props> = ({
  config,
  onChange,
  errors = {},
}) => {
  const handleChange = <K extends keyof SqlDatabaseConfig>(
    key: K,
    value: SqlDatabaseConfig[K]
  ) => {
    onChange({
      ...config,
      [key]: value,
    });
  };

  const handleFieldMappingChange = (
    field: keyof SqlDatabaseConfig['fieldMapping'],
    value: string
  ) => {
    onChange({
      ...config,
      fieldMapping: {
        ...config.fieldMapping,
        [field]: value,
      },
    });
  };

  // Validate Redshift workgroup ARN format
  const workgroupArnHint = useMemo(() => {
    if (
      config.workgroupArn &&
      !config.workgroupArn.match(
        /^arn:aws:redshift-serverless:[a-z0-9-]+:\d{12}:workgroup\/.+$/
      )
    ) {
      return 'Expected format: arn:aws:redshift-serverless:REGION:ACCOUNT:workgroup/NAME';
    }
    return undefined;
  }, [config.workgroupArn]);

  // Validate secret ARN format
  const secretArnHint = useMemo(() => {
    if (
      config.secretArn &&
      !config.secretArn.match(
        /^arn:aws:secretsmanager:[a-z0-9-]+:\d{12}:secret:.+$/
      )
    ) {
      return 'Expected format: arn:aws:secretsmanager:REGION:ACCOUNT:secret/NAME';
    }
    return undefined;
  }, [config.secretArn]);

  return (
    <div className="flex flex-col gap-4">
      <div className="text-sm text-dark-gray dark:text-light-gray">
        Configure the connection to your Amazon Redshift Serverless database.
        The database table must have columns for id, content, and metadata.
      </div>

      <InputText
        label="Workgroup Name *"
        value={config.workgroupName}
        onChange={(value) => handleChange('workgroupName', value)}
        placeholder="my-redshift-workgroup"
        hint="The name of your Redshift Serverless workgroup"
        errorMessage={errors.workgroupName}
      />

      <InputText
        label="Workgroup ARN *"
        value={config.workgroupArn}
        onChange={(value) => handleChange('workgroupArn', value)}
        placeholder="arn:aws:redshift-serverless:us-east-1:123456789012:workgroup/my-workgroup"
        hint={
          workgroupArnHint ||
          'The full ARN of your Redshift Serverless workgroup'
        }
        errorMessage={errors.workgroupArn}
      />

      <InputText
        label="Database Name *"
        value={config.databaseName}
        onChange={(value) => handleChange('databaseName', value)}
        placeholder="mydatabase"
        hint="The name of the database containing your data"
        errorMessage={errors.databaseName}
      />

      <InputText
        label="Table/View Name *"
        value={config.tableName}
        onChange={(value) => handleChange('tableName', value)}
        placeholder="my_table"
        hint="The table or view name that Bedrock KB will query"
        errorMessage={errors.tableName}
      />

      <InputText
        label="Secret ARN *"
        value={config.secretArn}
        onChange={(value) => handleChange('secretArn', value)}
        placeholder="arn:aws:secretsmanager:us-east-1:123456789012:secret:my-secret"
        hint={
          secretArnHint ||
          'AWS Secrets Manager ARN containing Redshift credentials'
        }
        errorMessage={errors.secretArn}
      />

      <div className="mt-4 border-t pt-4 dark:border-aws-font-color-dark/30">
        <div className="mb-2 text-sm font-semibold text-dark-gray dark:text-light-gray">
          Field Mapping *
        </div>
        <div className="mb-3 text-xs text-gray dark:text-aws-font-color-dark">
          Map your table columns to the required Bedrock Knowledge Base fields.
          These mappings tell Bedrock how to interpret your data.
        </div>

        <div className="flex flex-col gap-3">
          <InputText
            label="ID Column"
            value={config.fieldMapping.id}
            onChange={(value) => handleFieldMappingChange('id', value)}
            placeholder="id"
            hint="Column containing unique identifiers (primary key)"
            errorMessage={errors.fieldMapping}
          />

          <InputText
            label="Content Column"
            value={config.fieldMapping.content}
            onChange={(value) => handleFieldMappingChange('content', value)}
            placeholder="content"
            hint="Column containing the main text content for semantic search"
            errorMessage={errors.fieldMapping}
          />

          <InputText
            label="Metadata Column"
            value={config.fieldMapping.metadata}
            onChange={(value) => handleFieldMappingChange('metadata', value)}
            placeholder="metadata"
            hint="Column containing additional metadata (JSON format recommended)"
            errorMessage={errors.fieldMapping}
          />
        </div>
      </div>
    </div>
  );
};

export default SqlDatabaseConfigForm;
