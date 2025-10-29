"""
Base Strands agent wrapper for Bedrock Chat.

This module provides the StrandsAgentWrapper class that bridges the existing
BotModel configuration with the Strands agent framework, enabling a gradual
migration from custom Bedrock implementation to Strands.
"""

import logging
from typing import Any, Callable, Optional

from app.repositories.models.custom_bot import BotModel, GenerationParamsModel
from app.routes.schemas.conversation import type_model_name

# Strands imports will be added when dependencies are installed
# from strands import Agent, tool
# from strands.models import BedrockModel

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class StrandsAgentWrapper:
    """
    Wrapper class that converts BotModel configuration to Strands Agent.

    This class acts as a bridge between the existing Bedrock Chat architecture
    and the new Strands agent framework, enabling gradual migration without
    breaking existing functionality.

    Key responsibilities:
    - Map BotModel to Strands Agent configuration
    - Convert generation parameters to Strands format
    - Handle model initialization with appropriate settings
    - Provide streaming callback integration
    - Support both tool-use and non-tool-use models

    Example:
        ```python
        bot = get_bot_by_id(bot_id)
        agent_wrapper = StrandsAgentWrapper(bot, model_name="claude-3-5-sonnet")

        # Use agent with streaming
        result = agent_wrapper.invoke(
            user_message="What is the capital of France?",
            on_stream=lambda text: print(text, end=""),
            on_tool_use=lambda tool_name, tool_input: print(f"Using {tool_name}"),
        )
        ```
    """

    def __init__(
        self,
        bot: BotModel,
        model_name: type_model_name,
        bedrock_region: str = "us-east-1",
    ):
        """
        Initialize the Strands agent wrapper.

        Args:
            bot: The bot configuration model
            model_name: The model identifier (e.g., "claude-3-5-sonnet")
            bedrock_region: AWS region for Bedrock service
        """
        self.bot = bot
        self.model_name = model_name
        self.bedrock_region = bedrock_region

        # Extract configuration
        self.instruction = bot.instruction
        self.generation_params = bot.generation_params
        self.agent_config = bot.agent

        # Initialize agent (will be implemented when strands is available)
        self.agent = None

        logger.info(f"Initialized StrandsAgentWrapper for bot {bot.id} with model {model_name}")

    def _build_system_prompt(self) -> str:
        """
        Build the system prompt from bot instruction.

        Returns:
            System prompt string
        """
        return self.instruction

    def _map_generation_params(self) -> dict[str, Any]:
        """
        Map GenerationParamsModel to Strands-compatible format.

        Converts the bot's generation parameters to the format expected by
        Strands and the underlying Bedrock models.

        Returns:
            Dictionary of generation parameters
        """
        params = self.generation_params

        # Map to Strands format
        strands_params = {
            "temperature": params.temperature,
            "top_p": params.top_p,
            "max_tokens": params.max_tokens,
        }

        # Add optional parameters if present
        if hasattr(params, "top_k") and params.top_k is not None:
            strands_params["top_k"] = params.top_k

        if hasattr(params, "stop_sequences") and params.stop_sequences:
            strands_params["stop_sequences"] = params.stop_sequences

        # Handle reasoning parameters if present
        if hasattr(params, "reasoning_params") and params.reasoning_params:
            reasoning = params.reasoning_params
            if reasoning.enabled:
                strands_params["reasoning"] = {
                    "enabled": True,
                    "budget_tokens": reasoning.budget_tokens,
                }

        return strands_params

    def _initialize_strands_agent(self, tools: Optional[list[Any]] = None):
        """
        Initialize the Strands Agent with configuration.

        This method will be implemented once strands-agents is available.
        It will create the actual Strands Agent instance with:
        - Model configuration (Bedrock + region)
        - System prompt
        - Generation parameters
        - Tools (if provided)

        Args:
            tools: Optional list of Strands tools
        """
        # TODO: Implement when strands-agents is available
        # from strands import Agent
        # from strands.models import BedrockModel

        # model = BedrockModel(
        #     model_id=self.model_name,
        #     region=self.bedrock_region,
        #     **self._map_generation_params()
        # )

        # self.agent = Agent(
        #     model=model,
        #     system_prompt=self._build_system_prompt(),
        #     tools=tools or [],
        # )

        logger.warning("Strands agent initialization not yet implemented (dependencies pending)")

    def invoke(
        self,
        user_message: str,
        conversation_history: Optional[list[dict[str, Any]]] = None,
        on_stream: Optional[Callable[[str], None]] = None,
        on_tool_use: Optional[Callable[[str, dict[str, Any]], None]] = None,
        on_tool_result: Optional[Callable[[str, Any], None]] = None,
        on_reasoning: Optional[Callable[[str], None]] = None,
    ) -> dict[str, Any]:
        """
        Invoke the Strands agent with a user message.

        This method provides the main interface for interacting with the agent,
        supporting streaming callbacks and tool execution feedback.

        Args:
            user_message: The user's input message
            conversation_history: Optional list of previous messages
            on_stream: Callback for streaming text chunks
            on_tool_use: Callback when agent uses a tool (tool_name, input_dict)
            on_tool_result: Callback with tool execution results
            on_reasoning: Callback for reasoning/thinking content

        Returns:
            Dictionary containing:
                - message: The final agent response
                - tool_uses: List of tools used
                - related_documents: Documents retrieved from tools
                - token_usage: Token consumption statistics
        """
        if self.agent is None:
            logger.error("Strands agent not initialized - falling back to error response")
            return {
                "message": "Agent not yet initialized. Strands dependencies pending.",
                "tool_uses": [],
                "related_documents": [],
                "token_usage": {},
            }

        # TODO: Implement actual Strands agent invocation
        # This will use the Strands Agent API to:
        # 1. Process the message with conversation history
        # 2. Stream responses via callbacks
        # 3. Execute tools as needed
        # 4. Return structured results

        logger.warning("Strands agent invocation not yet implemented")
        return {
            "message": "Not implemented",
            "tool_uses": [],
            "related_documents": [],
            "token_usage": {},
        }

    def get_tools(self) -> list[Any]:
        """
        Get the list of tools configured for this bot.

        Returns the tools based on the bot's agent configuration,
        including knowledge base access, internet search, and nested agents.

        Returns:
            List of Strands tool objects
        """
        tools = []

        # TODO: Implement tool loading based on bot.agent.tools
        # This will be implemented in Phase 2.2-2.4:
        # - Knowledge base tool (Phase 2.2)
        # - Internet search via Gateway (Phase 2.3)
        # - Nested Bedrock agents (Phase 2.4)

        logger.info(f"Loading {len(self.agent_config.tools)} tools for bot {self.bot.id}")

        return tools

    def supports_streaming(self) -> bool:
        """
        Check if the current model supports streaming.

        Returns:
            True if streaming is supported
        """
        # All modern Bedrock models support streaming
        return True

    def supports_tool_use(self) -> bool:
        """
        Check if the current model supports tool use.

        This checks against the model capabilities to determine if
        the agent can use tools or if RAG must be prompt-based.

        Returns:
            True if tool use is supported
        """
        # Import the tool use check from existing bedrock module
        try:
            from app.bedrock import is_tooluse_supported
            return is_tooluse_supported(self.model_name)
        except ImportError:
            logger.warning("Could not import is_tooluse_supported, assuming true")
            return True

    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"StrandsAgentWrapper("
            f"bot_id={self.bot.id}, "
            f"model={self.model_name}, "
            f"tools={len(self.agent_config.tools)}, "
            f"has_knowledge={self.bot.bedrock_knowledge_base is not None}"
            f")"
        )
