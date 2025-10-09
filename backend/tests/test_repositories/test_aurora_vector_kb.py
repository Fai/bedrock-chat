import pytest
from unittest.mock import Mock, patch, MagicMock
from botocore.exceptions import ClientError

from app.repositories.aurora_vector_kb import (
    create_aurora_knowledge_base,
    query_aurora_knowledge_base,
    delete_aurora_knowledge_base,
    get_aurora_knowledge_base_status,
    _get_embeddings_model_arn,
    _get_parsing_model_arn,
    _build_chunking_configuration,
)
from app.repositories.models.custom_bot_kb import AuroraVectorConfigModel


@pytest.fixture
def mock_aurora_config():
    """Mock Aurora configuration for testing"""
    from app.repositories.models.custom_bot_kb import HierarchicalParamsModel
    
    chunking_config = HierarchicalParamsModel(
        chunking_strategy="hierarchical",
        max_parent_token_size=1500,
        max_child_token_size=300,
        overlap_tokens=60
    )

    return AuroraVectorConfigModel(
        cluster_name="test-cluster",
        cluster_arn="arn:aws:rds:us-east-1:123456789012:cluster:test-cluster",
        database_name="bedrock_kb",
        table_name="bedrock_integration.kb_vectors",
        secret_arn="arn:aws:secretsmanager:us-east-1:123456789012:secret:test-secret",
        embeddings_model="titan_v2",
        embedding_dimensions=1024,
        chunking_configuration=chunking_config,
        parsing_model="anthropic.claude-3-haiku-v1",
    )


class TestCreateAuroraKnowledgeBase:
    """Test Aurora Knowledge Base creation"""

    @patch.dict('os.environ', {'BEDROCK_KB_ROLE_ARN': 'arn:aws:iam::123456789012:role/BedrockKBRole'})
    @patch('app.repositories.aurora_vector_kb.get_bedrock_agent_client')
    def test_create_aurora_kb_success(self, mock_get_client, mock_aurora_config):
        """Test successful Aurora KB creation"""
        # Mock Bedrock client
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        
        # Mock create_knowledge_base response
        mock_client.create_knowledge_base.return_value = {
            'knowledgeBase': {'knowledgeBaseId': 'TEST123'}
        }
        
        # Mock create_data_source response
        mock_client.create_data_source.return_value = {
            'dataSource': {'dataSourceId': 'DS456'}
        }
        
        # Mock start_ingestion_job response
        mock_client.start_ingestion_job.return_value = {
            'ingestionJob': {'ingestionJobId': 'JOB789'}
        }

        # Call function
        kb_id, ds_id = create_aurora_knowledge_base(
            bot_id='bot-123',
            aurora_config=mock_aurora_config,
            kb_name='Test KB',
            document_bucket_arn='arn:aws:s3:::test-bucket'
        )

        # Assertions
        assert kb_id == 'TEST123'
        assert ds_id == 'DS456'
        
        # Verify create_knowledge_base was called with correct parameters
        mock_client.create_knowledge_base.assert_called_once()
        call_args = mock_client.create_knowledge_base.call_args[1]
        
        assert call_args['name'] == 'Test KB'
        assert call_args['description'] == 'Aurora Vector Knowledge Base for bot bot-123'
        assert call_args['knowledgeBaseConfiguration']['type'] == 'VECTOR'
        assert call_args['storageConfiguration']['type'] == 'RDS'
        assert call_args['storageConfiguration']['rdsConfiguration']['resourceArn'] == mock_aurora_config.cluster_arn

    @patch.dict('os.environ', {}, clear=True)
    def test_create_aurora_kb_missing_env_var(self, mock_aurora_config):
        """Test error when BEDROCK_KB_ROLE_ARN missing"""
        with pytest.raises(ValueError, match="BEDROCK_KB_ROLE_ARN environment variable is not set"):
            create_aurora_knowledge_base(
                bot_id='bot-123',
                aurora_config=mock_aurora_config,
                kb_name='Test KB',
                document_bucket_arn='arn:aws:s3:::test-bucket'
            )

    @patch.dict('os.environ', {'BEDROCK_KB_ROLE_ARN': 'arn:aws:iam::123456789012:role/BedrockKBRole'})
    @patch('app.repositories.aurora_vector_kb.get_bedrock_agent_client')
    def test_create_aurora_kb_bedrock_error(self, mock_get_client, mock_aurora_config):
        """Test error handling when Bedrock API fails"""
        # Mock Bedrock client to raise error
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        mock_client.create_knowledge_base.side_effect = ClientError(
            {'Error': {'Code': 'ValidationException', 'Message': 'Invalid cluster ARN'}},
            'CreateKnowledgeBase'
        )

        # Call function and expect exception
        with pytest.raises(ClientError):
            create_aurora_knowledge_base(
                bot_id='bot-123',
                aurora_config=mock_aurora_config,
                kb_name='Test KB',
                document_bucket_arn='arn:aws:s3:::test-bucket'
            )


