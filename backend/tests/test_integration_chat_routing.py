"""
Integration tests for chat routing and adapters.

Tests the integration between AgentCore/Strands and legacy implementations.
"""

import pytest
from unittest.mock import Mock, patch

from app.usecases.chat_router import route_chat_request
from app.adapters.conversation_adapter import ConversationStorageAdapter
from app.adapters.streaming_adapter import StreamingProtocolAdapter
from app.repositories.models.custom_bot import BotModel, GenerationParamsModel, AgentModel
from app.repositories.models.conversation import ConversationModel
from app.routes.schemas.conversation import ChatInput, ChatOutput, MessageOutput


class TestChatRouting:
    """Test suite for chat routing integration."""

    @pytest.fixture
    def mock_bot(self):
        """Create mock bot."""
        return BotModel(
            id="test-bot",
            title="Test Bot",
            instruction="Test instruction",
            description="Test",
            generation_params=GenerationParamsModel(temperature=0.7, top_p=0.9, max_tokens=1024),
            agent=AgentModel(tools=[]),
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

    @pytest.fixture
    def mock_conversation(self):
        """Create mock conversation."""
        conversation = Mock(spec=ConversationModel)
        conversation.id = "conv-123"
        conversation.message_map = {}
        return conversation

    @pytest.fixture
    def mock_chat_input(self):
        """Create mock chat input."""
        return ChatInput(
            conversation_id="conv-123",
            message="Hello",
            bot_id="test-bot",
        )

    @patch('app.usecases.chat_router.is_agentcore_enabled')
    @patch('app.usecases.chat_router.legacy_chat')
    def test_route_to_legacy_when_disabled(self, mock_legacy_chat, mock_is_enabled, mock_bot, mock_conversation, mock_chat_input):
        """Test routing to legacy when AgentCore is disabled."""
        mock_is_enabled.return_value = False
        mock_legacy_chat.return_value = Mock(spec=ChatOutput)
        
        result = route_chat_request(
            mock_chat_input,
            mock_bot,
            "claude-3-5-sonnet",
            mock_conversation
        )
        
        mock_legacy_chat.assert_called_once()
        assert result is not None

    @patch('app.usecases.chat_router.is_agentcore_enabled')
    @patch('app.usecases.chat_router.create_strands_chat_orchestrator')
    def test_route_to_strands_when_enabled(self, mock_create_orchestrator, mock_is_enabled, mock_bot, mock_conversation, mock_chat_input):
        """Test routing to Strands when AgentCore is enabled."""
        mock_is_enabled.return_value = True
        
        mock_orchestrator = Mock()
        mock_orchestrator.chat.return_value = Mock(spec=ChatOutput)
        mock_create_orchestrator.return_value = mock_orchestrator
        
        result = route_chat_request(
            mock_chat_input,
            mock_bot,
            "claude-3-5-sonnet",
            mock_conversation
        )
        
        mock_create_orchestrator.assert_called_once_with(mock_bot, "claude-3-5-sonnet")
        mock_orchestrator.chat.assert_called_once()
        assert result is not None

    @patch('app.usecases.chat_router.is_agentcore_enabled')
    @patch('app.usecases.chat_router.create_strands_chat_orchestrator')
    @patch('app.usecases.chat_router.legacy_chat')
    def test_fallback_to_legacy_on_strands_error(self, mock_legacy_chat, mock_create_orchestrator, mock_is_enabled, mock_bot, mock_conversation, mock_chat_input):
        """Test fallback to legacy when Strands fails."""
        mock_is_enabled.return_value = True
        mock_create_orchestrator.side_effect = Exception("Strands failed")
        mock_legacy_chat.return_value = Mock(spec=ChatOutput)
        
        result = route_chat_request(
            mock_chat_input,
            mock_bot,
            "claude-3-5-sonnet",
            mock_conversation
        )
        
        mock_legacy_chat.assert_called_once()
        assert result is not None


class TestConversationAdapter:
    """Test suite for conversation storage adapter."""

    def test_adapt_chat_output_to_message(self):
        """Test adapting ChatOutput to MessageModel."""
        chat_output = Mock(spec=ChatOutput)
        message_output = Mock(spec=MessageOutput)
        message_output.role = "assistant"
        message_output.content = [{"content_type": "text", "body": "Hello"}]
        message_output.model = "claude-3-5-sonnet"
        message_output.children = []
        message_output.parent = None
        message_output.create_time = 1234567890.0
        message_output.feedback = None
        message_output.used_chunks = None
        message_output.thinking = None
        chat_output.message = message_output
        
        adapter = ConversationStorageAdapter()
        result = adapter.adapt_chat_output_to_message(chat_output)
        
        assert result.role == "assistant"
        assert len(result.content) == 1
        assert result.content[0].body == "Hello"

    def test_adapt_streaming_chunk_text(self):
        """Test adapting text streaming chunk."""
        chunk_data = {"type": "text", "content": "Hello world"}
        
        adapter = ConversationStorageAdapter()
        result = adapter.adapt_streaming_chunk(chunk_data)
        
        assert result == "Hello world"

    def test_adapt_streaming_chunk_tool_use(self):
        """Test adapting tool use streaming chunk."""
        chunk_data = {"type": "tool_use", "tool_name": "search", "content": "Searching..."}
        
        adapter = ConversationStorageAdapter()
        result = adapter.adapt_streaming_chunk(chunk_data)
        
        assert result == ""  # Tool use doesn't stream content

    def test_adapt_streaming_chunk_reasoning(self):
        """Test adapting reasoning streaming chunk."""
        chunk_data = {"type": "reasoning", "content": "Let me think about this"}
        
        adapter = ConversationStorageAdapter()
        result = adapter.adapt_streaming_chunk(chunk_data)
        
        assert "[Thinking:" in result
        assert "Let me think about this" in result


class TestStreamingAdapter:
    """Test suite for streaming protocol adapter."""

    def test_on_stream_callback(self):
        """Test streaming text callback."""
        mock_callback = Mock()
        adapter = StreamingProtocolAdapter(mock_callback)
        
        adapter.on_stream("Hello world")
        
        mock_callback.assert_called_once_with("Hello world")

    def test_on_tool_use_callback(self):
        """Test tool use callback."""
        mock_callback = Mock()
        adapter = StreamingProtocolAdapter(mock_callback)
        
        adapter.on_tool_use("search", {"query": "test"})
        
        mock_callback.assert_called_once()
        call_args = mock_callback.call_args[0][0]
        assert "Using search" in call_args

    def test_on_reasoning_callback(self):
        """Test reasoning callback."""
        mock_callback = Mock()
        adapter = StreamingProtocolAdapter(mock_callback)
        
        adapter.on_reasoning("Let me think")
        
        mock_callback.assert_called_once()
        call_args = mock_callback.call_args[0][0]
        assert "[Thinking:" in call_args
        assert "Let me think" in call_args

    def test_no_callback_handling(self):
        """Test adapter works without callback."""
        adapter = StreamingProtocolAdapter(None)
        
        # Should not raise exceptions
        adapter.on_stream("test")
        adapter.on_tool_use("search", {})
        adapter.on_reasoning("thinking")
