import React from 'react';
import { useTranslation } from 'react-i18next';
import InputText from '../../../components/InputText';
import { SqlDatabaseConfig } from '../types';

interface SqlDatabaseConfigFormProps {
  config: SqlDatabaseConfig;
  onChange: (config: SqlDatabaseConfig) => void;
  errors?: Record<string, string>;
}

const SqlDatabaseConfigForm: React.FC<SqlDatabaseConfigFormProps> = ({
  config,
  onChange,
  errors = {},
}) => {
  const { t } = useTranslation();

  const handleChange = (field: keyof SqlDatabaseConfig, value: string) => {
    onChange({
      ...config,
      [field]: value,
    });
  };

  const handleFieldMappingChange = (field: string, value: string) => {
    onChange({
      ...config,
      fieldMapping: {
        ...config.fieldMapping,
        [field]: value,
      },
    });
  };

  return (
    <div className="space-y-4" data-testid="sql-database-config">
      <div>
        <InputText
          label={t('knowledgeBaseSettings.sql.workgroupName.label')}
          value={config.workgroupName}
          onChange={(value) => handleChange('workgroupName', value)}
          placeholder={t('knowledgeBaseSettings.sql.workgroupName.placeholder')}
          errorMessage={errors.workgroupName}
          data-testid="workgroup-name-input"
        />
        <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
          {t('knowledgeBaseSettings.sql.workgroupName.help')}
        </p>
      </div>

      <div>
        <InputText
          label={t('knowledgeBaseSettings.sql.databaseName.label')}
          value={config.databaseName}
          onChange={(value) => handleChange('databaseName', value)}
          placeholder={t('knowledgeBaseSettings.sql.databaseName.placeholder')}
          errorMessage={errors.databaseName}
          data-testid="database-name-input"
        />
      </div>

      <div>
        <InputText
          label={t('knowledgeBaseSettings.sql.tableName.label')}
          value={config.tableName}
          onChange={(value) => handleChange('tableName', value)}
          placeholder={t('knowledgeBaseSettings.sql.tableName.placeholder')}
          errorMessage={errors.tableName}
          data-testid="table-name-input"
        />
      </div>

      <div>
        <InputText
          label={t('knowledgeBaseSettings.sql.secretArn.label')}
          value={config.secretArn}
          onChange={(value) => handleChange('secretArn', value)}
          placeholder={t('knowledgeBaseSettings.sql.secretArn.placeholder')}
          errorMessage={errors.secretArn}
          data-testid="secret-arn-input"
        />
        <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
          {t('knowledgeBaseSettings.sql.secretArn.help')}
        </p>
      </div>

      <div className="border-t pt-4">
        <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-3">
          {t('knowledgeBaseSettings.sql.fieldMapping.title')}
        </h4>
        <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
          {t('knowledgeBaseSettings.sql.fieldMapping.description')}
        </p>
        
        <div className="grid grid-cols-2 gap-4">
          <InputText
            label={t('knowledgeBaseSettings.sql.fieldMapping.id')}
            value={config.fieldMapping.id}
            onChange={(value) => handleFieldMappingChange('id', value)}
            placeholder="id"
            data-testid="field-mapping-id"
          />
          
          <InputText
            label={t('knowledgeBaseSettings.sql.fieldMapping.content')}
            value={config.fieldMapping.content}
            onChange={(value) => handleFieldMappingChange('content', value)}
            placeholder="content"
            data-testid="field-mapping-content"
          />
          
          <InputText
            label={t('knowledgeBaseSettings.sql.fieldMapping.metadata')}
            value={config.fieldMapping.metadata}
            onChange={(value) => handleFieldMappingChange('metadata', value)}
            placeholder="metadata"
            data-testid="field-mapping-metadata"
          />
          
          <InputText
            label={t('knowledgeBaseSettings.sql.fieldMapping.embedding')}
            value={config.fieldMapping.embedding}
            onChange={(value) => handleFieldMappingChange('embedding', value)}
            placeholder="embedding"
            data-testid="field-mapping-embedding"
          />
        </div>
      </div>
    </div>
  );
};

export default SqlDatabaseConfigForm;