class TestQueryAuroraKnowledgeBase:
    """Test Aurora Knowledge Base querying"""

    @patch('app.repositories.aurora_vector_kb.get_bedrock_agent_runtime_client')
    def test_query_aurora_kb_success(self, mock_get_client):
        """Test successful Aurora KB query"""
        # Mock Bedrock runtime client
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        
        # Mock retrieve response
        mock_client.retrieve.return_value = {
            'retrievalResults': [
                {
                    'score': 0.95,
                    'content': {'text': 'Aurora PostgreSQL is a managed database service...'},
                    'metadata': {'source': 'aurora-guide.pdf', 'page': 1},
                    'location': {'s3Location': {'uri': 's3://bucket/file.pdf'}}
                },
                {
                    'score': 0.87,
                    'content': {'text': 'pgvector extension provides vector similarity search...'},
                    'metadata': {'source': 'pgvector-docs.pdf', 'page': 5},
                    'location': {'s3Location': {'uri': 's3://bucket/pgvector.pdf'}}
                }
            ]
        }

        # Call function
        result = query_aurora_knowledge_base(
            knowledge_base_id='KB123',
            query='What is Aurora PostgreSQL?',
            max_results=5,
            min_similarity_score=0.7
        )

        # Assertions
        assert result['total_results'] == 2
        assert result['knowledge_base_id'] == 'KB123'
        assert len(result['citations']) == 2
        
        # Check first citation
        citation = result['citations'][0]
        assert citation['score'] == 0.95
        assert 'Aurora PostgreSQL' in citation['text']
        assert citation['metadata']['source'] == 'aurora-guide.pdf'

    @patch('app.repositories.aurora_vector_kb.get_bedrock_agent_runtime_client')
    def test_query_aurora_kb_with_filters(self, mock_get_client):
        """Test Aurora KB query with metadata filters"""
        # Mock Bedrock runtime client
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        mock_client.retrieve.return_value = {'retrievalResults': []}

        # Call function with metadata filter
        query_aurora_knowledge_base(
            knowledge_base_id='KB123',
            query='test query',
            metadata_filter={'bot_id': 'bot-123', 'document_type': 'user_guide'}
        )

        # Verify retrieve was called with correct filter
        mock_client.retrieve.assert_called_once()
        call_args = mock_client.retrieve.call_args[1]
        
        filter_config = call_args['retrievalConfiguration']['vectorSearchConfiguration']['filter']
        assert 'andAll' in filter_config
        assert len(filter_config['andAll']) == 2

    @patch('app.repositories.aurora_vector_kb.get_bedrock_agent_runtime_client')
    def test_query_aurora_kb_similarity_threshold(self, mock_get_client):
        """Test Aurora KB query with similarity score threshold"""
        # Mock Bedrock runtime client
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        
        # Mock retrieve response with mixed scores
        mock_client.retrieve.return_value = {
            'retrievalResults': [
                {'score': 0.95, 'content': {'text': 'High score result'}, 'metadata': {}},
                {'score': 0.65, 'content': {'text': 'Low score result'}, 'metadata': {}},
                {'score': 0.85, 'content': {'text': 'Medium score result'}, 'metadata': {}}
            ]
        }

        # Call function with similarity threshold
        result = query_aurora_knowledge_base(
            knowledge_base_id='KB123',
            query='test query',
            min_similarity_score=0.7
        )

        # Should only return results with score >= 0.7
        assert result['total_results'] == 2
        scores = [citation['score'] for citation in result['citations']]
        assert all(score >= 0.7 for score in scores)


