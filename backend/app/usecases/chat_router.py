"""
Chat router for AgentCore and legacy implementations.

Routes chat requests between legacy Bedrock implementation and new
AgentCore/Strands implementation based on feature flags and bot configuration.
"""

import logging
from typing import Callable

from app.agents.strands.config import is_agentcore_enabled
from app.repositories.models.custom_bot import BotModel
from app.repositories.models.conversation import ConversationModel
from app.routes.schemas.conversation import ChatInput, ChatOutput, type_model_name
from app.usecases.strands_chat import create_strands_chat_orchestrator
from app.usecases.chat import chat as legacy_chat

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def route_chat_request(
    chat_input: ChatInput,
    bot: BotModel,
    model_name: type_model_name,
    conversation: ConversationModel,
    on_stream: Callable[[str], None] = None,
    **kwargs
) -> ChatOutput:
    """
    Route chat request to appropriate implementation.
    
    Args:
        chat_input: User input and configuration
        bot: Bot configuration
        model_name: Model identifier
        conversation: Conversation context
        on_stream: Streaming callback
        **kwargs: Additional arguments for legacy chat
        
    Returns:
        ChatOutput from appropriate implementation
    """
    # Check if AgentCore is enabled globally
    if not is_agentcore_enabled():
        logger.info("AgentCore disabled - routing to legacy implementation")
        return legacy_chat(
            chat_input=chat_input,
            bot=bot,
            model_name=model_name,
            conversation=conversation,
            on_stream=on_stream,
            **kwargs
        )
    
    # Check bot-specific AgentCore enablement (future enhancement)
    # For now, use global setting
    
    logger.info(f"AgentCore enabled - routing to Strands implementation for bot {bot.id}")
    
    try:
        # Create Strands orchestrator
        orchestrator = create_strands_chat_orchestrator(bot, model_name)
        
        # Convert streaming callback for Strands format
        def strands_stream_callback(text: str):
            if on_stream:
                on_stream(text)
        
        # Execute via Strands
        return orchestrator.chat(
            chat_input=chat_input,
            conversation=conversation,
            on_stream=strands_stream_callback,
        )
        
    except Exception as e:
        logger.error(f"Strands chat failed, falling back to legacy: {e}")
        
        # Fallback to legacy implementation
        return legacy_chat(
            chat_input=chat_input,
            bot=bot,
            model_name=model_name,
            conversation=conversation,
            on_stream=on_stream,
            **kwargs
        )
