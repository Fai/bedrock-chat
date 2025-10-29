"""
Unit tests for StrandsAgentWrapper class.

Tests the bridge between BotModel configuration and Strands agent framework,
including configuration mapping, parameter handling, and streaming support.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Any, Dict, List, Optional

# Import the classes we're testing
from app.agents.strands.base_agent import StrandsAgentWrapper
from app.repositories.models.custom_bot import (
    BotModel,
    GenerationParamsModel,
    AgentModel,
    AgentToolModel,
    BedrockKnowledgeBaseModel,
)


class TestStrandsAgentWrapper:
    """Test suite for StrandsAgentWrapper class."""

    @pytest.fixture
    def mock_generation_params(self) -> GenerationParamsModel:
        """Create mock generation parameters."""
        return GenerationParamsModel(
            temperature=0.7,
            top_p=0.9,
            max_tokens=2048,
            top_k=50,
            stop_sequences=["Human:", "Assistant:"],
        )

    @pytest.fixture
    def mock_agent_config(self) -> AgentModel:
        """Create mock agent configuration."""
        return AgentModel(
            tools=[
                AgentToolModel(name="knowledge", enabled=True),
                AgentToolModel(name="internet_search", enabled=True),
            ]
        )

    @pytest.fixture
    def mock_bot(self, mock_generation_params, mock_agent_config) -> BotModel:
        """Create mock bot model."""
        return BotModel(
            id="test-bot-123",
            title="Test Bot",
            instruction="You are a helpful AI assistant specialized in testing.",
            description="A test bot for unit testing",
            generation_params=mock_generation_params,
            agent=mock_agent_config,
            bedrock_knowledge_base=BedrockKnowledgeBaseModel(
                knowledge_base_id="kb-123",
                data_source_ids=["ds-456"],
            ),
            is_pinned=False,
            is_public=False,
            owned=True,
            available=True,
            sync_status="SUCCEEDED",
            has_knowledge=True,
            display_retrieved_chunks=True,
            create_time=1234567890.0,
            last_used_time=1234567890.0,
        )

    def test_initialization(self, mock_bot):
        """Test StrandsAgentWrapper initialization."""
        wrapper = StrandsAgentWrapper(
            bot=mock_bot,
            model_name="claude-3-5-sonnet",
            bedrock_region="us-west-2",
        )

        assert wrapper.bot == mock_bot
        assert wrapper.model_name == "claude-3-5-sonnet"
        assert wrapper.bedrock_region == "us-west-2"
        assert wrapper.instruction == mock_bot.instruction
        assert wrapper.generation_params == mock_bot.generation_params
        assert wrapper.agent_config == mock_bot.agent
        assert wrapper.agent is None  # Not initialized until dependencies available

    def test_build_system_prompt(self, mock_bot):
        """Test system prompt building."""
        wrapper = StrandsAgentWrapper(mock_bot, "claude-3-5-sonnet")
        
        system_prompt = wrapper._build_system_prompt()
        
        assert system_prompt == mock_bot.instruction
        assert "helpful AI assistant specialized in testing" in system_prompt

    def test_map_generation_params_basic(self, mock_bot):
        """Test basic generation parameter mapping."""
        wrapper = StrandsAgentWrapper(mock_bot, "claude-3-5-sonnet")
        
        params = wrapper._map_generation_params()
        
        expected = {
            "temperature": 0.7,
            "top_p": 0.9,
            "max_tokens": 2048,
            "top_k": 50,
            "stop_sequences": ["Human:", "Assistant:"],
        }
        
        assert params == expected

    def test_map_generation_params_minimal(self, mock_bot):
        """Test generation parameter mapping with minimal parameters."""
        # Create minimal generation params
        minimal_params = GenerationParamsModel(
            temperature=0.5,
            top_p=0.8,
            max_tokens=1024,
        )
        mock_bot.generation_params = minimal_params
        
        wrapper = StrandsAgentWrapper(mock_bot, "claude-3-5-sonnet")
        params = wrapper._map_generation_params()
        
        expected = {
            "temperature": 0.5,
            "top_p": 0.8,
            "max_tokens": 1024,
        }
        
        assert params == expected
        assert "top_k" not in params
        assert "stop_sequences" not in params

    def test_map_generation_params_with_reasoning(self, mock_bot):
        """Test generation parameter mapping with reasoning parameters."""
        # Mock reasoning parameters
        reasoning_params = Mock()
        reasoning_params.enabled = True
        reasoning_params.budget_tokens = 5000
        
        mock_bot.generation_params.reasoning_params = reasoning_params
        
        wrapper = StrandsAgentWrapper(mock_bot, "claude-3-5-sonnet")
        params = wrapper._map_generation_params()
        
        assert "reasoning" in params
        assert params["reasoning"]["enabled"] is True
        assert params["reasoning"]["budget_tokens"] == 5000

    def test_initialize_strands_agent_not_implemented(self, mock_bot, caplog):
        """Test that Strands agent initialization logs warning when not implemented."""
        wrapper = StrandsAgentWrapper(mock_bot, "claude-3-5-sonnet")
        
        wrapper._initialize_strands_agent()
        
        assert "Strands agent initialization not yet implemented" in caplog.text
        assert wrapper.agent is None

    def test_invoke_without_agent(self, mock_bot, caplog):
        """Test invoke method when agent is not initialized."""
        wrapper = StrandsAgentWrapper(mock_bot, "claude-3-5-sonnet")
        
        result = wrapper.invoke("Hello, how are you?")
        
        expected = {
            "message": "Agent not yet initialized. Strands dependencies pending.",
            "tool_uses": [],
            "related_documents": [],
            "token_usage": {},
        }
        
        assert result == expected
        assert "Strands agent not initialized" in caplog.text

    def test_invoke_with_callbacks(self, mock_bot):
        """Test invoke method with streaming callbacks."""
        wrapper = StrandsAgentWrapper(mock_bot, "claude-3-5-sonnet")
        
        # Mock callbacks
        on_stream = Mock()
        on_tool_use = Mock()
        on_tool_result = Mock()
        on_reasoning = Mock()
        
        result = wrapper.invoke(
            user_message="Test message",
            conversation_history=[{"role": "user", "content": "Previous message"}],
            on_stream=on_stream,
            on_tool_use=on_tool_use,
            on_tool_result=on_tool_result,
            on_reasoning=on_reasoning,
        )
        
        # Should return not implemented response
        assert result["message"] == "Agent not yet initialized. Strands dependencies pending."
        
        # Callbacks should not be called when agent is not initialized
        on_stream.assert_not_called()
        on_tool_use.assert_not_called()
        on_tool_result.assert_not_called()
        on_reasoning.assert_not_called()

    def test_get_tools_not_implemented(self, mock_bot, caplog):
        """Test get_tools method logs info about tool loading."""
        wrapper = StrandsAgentWrapper(mock_bot, "claude-3-5-sonnet")
        
        tools = wrapper.get_tools()
        
        assert tools == []
        assert f"Loading {len(mock_bot.agent.tools)} tools for bot {mock_bot.id}" in caplog.text

    def test_supports_streaming(self, mock_bot):
        """Test streaming support check."""
        wrapper = StrandsAgentWrapper(mock_bot, "claude-3-5-sonnet")
        
        assert wrapper.supports_streaming() is True

    @patch('app.agents.strands.base_agent.is_tooluse_supported')
    def test_supports_tool_use_with_import(self, mock_is_tooluse_supported, mock_bot):
        """Test tool use support check with successful import."""
        mock_is_tooluse_supported.return_value = True
        
        wrapper = StrandsAgentWrapper(mock_bot, "claude-3-5-sonnet")
        
        assert wrapper.supports_tool_use() is True
        mock_is_tooluse_supported.assert_called_once_with("claude-3-5-sonnet")

    @patch('app.agents.strands.base_agent.is_tooluse_supported')
    def test_supports_tool_use_no_tool_support(self, mock_is_tooluse_supported, mock_bot):
        """Test tool use support check for non-tool-use model."""
        mock_is_tooluse_supported.return_value = False
        
        wrapper = StrandsAgentWrapper(mock_bot, "claude-3-5-sonnet")
        
        assert wrapper.supports_tool_use() is False

    def test_supports_tool_use_import_error(self, mock_bot, caplog):
        """Test tool use support check with import error."""
        with patch('app.agents.strands.base_agent.is_tooluse_supported', side_effect=ImportError):
            wrapper = StrandsAgentWrapper(mock_bot, "claude-3-5-sonnet")
            
            result = wrapper.supports_tool_use()
            
            assert result is True  # Default to True on import error
            assert "Could not import is_tooluse_supported" in caplog.text

    def test_repr(self, mock_bot):
        """Test string representation."""
        wrapper = StrandsAgentWrapper(mock_bot, "claude-3-5-sonnet")
        
        repr_str = repr(wrapper)
        
        assert "StrandsAgentWrapper" in repr_str
        assert "bot_id=test-bot-123" in repr_str
        assert "model=claude-3-5-sonnet" in repr_str
        assert "tools=2" in repr_str  # 2 tools in mock_agent_config
        assert "has_knowledge=True" in repr_str

    def test_repr_no_knowledge(self, mock_bot):
        """Test string representation for bot without knowledge base."""
        mock_bot.bedrock_knowledge_base = None
        wrapper = StrandsAgentWrapper(mock_bot, "claude-3-5-sonnet")
        
        repr_str = repr(wrapper)
        
        assert "has_knowledge=False" in repr_str

    def test_different_model_names(self, mock_bot):
        """Test initialization with different model names."""
        models = [
            "claude-3-5-sonnet",
            "claude-3-haiku",
            "amazon-nova-pro",
            "llama3-3-70b-instruct",
        ]
        
        for model_name in models:
            wrapper = StrandsAgentWrapper(mock_bot, model_name)
            assert wrapper.model_name == model_name

    def test_different_regions(self, mock_bot):
        """Test initialization with different AWS regions."""
        regions = ["us-east-1", "us-west-2", "eu-west-1", "ap-northeast-1"]
        
        for region in regions:
            wrapper = StrandsAgentWrapper(mock_bot, "claude-3-5-sonnet", region)
            assert wrapper.bedrock_region == region

    def test_bot_without_agent_config(self, mock_generation_params):
        """Test with bot that has no agent configuration."""
        bot_no_agent = BotModel(
            id="simple-bot",
            title="Simple Bot",
            instruction="Simple instruction",
            description="Simple bot",
            generation_params=mock_generation_params,
            agent=AgentModel(tools=[]),  # Empty tools
            bedrock_knowledge_base=None,
            is_pinned=False,
            is_public=False,
            owned=True,
            available=True,
            sync_status="SUCCEEDED",
            has_knowledge=False,
            display_retrieved_chunks=False,
            create_time=1234567890.0,
            last_used_time=1234567890.0,
        )
        
        wrapper = StrandsAgentWrapper(bot_no_agent, "claude-3-5-sonnet")
        
        assert len(wrapper.agent_config.tools) == 0
        assert wrapper.bot.bedrock_knowledge_base is None

    def test_logging_initialization(self, mock_bot, caplog):
        """Test that initialization logs appropriate messages."""
        wrapper = StrandsAgentWrapper(mock_bot, "claude-3-5-sonnet")
        
        assert f"Initialized StrandsAgentWrapper for bot {mock_bot.id}" in caplog.text
        assert "claude-3-5-sonnet" in caplog.text


class TestStrandsAgentWrapperIntegration:
    """Integration-style tests for StrandsAgentWrapper."""

    def test_full_workflow_without_dependencies(self, mock_bot):
        """Test complete workflow when Strands dependencies are not available."""
        wrapper = StrandsAgentWrapper(mock_bot, "claude-3-5-sonnet")
        
        # Test configuration mapping
        params = wrapper._map_generation_params()
        assert params["temperature"] == 0.7
        
        # Test system prompt
        prompt = wrapper._build_system_prompt()
        assert "helpful AI assistant" in prompt
        
        # Test capabilities
        assert wrapper.supports_streaming() is True
        
        # Test tools (empty for now)
        tools = wrapper.get_tools()
        assert tools == []
        
        # Test invocation (should return not implemented)
        result = wrapper.invoke("Hello")
        assert "not yet initialized" in result["message"]

    def test_configuration_edge_cases(self):
        """Test edge cases in configuration handling."""
        # Bot with minimal configuration
        minimal_bot = BotModel(
            id="minimal",
            title="Minimal",
            instruction="",  # Empty instruction
            description="",
            generation_params=GenerationParamsModel(
                temperature=0.0,  # Edge case: zero temperature
                top_p=1.0,        # Edge case: max top_p
                max_tokens=1,     # Edge case: minimal tokens
            ),
            agent=AgentModel(tools=[]),
            bedrock_knowledge_base=None,
            is_pinned=False,
            is_public=False,
            owned=True,
            available=True,
            sync_status="SUCCEEDED",
            has_knowledge=False,
            display_retrieved_chunks=False,
            create_time=0.0,
            last_used_time=0.0,
        )
        
        wrapper = StrandsAgentWrapper(minimal_bot, "claude-3-5-sonnet")
        
        # Should handle empty instruction
        assert wrapper._build_system_prompt() == ""
        
        # Should handle edge case parameters
        params = wrapper._map_generation_params()
        assert params["temperature"] == 0.0
        assert params["top_p"] == 1.0
        assert params["max_tokens"] == 1