class TestDeleteAuroraKnowledgeBase:
    """Test Aurora Knowledge Base deletion"""

    @patch('app.repositories.aurora_vector_kb.get_bedrock_agent_client')
    def test_delete_aurora_kb_success(self, mock_get_client):
        """Test successful Aurora KB deletion"""
        # Mock Bedrock client
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        
        # Mock list_data_sources response
        mock_client.list_data_sources.return_value = {
            'dataSourceSummaries': [
                {'dataSourceId': 'DS123'},
                {'dataSourceId': 'DS456'}
            ]
        }

        # Call function
        result = delete_aurora_knowledge_base('KB123')

        # Assertions
        assert result is True
        
        # Verify data sources were deleted
        assert mock_client.delete_data_source.call_count == 2
        mock_client.delete_data_source.assert_any_call(knowledgeBaseId='KB123', dataSourceId='DS123')
        mock_client.delete_data_source.assert_any_call(knowledgeBaseId='KB123', dataSourceId='DS456')
        
        # Verify knowledge base was deleted
        mock_client.delete_knowledge_base.assert_called_once_with(knowledgeBaseId='KB123')

    @patch('app.repositories.aurora_vector_kb.get_bedrock_agent_client')
    def test_delete_aurora_kb_error(self, mock_get_client):
        """Test error handling during Aurora KB deletion"""
        # Mock Bedrock client to raise error
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        mock_client.list_data_sources.side_effect = ClientError(
            {'Error': {'Code': 'ResourceNotFoundException', 'Message': 'KB not found'}},
            'ListDataSources'
        )

        # Call function and expect exception
        with pytest.raises(ClientError):
            delete_aurora_knowledge_base('KB123')


class TestGetAuroraKnowledgeBaseStatus:
    """Test Aurora Knowledge Base status retrieval"""

    @patch('app.repositories.aurora_vector_kb.get_bedrock_agent_client')
    def test_get_aurora_kb_status_success(self, mock_get_client):
        """Test successful Aurora KB status retrieval"""
        # Mock Bedrock client
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        
        # Mock get_knowledge_base response
        mock_client.get_knowledge_base.return_value = {
            'knowledgeBase': {
                'knowledgeBaseId': 'KB123',
                'name': 'Test Aurora KB',
                'status': 'ACTIVE',
                'description': 'Test description',
                'storageConfiguration': {
                    'type': 'RDS',
                    'rdsConfiguration': {
                        'resourceArn': 'arn:aws:rds:us-east-1:123456789012:cluster:test-cluster',
                        'databaseName': 'bedrock_kb',
                        'tableName': 'bedrock_integration.kb_vectors'
                    }
                },
                'knowledgeBaseConfiguration': {
                    'vectorKnowledgeBaseConfiguration': {
                        'embeddingModelArn': 'arn:aws:bedrock:us-east-1::foundation-model/amazon.titan-embed-text-v2:0'
                    }
                },
                'createdAt': '2025-10-08T12:00:00Z',
                'updatedAt': '2025-10-08T12:00:00Z'
            }
        }

        # Call function
        result = get_aurora_knowledge_base_status('KB123')

        # Assertions
        assert result['knowledge_base_id'] == 'KB123'
        assert result['name'] == 'Test Aurora KB'
        assert result['status'] == 'ACTIVE'
        assert result['storage_type'] == 'RDS'
        assert result['cluster_arn'] == 'arn:aws:rds:us-east-1:123456789012:cluster:test-cluster'
        assert result['database_name'] == 'bedrock_kb'
        assert result['table_name'] == 'bedrock_integration.kb_vectors'


