"""
Integration tests for S3 Vector Knowledge Base feature.

These tests verify the end-to-end flow of creating, using, and deleting
S3 Vector Knowledge Bases, including interactions with AWS Bedrock services.

Prerequisites:
- AWS credentials configured
- BEDROCK_KB_ROLE_ARN environment variable set
- Bedrock region that supports S3 Vectors (us-east-1, us-east-2, us-west-2, eu-central-1, ap-southeast-2)
- S3 bucket for document storage

Run: python3 -m pytest tests/integration/test_s3_vector_integration.py -v
"""

import os
import sys
import time
import unittest
from unittest.mock import patch

sys.path.insert(0, ".")

from app.repositories.s3_vector_kb import (
    create_s3_vector_knowledge_base,
    delete_s3_vector_knowledge_base,
    get_s3_vector_kb_info,
)
from app.repositories.models.custom_bot_kb import (
    DefaultParamsModel,
    FixedSizeParamsModel,
    HierarchicalParamsModel,
    SemanticParamsModel,
    NoneParamsModel,
)


class TestS3VectorKBIntegration(unittest.TestCase):
    """Integration tests for S3 Vector Knowledge Base operations."""

    @classmethod
    def setUpClass(cls):
        """Set up test environment variables."""
        # Check for required environment variables
        required_env_vars = {
            "BEDROCK_KB_ROLE_ARN": os.getenv("BEDROCK_KB_ROLE_ARN"),
            "DEFAULT_MODEL_ARN": os.getenv("DEFAULT_MODEL_ARN"),
            "BEDROCK_REGION": os.getenv("BEDROCK_REGION", "us-east-1"),
        }

        missing_vars = [k for k, v in required_env_vars.items() if not v]
        if missing_vars:
            raise unittest.SkipTest(
                f"Skipping integration tests. Missing environment variables: {', '.join(missing_vars)}"
            )

        cls.kb_role_arn = required_env_vars["BEDROCK_KB_ROLE_ARN"]
        cls.default_model_arn = required_env_vars["DEFAULT_MODEL_ARN"]
        cls.bedrock_region = required_env_vars["BEDROCK_REGION"]

        # Verify region supports S3 Vectors
        supported_regions = [
            "us-east-1",
            "us-east-2",
            "us-west-2",
            "eu-central-1",
            "ap-southeast-2",
        ]
        if cls.bedrock_region not in supported_regions:
            raise unittest.SkipTest(
                f"S3 Vectors not supported in region: {cls.bedrock_region}. "
                f"Supported regions: {', '.join(supported_regions)}"
            )

        cls.created_kbs = []  # Track created KBs for cleanup

    @classmethod
    def tearDownClass(cls):
        """Clean up any remaining knowledge bases."""
        for kb_id in cls.created_kbs:
            try:
                delete_s3_vector_knowledge_base(kb_id)
                print(f"Cleaned up KB: {kb_id}")
            except Exception as e:
                print(f"Failed to clean up KB {kb_id}: {e}")

    def test_01_create_s3_vector_kb_with_default_chunking(self):
        """Test creating S3 Vector KB with default chunking configuration."""
        kb_name = "integration-test-s3-vector-default"
        bot_id = "test-bot-001"
        document_bucket_arn = os.getenv(
            "TEST_DOCUMENT_BUCKET_ARN", f"arn:aws:s3:::test-bucket"
        )

        embeddings_config = EmbeddingsModel(model_id="titan_v2")

        chunking_config = ChunkingConfigurationModel(chunking_strategy="default")

        # Create KB
        kb_info = create_s3_vector_knowledge_base(
            bot_id=bot_id,
            kb_name=kb_name,
            embeddings_config=embeddings_config,
            chunking_config=chunking_config,
            document_bucket_arn=document_bucket_arn,
        )

        # Track for cleanup
        self.__class__.created_kbs.append(kb_info["knowledgeBaseId"])

        # Assertions
        self.assertIsNotNone(kb_info["knowledgeBaseId"])
        self.assertEqual(kb_info["status"], "ACTIVE")
        self.assertGreater(len(kb_info["dataSourceIds"]), 0)
        self.assertIn("knowledgeBaseArn", kb_info)

        print(f"✅ Created S3 Vector KB: {kb_info['knowledgeBaseId']}")

    def test_02_create_s3_vector_kb_with_fixed_size_chunking(self):
        """Test creating S3 Vector KB with fixed size chunking (500 tokens max for S3)."""
        kb_name = "integration-test-s3-vector-fixed"
        bot_id = "test-bot-002"
        document_bucket_arn = os.getenv(
            "TEST_DOCUMENT_BUCKET_ARN", f"arn:aws:s3:::test-bucket"
        )

        embeddings_config = EmbeddingsModel(model_id="titan_v2")

        chunking_config = ChunkingConfigurationModel(
            chunking_strategy="fixed_size", max_tokens=500, overlap_percentage=20
        )

        # Create KB
        kb_info = create_s3_vector_knowledge_base(
            bot_id=bot_id,
            kb_name=kb_name,
            embeddings_config=embeddings_config,
            chunking_config=chunking_config,
            document_bucket_arn=document_bucket_arn,
        )

        # Track for cleanup
        self.__class__.created_kbs.append(kb_info["knowledgeBaseId"])

        # Assertions
        self.assertIsNotNone(kb_info["knowledgeBaseId"])
        self.assertEqual(kb_info["status"], "ACTIVE")

        print(f"✅ Created S3 Vector KB with fixed chunking: {kb_info['knowledgeBaseId']}")

    def test_03_create_s3_vector_kb_with_cohere_embeddings(self):
        """Test creating S3 Vector KB with Cohere Multilingual V3 embeddings."""
        kb_name = "integration-test-s3-vector-cohere"
        bot_id = "test-bot-003"
        document_bucket_arn = os.getenv(
            "TEST_DOCUMENT_BUCKET_ARN", f"arn:aws:s3:::test-bucket"
        )

        embeddings_config = EmbeddingsModel(model_id="cohere_multilingual_v3")

        chunking_config = ChunkingConfigurationModel(chunking_strategy="default")

        # Create KB
        kb_info = create_s3_vector_knowledge_base(
            bot_id=bot_id,
            kb_name=kb_name,
            embeddings_config=embeddings_config,
            chunking_config=chunking_config,
            document_bucket_arn=document_bucket_arn,
        )

        # Track for cleanup
        self.__class__.created_kbs.append(kb_info["knowledgeBaseId"])

        # Assertions
        self.assertIsNotNone(kb_info["knowledgeBaseId"])
        self.assertEqual(kb_info["status"], "ACTIVE")

        print(f"✅ Created S3 Vector KB with Cohere: {kb_info['knowledgeBaseId']}")

    def test_04_get_s3_vector_kb_info(self):
        """Test retrieving S3 Vector KB information."""
        # Use KB from test_01
        if not self.__class__.created_kbs:
            self.skipTest("No KB created in previous tests")

        kb_id = self.__class__.created_kbs[0]

        # Get KB info
        kb_info = get_s3_vector_kb_info(kb_id)

        # Assertions
        self.assertEqual(kb_info["knowledgeBaseId"], kb_id)
        self.assertEqual(kb_info["status"], "ACTIVE")
        self.assertIn("knowledgeBaseArn", kb_info)
        self.assertIn("storageConfiguration", kb_info)
        self.assertEqual(kb_info["storageConfiguration"]["type"], "S3_VECTORS")

        print(f"✅ Retrieved S3 Vector KB info: {kb_id}")

    def test_05_delete_s3_vector_kb(self):
        """Test deleting S3 Vector KB."""
        # Create a temporary KB for deletion test
        kb_name = "integration-test-s3-vector-delete"
        bot_id = "test-bot-delete"
        document_bucket_arn = os.getenv(
            "TEST_DOCUMENT_BUCKET_ARN", f"arn:aws:s3:::test-bucket"
        )

        embeddings_config = EmbeddingsModel(model_id="titan_v2")
        chunking_config = ChunkingConfigurationModel(chunking_strategy="default")

        kb_info = create_s3_vector_knowledge_base(
            bot_id=bot_id,
            kb_name=kb_name,
            embeddings_config=embeddings_config,
            chunking_config=chunking_config,
            document_bucket_arn=document_bucket_arn,
        )

        kb_id = kb_info["knowledgeBaseId"]

        # Wait a moment for KB to be fully created
        time.sleep(2)

        # Delete KB
        delete_s3_vector_knowledge_base(kb_id)

        # Verify deletion (should raise error)
        with self.assertRaises(Exception):
            get_s3_vector_kb_info(kb_id)

        print(f"✅ Deleted S3 Vector KB: {kb_id}")

    def test_06_create_kb_with_document_prefix(self):
        """Test creating S3 Vector KB with specific document prefix."""
        kb_name = "integration-test-s3-vector-prefix"
        bot_id = "test-bot-006"
        document_bucket_arn = os.getenv(
            "TEST_DOCUMENT_BUCKET_ARN", f"arn:aws:s3:::test-bucket"
        )
        document_prefix = f"documents/user123/{bot_id}/"

        embeddings_config = EmbeddingsModel(model_id="titan_v2")
        chunking_config = ChunkingConfigurationModel(chunking_strategy="default")

        # Create KB
        kb_info = create_s3_vector_knowledge_base(
            bot_id=bot_id,
            kb_name=kb_name,
            embeddings_config=embeddings_config,
            chunking_config=chunking_config,
            document_bucket_arn=document_bucket_arn,
            document_prefix=document_prefix,
        )

        # Track for cleanup
        self.__class__.created_kbs.append(kb_info["knowledgeBaseId"])

        # Assertions
        self.assertIsNotNone(kb_info["knowledgeBaseId"])
        self.assertEqual(kb_info["status"], "ACTIVE")

        print(f"✅ Created S3 Vector KB with prefix: {kb_info['knowledgeBaseId']}")

    def test_07_create_kb_exceeding_500_token_limit_should_fail(self):
        """Test that creating KB with >500 token chunks fails for S3 Vectors."""
        kb_name = "integration-test-s3-vector-invalid"
        bot_id = "test-bot-007"
        document_bucket_arn = os.getenv(
            "TEST_DOCUMENT_BUCKET_ARN", f"arn:aws:s3:::test-bucket"
        )

        embeddings_config = EmbeddingsModel(model_id="titan_v2")

        # Try to create with 600 tokens (exceeds S3 Vector 500 token limit)
        chunking_config = ChunkingConfigurationModel(
            chunking_strategy="fixed_size", max_tokens=600, overlap_percentage=20
        )

        # This should raise an error
        with self.assertRaises(Exception) as context:
            create_s3_vector_knowledge_base(
                bot_id=bot_id,
                kb_name=kb_name,
                embeddings_config=embeddings_config,
                chunking_config=chunking_config,
                document_bucket_arn=document_bucket_arn,
            )

        print(f"✅ Correctly rejected >500 token chunking: {str(context.exception)}")


