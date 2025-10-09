import os
import sys
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, ".")

from app.repositories.models.custom_bot_kb import (
    BedrockKnowledgeBaseModel,
    DefaultParamsModel,
    FixedSizeParamsModel,
    HierarchicalParamsModel,
    SearchParamsModel,
    SemanticParamsModel,
    NoneParamsModel,
)
from app.repositories.s3_vector_kb import (
    create_s3_vector_knowledge_base,
    delete_s3_vector_knowledge_base,
    get_s3_vector_kb_info,
    _get_embeddings_model_arn,
    _get_embedding_dimensions,
    _get_parsing_model_arn,
    _build_chunking_configuration,
)
from botocore.exceptions import ClientError


class TestS3VectorKB(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures"""
        self.kb_config = BedrockKnowledgeBaseModel(
            embeddings_model="titan_v2",
            storage_type="S3_VECTOR",
            chunking_configuration=DefaultParamsModel(chunking_strategy="default"),
            search_params=SearchParamsModel(max_results=5, search_type="semantic"),
            parsing_model="disabled",
        )

        self.document_bucket_arn = "arn:aws:s3:::test-document-bucket"
        self.document_prefix = "documents/user123/bot456"

    @patch.dict(
        os.environ,
        {
            "BEDROCK_KB_ROLE_ARN": "arn:aws:iam::123456789012:role/BedrockKbRole",
            "BEDROCK_REGION": "us-east-1",
        },
    )
    @patch("app.repositories.s3_vector_kb.get_bedrock_agent_client")
    def test_create_s3_vector_kb_success(self, mock_get_client):
        """Test successful S3 Vector KB creation with Quick Create"""
        # Mock Bedrock Agent client
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        # Mock create_knowledge_base response
        mock_client.create_knowledge_base.return_value = {
            "knowledgeBase": {"knowledgeBaseId": "test-kb-123"}
        }

        # Mock create_data_source response
        mock_client.create_data_source.return_value = {
            "dataSource": {"dataSourceId": "test-ds-456"}
        }

        # Mock start_ingestion_job response
        mock_client.start_ingestion_job.return_value = {
            "ingestionJob": {"ingestionJobId": "test-job-789"}
        }

        # Execute
        kb_id, data_source_id = create_s3_vector_knowledge_base(
            bot_id="test-bot-001",
            kb_config=self.kb_config,
            kb_name="test-s3-vector-kb",
            document_bucket_arn=self.document_bucket_arn,
            document_prefix=self.document_prefix,
        )

        # Assert
        self.assertEqual(kb_id, "test-kb-123")
        self.assertEqual(data_source_id, "test-ds-456")

        # Verify create_knowledge_base API call
        mock_client.create_knowledge_base.assert_called_once()
        call_kwargs = mock_client.create_knowledge_base.call_args[1]

        # Verify basic parameters
        self.assertEqual(call_kwargs["name"], "test-s3-vector-kb")
        self.assertEqual(
            call_kwargs["roleArn"], "arn:aws:iam::123456789012:role/BedrockKbRole"
        )
        self.assertEqual(call_kwargs["description"], "S3 Vector Knowledge Base for bot test-bot-001")

        # Verify knowledge base configuration
        kb_config = call_kwargs["knowledgeBaseConfiguration"]
        self.assertEqual(kb_config["type"], "VECTOR")
        self.assertEqual(
            kb_config["vectorKnowledgeBaseConfiguration"]["embeddingModelArn"],
            "arn:aws:bedrock:us-east-1::foundation-model/amazon.titan-embed-text-v2:0",
        )
        self.assertEqual(
            kb_config["vectorKnowledgeBaseConfiguration"]["embeddingModelConfiguration"][
                "bedrockEmbeddingModelConfiguration"
            ]["dimensions"],
            1024,
        )
        self.assertEqual(
            kb_config["vectorKnowledgeBaseConfiguration"]["embeddingModelConfiguration"][
                "bedrockEmbeddingModelConfiguration"
            ]["embeddingDataType"],
            "FLOAT32",
        )

        # Verify storage configuration (CRITICAL: must be S3_VECTORS)
        storage_config = call_kwargs["storageConfiguration"]
        self.assertEqual(storage_config["type"], "S3_VECTORS")
        self.assertIn("s3VectorsConfiguration", storage_config)
        # s3VectorsConfiguration should be empty dict for Quick Create
        self.assertEqual(storage_config["s3VectorsConfiguration"], {})

        # Verify data source creation
        mock_client.create_data_source.assert_called_once()
        ds_call_kwargs = mock_client.create_data_source.call_args[1]
        self.assertEqual(ds_call_kwargs["knowledgeBaseId"], "test-kb-123")
        self.assertEqual(ds_call_kwargs["dataSourceConfiguration"]["type"], "S3")
        self.assertEqual(
            ds_call_kwargs["dataSourceConfiguration"]["s3Configuration"]["bucketArn"],
            self.document_bucket_arn,
        )
        self.assertEqual(
            ds_call_kwargs["dataSourceConfiguration"]["s3Configuration"]["inclusionPrefixes"],
            [self.document_prefix],
        )

        # Verify ingestion job started
        mock_client.start_ingestion_job.assert_called_once_with(
            knowledgeBaseId="test-kb-123", dataSourceId="test-ds-456"
        )

    @patch("app.repositories.s3_vector_kb.get_bedrock_agent_client")
    def test_create_s3_vector_kb_missing_env_var(self, mock_get_client):
        """Test KB creation fails when BEDROCK_KB_ROLE_ARN is missing"""
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError) as context:
                create_s3_vector_knowledge_base(
                    bot_id="test-bot-001",
                    kb_config=self.kb_config,
                    kb_name="test-s3-vector-kb",
                    document_bucket_arn=self.document_bucket_arn,
                )

            self.assertIn("BEDROCK_KB_ROLE_ARN", str(context.exception))

    @patch.dict(
        os.environ,
        {
            "BEDROCK_KB_ROLE_ARN": "arn:aws:iam::123456789012:role/BedrockKbRole",
            "BEDROCK_REGION": "us-east-1",
        },
    )
    @patch("app.repositories.s3_vector_kb.get_bedrock_agent_client")
    def test_create_s3_vector_kb_with_cohere_embeddings(self, mock_get_client):
        """Test S3 Vector KB creation with Cohere embeddings model"""
        # Update config to use Cohere
        self.kb_config.embeddings_model = "cohere_multilingual_v3"

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_client.create_knowledge_base.return_value = {
            "knowledgeBase": {"knowledgeBaseId": "test-kb-123"}
        }
        mock_client.create_data_source.return_value = {
            "dataSource": {"dataSourceId": "test-ds-456"}
        }

        kb_id, _ = create_s3_vector_knowledge_base(
            bot_id="test-bot-001",
            kb_config=self.kb_config,
            kb_name="test-s3-vector-kb",
            document_bucket_arn=self.document_bucket_arn,
        )

        # Verify Cohere model ARN
        call_kwargs = mock_client.create_knowledge_base.call_args[1]
        self.assertIn(
            "cohere.embed-multilingual-v3",
            call_kwargs["knowledgeBaseConfiguration"]["vectorKnowledgeBaseConfiguration"][
                "embeddingModelArn"
            ],
        )

    @patch.dict(
        os.environ,
        {
            "BEDROCK_KB_ROLE_ARN": "arn:aws:iam::123456789012:role/BedrockKbRole",
            "BEDROCK_REGION": "us-east-1",
        },
    )
    @patch("app.repositories.s3_vector_kb.get_bedrock_agent_client")
    def test_create_s3_vector_kb_with_fixed_size_chunking(self, mock_get_client):
        """Test S3 Vector KB creation with fixed size chunking"""
        # Update config with fixed size chunking
        self.kb_config.chunking_configuration = FixedSizeParamsModel(
            chunking_strategy="fixed_size", max_tokens=500, overlap_percentage=20
        )

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_client.create_knowledge_base.return_value = {
            "knowledgeBase": {"knowledgeBaseId": "test-kb-123"}
        }
        mock_client.create_data_source.return_value = {
            "dataSource": {"dataSourceId": "test-ds-456"}
        }

        create_s3_vector_knowledge_base(
            bot_id="test-bot-001",
            kb_config=self.kb_config,
            kb_name="test-s3-vector-kb",
            document_bucket_arn=self.document_bucket_arn,
        )

        # Verify chunking configuration
        call_kwargs = mock_client.create_data_source.call_args[1]
        chunking_config = call_kwargs["vectorIngestionConfiguration"]["chunkingConfiguration"]
        self.assertEqual(chunking_config["chunkingStrategy"], "FIXED_SIZE")
        self.assertEqual(chunking_config["fixedSizeChunkingConfiguration"]["maxTokens"], 500)
        self.assertEqual(
            chunking_config["fixedSizeChunkingConfiguration"]["overlapPercentage"], 20
        )

    @patch.dict(
        os.environ,
        {
            "BEDROCK_KB_ROLE_ARN": "arn:aws:iam::123456789012:role/BedrockKbRole",
            "BEDROCK_REGION": "us-east-1",
        },
    )
    @patch("app.repositories.s3_vector_kb.get_bedrock_agent_client")
    def test_create_s3_vector_kb_with_hierarchical_chunking(self, mock_get_client):
        """Test S3 Vector KB creation with hierarchical chunking"""
        # Update config with hierarchical chunking
        self.kb_config.chunking_configuration = HierarchicalParamsModel(
            chunking_strategy="hierarchical",
            max_parent_token_size=400,
            max_child_token_size=200,
            overlap_tokens=50,
        )

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_client.create_knowledge_base.return_value = {
            "knowledgeBase": {"knowledgeBaseId": "test-kb-123"}
        }
        mock_client.create_data_source.return_value = {
            "dataSource": {"dataSourceId": "test-ds-456"}
        }

        create_s3_vector_knowledge_base(
            bot_id="test-bot-001",
            kb_config=self.kb_config,
            kb_name="test-s3-vector-kb",
            document_bucket_arn=self.document_bucket_arn,
        )

        # Verify hierarchical chunking configuration
        call_kwargs = mock_client.create_data_source.call_args[1]
        chunking_config = call_kwargs["vectorIngestionConfiguration"]["chunkingConfiguration"]
        self.assertEqual(chunking_config["chunkingStrategy"], "HIERARCHICAL")
        level_configs = chunking_config["hierarchicalChunkingConfiguration"]["levelConfigurations"]
        self.assertEqual(level_configs[0]["maxTokens"], 400)
        self.assertEqual(level_configs[1]["maxTokens"], 200)
        self.assertEqual(
            chunking_config["hierarchicalChunkingConfiguration"]["overlapTokens"], 50
        )

    @patch.dict(
        os.environ,
        {
            "BEDROCK_KB_ROLE_ARN": "arn:aws:iam::123456789012:role/BedrockKbRole",
            "BEDROCK_REGION": "us-east-1",
        },
    )
    @patch("app.repositories.s3_vector_kb.get_bedrock_agent_client")
    def test_create_s3_vector_kb_with_semantic_chunking(self, mock_get_client):
        """Test S3 Vector KB creation with semantic chunking"""
        # Update config with semantic chunking
        self.kb_config.chunking_configuration = SemanticParamsModel(
            chunking_strategy="semantic",
            max_tokens=300,
            buffer_size=1,
            breakpoint_percentile_threshold=95,
        )

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_client.create_knowledge_base.return_value = {
            "knowledgeBase": {"knowledgeBaseId": "test-kb-123"}
        }
        mock_client.create_data_source.return_value = {
            "dataSource": {"dataSourceId": "test-ds-456"}
        }

        create_s3_vector_knowledge_base(
            bot_id="test-bot-001",
            kb_config=self.kb_config,
            kb_name="test-s3-vector-kb",
            document_bucket_arn=self.document_bucket_arn,
        )

        # Verify semantic chunking configuration
        call_kwargs = mock_client.create_data_source.call_args[1]
        chunking_config = call_kwargs["vectorIngestionConfiguration"]["chunkingConfiguration"]
        self.assertEqual(chunking_config["chunkingStrategy"], "SEMANTIC")
        self.assertEqual(chunking_config["semanticChunkingConfiguration"]["maxTokens"], 300)
        self.assertEqual(chunking_config["semanticChunkingConfiguration"]["bufferSize"], 1)
        self.assertEqual(
            chunking_config["semanticChunkingConfiguration"]["breakpointPercentileThreshold"], 95
        )

    @patch.dict(
        os.environ,
        {
            "BEDROCK_KB_ROLE_ARN": "arn:aws:iam::123456789012:role/BedrockKbRole",
            "BEDROCK_REGION": "us-east-1",
        },
    )
    @patch("app.repositories.s3_vector_kb.get_bedrock_agent_client")
    def test_create_s3_vector_kb_with_parsing_model(self, mock_get_client):
        """Test S3 Vector KB creation with foundation model parsing"""
        # Update config to use Claude for parsing
        self.kb_config.parsing_model = "anthropic.claude-3-5-sonnet-v1"

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_client.create_knowledge_base.return_value = {
            "knowledgeBase": {"knowledgeBaseId": "test-kb-123"}
        }
        mock_client.create_data_source.return_value = {
            "dataSource": {"dataSourceId": "test-ds-456"}
        }

        create_s3_vector_knowledge_base(
            bot_id="test-bot-001",
            kb_config=self.kb_config,
            kb_name="test-s3-vector-kb",
            document_bucket_arn=self.document_bucket_arn,
        )

        # Verify parsing configuration
        call_kwargs = mock_client.create_data_source.call_args[1]
        parsing_config = call_kwargs["vectorIngestionConfiguration"]["parsingConfiguration"]
        self.assertEqual(parsing_config["parsingStrategy"], "BEDROCK_FOUNDATION_MODEL")
        self.assertIn(
            "claude-3-5-sonnet",
            parsing_config["bedrockFoundationModelConfiguration"]["modelArn"],
        )

    @patch.dict(
        os.environ,
        {
            "BEDROCK_KB_ROLE_ARN": "arn:aws:iam::123456789012:role/BedrockKbRole",
            "BEDROCK_REGION": "us-east-1",
        },
    )
    @patch("app.repositories.s3_vector_kb.get_bedrock_agent_client")
    def test_create_s3_vector_kb_without_prefix(self, mock_get_client):
        """Test S3 Vector KB creation without document prefix"""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_client.create_knowledge_base.return_value = {
            "knowledgeBase": {"knowledgeBaseId": "test-kb-123"}
        }
        mock_client.create_data_source.return_value = {
            "dataSource": {"dataSourceId": "test-ds-456"}
        }

        # Create without prefix
        create_s3_vector_knowledge_base(
            bot_id="test-bot-001",
            kb_config=self.kb_config,
            kb_name="test-s3-vector-kb",
            document_bucket_arn=self.document_bucket_arn,
            document_prefix="",  # Empty prefix
        )

        # Verify no inclusionPrefixes in data source config
        call_kwargs = mock_client.create_data_source.call_args[1]
        s3_config = call_kwargs["dataSourceConfiguration"]["s3Configuration"]
        self.assertNotIn("inclusionPrefixes", s3_config)

    @patch.dict(
        os.environ,
        {
            "BEDROCK_KB_ROLE_ARN": "arn:aws:iam::123456789012:role/BedrockKbRole",
            "BEDROCK_REGION": "us-east-1",
        },
    )
    @patch("app.repositories.s3_vector_kb.get_bedrock_agent_client")
    def test_create_s3_vector_kb_data_source_failure(self, mock_get_client):
        """Test S3 Vector KB creation when data source creation fails"""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        # KB creation succeeds
        mock_client.create_knowledge_base.return_value = {
            "knowledgeBase": {"knowledgeBaseId": "test-kb-123"}
        }

        # Data source creation fails
        mock_client.create_data_source.side_effect = ClientError(
            {"Error": {"Code": "ValidationException", "Message": "Invalid bucket ARN"}},
            "CreateDataSource",
        )

        # Execute - should not raise, returns KB ID with None data source
        kb_id, data_source_id = create_s3_vector_knowledge_base(
            bot_id="test-bot-001",
            kb_config=self.kb_config,
            kb_name="test-s3-vector-kb",
            document_bucket_arn="invalid-arn",
        )

        # Assert KB created but no data source
        self.assertEqual(kb_id, "test-kb-123")
        self.assertIsNone(data_source_id)

    @patch.dict(os.environ, {"BEDROCK_REGION": "us-east-1"})
    @patch("app.repositories.s3_vector_kb.get_bedrock_agent_client")
    def test_get_s3_vector_kb_info_success(self, mock_get_client):
        """Test retrieving S3 Vector KB info"""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_client.get_knowledge_base.return_value = {
            "knowledgeBase": {
                "knowledgeBaseId": "test-kb-123",
                "name": "test-s3-vector-kb",
                "storageConfiguration": {"type": "S3_VECTORS"},
            }
        }

        kb_info = get_s3_vector_kb_info("test-kb-123")

        self.assertEqual(kb_info["knowledgeBaseId"], "test-kb-123")
        self.assertEqual(kb_info["storageConfiguration"]["type"], "S3_VECTORS")
        mock_client.get_knowledge_base.assert_called_once_with(knowledgeBaseId="test-kb-123")

    @patch.dict(os.environ, {"BEDROCK_REGION": "us-east-1"})
    @patch("app.repositories.s3_vector_kb.get_bedrock_agent_client")
    def test_delete_s3_vector_kb_success(self, mock_get_client):
        """Test deleting S3 Vector KB"""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        # Mock list_data_sources response
        mock_client.list_data_sources.return_value = {
            "dataSourceSummaries": [
                {"dataSourceId": "test-ds-456"},
                {"dataSourceId": "test-ds-789"},
            ]
        }

        # Execute
        result = delete_s3_vector_knowledge_base("test-kb-123")

        # Assert
        self.assertTrue(result)

        # Verify data sources deleted
        self.assertEqual(mock_client.delete_data_source.call_count, 2)
        mock_client.delete_data_source.assert_any_call(
            knowledgeBaseId="test-kb-123", dataSourceId="test-ds-456"
        )
        mock_client.delete_data_source.assert_any_call(
            knowledgeBaseId="test-kb-123", dataSourceId="test-ds-789"
        )

        # Verify KB deleted
        mock_client.delete_knowledge_base.assert_called_once_with(
            knowledgeBaseId="test-kb-123"
        )

    def test_get_embeddings_model_arn_titan_v2(self):
        """Test embeddings model ARN mapping for Titan V2"""
        with patch.dict(os.environ, {"BEDROCK_REGION": "us-west-2"}):
            arn = _get_embeddings_model_arn("titan_v2")
            self.assertEqual(
                arn,
                "arn:aws:bedrock:us-west-2::foundation-model/amazon.titan-embed-text-v2:0",
            )

    def test_get_embeddings_model_arn_cohere(self):
        """Test embeddings model ARN mapping for Cohere"""
        with patch.dict(os.environ, {"BEDROCK_REGION": "eu-central-1"}):
            arn = _get_embeddings_model_arn("cohere_multilingual_v3")
            self.assertEqual(
                arn,
                "arn:aws:bedrock:eu-central-1::foundation-model/cohere.embed-multilingual-v3",
            )

    def test_get_embedding_dimensions(self):
        """Test embedding dimensions for different models"""
        self.assertEqual(_get_embedding_dimensions("titan_v2"), 1024)
        self.assertEqual(_get_embedding_dimensions("cohere_multilingual_v3"), 1024)
        self.assertEqual(_get_embedding_dimensions("unknown_model"), 1024)  # Default

    def test_get_parsing_model_arn(self):
        """Test parsing model ARN mapping"""
        with patch.dict(os.environ, {"BEDROCK_REGION": "us-east-1"}):
            arn = _get_parsing_model_arn("anthropic.claude-3-5-sonnet-v1")
            self.assertIn("claude-3-5-sonnet", arn)

    def test_build_chunking_configuration_default(self):
        """Test chunking configuration builder for default strategy"""
        config = DefaultParamsModel(chunking_strategy="default")
        result = _build_chunking_configuration(config)

        self.assertEqual(result["chunkingStrategy"], "HIERARCHICAL")
        self.assertIn("hierarchicalChunkingConfiguration", result)

    def test_build_chunking_configuration_none(self):
        """Test chunking configuration builder for none strategy"""
        config = NoneParamsModel(chunking_strategy="none")
        result = _build_chunking_configuration(config)

        self.assertEqual(result["chunkingStrategy"], "NONE")


if __name__ == "__main__":
    unittest.main()
