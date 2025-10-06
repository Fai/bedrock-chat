import {
  KnowledgeBaseStatusInfo,
  SqlDatabaseConfig,
  SqlKnowledgeBase,
  SqlQueryResult,
} from '../features/knowledgeBase/types';
import useHttp from './useHttp';

export type CreateSqlKnowledgeBaseRequest = {
  knowledgeBaseType: 'SQL';
  databaseConfig: SqlDatabaseConfig;
  searchParams: {
    maxResults: number;
    searchType: 'hybrid' | 'semantic';
  };
  embeddingModelArn?: string;
};

export type CreateSqlKnowledgeBaseResponse = SqlKnowledgeBase & {
  status: string;
};

export type QuerySqlKnowledgeBaseRequest = {
  query: string;
  maxResults?: number;
};

export type DeleteKnowledgeBaseResponse = {
  success: boolean;
  message: string;
};

const useSqlKnowledgeBaseApi = () => {
  const http = useHttp();

  return {
    /**
     * Create SQL Knowledge Base for a bot
     */
    createSqlKnowledgeBase: (
      botId: string,
      params: CreateSqlKnowledgeBaseRequest
    ) => {
      return http.post<CreateSqlKnowledgeBaseResponse>(
        `bot/${botId}/knowledge-base/sql`,
        params
      );
    },

    /**
     * Get Knowledge Base ingestion status
     */
    getKnowledgeBaseStatus: (botId: string, knowledgeBaseId: string) => {
      return http.get<KnowledgeBaseStatusInfo>(
        `bot/${botId}/knowledge-base/status?knowledge_base_id=${knowledgeBaseId}`,
        {
          refreshInterval: (data?: KnowledgeBaseStatusInfo) => {
            // Poll every 5 seconds if KB is being created or ingestion is in progress
            if (
              data?.status === 'CREATING' ||
              data?.ingestionJobStatus === 'STARTING' ||
              data?.ingestionJobStatus === 'IN_PROGRESS'
            ) {
              return 5000;
            }
            return 0;
          },
        }
      );
    },

    /**
     * Query SQL Knowledge Base with natural language
     */
    querySqlKnowledgeBase: (
      botId: string,
      knowledgeBaseId: string,
      params: QuerySqlKnowledgeBaseRequest
    ) => {
      return http.post<SqlQueryResult>(
        `bot/${botId}/knowledge-base/query?knowledge_base_id=${knowledgeBaseId}`,
        params
      );
    },

    /**
     * Delete SQL Knowledge Base
     */
    deleteKnowledgeBase: (botId: string, knowledgeBaseId: string) => {
      return http.delete<DeleteKnowledgeBaseResponse>(
        `bot/${botId}/knowledge-base?knowledge_base_id=${knowledgeBaseId}`
      );
    },
  };
};

export default useSqlKnowledgeBaseApi;