class TestUtilityFunctions:
    """Test utility functions"""

    def test_get_embeddings_model_arn(self):
        """Test embeddings model ARN mapping"""
        with patch.dict('os.environ', {'BEDROCK_REGION': 'us-west-2'}):
            # Test titan_v2
            arn = _get_embeddings_model_arn('titan_v2')
            assert 'us-west-2' in arn
            assert 'amazon.titan-embed-text-v2:0' in arn
            
            # Test cohere
            arn = _get_embeddings_model_arn('cohere_multilingual_v3')
            assert 'us-west-2' in arn
            assert 'cohere.embed-multilingual-v3' in arn
            
            # Test default fallback
            arn = _get_embeddings_model_arn('unknown_model')
            assert 'amazon.titan-embed-text-v2:0' in arn

    def test_get_parsing_model_arn(self):
        """Test parsing model ARN mapping"""
        with patch.dict('os.environ', {'BEDROCK_REGION': 'us-west-2'}):
            # Test Claude Sonnet
            arn = _get_parsing_model_arn('anthropic.claude-3-5-sonnet-v1')
            assert 'us-west-2' in arn
            assert 'anthropic.claude-3-5-sonnet' in arn
            
            # Test Claude Haiku
            arn = _get_parsing_model_arn('anthropic.claude-3-haiku-v1')
            assert 'us-west-2' in arn
            assert 'anthropic.claude-3-haiku' in arn

    def test_build_chunking_configuration(self):
        """Test chunking configuration building"""
        # Test hierarchical chunking
        chunking_config = Mock()
        chunking_config.chunking_strategy = "hierarchical"
        chunking_config.max_parent_token_size = 1500
        chunking_config.max_child_token_size = 300
        chunking_config.overlap_tokens = 60
        
        result = _build_chunking_configuration(chunking_config)
        
        assert result['chunkingStrategy'] == 'HIERARCHICAL'
        assert result['hierarchicalChunkingConfiguration']['levelConfigurations'][0]['maxTokens'] == 1500
        assert result['hierarchicalChunkingConfiguration']['levelConfigurations'][1]['maxTokens'] == 300
        assert result['hierarchicalChunkingConfiguration']['overlapTokens'] == 60

        # Test fixed size chunking
        chunking_config.chunking_strategy = "fixed_size"
        chunking_config.max_tokens = 500
        chunking_config.overlap_percentage = 20
        
        result = _build_chunking_configuration(chunking_config)
        
        assert result['chunkingStrategy'] == 'FIXED_SIZE'
        assert result['fixedSizeChunkingConfiguration']['maxTokens'] == 500
        assert result['fixedSizeChunkingConfiguration']['overlapPercentage'] == 20

        # Test semantic chunking
        chunking_config.chunking_strategy = "semantic"
        chunking_config.max_tokens = 400
        chunking_config.buffer_size = 1
        chunking_config.breakpoint_percentile_threshold = 95
        
        result = _build_chunking_configuration(chunking_config)
        
        assert result['chunkingStrategy'] == 'SEMANTIC'
        assert result['semanticChunkingConfiguration']['maxTokens'] == 400
        assert result['semanticChunkingConfiguration']['bufferSize'] == 1
        assert result['semanticChunkingConfiguration']['breakpointPercentileThreshold'] == 95

        # Test default fallback
        chunking_config.chunking_strategy = "unknown"
        
        result = _build_chunking_configuration(chunking_config)
        
        assert result['chunkingStrategy'] == 'HIERARCHICAL'
        assert result['hierarchicalChunkingConfiguration']['levelConfigurations'][0]['maxTokens'] == 1500
