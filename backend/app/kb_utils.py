"""Knowledge Base utilities for type detection and routing."""

import logging
from app.repositories.models.custom_bot import BotModel

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Module loaded marker for debugging
logger.info("=== KB_UTILS MODULE LOADED - VERSION 2025-10-03-08:50 ===")



def detect_kb_type(bot: BotModel) -> str:
    """Detect the Knowledge Base type (SQL or VECTOR).

    Returns: "SQL" or "VECTOR"
    """
    if not bot.bedrock_knowledge_base:
        return "VECTOR"

    # First check if it has knowledge_base_type attribute (SqlKnowledgeBaseModel)
    if hasattr(bot.bedrock_knowledge_base, 'knowledge_base_type'):
        kb_type = bot.bedrock_knowledge_base.knowledge_base_type  # type: ignore
        logger.info(f"Bot has knowledge_base_type attribute: {kb_type}")
        return kb_type

    # Fallback: Check via Bedrock API
    from app.repositories.knowledge_base import get_knowledge_base_info
    knowledge_base_id = (
        bot.bedrock_knowledge_base.exist_knowledge_base_id
        if bot.bedrock_knowledge_base.exist_knowledge_base_id is not None
        else bot.bedrock_knowledge_base.knowledge_base_id
    )
    if knowledge_base_id:
        logger.info(f"Checking KB type via Bedrock API for KB ID: {knowledge_base_id}")
        try:
            kb_info = get_knowledge_base_info(knowledge_base_id=knowledge_base_id)
            kb_config_type = kb_info.knowledge_base.knowledge_base_configuration.type
            logger.info(f"KB type from Bedrock API: {kb_config_type}")
            return kb_config_type
        except Exception as e:
            logger.warning(f"Failed to get KB info from Bedrock API: {e}")

    return "VECTOR"
