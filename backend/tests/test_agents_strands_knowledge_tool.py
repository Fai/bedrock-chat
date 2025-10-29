"""
Unit tests for Strands knowledge tool.

Tests the knowledge base search functionality converted to Strands @tool format.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Any, Dict, List

from app.agents.strands.tools.knowledge_tool import create_knowledge_tool, get_knowledge_tools
from app.repositories.models.custom_bot import BotModel, BedrockKnowledgeBaseModel, GenerationParamsModel, AgentModel


class TestStrandsKnowledgeTool:
    """Test suite for Strands knowledge tool."""

    @pytest.fixture
    def mock_vector_bot(self) -> BotModel:
        """Create mock bot with vector knowledge base."""
        return BotModel(
            id="vector-bot",
            title="Vector Bot",
            instruction="Test bot with vector KB",
            description="Test",
            generation_params=GenerationParamsModel(temperature=0.7, top_p=0.9, max_tokens=1024),
            agent=AgentModel(tools=[]),
            bedrock_knowledge_base=BedrockKnowledgeBaseModel(
                knowledge_base_id="kb-vector-123",
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
    def mock_sql_bot(self) -> BotModel:
        """Create mock bot with SQL knowledge base."""
        return BotModel(
            id="sql-bot",
            title="SQL Bot", 
            instruction="Test bot with SQL KB",
            description="Test",
            generation_params=GenerationParamsModel(temperature=0.7, top_p=0.9, max_tokens=1024),
            agent=AgentModel(tools=[]),
            bedrock_knowledge_base=BedrockKnowledgeBaseModel(
                knowledge_base_id="kb-sql-123",
                data_source_ids=["ds-789"],
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
    def mock_no_kb_bot(self) -> BotModel:
        """Create mock bot without knowledge base."""
        return BotModel(
            id="no-kb-bot",
            title="No KB Bot",
            instruction="Test bot without KB",
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

    @patch('app.agents.strands.tools.knowledge_tool.detect_kb_type')
    def test_create_knowledge_tool_vector(self, mock_detect_kb_type, mock_vector_bot):
        """Test creating knowledge tool for vector KB."""
        mock_detect_kb_type.return_value = "VECTOR"
        mock_vector_bot.knowledge = Mock()
        mock_vector_bot.knowledge.__str_in_claude_format__ = Mock(return_value="Test KB info")
        
        tool_func = create_knowledge_tool(mock_vector_bot)
        
        assert callable(tool_func)
        mock_detect_kb_type.assert_called_once_with(mock_vector_bot)

    @patch('app.agents.strands.tools.knowledge_tool.detect_kb_type')
    def test_create_knowledge_tool_sql(self, mock_detect_kb_type, mock_sql_bot):
        """Test creating knowledge tool for SQL KB."""
        mock_detect_kb_type.return_value = "SQL"
        mock_sql_bot.knowledge = Mock()
        mock_sql_bot.knowledge.__str_in_claude_format__ = Mock(return_value="Test SQL KB info")
        
        tool_func = create_knowledge_tool(mock_sql_bot)
        
        assert callable(tool_func)
        mock_detect_kb_type.assert_called_once_with(mock_sql_bot)

    @patch('app.agents.strands.tools.knowledge_tool.detect_kb_type')
    @patch('app.agents.strands.tools.knowledge_tool.search_related_docs')
    def test_vector_search_success(self, mock_search_docs, mock_detect_kb_type, mock_vector_bot):
        """Test successful vector search."""
        mock_detect_kb_type.return_value = "VECTOR"
        mock_vector_bot.knowledge = Mock()
        mock_vector_bot.knowledge.__str_in_claude_format__ = Mock(return_value="Test KB")
        
        mock_search_docs.return_value = [
            {
                "content": "Test content",
                "source_name": "test.pdf",
                "source_link": "https://example.com/test.pdf",
                "rank": 1,
                "metadata": {"page": 1}
            }
        ]
        
        tool_func = create_knowledge_tool(mock_vector_bot)
        results = tool_func("What is the test content?")
        
        assert len(results) == 1
        assert results[0]["content"] == "Test content"
        assert results[0]["source_name"] == "test.pdf"
        mock_search_docs.assert_called_once_with(mock_vector_bot, query="What is the test content?")

    @patch('app.agents.strands.tools.knowledge_tool.detect_kb_type')
    @patch('app.agents.strands.tools.knowledge_tool.search_sql_knowledge_base')
    def test_sql_search_success(self, mock_search_sql, mock_detect_kb_type, mock_sql_bot):
        """Test successful SQL search."""
        mock_detect_kb_type.return_value = "SQL"
        mock_sql_bot.knowledge = Mock()
        mock_sql_bot.knowledge.__str_in_claude_format__ = Mock(return_value="Test SQL KB")
        
        mock_search_sql.return_value = [
            {
                "content": "Product: Yoga Mat, Price: $29.99",
                "source_name": "products.db",
                "source_link": "",
                "rank": 1,
                "metadata": {"table": "products"}
            }
        ]
        
        tool_func = create_knowledge_tool(mock_sql_bot)
        results = tool_func("What is the price of Yoga Mat?")
        
        assert len(results) == 1
        assert "Yoga Mat" in results[0]["content"]
        assert "$29.99" in results[0]["content"]
        mock_search_sql.assert_called_once_with(mock_sql_bot, query="What is the price of Yoga Mat?")

    @patch('app.agents.strands.tools.knowledge_tool.detect_kb_type')
    @patch('app.agents.strands.tools.knowledge_tool.search_related_docs')
    def test_search_error_handling(self, mock_search_docs, mock_detect_kb_type, mock_vector_bot):
        """Test error handling in search."""
        mock_detect_kb_type.return_value = "VECTOR"
        mock_vector_bot.knowledge = Mock()
        mock_vector_bot.knowledge.__str_in_claude_format__ = Mock(return_value="Test KB")
        
        mock_search_docs.side_effect = Exception("Search failed")
        
        tool_func = create_knowledge_tool(mock_vector_bot)
        results = tool_func("test query")
        
        assert len(results) == 1
        assert "Search failed" in results[0]["content"]
        assert results[0]["source_name"] == "Error"

    @patch('app.agents.strands.tools.knowledge_tool.detect_kb_type')
    @patch('app.agents.strands.tools.knowledge_tool.search_related_docs')
    def test_empty_search_results(self, mock_search_docs, mock_detect_kb_type, mock_vector_bot):
        """Test handling of empty search results."""
        mock_detect_kb_type.return_value = "VECTOR"
        mock_vector_bot.knowledge = Mock()
        mock_vector_bot.knowledge.__str_in_claude_format__ = Mock(return_value="Test KB")
        
        mock_search_docs.return_value = []
        
        tool_func = create_knowledge_tool(mock_vector_bot)
        results = tool_func("non-existent query")
        
        assert len(results) == 0

    @patch('app.agents.strands.tools.knowledge_tool.detect_kb_type')
    @patch('app.agents.strands.tools.knowledge_tool.search_related_docs')
    def test_result_formatting(self, mock_search_docs, mock_detect_kb_type, mock_vector_bot):
        """Test proper formatting of search results."""
        mock_detect_kb_type.return_value = "VECTOR"
        mock_vector_bot.knowledge = Mock()
        mock_vector_bot.knowledge.__str_in_claude_format__ = Mock(return_value="Test KB")
        
        mock_search_docs.return_value = [
            {
                "content": "Test content",
                "source_name": "test.pdf",
                # Missing source_link to test default handling
                "rank": 1,
                # Missing metadata to test default handling
            }
        ]
        
        tool_func = create_knowledge_tool(mock_vector_bot)
        results = tool_func("test query")
        
        assert len(results) == 1
        assert results[0]["content"] == "Test content"
        assert results[0]["source_name"] == "test.pdf"
        assert results[0]["source_link"] == ""  # Default value
        assert results[0]["rank"] == 1
        assert results[0]["metadata"] == {}  # Default value

    def test_get_knowledge_tools_with_kb(self, mock_vector_bot):
        """Test get_knowledge_tools with bot that has KB."""
        with patch('app.agents.strands.tools.knowledge_tool.create_knowledge_tool') as mock_create:
            mock_tool = Mock()
            mock_create.return_value = mock_tool
            
            tools = get_knowledge_tools(mock_vector_bot)
            
            assert len(tools) == 1
            assert tools[0] == mock_tool
            mock_create.assert_called_once_with(mock_vector_bot)

    def test_get_knowledge_tools_without_kb(self, mock_no_kb_bot):
        """Test get_knowledge_tools with bot that has no KB."""
        tools = get_knowledge_tools(mock_no_kb_bot)
        
        assert len(tools) == 0

    @patch('app.agents.strands.tools.knowledge_tool.detect_kb_type')
    def test_sql_kb_description(self, mock_detect_kb_type, mock_sql_bot, caplog):
        """Test that SQL KB gets appropriate description."""
        mock_detect_kb_type.return_value = "SQL"
        mock_sql_bot.knowledge = Mock()
        mock_sql_bot.knowledge.__str_in_claude_format__ = Mock(return_value="SQL KB info")
        
        create_knowledge_tool(mock_sql_bot)
        
        assert "Creating Strands knowledge tool - SQL KB: True" in caplog.text

    @patch('app.agents.strands.tools.knowledge_tool.detect_kb_type')
    def test_vector_kb_description(self, mock_detect_kb_type, mock_vector_bot, caplog):
        """Test that vector KB gets appropriate description."""
        mock_detect_kb_type.return_value = "VECTOR"
        mock_vector_bot.knowledge = Mock()
        mock_vector_bot.knowledge.__str_in_claude_format__ = Mock(return_value="Vector KB info")
        
        create_knowledge_tool(mock_vector_bot)
        
        assert "Creating Strands knowledge tool - SQL KB: False" in caplog.text
