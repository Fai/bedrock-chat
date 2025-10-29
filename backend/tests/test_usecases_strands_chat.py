"""
Unit tests for Strands chat orchestrator.

Tests the chat orchestration using Strands model-driven approach.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Any, Dict, List

from app.usecases.strands_chat import StrandsChatOrchestrator, create_strands_chat_orchestrator
from app.repositories.models.custom_bot import (
    BotModel,
    GenerationParamsModel,
    AgentModel,
    AgentToolModel,
    BedrockKnowledgeBaseModel,
)
from app.repositories.models.conversation import ConversationModel, MessageModel, TextContentModel
from app.routes.schemas.conversation import ChatInput, ChatOutput


class TestStrandsChatOrchestrator:
    """Test suite for StrandsChatOrchestrator."""

    @pytest.fixture
    def mock_bot(self):
        """Create mock bot with various tools."""
        return BotModel(
            id="test-bot",
            title="Test Bot",
            instruction="You are a helpful assistant",
            description="Test bot",
            generation_params=GenerationParamsModel(temperature=0.7, top_p=0.9, max_tokens=1024),
            agent=AgentModel(tools=[
                AgentToolModel(name="knowledge", enabled=True),
                AgentToolModel(name="internet_search", enabled=True),
            ]),
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

    @pytest.fixture
    def mock_conversation(self):
        """Create mock conversation with message history."""
        conversation = Mock(spec=ConversationModel)
        conversation.id = "conv-123"
        
        # Mock message history
        user_message = Mock(spec=MessageModel)
        user_message.role = "user"
        user_message.content = [Mock(body="Hello")]
        
        assistant_message = Mock(spec=MessageModel)
        assistant_message.role = "assistant"
        assistant_message.content = [Mock(body="Hi there!")]
        
        conversation.message_map = {
            "msg-1": user_message,
            "msg-2": assistant_message,
        }
        
        return conversation

    @pytest.fixture
    def mock_chat_input(self):
        """Create mock chat input."""
        return ChatInput(
            conversation_id="conv-123",
            message="What is the weather today?",
            bot_id="test-bot",
            continue_generate=False,
        )

    @patch('app.usecases.strands_chat.get_knowledge_tools')
    @patch('app.usecases.strands_chat.get_internet_search_tools')
    @patch('app.usecases.strands_chat.get_bedrock_agent_tools')
    @patch('app.usecases.strands_chat.StrandsAgentWrapper')
    def test_initialization(self, mock_wrapper, mock_bedrock_tools, mock_internet_tools, mock_knowledge_tools, mock_bot):
        """Test orchestrator initialization."""
        mock_knowledge_tools.return_value = ["knowledge_tool"]
        mock_internet_tools.return_value = ["internet_tool"]
        mock_bedrock_tools.return_value = []
        
        orchestrator = StrandsChatOrchestrator(mock_bot, "claude-3-5-sonnet")
        
        assert orchestrator.bot == mock_bot
        assert orchestrator.model_name == "claude-3-5-sonnet"
        assert len(orchestrator.tools) == 2
        mock_wrapper.assert_called_once_with(mock_bot, "claude-3-5-sonnet")

    @patch('app.usecases.strands_chat.get_knowledge_tools')
    @patch('app.usecases.strands_chat.get_internet_search_tools')
    @patch('app.usecases.strands_chat.get_bedrock_agent_tools')
    @patch('app.usecases.strands_chat.StrandsAgentWrapper')
    def test_collect_tools(self, mock_wrapper, mock_bedrock_tools, mock_internet_tools, mock_knowledge_tools, mock_bot, caplog):
        """Test tool collection."""
        mock_knowledge_tools.return_value = ["kb_tool1", "kb_tool2"]
        mock_internet_tools.return_value = ["internet_tool"]
        mock_bedrock_tools.return_value = ["bedrock_tool"]
        
        orchestrator = StrandsChatOrchestrator(mock_bot, "claude-3-5-sonnet")
        
        assert len(orchestrator.tools) == 4
        assert "Collected tools: 2 knowledge, 1 internet, 1 bedrock agent" in caplog.text

    @patch('app.usecases.strands_chat.StrandsAgentWrapper')
    def test_prepare_conversation_history(self, mock_wrapper, mock_bot, mock_conversation):
        """Test conversation history preparation."""
        orchestrator = StrandsChatOrchestrator(mock_bot, "claude-3-5-sonnet")
        
        history = orchestrator._prepare_conversation_history(mock_conversation)
        
        assert len(history) == 2
        assert history[0]["role"] == "user"
        assert history[0]["content"] == "Hello"
        assert history[1]["role"] == "assistant"
        assert history[1]["content"] == "Hi there!"

    @patch('app.usecases.strands_chat.build_rag_prompt')
    @patch('app.usecases.strands_chat.StrandsAgentWrapper')
    def test_handle_non_tooluse_rag(self, mock_wrapper, mock_build_rag, mock_bot):
        """Test RAG prompt injection for non-tool-use models."""
        mock_wrapper_instance = Mock()
        mock_wrapper_instance.supports_tool_use.return_value = False
        mock_wrapper.return_value = mock_wrapper_instance
        
        mock_build_rag.return_value = "RAG enhanced prompt"
        
        orchestrator = StrandsChatOrchestrator(mock_bot, "claude-3-5-sonnet")
        
        result = orchestrator._handle_non_tooluse_rag("What is AI?")
        
        assert result == "RAG enhanced prompt"
        mock_build_rag.assert_called_once_with(
            bot=mock_bot,
            query="What is AI?",
            model="claude-3-5-sonnet"
        )

    @patch('app.usecases.strands_chat.StrandsAgentWrapper')
    def test_handle_tooluse_no_rag(self, mock_wrapper, mock_bot):
        """Test no RAG injection for tool-use models."""
        mock_wrapper_instance = Mock()
        mock_wrapper_instance.supports_tool_use.return_value = True
        mock_wrapper.return_value = mock_wrapper_instance
        
        orchestrator = StrandsChatOrchestrator(mock_bot, "claude-3-5-sonnet")
        
        result = orchestrator._handle_non_tooluse_rag("What is AI?")
        
        assert result == "What is AI?"  # No modification

    @patch('app.usecases.strands_chat.get_knowledge_tools')
    @patch('app.usecases.strands_chat.get_internet_search_tools')
    @patch('app.usecases.strands_chat.get_bedrock_agent_tools')
    @patch('app.usecases.strands_chat.StrandsAgentWrapper')
    def test_chat_success(self, mock_wrapper, mock_bedrock_tools, mock_internet_tools, mock_knowledge_tools, mock_bot, mock_conversation, mock_chat_input):
        """Test successful chat execution."""
        # Setup mocks
        mock_knowledge_tools.return_value = []
        mock_internet_tools.return_value = []
        mock_bedrock_tools.return_value = []
        
        mock_wrapper_instance = Mock()
        mock_wrapper_instance.supports_tool_use.return_value = True
        mock_wrapper_instance.invoke.return_value = {
            "message": "The weather is sunny today!",
            "tool_uses": [],
            "related_documents": [],
            "token_usage": {},
        }
        mock_wrapper.return_value = mock_wrapper_instance
        
        orchestrator = StrandsChatOrchestrator(mock_bot, "claude-3-5-sonnet")
        
        # Mock callbacks
        on_stream = Mock()
        on_tool_use = Mock()
        
        result = orchestrator.chat(
            mock_chat_input,
            mock_conversation,
            on_stream=on_stream,
            on_tool_use=on_tool_use,
        )
        
        assert isinstance(result, ChatOutput)
        assert result.bot_id == "test-bot"
        assert result.message.content[0]["body"] == "The weather is sunny today!"
        mock_wrapper_instance.invoke.assert_called_once()

    @patch('app.usecases.strands_chat.get_knowledge_tools')
    @patch('app.usecases.strands_chat.get_internet_search_tools')
    @patch('app.usecases.strands_chat.get_bedrock_agent_tools')
    @patch('app.usecases.strands_chat.StrandsAgentWrapper')
    def test_chat_with_related_documents(self, mock_wrapper, mock_bedrock_tools, mock_internet_tools, mock_knowledge_tools, mock_bot, mock_conversation, mock_chat_input):
        """Test chat with related documents from tools."""
        # Setup mocks
        mock_knowledge_tools.return_value = []
        mock_internet_tools.return_value = []
        mock_bedrock_tools.return_value = []
        
        mock_wrapper_instance = Mock()
        mock_wrapper_instance.supports_tool_use.return_value = True
        mock_wrapper_instance.invoke.return_value = {
            "message": "Based on the documents, here's the answer.",
            "tool_uses": [],
            "related_documents": [
                {
                    "content": "Document content",
                    "source_id": "doc-1",
                    "source_name": "test.pdf",
                    "source_link": "https://example.com/test.pdf",
                    "page_number": 1,
                }
            ],
            "token_usage": {},
        }
        mock_wrapper.return_value = mock_wrapper_instance
        
        orchestrator = StrandsChatOrchestrator(mock_bot, "claude-3-5-sonnet")
        result = orchestrator.chat(mock_chat_input, mock_conversation)
        
        assert result.message.used_chunks is not None
        assert len(result.message.used_chunks) == 1
        assert result.message.used_chunks[0].source_name == "test.pdf"

    @patch('app.usecases.strands_chat.get_knowledge_tools')
    @patch('app.usecases.strands_chat.get_internet_search_tools')
    @patch('app.usecases.strands_chat.get_bedrock_agent_tools')
    @patch('app.usecases.strands_chat.StrandsAgentWrapper')
    def test_chat_error_handling(self, mock_wrapper, mock_bedrock_tools, mock_internet_tools, mock_knowledge_tools, mock_bot, mock_conversation, mock_chat_input):
        """Test chat error handling."""
        # Setup mocks
        mock_knowledge_tools.return_value = []
        mock_internet_tools.return_value = []
        mock_bedrock_tools.return_value = []
        
        mock_wrapper_instance = Mock()
        mock_wrapper_instance.invoke.side_effect = Exception("Agent failed")
        mock_wrapper.return_value = mock_wrapper_instance
        
        orchestrator = StrandsChatOrchestrator(mock_bot, "claude-3-5-sonnet")
        result = orchestrator.chat(mock_chat_input, mock_conversation)
        
        assert isinstance(result, ChatOutput)
        assert "I apologize, but I encountered an error" in result.message.content[0]["body"]
        assert "Agent failed" in result.message.content[0]["body"]

    def test_convert_to_chat_output(self, mock_bot):
        """Test conversion from Strands result to ChatOutput."""
        with patch('app.usecases.strands_chat.StrandsAgentWrapper'):
            orchestrator = StrandsChatOrchestrator(mock_bot, "claude-3-5-sonnet")
            
            strands_result = {
                "message": "Test response",
                "tool_uses": [],
                "related_documents": [],
                "token_usage": {"input": 10, "output": 20},
            }
            
            chat_input = ChatInput(
                conversation_id="conv-123",
                message="Test message",
                bot_id="test-bot",
            )
            
            result = orchestrator._convert_to_chat_output(strands_result, chat_input)
            
            assert isinstance(result, ChatOutput)
            assert result.conversation_id == "conv-123"
            assert result.bot_id == "test-bot"
            assert result.message.content[0]["body"] == "Test response"

    def test_create_strands_chat_orchestrator(self, mock_bot):
        """Test orchestrator factory function."""
        with patch('app.usecases.strands_chat.StrandsChatOrchestrator') as mock_orchestrator:
            mock_instance = Mock()
            mock_orchestrator.return_value = mock_instance
            
            result = create_strands_chat_orchestrator(mock_bot, "claude-3-5-sonnet")
            
            assert result == mock_instance
            mock_orchestrator.assert_called_once_with(mock_bot, "claude-3-5-sonnet")
