"""
Strands agent framework integration for Bedrock Chat.

This module provides the Strands agent wrapper and tools for migrating
from the custom Bedrock implementation to Amazon Bedrock AgentCore and
the Strands agent framework.
"""

from .base_agent import StrandsAgentWrapper

__all__ = ["StrandsAgentWrapper"]
