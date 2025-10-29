"""
Strands knowledge base tool for Bedrock Chat.

Converts existing knowledge base search functionality to Strands @tool format,
supporting both vector search (OpenSearch) and SQL knowledge bases.
"""

import logging
from typing import Any, Dict, List

from app.repositories.models.custom_bot import BotModel
from app.vector_search import search_related_docs
from app.sql_kb_search import search_sql_knowledge_base
from app.kb_utils import detect_kb_type

# Strands imports (will be available when dependencies are installed)
# from strands import tool

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def create_knowledge_tool(bot: BotModel):
    """
    Create a Strands knowledge tool for the given bot.
    
    Args:
        bot: Bot model with knowledge base configuration
        
    Returns:
        Strands tool function decorated with @tool
    """
    # Detect KB type
    kb_type = detect_kb_type(bot)
    is_sql_kb = (kb_type == "SQL")
    
    # Get knowledge base description
    kb_info = bot.knowledge.__str_in_claude_format__()
    
    # Create appropriate description
    if is_sql_kb:
        description = (
            "Retrieve information to answer the user's question. "
            "IMPORTANT: Provide your query as a simple natural language question in plain English. "
            "Example: 'What is the price of Yoga Mat?' or 'Air Fryer product information'. "
            "DO NOT use technical syntax - just ask the question naturally. "
            f"Available information: {kb_info}"
        )
    else:
        description = f"Answer a user's question using information. The description is: {kb_info}"
    
    logger.info(f"Creating Strands knowledge tool - SQL KB: {is_sql_kb}")
    
    # TODO: Implement when strands-agents is available
    # @tool(description=description)
    def search_knowledge_base(query: str) -> List[Dict[str, Any]]:
        """
        Search the knowledge base for relevant information.
        
        Args:
            query: Natural language question to search for
            
        Returns:
            List of search results with content and metadata
        """
        logger.info(f"Searching knowledge base with query: {query}")
        
        try:
            if is_sql_kb:
                logger.info("Using SQL KB search")
                search_results = search_sql_knowledge_base(bot, query=query)
            else:
                logger.info("Using vector search")
                search_results = search_related_docs(bot, query=query)
            
            # Convert to Strands-compatible format
            formatted_results = []
            for result in search_results:
                formatted_results.append({
                    "content": result["content"],
                    "source_name": result["source_name"],
                    "source_link": result.get("source_link", ""),
                    "rank": result.get("rank", 0),
                    "metadata": result.get("metadata", {}),
                })
            
            logger.info(f"Found {len(formatted_results)} results")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Knowledge base search failed: {e}")
            return [{"content": f"Search failed: {str(e)}", "source_name": "Error", "source_link": "", "rank": 0, "metadata": {}}]
    
    return search_knowledge_base


def get_knowledge_tools(bot: BotModel) -> List[Any]:
    """
    Get all knowledge-related tools for a bot.
    
    Args:
        bot: Bot model with knowledge base configuration
        
    Returns:
        List of Strands tools for knowledge base access
    """
    tools = []
    
    if bot.bedrock_knowledge_base:
        knowledge_tool = create_knowledge_tool(bot)
        tools.append(knowledge_tool)
        logger.info(f"Added knowledge tool for bot {bot.id}")
    
    return tools
