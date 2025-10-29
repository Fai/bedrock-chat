"""
Conversation storage adapter for Strands integration.

Adapts Strands chat output to existing conversation storage format,
maintaining compatibility with existing database schema and UI expectations.
"""

import logging
from typing import List, Dict, Any

from app.repositories.models.conversation import (
    MessageModel,
    TextContentModel,
    RelatedDocumentModel,
)
from app.routes.schemas.conversation import ChatOutput, MessageOutput

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class ConversationStorageAdapter:
    """
    Adapter for converting Strands chat output to conversation storage format.
    
    Ensures compatibility between Strands agent responses and existing
    conversation storage schema.
    """
    
    @staticmethod
    def adapt_chat_output_to_message(chat_output: ChatOutput) -> MessageModel:
        """
        Convert ChatOutput to MessageModel for storage.
        
        Args:
            chat_output: Chat output from Strands orchestrator
            
        Returns:
            MessageModel compatible with existing storage
        """
        message_output = chat_output.message
        
        # Convert content
        content = []
        for content_item in message_output.content:
            if content_item.get("content_type") == "text":
                content.append(TextContentModel(
                    body=content_item["body"]
                ))
        
        # Convert related documents
        related_docs = []
        if message_output.used_chunks:
            for chunk in message_output.used_chunks:
                if isinstance(chunk, RelatedDocumentModel):
                    related_docs.append(chunk)
                elif isinstance(chunk, dict):
                    related_docs.append(RelatedDocumentModel(
                        content=chunk.get("content", ""),
                        source_id=chunk.get("source_id", ""),
                        source_name=chunk.get("source_name", ""),
                        source_link=chunk.get("source_link", ""),
                        page_number=chunk.get("page_number"),
                    ))
        
        # Create MessageModel
        message = MessageModel(
            role=message_output.role,
            content=content,
            model=message_output.model,
            children=message_output.children,
            parent=message_output.parent,
            create_time=message_output.create_time,
            feedback=message_output.feedback,
            used_chunks=related_docs if related_docs else None,
            thinking=message_output.thinking,
        )
        
        logger.info(f"Adapted Strands output to MessageModel with {len(content)} content items")
        return message
    
    @staticmethod
    def adapt_streaming_chunk(chunk_data: Dict[str, Any]) -> str:
        """
        Adapt Strands streaming chunk to legacy format.
        
        Args:
            chunk_data: Streaming chunk from Strands
            
        Returns:
            Text content for streaming
        """
        if isinstance(chunk_data, dict):
            chunk_type = chunk_data.get("type", "text")
            
            if chunk_type == "text":
                return chunk_data.get("content", "")
            elif chunk_type == "tool_use":
                # Log tool usage but don't stream it
                logger.info(f"Tool used: {chunk_data.get('tool_name', 'unknown')}")
                return ""
            elif chunk_type == "reasoning":
                # Handle reasoning content
                return f"[Thinking: {chunk_data.get('content', '')}]"
            
        return str(chunk_data) if chunk_data else ""