class TestS3VectorKBPerformance(unittest.TestCase):
    """Performance tests for S3 Vector KB operations."""

    def test_kb_creation_latency(self):
        """Measure KB creation time (should be <30 seconds for Quick Create)."""
        if not os.getenv("BEDROCK_KB_ROLE_ARN"):
            self.skipTest("BEDROCK_KB_ROLE_ARN not set")

        kb_name = "perf-test-s3-vector"
        bot_id = "perf-test-bot"
        document_bucket_arn = os.getenv(
            "TEST_DOCUMENT_BUCKET_ARN", f"arn:aws:s3:::test-bucket"
        )

        embeddings_config = EmbeddingsModel(model_id="titan_v2")
        chunking_config = ChunkingConfigurationModel(chunking_strategy="default")

        start_time = time.time()

        kb_info = create_s3_vector_knowledge_base(
            bot_id=bot_id,
            kb_name=kb_name,
            embeddings_config=embeddings_config,
            chunking_config=chunking_config,
            document_bucket_arn=document_bucket_arn,
        )

        creation_time = time.time() - start_time

        # Cleanup
        try:
            delete_s3_vector_knowledge_base(kb_info["knowledgeBaseId"])
        except:
            pass

        # Assertions
        self.assertLess(
            creation_time,
            60,
            f"KB creation took {creation_time:.2f}s (expected <60s for Quick Create)",
        )

        print(f"✅ KB creation time: {creation_time:.2f}s")


if __name__ == "__main__":
    unittest.main(verbosity=2)
