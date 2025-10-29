"""
Strands chat orchestrator for Bedrock Chat.

Replaces custom agentic loop with Strands model-driven approach while
maintaining compatibility with existing ChatOutput schema.
"""

import logging
from typing import Callable, Dict, List, Any

from app.agents.strands.base_agent import StrandsAgentWrapper
from app.agents.strands.tools.knowledge_tool import get_knowledge_tools
from app.agents.strands.tools.gateway_tools import get_internet_search_tools
from app.agents.strands.tools.bedrock_agent_tool import get_bedrock_agent_tools
from app.repositories.models.custom_bot import BotModel
from app.repositories.models.conversation import (
    ConversationModel,
    MessageModel,
    RelatedDocumentModel,
)
from app.routes.schemas.conversation import (
    ChatInput,
    ChatOutput,
    Chunk,
    MessageOutput,
    type_model_name,
)
from app.prompt import build_rag_prompt

# Strands imports (will be available when dependencies are installed)
# from strands import Agent

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class StrandsChatOrchestrator:
    """
    Orchestrates chat conversations using Strands agent framework.
    
    Replaces the custom agentic loop with Strands' model-driven approach
    while maintaining compatibility with existing ChatOutput schema.
    """
    
    def __init__(self, bot: BotModel, model_name: type_model_name):
        """
        Initialize the Strands chat orchestrator.
        
        Args:
            bot: Bot configuration model
            model_name: The model identifier
        """
        self.bot = bot
        self.model_name = model_name
        
        # Initialize Strands agent wrapper
        self.agent_wrapper = StrandsAgentWrapper(bot, model_name)
        
        # Collect all tools for this bot
        self.tools = self._collect_tools()
        
        logger.info(f"Initialized Strands orchestrator for bot {bot.id} with {len(self.tools)} tools")

    def _collect_tools(self) -> List[Any]:
        """
        Collect all tools available for this bot.
        
        Returns:
            List of Strands tools
        """
        tools = []
        
        # Knowledge base tools
        knowledge_tools = get_knowledge_tools(self.bot)
        tools.extend(knowledge_tools)
        
        # Internet search tools
        internet_tools = get_internet_search_tools(self.bot)
        tools.extend(internet_tools)
        
        # Bedrock Agent tools
        bedrock_agent_tools = get_bedrock_agent_tools(self.bot)
        tools.extend(bedrock_agent_tools)
        
        logger.info(f"Collected tools: {len(knowledge_tools)} knowledge, {len(internet_tools)} internet, {len(bedrock_agent_tools)} bedrock agent")
        
        return tools

    def _prepare_conversation_history(self, conversation: ConversationModel) -> List[Dict[str, Any]]:
        """
        Prepare conversation history for Strands agent.
        
        Args:
            conversation: Conversation model with message history
            
        Returns:
            List of messages in Strands format
        """
        messages = []
        
        for message in conversation.message_map.values():
            if message.role == "user":
                messages.append({
                    "role": "user",
                    "content": message.content[0].body if message.content else ""
                })
            elif message.role == "assistant":
                content = ""
                if message.content:
                    for content_item in message.content:
                        if hasattr(content_item, 'body'):
                            content += content_item.body
                
                messages.append({
                    "role": "assistant", 
                    "content": content
                })
        
        return messages

    def _handle_non_tooluse_rag(self, user_message: str) -> str:
        """
        Handle RAG prompt injection for non-tool-use models.
        
        Args:
            user_message: Original user message
            
        Returns:
            Modified message with RAG context injected
        """
        if not self.agent_wrapper.supports_tool_use() and self.bot.bedrock_knowledge_base:
            logger.info("Non-tool-use model detected, injecting RAG context")
            
            # Use existing RAG prompt building logic
            rag_prompt = build_rag_prompt(
                bot=self.bot,
                query=user_message,
                model=self.model_name
            )
            
            return rag_prompt
        
        return user_message

    def chat(
        self,
        chat_input: ChatInput,
        conversation: ConversationModel,
        on_stream: Callable[[str], None] = None,
        on_tool_use: Callable[[str, Dict[str, Any]], None] = None,
        on_tool_result: Callable[[str, Any], None] = None,
        on_reasoning: Callable[[str], None] = None,
    ) -> ChatOutput:
        """
        Execute chat conversation using Strands orchestration.
        
        Args:
            chat_input: User input and configuration
            conversation: Conversation context
            on_stream: Streaming text callback
            on_tool_use: Tool usage callback
            on_tool_result: Tool result callback
            on_reasoning: Reasoning content callback
            
        Returns:
            ChatOutput with response and metadata
        """
        logger.info(f"Starting Strands chat for bot {self.bot.id}")
        
        try:
            # Prepare conversation history
            history = self._prepare_conversation_history(conversation)
            
            # Handle RAG for non-tool-use models
            user_message = self._handle_non_tooluse_rag(chat_input.message)
            
            # Initialize agent with tools (when Strands is available)
            self.agent_wrapper._initialize_strands_agent(self.tools)
            
            # Invoke Strands agent
            result = self.agent_wrapper.invoke(
                user_message=user_message,
                conversation_history=history,
                on_stream=on_stream,
                on_tool_use=on_tool_use,
                on_tool_result=on_tool_result,
                on_reasoning=on_reasoning,
            )
            
            # Convert Strands result to ChatOutput format
            return self._convert_to_chat_output(result, chat_input)
            
        except Exception as e:
            logger.error(f"Strands chat failed: {e}")
            
            # Fallback response
            return ChatOutput(
                conversation_id=conversation.id,
                message=MessageOutput(
                    role="assistant",
                    content=[{
                        "content_type": "text",
                        "body": f"I apologize, but I encountered an error: {str(e)}"
                    }],
                    model=self.model_name,
                    children=[],
                    parent=None,
                    create_time=0.0,
                    feedback=None,
                    used_chunks=None,
                    thinking=None,
                ),
                bot_id=self.bot.id,
                create_time=0.0,
                suggested_follow_ups=[],
            )

    def _convert_to_chat_output(self, strands_result: Dict[str, Any], chat_input: ChatInput) -> ChatOutput:
        """
        Convert Strands agent result to ChatOutput format.
        
        Args:
            strands_result: Result from Strands agent invocation
            chat_input: Original chat input
            
        Returns:
            ChatOutput in expected format
        """
        # Extract response message
        message_text = strands_result.get("message", "No response")
        
        # Extract related documents from tool uses
        related_documents = []
        for doc in strands_result.get("related_documents", []):
            if isinstance(doc, dict):
                related_documents.append(RelatedDocumentModel(
                    content=doc.get("content", ""),
                    source_id=doc.get("source_id", ""),
                    source_name=doc.get("source_name", ""),
                    source_link=doc.get("source_link", ""),
                    page_number=doc.get("page_number"),
                ))
        
        # Create message output
        message_output = MessageOutput(
            role="assistant",
            content=[{
                "content_type": "text",
                "body": message_text
            }],
            model=self.model_name,
            children=[],
            parent=None,
            create_time=0.0,
            feedback=None,
            used_chunks=related_documents if related_documents else None,
            thinking=None,
        )
        
        return ChatOutput(
            conversation_id=chat_input.conversation_id or "",
            message=message_output,
            bot_id=self.bot.id,
            create_time=0.0,
            suggested_follow_ups=[],
        )


def create_strands_chat_orchestrator(bot: BotModel, model_name: type_model_name) -> StrandsChatOrchestrator:
    """
    Create a Strands chat orchestrator for the given bot.
    
    Args:
        bot: Bot configuration model
        model_name: The model identifier
        
    Returns:
        Configured StrandsChatOrchestrator instance
    """
    return StrandsChatOrchestrator(bot, model_name)
