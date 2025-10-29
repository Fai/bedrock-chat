"""
Unit tests for AgentCore runtime registry.

Tests runtime management, bot-to-runtime mapping, and lifecycle operations.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import time
from datetime import datetime, timedelta

from app.repositories.agentcore_runtime import AgentCoreRuntimeRegistry, get_runtime_registry


class TestAgentCoreRuntimeRegistry:
    """Test suite for AgentCoreRuntimeRegistry."""

    @pytest.fixture
    def mock_config(self):
        """Mock AgentCore configuration."""
        config = Mock()
        config.get_runtime_table_name.return_value = "test-runtime-table"
        config.get_container_repository_uri.return_value = "123456789012.dkr.ecr.us-east-1.amazonaws.com/bedrock-chat-agents"
        config.get_runtime_execution_role_arn.return_value = "arn:aws:iam::123456789012:role/AgentRuntimeExecutionRole"
        config.get_build_project_name.return_value = "AgentCoreBuild"
        return config

    @pytest.fixture
    def mock_table(self):
        """Mock DynamoDB table."""
        return Mock()

    @pytest.fixture
    def mock_agentcore_client(self):
        """Mock AgentCore client."""
        return Mock()

    @patch('app.repositories.agentcore_runtime.get_agentcore_config')
    @patch('app.repositories.agentcore_runtime.boto3')
    def test_initialization(self, mock_boto3, mock_get_config, mock_config, mock_table):
        """Test registry initialization."""
        mock_get_config.return_value = mock_config
        mock_dynamodb = Mock()
        mock_dynamodb.Table.return_value = mock_table
        mock_boto3.resource.return_value = mock_dynamodb
        mock_boto3.client.return_value = Mock()
        
        registry = AgentCoreRuntimeRegistry()
        
        assert registry.config == mock_config
        assert registry.table == mock_table
        mock_boto3.resource.assert_called_with('dynamodb')
        mock_boto3.client.assert_called_with('bedrock-agentcore')

    @patch('app.repositories.agentcore_runtime.get_agentcore_config')
    @patch('app.repositories.agentcore_runtime.boto3')
    @patch('app.repositories.agentcore_runtime.time.time')
    def test_create_runtime(self, mock_time, mock_boto3, mock_get_config, mock_config, mock_table):
        """Test runtime creation."""
        mock_get_config.return_value = mock_config
        mock_dynamodb = Mock()
        mock_dynamodb.Table.return_value = mock_table
        mock_boto3.resource.return_value = mock_dynamodb
        mock_boto3.client.return_value = Mock()
        mock_time.return_value = 1234567890
        
        registry = AgentCoreRuntimeRegistry()
        
        bot_config = {"id": "test-bot", "title": "Test Bot"}
        result = registry.create_runtime("test-bot", bot_config)
        
        assert result["BotId"] == "test-bot"
        assert "RuntimeArn" in result
        assert result["Status"] == "CREATING"
        assert result["BotConfig"] == bot_config
        mock_table.put_item.assert_called_once()

    @patch('app.repositories.agentcore_runtime.get_agentcore_config')
    @patch('app.repositories.agentcore_runtime.boto3')
    def test_get_runtime_found(self, mock_boto3, mock_get_config, mock_config, mock_table):
        """Test getting existing runtime."""
        mock_get_config.return_value = mock_config
        mock_dynamodb = Mock()
        mock_dynamodb.Table.return_value = mock_table
        mock_boto3.resource.return_value = mock_dynamodb
        mock_boto3.client.return_value = Mock()
        
        mock_table.get_item.return_value = {
            'Item': {
                'BotId': 'test-bot',
                'RuntimeArn': 'arn:aws:bedrock-agentcore:us-east-1:123456789012:runtime/test-bot',
                'Status': 'ACTIVE'
            }
        }
        
        registry = AgentCoreRuntimeRegistry()
        result = registry.get_runtime("test-bot")
        
        assert result is not None
        assert result["BotId"] == "test-bot"
        assert result["Status"] == "ACTIVE"
        mock_table.get_item.assert_called_once_with(Key={'BotId': 'test-bot'})

    @patch('app.repositories.agentcore_runtime.get_agentcore_config')
    @patch('app.repositories.agentcore_runtime.boto3')
    def test_get_runtime_not_found(self, mock_boto3, mock_get_config, mock_config, mock_table):
        """Test getting non-existent runtime."""
        mock_get_config.return_value = mock_config
        mock_dynamodb = Mock()
        mock_dynamodb.Table.return_value = mock_table
        mock_boto3.resource.return_value = mock_dynamodb
        mock_boto3.client.return_value = Mock()
        
        mock_table.get_item.return_value = {}  # No Item key
        
        registry = AgentCoreRuntimeRegistry()
        result = registry.get_runtime("nonexistent-bot")
        
        assert result is None

    @patch('app.repositories.agentcore_runtime.get_agentcore_config')
    @patch('app.repositories.agentcore_runtime.boto3')
    @patch('app.repositories.agentcore_runtime.time.time')
    def test_update_runtime_status(self, mock_time, mock_boto3, mock_get_config, mock_config, mock_table):
        """Test runtime status update."""
        mock_get_config.return_value = mock_config
        mock_dynamodb = Mock()
        mock_dynamodb.Table.return_value = mock_table
        mock_boto3.resource.return_value = mock_dynamodb
        mock_boto3.client.return_value = Mock()
        mock_time.return_value = 1234567890
        
        registry = AgentCoreRuntimeRegistry()
        result = registry.update_runtime_status("test-bot", "ACTIVE", {"Endpoint": "https://example.com"})
        
        assert result is True
        mock_table.update_item.assert_called_once()
        
        # Check update expression includes status and metadata
        call_args = mock_table.update_item.call_args
        assert "SET #status = :status" in call_args[1]["UpdateExpression"]
        assert ":status" in call_args[1]["ExpressionAttributeValues"]
        assert call_args[1]["ExpressionAttributeValues"][":status"] == "ACTIVE"

    @patch('app.repositories.agentcore_runtime.get_agentcore_config')
    @patch('app.repositories.agentcore_runtime.boto3')
    def test_delete_runtime(self, mock_boto3, mock_get_config, mock_config, mock_table):
        """Test runtime deletion."""
        mock_get_config.return_value = mock_config
        mock_dynamodb = Mock()
        mock_dynamodb.Table.return_value = mock_table
        mock_boto3.resource.return_value = mock_dynamodb
        mock_boto3.client.return_value = Mock()
        
        registry = AgentCoreRuntimeRegistry()
        
        # Mock get_runtime to return existing runtime
        registry.get_runtime = Mock(return_value={
            'BotId': 'test-bot',
            'RuntimeArn': 'arn:aws:bedrock-agentcore:us-east-1:123456789012:runtime/test-bot'
        })
        
        result = registry.delete_runtime("test-bot")
        
        assert result is True
        mock_table.delete_item.assert_called_once_with(Key={'BotId': 'test-bot'})

    @patch('app.repositories.agentcore_runtime.get_agentcore_config')
    @patch('app.repositories.agentcore_runtime.boto3')
    def test_list_runtimes(self, mock_boto3, mock_get_config, mock_config, mock_table):
        """Test listing runtimes."""
        mock_get_config.return_value = mock_config
        mock_dynamodb = Mock()
        mock_dynamodb.Table.return_value = mock_table
        mock_boto3.resource.return_value = mock_dynamodb
        mock_boto3.client.return_value = Mock()
        
        mock_table.scan.return_value = {
            'Items': [
                {'BotId': 'bot1', 'Status': 'ACTIVE'},
                {'BotId': 'bot2', 'Status': 'CREATING'}
            ]
        }
        
        registry = AgentCoreRuntimeRegistry()
        result = registry.list_runtimes()
        
        assert len(result) == 2
        assert result[0]['BotId'] == 'bot1'
        assert result[1]['BotId'] == 'bot2'
        mock_table.scan.assert_called_once()

    @patch('app.repositories.agentcore_runtime.get_agentcore_config')
    @patch('app.repositories.agentcore_runtime.boto3')
    def test_list_runtimes_with_filter(self, mock_boto3, mock_get_config, mock_config, mock_table):
        """Test listing runtimes with status filter."""
        mock_get_config.return_value = mock_config
        mock_dynamodb = Mock()
        mock_dynamodb.Table.return_value = mock_table
        mock_boto3.resource.return_value = mock_dynamodb
        mock_boto3.client.return_value = Mock()
        
        mock_table.scan.return_value = {'Items': [{'BotId': 'bot1', 'Status': 'ACTIVE'}]}
        
        registry = AgentCoreRuntimeRegistry()
        result = registry.list_runtimes(status_filter="ACTIVE")
        
        assert len(result) == 1
        mock_table.scan.assert_called_once()
        
        # Check filter expression
        call_args = mock_table.scan.call_args
        assert "FilterExpression" in call_args[1]

    @patch('app.repositories.agentcore_runtime.get_agentcore_config')
    @patch('app.repositories.agentcore_runtime.boto3')
    def test_trigger_container_build(self, mock_boto3, mock_get_config, mock_config, mock_table):
        """Test triggering container build."""
        mock_get_config.return_value = mock_config
        mock_dynamodb = Mock()
        mock_dynamodb.Table.return_value = mock_table
        mock_boto3.resource.return_value = mock_dynamodb
        
        mock_codebuild = Mock()
        mock_codebuild.start_build.return_value = {
            'build': {'id': 'build-123'}
        }
        mock_boto3.client.side_effect = lambda service: mock_codebuild if service == 'codebuild' else Mock()
        
        registry = AgentCoreRuntimeRegistry()
        registry.update_runtime_status = Mock(return_value=True)
        
        result = registry.trigger_container_build("test-bot")
        
        assert result is True
        mock_codebuild.start_build.assert_called_once()
        registry.update_runtime_status.assert_called_once_with(
            "test-bot", "BUILDING", {"BuildId": "build-123"}
        )

    @patch('app.repositories.agentcore_runtime.get_agentcore_config')
    @patch('app.repositories.agentcore_runtime.boto3')
    @patch('app.repositories.agentcore_runtime.time.time')
    def test_cleanup_expired_runtimes(self, mock_time, mock_boto3, mock_get_config, mock_config, mock_table):
        """Test cleanup of expired runtimes."""
        mock_get_config.return_value = mock_config
        mock_dynamodb = Mock()
        mock_dynamodb.Table.return_value = mock_table
        mock_boto3.resource.return_value = mock_dynamodb
        mock_boto3.client.return_value = Mock()
        mock_time.return_value = 1234567890
        
        mock_table.scan.return_value = {
            'Items': [
                {'BotId': 'expired-bot1'},
                {'BotId': 'expired-bot2'}
            ]
        }
        
        registry = AgentCoreRuntimeRegistry()
        registry.delete_runtime = Mock(return_value=True)
        
        result = registry.cleanup_expired_runtimes()
        
        assert result == 2
        assert registry.delete_runtime.call_count == 2

    @patch('app.repositories.agentcore_runtime.AgentCoreRuntimeRegistry')
    def test_get_runtime_registry_singleton(self, mock_registry_class):
        """Test runtime registry singleton pattern."""
        mock_instance = Mock()
        mock_registry_class.return_value = mock_instance
        
        # First call creates instance
        registry1 = get_runtime_registry()
        assert registry1 == mock_instance
        
        # Second call returns same instance
        registry2 = get_runtime_registry()
        assert registry2 == mock_instance
        assert registry1 is registry2
        
        # Registry class should only be called once
        mock_registry_class.assert_called_once()
