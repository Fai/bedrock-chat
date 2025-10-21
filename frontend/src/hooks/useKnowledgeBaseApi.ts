import useHttp from './useHttp';

type KnowledgeBaseDetails = {
  knowledgeBaseId: string;
  type: 'VECTOR' | 'SQL';
};

const useKnowledgeBaseApi = () => {
  const http = useHttp();

  return {
    getKnowledgeBaseDetails: async (knowledgeBaseId: string): Promise<KnowledgeBaseDetails> => {
      const response = await http.get<KnowledgeBaseDetails>(`knowledge-base/${knowledgeBaseId}`);
      if (!response.data) {
        throw new Error('No data received from knowledge base API');
      }
      return response.data;
    },
  };
};

export default useKnowledgeBaseApi;
