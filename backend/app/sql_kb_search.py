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
    logger.info("=" * 80)
    logger.info("STEP 1: SQL KB Search Started")
    logger.info(f"Bot ID: {bot.id}")
    logger.info(f"Query: {query}")

    assert bot.bedrock_knowledge_base is not None

    knowledge_base_id = (
        bot.bedrock_knowledge_base.exist_knowledge_base_id
        if bot.bedrock_knowledge_base.exist_knowledge_base_id is not None
        else bot.bedrock_knowledge_base.knowledge_base_id
    )
    assert knowledge_base_id is not None, "knowledge_base_id must be set for SQL KB"

    logger.info(f"STEP 2: KB ID resolved: {knowledge_base_id}")

    # Get model ARN from environment or use Amazon Nova Lite (works with SQL KBs)
    model_arn = os.environ.get(
        "DEFAULT_MODEL_ARN",
        "arn:aws:bedrock:us-east-1::foundation-model/amazon.nova-lite-v1:0"
    )
    logger.info(f"STEP 3: Model ARN: {model_arn}")

    try:
        logger.info(f"STEP 4: Calling retrieve_and_generate API...")
        logger.info(f"  - KB ID: {knowledge_base_id}")
        logger.info(f"  - Query: {query}")
        logger.info(f"  - Model: {model_arn}")

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

        logger.info("STEP 5: retrieve_and_generate API returned successfully")
        logger.info(f"Response keys: {list(response.keys())}")

        # Log the raw response for debugging
        import json
        logger.info("STEP 5.5: RAW RESPONSE DUMP:")
        logger.info(json.dumps(response, indent=2, default=str))

        # Extract generated response and citations
        generated_text = response.get('output', {}).get('text', '')
        citations = response.get('citations', [])

        logger.info(f"STEP 6: Parsing response")
        logger.info(f"  - Generated text length: {len(generated_text)}")
        logger.info(f"  - Generated text preview: {generated_text[:200]}...")
        logger.info(f"  - Number of citations: {len(citations)}")

        results: list[SqlSearchResult] = []

        # Process citations to extract SQL query results
        for idx, citation in enumerate(citations):
            logger.info(f"STEP 7.{idx+1}: Processing citation {idx+1}")

            retrieved_references = citation.get('retrievedReferences', [])
            logger.info(f"  - Retrieved references count: {len(retrieved_references)}")

            for ref_idx, ref in enumerate(retrieved_references):
                content_text = ref.get('content', {}).get('text', '')
                location = ref.get('location', {})

                logger.info(f"  - Reference {ref_idx+1}:")
                logger.info(f"    - Content length: {len(content_text)}")
                logger.info(f"    - Content preview: {content_text[:100]}...")
                logger.info(f"    - Location type: {location.get('type')}")

                # Extract SQL query information
                source_name = "SQL Query Result"
                source_link = ""

                if location.get('type') == 'SQL':
                    sql_location = location.get('sqlLocation', {})
                    sql_query = sql_location.get('query', '')

                    logger.info(f"    - SQL Query detected!")
                    logger.info(f"    - SQL: {sql_query}")

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
            logger.info("STEP 8: No citations found, using generated text as result")
            results.append({
                'bot_id': bot.id,
                'content': generated_text,
                'source_name': 'SQL Knowledge Base Response',
                'source_link': '',
                'rank': 1,
                'metadata': {},
                'page_number': None,
            })

        logger.info(f"STEP 9: Returning {len(results)} results")
        for i, result in enumerate(results):
            logger.info(f"  Result {i+1}:")
            logger.info(f"    - Content: {result['content'][:100]}...")
            logger.info(f"    - Source: {result['source_name']}")

        logger.info("=" * 80)
        return results

    except ClientError as e:
        logger.error("=" * 80)
        logger.error(f"ERROR: SQL KB query failed!")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Error message: {str(e)}")
        logger.error(f"Error code: {e.response.get('Error', {}).get('Code', 'Unknown')}")
        logger.error(f"Error details: {e.response.get('Error', {}).get('Message', 'Unknown')}")
        logger.error("=" * 80)
        raise e
