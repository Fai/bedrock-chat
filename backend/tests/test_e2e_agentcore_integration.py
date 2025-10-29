"""
End-to-end tests for AgentCore integration.

Tests complete system integration from chat request to response,
including routing, adapters, and compatibility.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import asyncio

from app.usecases.chat_router import route_chat_request
from app.adapters.enhanced_conversation_adapter import EnhancedConversationStorageAdapter
from app.adapters.enhanced_streaming_adapter import EnhancedStreamingProtocolAdapter
from app.repositories.models.custom_bot import BotModel, GenerationParamsModel, AgentModel, AgentToolModel
from app.repositories.models.conversation import ConversationModel
from app.routes.schemas.conversation import ChatInput, ChatOutput, MessageOutput


class TestEndToEndIntegration:
    """End-to-end integration test suite."""

    @pytest.fixture
    def complete_bot(self):
        """Create bot with all tool types."""
        return BotModel(
            id="e2e-bot",
            title="E2E Test Bot",
            instruction="You are a comprehensive test assistant",
            description="Bot for end-to-end testing",
            generation_params=GenerationParamsModel(temperature=0.7, top_p=0.9, max_tokens=2048),
            agent=AgentModel(tools=[
                AgentToolModel(name="knowledge", enabled=True),
                AgentToolModel(name="internet_search", enabled=True),
                AgentToolModel(name="bedrock_agent", enabled=True),
            ]),
            bedrock_knowledge_base=Mock(),
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

    @pytest.fixture
    def conversation_with_history(self):
        """Create conversation with message history."""
        conversation = Mock(spec=ConversationModel)
        conversation.id = "e2e-conv-123"
        
        # Mock message history
        user_msg = Mock()
        user_msg.role = "user"
        user_msg.content = [Mock(body="What is machine learning?")]
        
        assistant_msg = Mock()
        assistant_msg.role = "assistant"
        assistant_msg.content = [Mock(body="Machine learning is a subset of AI...")]
        
        conversation.message_map = {
            "msg-1": user_msg,
            "msg-2": assistant_msg,
        }
        
        return conversation

    @patch('app.usecases.chat_router.is_agentcore_enabled')
    @patch('app.usecases.strands_chat.StrandsChatOrchestrator')
    def test_complete_agentcore_flow(self, mock_orchestrator_class, mock_is_enabled, complete_bot, conversation_with_history):
        """Test complete AgentCore flow from request to response."""
        # Setup
        mock_is_enabled.return_value = True
        
        mock_orchestrator = Mock()
        mock_orchestrator.chat.return_value = ChatOutput(
            conversation_id="e2e-conv-123",
            message=MessageOutput(
                role="assistant",
                content=[{"content_type": "text", "body": "AgentCore response with tool usage"}],
                model="claude-3-5-sonnet",
                children=[],
                parent=None,
                create_time=1234567890.0,
                feedback=None,
                used_chunks=[{
                    "content": "Retrieved document content",
                    "source_name": "knowledge_base.pdf",
                    "source_link": "https://example.com/kb.pdf",
                    "source_id": "doc-123",
                    "page_number": 1,
                }],
                thinking=None,
            ),
            bot_id="e2e-bot",
            create_time=1234567890.0,
            suggested_follow_ups=["Tell me more about neural networks"],
        )
        mock_orchestrator_class.return_value = mock_orchestrator
        
        # Test streaming callback
        streamed_content = []
        def capture_stream(text):
            streamed_content.append(text)
        
        # Execute
        chat_input = ChatInput(
            conversation_id="e2e-conv-123",
            message="Explain deep learning with examples",
            bot_id="e2e-bot",
        )
        
        result = route_chat_request(
            chat_input=chat_input,
            bot=complete_bot,
            model_name="claude-3-5-sonnet",
            conversation=conversation_with_history,
            on_stream=capture_stream,
        )
        
        # Verify
        assert isinstance(result, ChatOutput)
        assert result.bot_id == "e2e-bot"
        assert "AgentCore response" in result.message.content[0]["body"]
        assert len(result.message.used_chunks) == 1
        assert result.suggested_follow_ups == ["Tell me more about neural networks"]
        
        # Verify orchestrator was called with correct parameters
        mock_orchestrator.chat.assert_called_once()
        call_args = mock_orchestrator.chat.call_args
        assert call_args[1]["chat_input"] == chat_input
        assert call_args[1]["conversation"] == conversation_with_history

    def test_enhanced_conversation_adapter_with_tools(self):
        """Test enhanced conversation adapter with tool results."""
        chat_output = Mock(spec=ChatOutput)
        message_output = Mock(spec=MessageOutput)
        message_output.role = "assistant"
        message_output.content = [{"content_type": "text", "body": "Response with tool usage"}]
        message_output.model = "claude-3-5-sonnet"
        message_output.children = []
        message_output.parent = None
        message_output.create_time = 1234567890.0
        message_output.feedback = None
        message_output.used_chunks = [{
            "content": "Tool result content",
            "source_name": "search_results",
            "source_id": "search-1",
        }]
        message_output.thinking = None
        chat_output.message = message_output
        
        tool_results = [
            {
                "type": "tool_use",
                "id": "tool-1",
                "name": "search",
                "input": {"query": "test query"}
            },
            {
                "type": "tool_result",
                "tool_use_id": "tool-1",
                "content": "Search results here"
            }
        ]
        
        adapter = EnhancedConversationStorageAdapter()
        result = adapter.adapt_with_tool_results(chat_output, tool_results)
        
        assert result.role == "assistant"
        assert len(result.content) == 3  # tool_use + tool_result + text
        assert len(result.used_chunks) == 1

    def test_enhanced_streaming_adapter_performance(self):
        """Test enhanced streaming adapter performance monitoring."""
        captured_content = []
        def capture_callback(text):
            captured_content.append(text)
        
        adapter = EnhancedStreamingProtocolAdapter(capture_callback, buffer_size=50)
        
        # Simulate streaming
        for i in range(10):
            adapter.on_stream(f"Chunk {i}")
        
        adapter.on_tool_use("search", {"query": "test"})
        adapter.on_tool_use("knowledge", {"question": "what is AI?"})
        
        # Get performance stats
        stats = adapter.get_streaming_stats()
        
        assert stats["chunk_count"] == 10
        assert stats["error_count"] == 0
        assert stats["success_rate"] == 1.0
        assert stats["chunks_per_second"] > 0
        assert len(captured_content) == 12  # 10 chunks + 2 tool messages

    def test_streaming_error_recovery(self):
        """Test streaming error recovery mechanism."""
        error_callback = Mock(side_effect=[Exception("Stream error"), None, None])
        
        adapter = EnhancedStreamingProtocolAdapter(error_callback)
        
        # This should trigger error and recovery
        adapter.on_stream("Test content")
        adapter.on_stream("Recovery content")
        
        stats = adapter.get_streaming_stats()
        assert stats["error_count"] == 1
        assert stats["chunk_count"] == 2

    @patch('app.usecases.chat_router.is_agentcore_enabled')
    @patch('app.usecases.chat_router.legacy_chat')
    def test_fallback_mechanism_integration(self, mock_legacy_chat, mock_is_enabled, complete_bot, conversation_with_history):
        """Test complete fallback mechanism integration."""
        mock_is_enabled.return_value = True
        mock_legacy_chat.return_value = ChatOutput(
            conversation_id="e2e-conv-123",
            message=MessageOutput(
                role="assistant",
                content=[{"content_type": "text", "body": "Legacy fallback response"}],
                model="claude-3-5-sonnet",
                children=[],
                parent=None,
                create_time=1234567890.0,
                feedback=None,
                used_chunks=None,
                thinking=None,
            ),
            bot_id="e2e-bot",
            create_time=1234567890.0,
            suggested_follow_ups=[],
        )
        
        # Mock Strands orchestrator to fail
        with patch('app.usecases.chat_router.create_strands_chat_orchestrator', side_effect=Exception("Strands failed")):
            chat_input = ChatInput(
                conversation_id="e2e-conv-123",
                message="Test fallback",
                bot_id="e2e-bot",
            )
            
            result = route_chat_request(
                chat_input=chat_input,
                bot=complete_bot,
                model_name="claude-3-5-sonnet",
                conversation=conversation_with_history,
            )
            
            # Should fallback to legacy
            assert "Legacy fallback response" in result.message.content[0]["body"]
            mock_legacy_chat.assert_called_once()

    def test_metadata_preservation(self):
        """Test metadata preservation through adapters."""
        chat_output = ChatOutput(
            conversation_id="test-conv",
            message=MessageOutput(
                role="assistant",
                content=[{"content_type": "text", "body": "Test response"}],
                model="claude-3-5-sonnet",
                children=[],
                parent=None,
                create_time=1234567890.0,
                feedback=None,
                used_chunks=None,
                thinking=None,
            ),
            bot_id="test-bot",
            create_time=1234567890.0,
            suggested_follow_ups=["Follow up 1", "Follow up 2"],
        )
        
        adapter = EnhancedConversationStorageAdapter()
        metadata = adapter.preserve_metadata(chat_output)
        
        assert metadata["bot_id"] == "test-bot"
        assert metadata["conversation_id"] == "test-conv"
        assert len(metadata["suggested_follow_ups"]) == 2
