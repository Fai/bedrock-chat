"""SQL Knowledge Base search module.

This module handles retrieval from SQL Knowledge Bases using Bedrock's
retrieve_and_generate API to execute text-to-SQL queries.
"""

import logging
import os
from typing import TypedDict, Any

from app.repositories.models.custom_bot import BotModel
from app.utils import get_bedrock_agent_runtime_client
from botocore.exceptions import ClientError


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
agent_client = get_bedrock_agent_runtime_client()


class SqlSearchResult(TypedDict):
    """Search result from SQL Knowledge Base."""
    bot_id: str
    content: str
    source_name: str
    source_link: str
    rank: int
    metadata: dict[str, Any]
    page_number: int | None


def search_sql_knowledge_base(bot: BotModel, query: str) -> list[SqlSearchResult]:
    """
    Search SQL Knowledge Base using retrieve_and_generate API.

    This uses Bedrock's text-to-SQL capability to:
    1. Convert natural language query to SQL
    2. Execute the SQL against the database
    3. Return formatted results with citations

    Args:
        bot: Bot model with SQL Knowledge Base configuration
        query: Natural language question (e.g., "What is the price of Yoga Mat?")

    Returns:
        List of search results with SQL query execution data
    """
    assert bot.bedrock_knowledge_base is not None

    knowledge_base_id = (
        bot.bedrock_knowledge_base.exist_knowledge_base_id
        if bot.bedrock_knowledge_base.exist_knowledge_base_id is not None
        else bot.bedrock_knowledge_base.knowledge_base_id
    )
    assert knowledge_base_id is not None, "knowledge_base_id must be set for SQL KB"

    # Get model ARN from environment or use default
    model_arn = os.environ.get(
        "DEFAULT_MODEL_ARN",
        "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-5-sonnet-20241022-v2:0"
    )

    try:
        logger.info(f"Querying SQL KB {knowledge_base_id} with: {query}")

        # Use retrieve_and_generate for SQL KBs - this executes the SQL
        response = agent_client.retrieve_and_generate(
            input={'text': query},
            retrieveAndGenerateConfiguration={
                'type': 'KNOWLEDGE_BASE',
                'knowledgeBaseConfiguration': {
                    'knowledgeBaseId': knowledge_base_id,
                    'modelArn': model_arn,
                }
            }
        )

        # Extract generated response and citations
        generated_text = response.get('output', {}).get('text', '')
        citations = response.get('citations', [])

        results: list[SqlSearchResult] = []

        # Process citations to extract SQL query results
        for idx, citation in enumerate(citations):
            retrieved_references = citation.get('retrievedReferences', [])

            for ref in retrieved_references:
                content_text = ref.get('content', {}).get('text', '')
                location = ref.get('location', {})

                # Extract SQL query information
                source_name = "SQL Query Result"
                source_link = ""

                if location.get('type') == 'SQL':
                    sql_location = location.get('sqlLocation', {})
                    sql_query = sql_location.get('query', '')
                    if sql_query:
                        # Show truncated SQL query as source
                        source_name = f"SQL: {sql_query[:100]}..." if len(sql_query) > 100 else f"SQL: {sql_query}"
                        source_link = sql_query

                results.append({
                    'bot_id': bot.id,
                    'content': content_text if content_text else generated_text,
                    'source_name': source_name,
                    'source_link': source_link,
                    'rank': idx + 1,
                    'metadata': ref.get('metadata', {}),
                    'page_number': None,
                })

        # If no citations but we have generated text, return that as result
        if not results and generated_text:
            results.append({
                'bot_id': bot.id,
                'content': generated_text,
                'source_name': 'SQL Knowledge Base Response',
                'source_link': '',
                'rank': 1,
                'metadata': {},
                'page_number': None,
            })

        logger.info(f"SQL KB returned {len(results)} results")
        return results

    except ClientError as e:
        logger.error(f"Error querying SQL Knowledge Base: {e}")
        raise e
