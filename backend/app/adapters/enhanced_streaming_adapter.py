"""
Enhanced streaming protocol adapter with buffering and error recovery.

Provides advanced streaming capabilities including buffering, error recovery,
and performance monitoring for production use.
"""

import logging
import time
from typing import Callable, Dict, Any, Optional, List
from collections import deque

from app.adapters.streaming_adapter import StreamingProtocolAdapter

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class EnhancedStreamingProtocolAdapter(StreamingProtocolAdapter):
    """
    Enhanced streaming adapter with buffering and error recovery.
    """
    
    def __init__(self, legacy_on_stream: Callable[[str], None] = None, buffer_size: int = 100):
        """
        Initialize enhanced streaming adapter.
        
        Args:
            legacy_on_stream: Legacy streaming callback
            buffer_size: Size of streaming buffer
        """
        super().__init__(legacy_on_stream)
        self.buffer_size = buffer_size
        self.stream_buffer = deque(maxlen=buffer_size)
        self.error_count = 0
        self.start_time = time.time()
        self.chunk_count = 0
        
    def on_stream(self, text: str) -> None:
        """
        Enhanced text streaming with buffering and error recovery.
        
        Args:
            text: Streaming text content
        """
        try:
            self.chunk_count += 1
            self.stream_buffer.append({
                "type": "text",
                "content": text,
                "timestamp": time.time(),
                "chunk_id": self.chunk_count
            })
            
            if self.legacy_on_stream:
                self.legacy_on_stream(text)
                
        except Exception as e:
            self.error_count += 1
            logger.error(f"Streaming error (count: {self.error_count}): {e}")
            
            # Attempt recovery for non-critical errors
            if self.error_count < 5 and self.legacy_on_stream:
                try:
                    self.legacy_on_stream(f"[Streaming resumed after error]")
                except:
                    logger.error("Failed to recover streaming")
    
    def on_tool_use(self, tool_name: str, tool_input: Dict[str, Any]) -> None:
        """
        Enhanced tool usage with detailed logging.
        
        Args:
            tool_name: Name of the tool being used
            tool_input: Input parameters for the tool
        """
        try:
            tool_info = {
                "type": "tool_use",
                "tool_name": tool_name,
                "input_keys": list(tool_input.keys()) if tool_input else [],
                "timestamp": time.time(),
                "chunk_id": self.chunk_count + 1
            }
            
            self.stream_buffer.append(tool_info)
            
            logger.info(f"Tool usage: {tool_name} with {len(tool_input)} parameters")
            
            if self.legacy_on_stream:
                tool_message = f"[Using {tool_name}...]"
                self.legacy_on_stream(tool_message)
                
        except Exception as e:
            self.error_count += 1
            logger.error(f"Tool use streaming error: {e}")
    
    def get_streaming_stats(self) -> Dict[str, Any]:
        """
        Get streaming performance statistics.
        
        Returns:
            Dictionary with streaming metrics
        """
        duration = time.time() - self.start_time
        
        return {
            "duration_seconds": duration,
            "chunk_count": self.chunk_count,
            "error_count": self.error_count,
            "chunks_per_second": self.chunk_count / duration if duration > 0 else 0,
            "buffer_size": len(self.stream_buffer),
            "success_rate": (self.chunk_count - self.error_count) / max(self.chunk_count, 1)
        }
    
    def get_buffer_contents(self) -> List[Dict[str, Any]]:
        """
        Get current buffer contents for debugging.
        
        Returns:
            List of buffered streaming events
        """
        return list(self.stream_buffer)
