"""
Integration tests for Aurora Vector Knowledge Base

These tests require actual AWS resources and should be run in a test environment.
They are marked with @pytest.mark.integration to be excluded from unit test runs.
"""

import pytest
import os
import time
from unittest.mock import Mock

from app.repositories.aurora_vector_kb import (
    create_aurora_knowledge_base,
    query_aurora_knowledge_base,
    delete_aurora_knowledge_base,
    get_aurora_knowledge_base_status,
)
from app.repositories.models.custom_bot_kb import AuroraVectorConfigModel


@pytest.mark.integration
@pytest.mark.skipif(
    not os.getenv("RUN_INTEGRATION_TESTS"), 
    reason="Integration tests require RUN_INTEGRATION_TESTS=1"
)
class TestAuroraVectorKBIntegration:
    """Integration tests for Aurora Vector Knowledge Base"""

    @pytest.fixture(scope="class")
    def aurora_config(self):
        """Aurora configuration for integration tests"""
        # These values should be set in test environment
        cluster_arn = os.getenv("TEST_AURORA_CLUSTER_ARN")
        secret_arn = os.getenv("TEST_AURORA_SECRET_ARN")
        
        if not cluster_arn or not secret_arn:
            pytest.skip("TEST_AURORA_CLUSTER_ARN and TEST_AURORA_SECRET_ARN must be set for integration tests")

        chunking_config = Mock()
        chunking_config.chunking_strategy = "hierarchical"
        chunking_config.max_parent_token_size = 1500
        chunking_config.max_child_token_size = 300
        chunking_config.overlap_tokens = 60

        return AuroraVectorConfigModel(
            cluster_name="test-integration-cluster",
            cluster_arn=cluster_arn,
            database_name="bedrock_kb",
            table_name="bedrock_integration.kb_vectors",
            secret_arn=secret_arn,
            embeddings_model="titan_v2",
            embedding_dimensions=1024,
            chunking_configuration=chunking_config,
            parsing_model="anthropic.claude-3-haiku-v1",
        )

    @pytest.fixture(scope="class")
    def document_bucket_arn(self):
        """S3 bucket ARN for test documents"""
        bucket_arn = os.getenv("TEST_DOCUMENT_BUCKET_ARN")
        if not bucket_arn:
            pytest.skip("TEST_DOCUMENT_BUCKET_ARN must be set for integration tests")
        return bucket_arn

    def test_aurora_kb_lifecycle(self, aurora_config, document_bucket_arn):
        """Test complete Aurora KB lifecycle: create, query, delete"""
        kb_id = None
        
        try:
            # Step 1: Create Aurora Knowledge Base
            print("Creating Aurora Vector Knowledge Base...")
            kb_id, data_source_id = create_aurora_knowledge_base(
                bot_id="integration-test-bot",
                aurora_config=aurora_config,
                kb_name="Integration Test KB",
                document_bucket_arn=document_bucket_arn,
                document_prefix="test-docs/",
            )
            
            assert kb_id is not None
            assert isinstance(kb_id, str)
            print(f"✓ Created KB: {kb_id}")
            
            if data_source_id:
                print(f"✓ Created data source: {data_source_id}")

            # Step 2: Wait for KB to become active
            print("Waiting for KB to become active...")
            max_wait_time = 300  # 5 minutes
            start_time = time.time()
            
            while time.time() - start_time < max_wait_time:
                status_info = get_aurora_knowledge_base_status(kb_id)
                status = status_info.get("status")
                print(f"KB Status: {status}")
                
                if status == "ACTIVE":
                    break
                elif status == "FAILED":
                    pytest.fail(f"Knowledge Base creation failed: {status_info}")
                
                time.sleep(30)  # Wait 30 seconds before checking again
            else:
                pytest.fail("Knowledge Base did not become active within 5 minutes")

            print("✓ KB is active")

            # Step 3: Test querying (even without documents, should not error)
            print("Testing KB query...")
            query_result = query_aurora_knowledge_base(
                knowledge_base_id=kb_id,
                query="What is Aurora PostgreSQL?",
                max_results=5,
                min_similarity_score=0.0,
            )
            
            assert "citations" in query_result
            assert "total_results" in query_result
            assert "knowledge_base_id" in query_result
            assert query_result["knowledge_base_id"] == kb_id
            print(f"✓ Query returned {query_result['total_results']} results")

            # Step 4: Test query with metadata filter
            print("Testing KB query with metadata filter...")
            filtered_result = query_aurora_knowledge_base(
                knowledge_base_id=kb_id,
                query="test query",
                max_results=3,
                metadata_filter={"bot_id": "integration-test-bot"},
            )
            
            assert "citations" in filtered_result
            print("✓ Filtered query completed successfully")

        finally:
            # Step 5: Cleanup - Delete KB
            if kb_id:
                print(f"Cleaning up KB: {kb_id}")
                try:
                    success = delete_aurora_knowledge_base(kb_id)
                    if success:
                        print("✓ KB deleted successfully")
                    else:
                        print("⚠ KB deletion returned False")
                except Exception as e:
                    print(f"⚠ Error during cleanup: {e}")

    def test_aurora_kb_error_handling(self, aurora_config):
        """Test error handling with invalid parameters"""
        
        # Test with invalid bucket ARN
        with pytest.raises(Exception):  # Should raise ClientError or similar
            create_aurora_knowledge_base(
                bot_id="error-test-bot",
                aurora_config=aurora_config,
                kb_name="Error Test KB",
                document_bucket_arn="arn:aws:s3:::nonexistent-bucket-12345",
            )

        # Test querying non-existent KB
        with pytest.raises(Exception):  # Should raise ClientError
            query_aurora_knowledge_base(
                knowledge_base_id="NONEXISTENT123",
                query="test query",
            )

        # Test getting status of non-existent KB
        with pytest.raises(Exception):  # Should raise ClientError
            get_aurora_knowledge_base_status("NONEXISTENT123")

    @pytest.mark.performance
    def test_aurora_kb_performance(self, aurora_config, document_bucket_arn):
        """Test Aurora KB performance characteristics"""
        kb_id = None
        
        try:
            # Create KB
            kb_id, _ = create_aurora_knowledge_base(
                bot_id="perf-test-bot",
                aurora_config=aurora_config,
                kb_name="Performance Test KB",
                document_bucket_arn=document_bucket_arn,
            )

            # Wait for active status
            max_wait = 300
            start_time = time.time()
            while time.time() - start_time < max_wait:
                status_info = get_aurora_knowledge_base_status(kb_id)
                if status_info.get("status") == "ACTIVE":
                    break
                time.sleep(30)

            # Test query performance
            query_times = []
            for i in range(5):  # Run 5 queries
                start = time.time()
                query_aurora_knowledge_base(
                    knowledge_base_id=kb_id,
                    query=f"Performance test query {i}",
                    max_results=10,
                )
                query_time = (time.time() - start) * 1000  # Convert to ms
                query_times.append(query_time)
                print(f"Query {i+1}: {query_time:.2f}ms")

            # Performance assertions
            avg_query_time = sum(query_times) / len(query_times)
            max_query_time = max(query_times)
            
            print(f"Average query time: {avg_query_time:.2f}ms")
            print(f"Max query time: {max_query_time:.2f}ms")
            
            # Performance targets from implementation plan
            assert avg_query_time < 200, f"Average query time {avg_query_time:.2f}ms exceeds 200ms target"
            assert max_query_time < 500, f"Max query time {max_query_time:.2f}ms exceeds 500ms target"
            
            print("✓ Performance targets met")

        finally:
            if kb_id:
                try:
                    delete_aurora_knowledge_base(kb_id)
                except Exception as e:
                    print(f"Cleanup error: {e}")


if __name__ == "__main__":
    # Run integration tests directly
    pytest.main([__file__, "-v", "-m", "integration"])
