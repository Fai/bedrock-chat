import logging
import traceback

from app.agents.tools.agent_tool import AgentTool
from app.repositories.models.custom_bot import BotModel
from app.routes.schemas.conversation import type_model_name
from app.vector_search import search_related_docs
from app.sql_kb_search import search_sql_knowledge_base

from pydantic import BaseModel, Field


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class KnowledgeToolInput(BaseModel):
    query: str = Field(
        description="A natural language question to search the knowledge base. Use plain English only - NEVER generate SQL queries yourself. Examples: 'What is the price of Yoga Mat?', 'Show me product information'. The system handles all technical query conversion automatically."
    )


def search_knowledge(
    tool_input: KnowledgeToolInput, bot: BotModel | None, model: type_model_name | None
) -> list:
    assert bot is not None

    query = tool_input.query
    logger.info(f"Running AnswerWithKnowledgeTool with query: {query}")

    try:
        # Check if this is a SQL Knowledge Base
        is_sql_kb = False
        if bot.bedrock_knowledge_base:
            if hasattr(bot.bedrock_knowledge_base, 'knowledge_base_type'):
                is_sql_kb = bot.bedrock_knowledge_base.knowledge_base_type == "SQL"  # type: ignore

        # Use appropriate search method based on KB type
        if is_sql_kb:
            logger.info("Using SQL Knowledge Base search (retrieve_and_generate)")
            search_results = search_sql_knowledge_base(bot, query=query)
        else:
            logger.info("Using vector/hybrid search (retrieve)")
            search_results = search_related_docs(bot, query=query)

        return search_results

    except Exception as e:
        error_traceback = traceback.format_exc()
        logger.error(
            f"Failed to run AnswerWithKnowledgeTool: {e}\nTraceback: {error_traceback}"
        )
        raise e


def create_knowledge_tool(bot: BotModel) -> AgentTool:
    # Check if this is a SQL Knowledge Base
    is_sql_kb = False
    if bot.bedrock_knowledge_base:
        # Check if it has knowledge_base_type attribute (SqlKnowledgeBaseModel)
        if hasattr(bot.bedrock_knowledge_base, 'knowledge_base_type'):
            is_sql_kb = bot.bedrock_knowledge_base.knowledge_base_type == "SQL"  # type: ignore

    logger.info(f"Creating knowledge tool - SQL KB: {is_sql_kb}, Has KB: {bot.bedrock_knowledge_base is not None}")

    kb_info = bot.knowledge.__str_in_claude_format__()

    if is_sql_kb:
        description = (
            "Retrieve information to answer the user's question. "
            "IMPORTANT: Provide your query as a simple natural language question in plain English. "
            "Example: 'What is the price of Yoga Mat?' or 'Air Fryer product information'. "
            "DO NOT use technical syntax - just ask the question naturally. "
            "Available information: {}".format(kb_info)
        )
        logger.info("Using SQL KB tool description (natural language queries)")
    else:
        description = (
            "Answer a user's question using information. The description is: {}".format(kb_info)
        )
        logger.info("Using vector search tool description")

    logger.info(f"Knowledge base tool description: {description}")
    return AgentTool(
        name=f"knowledge_base_tool",
        description=description,
        args_schema=KnowledgeToolInput,
        function=search_knowledge,
    )
