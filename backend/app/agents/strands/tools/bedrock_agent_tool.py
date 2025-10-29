"""
Strands nested agent tool for Bedrock Agent integration.

Models nested Bedrock agents as Strands sub-agents using the agents-as-tools pattern,
preserving trace log formatting and session management.
"""

import logging
import uuid
from typing import Any, Dict, List

from app.repositories.models.custom_bot import BotModel, AgentModel
from app.utils import get_bedrock_agent_client, get_bedrock_agent_runtime_client

# Strands imports (will be available when dependencies are installed)
# from strands import tool, Agent

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class StrandsBedrockAgent:
    """Wrapper for Bedrock Agent as Strands sub-agent."""
    
    def __init__(self, agent_id: str, alias_id: str):
        """
        Initialize Bedrock Agent wrapper.
        
        Args:
            agent_id: Bedrock Agent ID
            alias_id: Agent alias ID
        """
        self.agent_id = agent_id
        self.alias_id = alias_id
        self.runtime_client = get_bedrock_agent_runtime_client()
        self.client = get_bedrock_agent_client()
        
        # Get agent description for tool documentation
        self.description = self._get_agent_description()
        
        logger.info(f"Initialized Strands Bedrock Agent: {agent_id}/{alias_id}")

    def _get_agent_description(self) -> str:
        """Get agent description from Bedrock."""
        try:
            response = self.client.get_agent(agentId=self.agent_id)
            return response.get("agent", {}).get("description", "Bedrock Agent")
        except Exception as e:
            logger.error(f"Failed to get agent description: {e}")
            return "Bedrock Agent"

    def invoke(self, input_text: str, session_id: str = None) -> Dict[str, Any]:
        """
        Invoke the Bedrock Agent.
        
        Args:
            input_text: Query to send to the agent
            session_id: Optional session ID for conversation continuity
            
        Returns:
            Dictionary with response text and trace logs
        """
        if not session_id:
            session_id = str(uuid.uuid4())
            
        try:
            logger.info(f"Invoking Bedrock Agent: {self.agent_id}/{self.alias_id}")
            
            response = self.runtime_client.invoke_agent(
                agentId=self.agent_id,
                agentAliasId=self.alias_id,
                inputText=input_text,
                sessionId=session_id,
                enableTrace=True,
            )

            # Process response and preserve trace logs
            result_text = []
            trace_logs = []

            for event in response["completion"]:
                if "chunk" in event:
                    chunk = event["chunk"]
                    if "bytes" in chunk:
                        result_text.append(chunk["bytes"].decode("utf-8"))
                elif "trace" in event:
                    trace_logs.append(event["trace"])

            return {
                "response": "".join(result_text),
                "trace_logs": trace_logs,
                "session_id": session_id,
                "agent_id": self.agent_id,
                "alias_id": self.alias_id,
            }

        except Exception as e:
            logger.error(f"Bedrock Agent invocation failed: {e}")
            return {
                "response": f"Agent invocation failed: {str(e)}",
                "trace_logs": [],
                "session_id": session_id,
                "error": str(e),
            }


def create_bedrock_agent_tool(agent_config: AgentModel):
    """
    Create a Strands tool for Bedrock Agent invocation.
    
    Args:
        agent_config: Agent configuration with Bedrock Agent details
        
    Returns:
        Strands tool function decorated with @tool
    """
    agent_id = agent_config.bedrock_agent_id
    alias_id = agent_config.bedrock_agent_alias_id
    
    # Initialize the Bedrock Agent wrapper
    bedrock_agent = StrandsBedrockAgent(agent_id, alias_id)
    
    logger.info(f"Creating Bedrock Agent tool: {agent_id}")
    
    # TODO: Implement when strands-agents is available
    # @tool(description=f"Invoke Bedrock Agent: {bedrock_agent.description}")
    def invoke_bedrock_agent(input_text: str) -> Dict[str, Any]:
        """
        Invoke a nested Bedrock Agent.
        
        Args:
            input_text: Query to send to the Bedrock Agent
            
        Returns:
            Agent response with trace logs preserved
        """
        logger.info(f"Invoking nested Bedrock Agent with query: {input_text}")
        
        result = bedrock_agent.invoke(input_text)
        
        # Format for Strands consumption while preserving trace logs
        return {
            "content": result["response"],
            "source": f"Bedrock Agent ({agent_id})",
            "metadata": {
                "agent_id": result.get("agent_id"),
                "alias_id": result.get("alias_id"),
                "session_id": result.get("session_id"),
                "trace_logs": result.get("trace_logs", []),
                "has_error": "error" in result,
            }
        }
    
    return invoke_bedrock_agent


def get_bedrock_agent_tools(bot: BotModel) -> List[Any]:
    """
    Get all Bedrock Agent tools for a bot.
    
    Args:
        bot: Bot model with agent configuration
        
    Returns:
        List of Strands tools for Bedrock Agent invocation
    """
    tools = []
    
    # Check if bot has Bedrock Agent configured
    for tool_config in bot.agent.tools:
        if tool_config.name == "bedrock_agent" and tool_config.enabled:
            if hasattr(bot.agent, 'bedrock_agent_id') and bot.agent.bedrock_agent_id:
                bedrock_tool = create_bedrock_agent_tool(bot.agent)
                tools.append(bedrock_tool)
                logger.info(f"Added Bedrock Agent tool for bot {bot.id}")
                break
    
    return tools
