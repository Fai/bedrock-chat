"""
Streaming protocol adapter for Strands integration.

Adapts Strands streaming callbacks to existing streaming protocol,
maintaining compatibility with frontend expectations.
"""

import logging
from typing import Callable, Dict, Any

from app.adapters.conversation_adapter import ConversationStorageAdapter

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class StreamingProtocolAdapter:
    """
    Adapter for Strands streaming callbacks to legacy streaming format.
    
    Converts Strands streaming events to format expected by existing
    frontend and streaming infrastructure.
    """
    
    def __init__(self, legacy_on_stream: Callable[[str], None] = None):
        """
        Initialize streaming adapter.
        
        Args:
            legacy_on_stream: Legacy streaming callback
        """
        self.legacy_on_stream = legacy_on_stream
        self.conversation_adapter = ConversationStorageAdapter()
    
    def on_stream(self, text: str) -> None:
        """
        Handle text streaming from Strands.
        
        Args:
            text: Streaming text content
        """
        if self.legacy_on_stream:
            self.legacy_on_stream(text)
    
    def on_tool_use(self, tool_name: str, tool_input: Dict[str, Any]) -> None:
        """
        Handle tool usage notification from Strands.
        
        Args:
            tool_name: Name of the tool being used
            tool_input: Input parameters for the tool
        """
        logger.info(f"Tool usage: {tool_name} with input: {tool_input}")
        
        # Optionally stream tool usage notification
        if self.legacy_on_stream:
            tool_message = f"[Using {tool_name}...]"
            self.legacy_on_stream(tool_message)
    
    def on_tool_result(self, tool_name: str, result: Any) -> None:
        """
        Handle tool result from Strands.
        
        Args:
            tool_name: Name of the tool that executed
            result: Result from tool execution
        """
        logger.info(f"Tool result from {tool_name}: {type(result)}")
        
        # Tool results are typically not streamed to user
        # They're incorporated into the final response
    
    def on_reasoning(self, reasoning_content: str) -> None:
        """
        Handle reasoning/thinking content from Strands.
        
        Args:
            reasoning_content: Reasoning or thinking content
        """
        logger.info(f"Reasoning content: {reasoning_content[:100]}...")
        
        # Optionally stream reasoning content
        if self.legacy_on_stream:
            reasoning_message = f"[Thinking: {reasoning_content}]"
            self.legacy_on_stream(reasoning_message)


def create_streaming_adapter(legacy_on_stream: Callable[[str], None] = None) -> StreamingProtocolAdapter:
    """
    Create streaming protocol adapter.
    
    Args:
        legacy_on_stream: Legacy streaming callback
        
    Returns:
        Configured StreamingProtocolAdapter
    """
    return StreamingProtocolAdapter(legacy_on_stream)
