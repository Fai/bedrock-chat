"""
Unit tests for Strands Bedrock Agent tool.

Tests the nested agent functionality using agents-as-tools pattern.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Any, Dict, List

from app.agents.strands.tools.bedrock_agent_tool import (
    StrandsBedrockAgent,
    create_bedrock_agent_tool,
    get_bedrock_agent_tools
)
from app.repositories.models.custom_bot import (
    BotModel,
    GenerationParamsModel,
    AgentModel,
    AgentToolModel
)


class TestStrandsBedrockAgent:
    """Test suite for StrandsBedrockAgent wrapper."""

    @pytest.fixture
    def mock_runtime_client(self):
        """Mock Bedrock Agent runtime client."""
        return Mock()

    @pytest.fixture
    def mock_client(self):
        """Mock Bedrock Agent client."""
        return Mock()

    @patch('app.agents.strands.tools.bedrock_agent_tool.get_bedrock_agent_runtime_client')
    @patch('app.agents.strands.tools.bedrock_agent_tool.get_bedrock_agent_client')
    def test_initialization(self, mock_get_client, mock_get_runtime_client, mock_client, mock_runtime_client):
        """Test StrandsBedrockAgent initialization."""
        mock_get_client.return_value = mock_client
        mock_get_runtime_client.return_value = mock_runtime_client
        
        mock_client.get_agent.return_value = {
            "agent": {"description": "Test Bedrock Agent"}
        }
        
        agent = StrandsBedrockAgent("test-agent-id", "test-alias-id")
        
        assert agent.agent_id == "test-agent-id"
        assert agent.alias_id == "test-alias-id"
        assert agent.description == "Test Bedrock Agent"
        mock_client.get_agent.assert_called_once_with(agentId="test-agent-id")

    @patch('app.agents.strands.tools.bedrock_agent_tool.get_bedrock_agent_runtime_client')
    @patch('app.agents.strands.tools.bedrock_agent_tool.get_bedrock_agent_client')
    def test_get_agent_description_error(self, mock_get_client, mock_get_runtime_client, mock_client, mock_runtime_client):
        """Test agent description retrieval with error."""
        mock_get_client.return_value = mock_client
        mock_get_runtime_client.return_value = mock_runtime_client
        
        mock_client.get_agent.side_effect = Exception("API Error")
        
        agent = StrandsBedrockAgent("test-agent-id", "test-alias-id")
        
        assert agent.description == "Bedrock Agent"  # Default fallback

    @patch('app.agents.strands.tools.bedrock_agent_tool.get_bedrock_agent_runtime_client')
    @patch('app.agents.strands.tools.bedrock_agent_tool.get_bedrock_agent_client')
    def test_invoke_success(self, mock_get_client, mock_get_runtime_client, mock_client, mock_runtime_client):
        """Test successful agent invocation."""
        mock_get_client.return_value = mock_client
        mock_get_runtime_client.return_value = mock_runtime_client
        
        mock_client.get_agent.return_value = {"agent": {"description": "Test Agent"}}
        
        # Mock streaming response
        mock_runtime_client.invoke_agent.return_value = {
            "completion": [
                {"chunk": {"bytes": b"Hello "}},
                {"chunk": {"bytes": b"World!"}},
                {"trace": {"traceId": "trace-123", "step": 1}},
            ]
        }
        
        agent = StrandsBedrockAgent("test-agent-id", "test-alias-id")
        result = agent.invoke("test query", "session-123")
        
        assert result["response"] == "Hello World!"
        assert result["session_id"] == "session-123"
        assert result["agent_id"] == "test-agent-id"
        assert result["alias_id"] == "test-alias-id"
        assert len(result["trace_logs"]) == 1
        assert result["trace_logs"][0]["traceId"] == "trace-123"

    @patch('app.agents.strands.tools.bedrock_agent_tool.get_bedrock_agent_runtime_client')
    @patch('app.agents.strands.tools.bedrock_agent_tool.get_bedrock_agent_client')
    def test_invoke_with_auto_session(self, mock_get_client, mock_get_runtime_client, mock_client, mock_runtime_client):
        """Test agent invocation with auto-generated session ID."""
        mock_get_client.return_value = mock_client
        mock_get_runtime_client.return_value = mock_runtime_client
        
        mock_client.get_agent.return_value = {"agent": {"description": "Test Agent"}}
        mock_runtime_client.invoke_agent.return_value = {"completion": []}
        
        agent = StrandsBedrockAgent("test-agent-id", "test-alias-id")
        result = agent.invoke("test query")  # No session_id provided
        
        assert "session_id" in result
        assert len(result["session_id"]) > 0  # Auto-generated UUID

    @patch('app.agents.strands.tools.bedrock_agent_tool.get_bedrock_agent_runtime_client')
    @patch('app.agents.strands.tools.bedrock_agent_tool.get_bedrock_agent_client')
    def test_invoke_error(self, mock_get_client, mock_get_runtime_client, mock_client, mock_runtime_client):
        """Test agent invocation error handling."""
        mock_get_client.return_value = mock_client
        mock_get_runtime_client.return_value = mock_runtime_client
        
        mock_client.get_agent.return_value = {"agent": {"description": "Test Agent"}}
        mock_runtime_client.invoke_agent.side_effect = Exception("Invocation failed")
        
        agent = StrandsBedrockAgent("test-agent-id", "test-alias-id")
        result = agent.invoke("test query", "session-123")
        
        assert "Agent invocation failed" in result["response"]
        assert result["error"] == "Invocation failed"
        assert result["trace_logs"] == []


class TestBedrockAgentTool:
    """Test suite for Bedrock Agent tool creation."""

    @pytest.fixture
    def mock_agent_config(self):
        """Mock agent configuration with Bedrock Agent."""
        config = Mock(spec=AgentModel)
        config.bedrock_agent_id = "test-agent-id"
        config.bedrock_agent_alias_id = "test-alias-id"
        return config

    @patch('app.agents.strands.tools.bedrock_agent_tool.StrandsBedrockAgent')
    def test_create_bedrock_agent_tool(self, mock_strands_agent, mock_agent_config):
        """Test creating Bedrock Agent tool."""
        mock_agent_instance = Mock()
        mock_agent_instance.description = "Test Agent Description"
        mock_strands_agent.return_value = mock_agent_instance
        
        tool_func = create_bedrock_agent_tool(mock_agent_config)
        
        assert callable(tool_func)
        mock_strands_agent.assert_called_once_with("test-agent-id", "test-alias-id")

    @patch('app.agents.strands.tools.bedrock_agent_tool.StrandsBedrockAgent')
    def test_bedrock_agent_tool_invocation(self, mock_strands_agent, mock_agent_config):
        """Test Bedrock Agent tool invocation."""
        mock_agent_instance = Mock()
        mock_agent_instance.description = "Test Agent"
        mock_agent_instance.invoke.return_value = {
            "response": "Agent response",
            "trace_logs": [{"step": 1}],
            "session_id": "session-123",
            "agent_id": "test-agent-id",
            "alias_id": "test-alias-id",
        }
        mock_strands_agent.return_value = mock_agent_instance
        
        tool_func = create_bedrock_agent_tool(mock_agent_config)
        result = tool_func("test input")
        
        assert result["content"] == "Agent response"
        assert result["source"] == "Bedrock Agent (test-agent-id)"
        assert result["metadata"]["agent_id"] == "test-agent-id"
        assert result["metadata"]["alias_id"] == "test-alias-id"
        assert result["metadata"]["session_id"] == "session-123"
        assert len(result["metadata"]["trace_logs"]) == 1
        assert result["metadata"]["has_error"] is False

    @patch('app.agents.strands.tools.bedrock_agent_tool.StrandsBedrockAgent')
    def test_bedrock_agent_tool_error_handling(self, mock_strands_agent, mock_agent_config):
        """Test Bedrock Agent tool error handling."""
        mock_agent_instance = Mock()
        mock_agent_instance.description = "Test Agent"
        mock_agent_instance.invoke.return_value = {
            "response": "Agent invocation failed: Connection error",
            "trace_logs": [],
            "session_id": "session-123",
            "error": "Connection error",
        }
        mock_strands_agent.return_value = mock_agent_instance
        
        tool_func = create_bedrock_agent_tool(mock_agent_config)
        result = tool_func("test input")
        
        assert "Agent invocation failed" in result["content"]
        assert result["metadata"]["has_error"] is True


class TestGetBedrockAgentTools:
    """Test suite for getting Bedrock Agent tools."""

    @pytest.fixture
    def mock_bot_with_bedrock_agent(self):
        """Create mock bot with Bedrock Agent enabled."""
        bot = Mock(spec=BotModel)
        bot.id = "bedrock-agent-bot"
        
        agent_config = Mock(spec=AgentModel)
        agent_config.bedrock_agent_id = "test-agent-id"
        agent_config.bedrock_agent_alias_id = "test-alias-id"
        agent_config.tools = [
            Mock(name="bedrock_agent", enabled=True),
            Mock(name="knowledge", enabled=False),
        ]
        
        bot.agent = agent_config
        return bot

    @pytest.fixture
    def mock_bot_no_bedrock_agent(self):
        """Create mock bot without Bedrock Agent."""
        bot = Mock(spec=BotModel)
        bot.id = "no-bedrock-agent-bot"
        
        agent_config = Mock(spec=AgentModel)
        agent_config.tools = [
            Mock(name="bedrock_agent", enabled=False),
            Mock(name="knowledge", enabled=True),
        ]
        
        bot.agent = agent_config
        return bot

    @patch('app.agents.strands.tools.bedrock_agent_tool.create_bedrock_agent_tool')
    def test_get_bedrock_agent_tools_enabled(self, mock_create_tool, mock_bot_with_bedrock_agent, caplog):
        """Test getting Bedrock Agent tools when enabled."""
        mock_tool = Mock()
        mock_create_tool.return_value = mock_tool
        
        tools = get_bedrock_agent_tools(mock_bot_with_bedrock_agent)
        
        assert len(tools) == 1
        assert tools[0] == mock_tool
        assert "Added Bedrock Agent tool for bot bedrock-agent-bot" in caplog.text

    def test_get_bedrock_agent_tools_disabled(self, mock_bot_no_bedrock_agent):
        """Test getting Bedrock Agent tools when disabled."""
        tools = get_bedrock_agent_tools(mock_bot_no_bedrock_agent)
        
        assert len(tools) == 0

    def test_get_bedrock_agent_tools_no_agent_id(self):
        """Test getting tools when agent ID is missing."""
        bot = Mock(spec=BotModel)
        bot.id = "no-agent-id-bot"
        
        agent_config = Mock(spec=AgentModel)
        agent_config.tools = [Mock(name="bedrock_agent", enabled=True)]
        # Missing bedrock_agent_id attribute
        
        bot.agent = agent_config
        
        tools = get_bedrock_agent_tools(bot)
        
        assert len(tools) == 0

    def test_get_bedrock_agent_tools_empty_tools(self):
        """Test getting tools for bot with no tools configured."""
        bot = Mock(spec=BotModel)
        bot.id = "empty-tools-bot"
        
        agent_config = Mock(spec=AgentModel)
        agent_config.tools = []  # Empty tools list
        
        bot.agent = agent_config
        
        tools = get_bedrock_agent_tools(bot)
        
        assert len(tools) == 0
