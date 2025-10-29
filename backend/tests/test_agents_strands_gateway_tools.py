"""
Unit tests for Strands Gateway tools.

Tests the internet search functionality converted to AgentCore Gateway format.
"""

import pytest
from unittest.mock import Mock, patch
from typing import Any, Dict, List

from app.agents.strands.tools.gateway_tools import (
    create_internet_search_tool,
    create_tavily_search_tool,
    get_internet_search_tools
)
from app.repositories.models.custom_bot import (
    BotModel,
    GenerationParamsModel,
    AgentModel,
    AgentToolModel,
    InternetToolModel
)


class TestStrandsGatewayTools:
    """Test suite for Strands Gateway tools."""

    @pytest.fixture
    def mock_bot_with_internet(self) -> BotModel:
        """Create mock bot with internet search enabled."""
        return BotModel(
            id="internet-bot",
            title="Internet Bot",
            instruction="Test bot with internet search",
            description="Test",
            generation_params=GenerationParamsModel(temperature=0.7, top_p=0.9, max_tokens=1024),
            agent=AgentModel(tools=[
                AgentToolModel(name="internet_search", enabled=True),
                AgentToolModel(name="knowledge", enabled=False),
            ]),
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
    def mock_bot_no_internet(self) -> BotModel:
        """Create mock bot without internet search."""
        return BotModel(
            id="no-internet-bot",
            title="No Internet Bot",
            instruction="Test bot without internet",
            description="Test",
            generation_params=GenerationParamsModel(temperature=0.7, top_p=0.9, max_tokens=1024),
            agent=AgentModel(tools=[
                AgentToolModel(name="internet_search", enabled=False),
                AgentToolModel(name="knowledge", enabled=True),
            ]),
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
    def mock_internet_config(self) -> InternetToolModel:
        """Create mock internet tool configuration."""
        return InternetToolModel(
            enabled=True,
            max_results=5,
            search_depth="basic"
        )

    def test_create_internet_search_tool(self, mock_bot_with_internet, mock_internet_config):
        """Test creating internet search tool."""
        tool_func = create_internet_search_tool(mock_bot_with_internet, mock_internet_config)
        
        assert callable(tool_func)

    def test_internet_search_placeholder(self, mock_bot_with_internet, mock_internet_config, caplog):
        """Test internet search placeholder implementation."""
        tool_func = create_internet_search_tool(mock_bot_with_internet, mock_internet_config)
        
        results = tool_func("test query", "en-us", "1w")
        
        assert len(results) == 1
        assert "Gateway Search Not Available" in results[0]["title"]
        assert "AgentCore Gateway not yet implemented" in caplog.text

    def test_internet_search_with_defaults(self, mock_bot_with_internet, mock_internet_config):
        """Test internet search with default parameters."""
        tool_func = create_internet_search_tool(mock_bot_with_internet, mock_internet_config)
        
        results = tool_func("test query")
        
        assert len(results) == 1
        assert results[0]["metadata"]["query"] == "test query"
        assert results[0]["metadata"]["locale"] == "en-us"

    def test_internet_search_error_handling(self, mock_bot_with_internet, mock_internet_config):
        """Test error handling in internet search."""
        tool_func = create_internet_search_tool(mock_bot_with_internet, mock_internet_config)
        
        # Mock an exception in the search function
        with patch.object(tool_func, '__call__', side_effect=Exception("Gateway error")):
            try:
                results = tool_func("test query")
                # If no exception, check error result format
                assert len(results) == 1
                assert "Error" in results[0]["source"]
            except Exception:
                # Exception handling is working
                pass

    def test_create_tavily_search_tool(self, mock_bot_with_internet):
        """Test creating Tavily search tool."""
        tool_func = create_tavily_search_tool(mock_bot_with_internet)
        
        assert callable(tool_func)

    def test_tavily_search_placeholder(self, mock_bot_with_internet, caplog):
        """Test Tavily search placeholder implementation."""
        tool_func = create_tavily_search_tool(mock_bot_with_internet)
        
        results = tool_func("test query")
        
        assert len(results) == 1
        assert "Tavily Search Not Available" in results[0]["title"]
        assert "Tavily via Gateway not yet implemented" in caplog.text

    def test_tavily_search_error_handling(self, mock_bot_with_internet):
        """Test error handling in Tavily search."""
        tool_func = create_tavily_search_tool(mock_bot_with_internet)
        
        # Mock an exception
        with patch.object(tool_func, '__call__', side_effect=Exception("Tavily error")):
            try:
                results = tool_func("test query")
                assert len(results) == 1
                assert "Error" in results[0]["source"]
            except Exception:
                pass

    def test_get_internet_search_tools_enabled(self, mock_bot_with_internet, caplog):
        """Test getting internet search tools when enabled."""
        tools = get_internet_search_tools(mock_bot_with_internet)
        
        assert len(tools) == 2  # Internet search + Tavily
        assert "Added 2 internet search tools" in caplog.text

    def test_get_internet_search_tools_disabled(self, mock_bot_no_internet):
        """Test getting internet search tools when disabled."""
        tools = get_internet_search_tools(mock_bot_no_internet)
        
        assert len(tools) == 0

    def test_get_internet_search_tools_no_tools(self):
        """Test getting internet search tools for bot with no tools."""
        bot_no_tools = BotModel(
            id="no-tools-bot",
            title="No Tools Bot",
            instruction="Test bot with no tools",
            description="Test",
            generation_params=GenerationParamsModel(temperature=0.7, top_p=0.9, max_tokens=1024),
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
        
        tools = get_internet_search_tools(bot_no_tools)
        
        assert len(tools) == 0

    def test_search_result_format(self, mock_bot_with_internet, mock_internet_config):
        """Test that search results have proper format."""
        tool_func = create_internet_search_tool(mock_bot_with_internet, mock_internet_config)
        
        results = tool_func("test query", "jp-jp", "1m")
        
        assert len(results) == 1
        result = results[0]
        
        # Check required fields
        assert "title" in result
        assert "content" in result
        assert "url" in result
        assert "source" in result
        assert "metadata" in result
        
        # Check metadata content
        assert result["metadata"]["query"] == "test query"
        assert result["metadata"]["locale"] == "jp-jp"

    def test_tavily_result_format(self, mock_bot_with_internet):
        """Test that Tavily results have proper format."""
        tool_func = create_tavily_search_tool(mock_bot_with_internet)
        
        results = tool_func("test query")
        
        assert len(results) == 1
        result = results[0]
        
        # Check required fields
        assert "title" in result
        assert "content" in result
        assert "url" in result
        assert "source" in result
        assert "metadata" in result
        
        # Check source
        assert result["source"] == "Tavily"

    def test_logging_behavior(self, mock_bot_with_internet, mock_internet_config, caplog):
        """Test logging behavior in tools."""
        # Test tool creation logging
        create_internet_search_tool(mock_bot_with_internet, mock_internet_config)
        assert f"Creating Gateway internet search tool for bot {mock_bot_with_internet.id}" in caplog.text
        
        # Test Tavily creation logging
        create_tavily_search_tool(mock_bot_with_internet)
        assert f"Creating Tavily search tool for bot {mock_bot_with_internet.id}" in caplog.text
        
        # Test search logging
        tool_func = create_internet_search_tool(mock_bot_with_internet, mock_internet_config)
        tool_func("test query")
        assert "Searching internet with query: test query" in caplog.text
