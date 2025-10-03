import os
import sys
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, ".")

from app.repositories.models.custom_bot_kb import SqlDatabaseConfigModel
from app.repositories.sql_knowledge_base import (
    create_sql_knowledge_base,
    delete_sql_knowledge_base,
    extract_results_from_citations,
    extract_sql_from_citations,
    get_ingestion_job_status,
    query_sql_knowledge_base,
)
from app.routes.schemas.bot_kb import SqlQueryOutput


class TestSqlKnowledgeBase(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures"""
        self.sql_config = SqlDatabaseConfigModel(
            workgroup_name="test-workgroup",
            workgroup_arn="arn:aws:redshift-serverless:us-east-1:123456789012:workgroup/test-workgroup",
            database_name="test_database",
            table_name="test_table",
            field_mapping={"id": "id", "content": "content", "metadata": "metadata"},
            secret_arn="arn:aws:secretsmanager:us-east-1:123456789012:secret:test-secret",
            embedding_model_arn="arn:aws:bedrock:us-east-1::foundation-model/amazon.titan-embed-text-v2:0",
        )

    @patch.dict(os.environ, {"BEDROCK_KB_ROLE_ARN": "arn:aws:iam::123456789012:role/BedrockKbRole"})
    @patch("app.repositories.sql_knowledge_base.get_bedrock_agent_client")
    def test_create_sql_knowledge_base_success(self, mock_get_client):
        """Test successful SQL KB creation"""
        # Mock Bedrock Agent client
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        # Mock create_knowledge_base response
        mock_client.create_knowledge_base.return_value = {
            "knowledgeBase": {"knowledgeBaseId": "test-kb-123"}
        }

        # Mock get_knowledge_base response
        mock_client.get_knowledge_base.return_value = {
            "knowledgeBase": {"knowledgeBaseId": "test-kb-123"}
        }

        # Mock list_data_sources response
        mock_client.list_data_sources.return_value = {
            "dataSourceSummaries": [{"dataSourceId": "test-ds-456"}]
        }

        # Mock start_ingestion_job response
        mock_client.start_ingestion_job.return_value = {
            "ingestionJob": {"ingestionJobId": "test-job-789"}
        }

        # Execute
        kb_id, data_source_id = create_sql_knowledge_base(
            bot_id="test-bot-001",
            sql_config=self.sql_config,
            kb_name="test-sql-kb",
        )

        # Assert
        self.assertEqual(kb_id, "test-kb-123")
        self.assertEqual(data_source_id, "test-ds-456")

        # Verify API calls
        mock_client.create_knowledge_base.assert_called_once()
        call_kwargs = mock_client.create_knowledge_base.call_args[1]
        self.assertEqual(call_kwargs["name"], "test-sql-kb")
        self.assertEqual(call_kwargs["roleArn"], "arn:aws:iam::123456789012:role/BedrockKbRole")
        self.assertEqual(call_kwargs["knowledgeBaseConfiguration"]["type"], "VECTOR")
        self.assertEqual(call_kwargs["storageConfiguration"]["type"], "REDSHIFT")

        # Verify Redshift configuration
        redshift_config = call_kwargs["storageConfiguration"]["redshiftConfiguration"]
        self.assertEqual(redshift_config["workgroupName"], "test-workgroup")
        self.assertEqual(redshift_config["databaseName"], "test_database")
        self.assertEqual(redshift_config["tableName"], "test_table")
        self.assertEqual(redshift_config["fieldMapping"]["primaryKeyField"], "id")
        self.assertEqual(redshift_config["fieldMapping"]["textField"], "content")
        self.assertEqual(redshift_config["fieldMapping"]["metadataField"], "metadata")

        mock_client.start_ingestion_job.assert_called_once_with(
            knowledgeBaseId="test-kb-123", dataSourceId="test-ds-456"
        )

    @patch("app.repositories.sql_knowledge_base.get_bedrock_agent_client")
    def test_create_sql_knowledge_base_missing_env_var(self, mock_get_client):
        """Test KB creation fails when BEDROCK_KB_ROLE_ARN is missing"""
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError) as context:
                create_sql_knowledge_base(
                    bot_id="test-bot-001",
                    sql_config=self.sql_config,
                    kb_name="test-sql-kb",
                )

            self.assertIn("BEDROCK_KB_ROLE_ARN", str(context.exception))

    @patch.dict(os.environ, {"BEDROCK_KB_ROLE_ARN": "arn:aws:iam::123456789012:role/BedrockKbRole"})
    @patch("app.repositories.sql_knowledge_base.get_bedrock_agent_client")
    def test_create_sql_knowledge_base_no_data_source(self, mock_get_client):
        """Test KB creation when no data source is returned"""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_client.create_knowledge_base.return_value = {
            "knowledgeBase": {"knowledgeBaseId": "test-kb-123"}
        }

        mock_client.get_knowledge_base.return_value = {
            "knowledgeBase": {"knowledgeBaseId": "test-kb-123"}
        }

        # Empty data sources list
        mock_client.list_data_sources.return_value = {"dataSourceSummaries": []}

        kb_id, data_source_id = create_sql_knowledge_base(
            bot_id="test-bot-001",
            sql_config=self.sql_config,
            kb_name="test-sql-kb",
        )

        self.assertEqual(kb_id, "test-kb-123")
        self.assertEqual(data_source_id, "")
        mock_client.start_ingestion_job.assert_not_called()

    @patch("app.repositories.sql_knowledge_base.get_bedrock_agent_client")
    def test_get_ingestion_job_status_success(self, mock_get_client):
        """Test getting ingestion job status"""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_client.list_ingestion_jobs.return_value = {
            "ingestionJobSummaries": [
                {
                    "ingestionJobId": "test-job-789",
                    "status": "IN_PROGRESS",
                    "startedAt": "2025-10-02T10:00:00Z",
                    "updatedAt": "2025-10-02T10:05:00Z",
                    "statistics": {"documentsScanned": 100, "documentsFailed": 0},
                }
            ]
        }

        result = get_ingestion_job_status(
            knowledge_base_id="test-kb-123", data_source_id="test-ds-456"
        )

        self.assertEqual(result["status"], "IN_PROGRESS")
        self.assertEqual(result["ingestion_job_id"], "test-job-789")
        self.assertEqual(result["ingestion_job_status"], "IN_PROGRESS")
        self.assertEqual(result["statistics"]["documentsScanned"], 100)

    @patch("app.repositories.sql_knowledge_base.get_bedrock_agent_client")
    def test_get_ingestion_job_status_complete(self, mock_get_client):
        """Test getting completed ingestion job status"""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_client.list_ingestion_jobs.return_value = {
            "ingestionJobSummaries": [
                {
                    "ingestionJobId": "test-job-789",
                    "status": "COMPLETE",
                    "startedAt": "2025-10-02T10:00:00Z",
                    "updatedAt": "2025-10-02T10:10:00Z",
                }
            ]
        }

        result = get_ingestion_job_status(
            knowledge_base_id="test-kb-123", data_source_id="test-ds-456"
        )

        self.assertEqual(result["status"], "ACTIVE")
        self.assertEqual(result["ingestion_job_status"], "COMPLETE")

    @patch("app.repositories.sql_knowledge_base.get_bedrock_agent_client")
    def test_get_ingestion_job_status_not_started(self, mock_get_client):
        """Test getting status when no ingestion jobs exist"""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_client.list_ingestion_jobs.return_value = {"ingestionJobSummaries": []}

        result = get_ingestion_job_status(
            knowledge_base_id="test-kb-123", data_source_id="test-ds-456"
        )

        self.assertEqual(result["status"], "NOT_STARTED")
        self.assertIsNone(result["ingestion_job_id"])

    @patch("app.repositories.sql_knowledge_base.get_bedrock_agent_client")
    def test_get_ingestion_job_status_error(self, mock_get_client):
        """Test error handling in get_ingestion_job_status"""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_client.list_ingestion_jobs.side_effect = Exception("API Error")

        result = get_ingestion_job_status(
            knowledge_base_id="test-kb-123", data_source_id="test-ds-456"
        )

        self.assertEqual(result["status"], "UNKNOWN")
        self.assertIn("error", result)

    @patch.dict(
        os.environ,
        {
            "DEFAULT_MODEL_ARN": "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-5-sonnet-20241022-v2:0"
        },
    )
    @patch("app.repositories.sql_knowledge_base.get_bedrock_agent_runtime_client")
    def test_query_sql_knowledge_base_success(self, mock_get_client):
        """Test successful SQL KB query"""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_client.retrieve_and_generate.return_value = {
            "output": {"text": "The total sales for Q4 2024 is $1,234,567.89"},
            "citations": [
                {
                    "retrievedReferences": [
                        {
                            "metadata": {
                                "sql_query": "SELECT SUM(sales_amount) FROM sales WHERE quarter = 'Q4' AND year = 2024",
                                "total_sales": "1234567.89",
                            },
                            "content": {"text": "SQL query result data"},
                        }
                    ]
                }
            ],
        }

        result = query_sql_knowledge_base(
            knowledge_base_id="test-kb-123",
            query="What were the total sales for Q4 2024?",
            user_id="test-user",
            max_results=10,
        )

        self.assertIsInstance(result, SqlQueryOutput)
        self.assertIn("$1,234,567.89", result.answer)
        self.assertIsNotNone(result.sql_query)
        self.assertIn("SELECT", result.sql_query)
        self.assertIsNotNone(result.results)

        # Verify API call
        mock_client.retrieve_and_generate.assert_called_once()
        call_kwargs = mock_client.retrieve_and_generate.call_args[1]
        self.assertEqual(call_kwargs["input"]["text"], "What were the total sales for Q4 2024?")
        self.assertEqual(
            call_kwargs["retrieveAndGenerateConfiguration"]["knowledgeBaseConfiguration"][
                "knowledgeBaseId"
            ],
            "test-kb-123",
        )

    @patch("app.repositories.sql_knowledge_base.get_bedrock_agent_runtime_client")
    def test_query_sql_knowledge_base_error(self, mock_get_client):
        """Test error handling in query_sql_knowledge_base"""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_client.retrieve_and_generate.side_effect = Exception("Query failed")

        with self.assertRaises(Exception) as context:
            query_sql_knowledge_base(
                knowledge_base_id="test-kb-123",
                query="Test query",
                user_id="test-user",
            )

        self.assertIn("Query failed", str(context.exception))

    @patch("app.repositories.sql_knowledge_base.get_bedrock_agent_client")
    def test_delete_sql_knowledge_base_success(self, mock_get_client):
        """Test successful KB deletion"""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        result = delete_sql_knowledge_base(knowledge_base_id="test-kb-123")

        self.assertTrue(result)
        mock_client.delete_knowledge_base.assert_called_once_with(
            knowledgeBaseId="test-kb-123"
        )

    @patch("app.repositories.sql_knowledge_base.get_bedrock_agent_client")
    def test_delete_sql_knowledge_base_error(self, mock_get_client):
        """Test error handling in KB deletion"""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_client.delete_knowledge_base.side_effect = Exception("Deletion failed")

        result = delete_sql_knowledge_base(knowledge_base_id="test-kb-123")

        self.assertFalse(result)

    def test_extract_sql_from_citations_with_metadata(self):
        """Test SQL extraction from citation metadata"""
        citations = [
            {
                "retrievedReferences": [
                    {
                        "metadata": {
                            "sql_query": "SELECT * FROM users WHERE id = 1",
                        }
                    }
                ]
            }
        ]

        result = extract_sql_from_citations(citations)

        self.assertEqual(result, "SELECT * FROM users WHERE id = 1")

    def test_extract_sql_from_citations_with_content(self):
        """Test SQL extraction from citation content"""
        citations = [
            {
                "retrievedReferences": [
                    {
                        "metadata": {},
                        "content": {"text": "SELECT COUNT(*) FROM orders WHERE status = 'completed'"},
                    }
                ]
            }
        ]

        result = extract_sql_from_citations(citations)

        self.assertIn("SELECT", result)
        self.assertIn("FROM", result)

    def test_extract_sql_from_citations_no_sql(self):
        """Test SQL extraction when no SQL is present"""
        citations = [
            {"retrievedReferences": [{"metadata": {}, "content": {"text": "No SQL here"}}]}
        ]

        result = extract_sql_from_citations(citations)

        self.assertIsNone(result)

    def test_extract_sql_from_citations_empty(self):
        """Test SQL extraction from empty citations"""
        result = extract_sql_from_citations([])

        self.assertIsNone(result)

    def test_extract_results_from_citations(self):
        """Test extracting structured results from citations"""
        citations = [
            {
                "retrievedReferences": [
                    {
                        "metadata": {
                            "product_id": "123",
                            "product_name": "Widget A",
                            "price": "29.99",
                        }
                    },
                    {
                        "metadata": {
                            "product_id": "456",
                            "product_name": "Widget B",
                            "price": "39.99",
                        }
                    },
                ]
            }
        ]

        result = extract_results_from_citations(citations)

        self.assertIsNotNone(result)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["product_id"], "123")
        self.assertEqual(result[1]["product_name"], "Widget B")

    def test_extract_results_from_citations_empty(self):
        """Test extracting results from empty citations"""
        result = extract_results_from_citations([])

        self.assertIsNone(result)

    def test_extract_results_from_citations_no_metadata(self):
        """Test extracting results when no metadata is present"""
        citations = [{"retrievedReferences": [{"content": {"text": "No metadata"}}]}]

        result = extract_results_from_citations(citations)

        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
