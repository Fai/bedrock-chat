"""
Enhanced conversation storage adapter with metadata and tool result handling.

Extends the base conversation adapter with advanced features for tool results,
metadata preservation, and enhanced compatibility.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.adapters.conversation_adapter import ConversationStorageAdapter
from app.repositories.models.conversation import (
    MessageModel,
    TextContentModel,
    ToolUseContentModel,
    ToolResultContentModel,
    RelatedDocumentModel,
    TextToolResultModel,
)
from app.routes.schemas.conversation import ChatOutput

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class EnhancedConversationStorageAdapter(ConversationStorageAdapter):
    """
    Enhanced adapter with tool result handling and metadata preservation.
    """
    
    @staticmethod
    def adapt_with_tool_results(chat_output: ChatOutput, tool_results: List[Dict[str, Any]] = None) -> MessageModel:
        """
        Convert ChatOutput to MessageModel with tool results.
        
        Args:
            chat_output: Chat output from Strands orchestrator
            tool_results: Optional tool execution results
            
        Returns:
            MessageModel with tool results and metadata
        """
        message_output = chat_output.message
        
        # Convert content with tool results
        content = []
        
        # Add tool use content if present
        if tool_results:
            for tool_result in tool_results:
                if tool_result.get("type") == "tool_use":
                    content.append(ToolUseContentModel(
                        tool_use_id=tool_result.get("id", ""),
                        name=tool_result.get("name", ""),
                        input=tool_result.get("input", {})
                    ))
                elif tool_result.get("type") == "tool_result":
                    content.append(ToolResultContentModel(
                        tool_use_id=tool_result.get("tool_use_id", ""),
                        content=[TextToolResultModel(
                            text=str(tool_result.get("content", ""))
                        )]
                    ))
        
        # Add text content
        for content_item in message_output.content:
            if content_item.get("content_type") == "text":
                content.append(TextContentModel(
                    body=content_item["body"]
                ))
        
        # Enhanced related documents with metadata
        related_docs = []
        if message_output.used_chunks:
            for chunk in message_output.used_chunks:
                if isinstance(chunk, RelatedDocumentModel):
                    related_docs.append(chunk)
                elif isinstance(chunk, dict):
                    related_docs.append(RelatedDocumentModel(
                        content=TextToolResultModel(
                            text=chunk.get("content", "")
                        ),
                        source_id=chunk.get("source_id", ""),
                        source_name=chunk.get("source_name", ""),
                        source_link=chunk.get("source_link", ""),
                        page_number=chunk.get("page_number"),
                    ))
        
        # Create enhanced MessageModel
        message = MessageModel(
            role=message_output.role,
            content=content,
            model=message_output.model,
            children=message_output.children,
            parent=message_output.parent,
            create_time=message_output.create_time or datetime.now().timestamp(),
            feedback=message_output.feedback,
            used_chunks=related_docs if related_docs else None,
            thinking=message_output.thinking,
        )
        
        logger.info(f"Enhanced adapter: {len(content)} content items, {len(related_docs)} documents")
        return message
    
    @staticmethod
    def preserve_metadata(chat_output: ChatOutput) -> Dict[str, Any]:
        """
        Extract and preserve metadata from Strands output.
        
        Args:
            chat_output: Chat output from Strands
            
        Returns:
            Metadata dictionary for storage
        """
        metadata = {
            "bot_id": chat_output.bot_id,
            "create_time": chat_output.create_time,
            "conversation_id": chat_output.conversation_id,
            "suggested_follow_ups": chat_output.suggested_follow_ups,
        }
        
        # Add token usage if available
        if hasattr(chat_output, 'token_usage'):
            metadata["token_usage"] = chat_output.token_usage
        
        # Add tool usage statistics
        if hasattr(chat_output.message, 'tool_calls'):
            metadata["tool_calls_count"] = len(chat_output.message.tool_calls)
        
        return metadata
