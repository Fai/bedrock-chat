"""
Configuration utilities for AgentCore and Strands integration.

This module provides helpers for accessing AgentCore configuration from
environment variables and managing runtime settings.
"""

import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class AgentCoreConfig:
    """
    Configuration manager for AgentCore infrastructure.

    Reads environment variables set by the CDK infrastructure and provides
    typed access to AgentCore resources.
    """

    def __init__(self):
        """Initialize configuration from environment variables."""
        self.enabled = os.getenv("AGENTCORE_ENABLED", "false").lower() == "true"
        self.runtime_table_name = os.getenv("AGENTCORE_RUNTIME_TABLE_NAME", "")
        self.memory_table_name = os.getenv("AGENTCORE_MEMORY_TABLE_NAME", "")
        self.container_repository_uri = os.getenv("AGENTCORE_CONTAINER_REPOSITORY_URI", "")
        self.build_project_name = os.getenv("AGENTCORE_BUILD_PROJECT_NAME", "")
        self.runtime_execution_role_arn = os.getenv("AGENTCORE_RUNTIME_EXECUTION_ROLE_ARN", "")

        # Bedrock configuration
        self.bedrock_region = os.getenv("BEDROCK_REGION", "us-east-1")

        if self.enabled:
            logger.info("AgentCore is ENABLED - using Strands agent framework")
            self._validate_config()
        else:
            logger.info("AgentCore is DISABLED - using legacy agent implementation")

    def _validate_config(self) -> None:
        """
        Validate that required configuration is present.

        Raises:
            ValueError: If required configuration is missing when AgentCore is enabled
        """
        required_fields = [
            ("runtime_table_name", self.runtime_table_name),
            ("container_repository_uri", self.container_repository_uri),
            ("build_project_name", self.build_project_name),
            ("runtime_execution_role_arn", self.runtime_execution_role_arn),
        ]

        missing = [name for name, value in required_fields if not value]

        if missing:
            logger.error(f"AgentCore enabled but missing required config: {', '.join(missing)}")
            raise ValueError(
                f"AgentCore is enabled but required configuration is missing: {', '.join(missing)}"
            )

        logger.debug("AgentCore configuration validated successfully")

    def is_enabled(self) -> bool:
        """
        Check if AgentCore is enabled.

        Returns:
            True if AgentCore infrastructure is enabled
        """
        return self.enabled

    def has_memory_enabled(self) -> bool:
        """
        Check if AgentCore memory storage is configured.

        Returns:
            True if memory table is available
        """
        return bool(self.memory_table_name)

    def get_runtime_table_name(self) -> str:
        """
        Get the DynamoDB table name for runtime registry.

        Returns:
            Table name for bot-to-runtime mappings
        """
        return self.runtime_table_name

    def get_memory_table_name(self) -> Optional[str]:
        """
        Get the DynamoDB table name for agent memory.

        Returns:
            Table name for memory storage, or None if not configured
        """
        return self.memory_table_name if self.memory_table_name else None

    def get_container_repository_uri(self) -> str:
        """
        Get the ECR repository URI for agent containers.

        Returns:
            ECR repository URI
        """
        return self.container_repository_uri

    def get_build_project_name(self) -> str:
        """
        Get the CodeBuild project name for building agent containers.

        Returns:
            CodeBuild project name
        """
        return self.build_project_name

    def get_runtime_execution_role_arn(self) -> str:
        """
        Get the IAM role ARN for AgentCore runtime execution.

        Returns:
            IAM role ARN
        """
        return self.runtime_execution_role_arn

    def get_bedrock_region(self) -> str:
        """
        Get the AWS region for Bedrock service.

        Returns:
            AWS region name
        """
        return self.bedrock_region

    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"AgentCoreConfig("
            f"enabled={self.enabled}, "
            f"has_memory={self.has_memory_enabled()}, "
            f"region={self.bedrock_region}"
            f")"
        )


# Global configuration instance
_config: Optional[AgentCoreConfig] = None


def get_agentcore_config() -> AgentCoreConfig:
    """
    Get the global AgentCore configuration instance.

    Returns:
        AgentCoreConfig instance (singleton)
    """
    global _config
    if _config is None:
        _config = AgentCoreConfig()
    return _config


def is_agentcore_enabled() -> bool:
    """
    Quick check if AgentCore is enabled.

    Returns:
        True if AgentCore infrastructure is enabled
    """
    return get_agentcore_config().is_enabled()
