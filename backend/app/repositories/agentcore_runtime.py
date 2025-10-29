"""
AgentCore runtime registry repository.

Manages bot-to-runtime mappings, runtime lifecycle, and metadata storage
in DynamoDB for AgentCore runtime deployment and management.
"""

import logging
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

import boto3
from botocore.exceptions import ClientError

from app.agents.strands.config import get_agentcore_config

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class AgentCoreRuntimeRegistry:
    """
    Registry for managing AgentCore runtime mappings and lifecycle.
    
    Handles CRUD operations for bot-to-runtime mappings, runtime metadata,
    and deployment automation.
    """
    
    def __init__(self):
        """Initialize the runtime registry."""
        self.config = get_agentcore_config()
        self.dynamodb = boto3.resource('dynamodb')
        self.table = self.dynamodb.Table(self.config.get_runtime_table_name())
        self.agentcore_client = boto3.client('bedrock-agentcore')
        
        logger.info("Initialized AgentCore runtime registry")

    def create_runtime(self, bot_id: str, bot_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create new AgentCore runtime for a bot.
        
        Args:
            bot_id: Bot identifier
            bot_config: Bot configuration dictionary
            
        Returns:
            Runtime metadata with ARN and status
        """
        try:
            logger.info(f"Creating AgentCore runtime for bot {bot_id}")
            
            # TODO: Implement when bedrock-agentcore is available
            # runtime_response = self.agentcore_client.create_runtime(
            #     RuntimeName=f"bedrock-chat-{bot_id}",
            #     ContainerImage=self.config.get_container_repository_uri() + ":latest",
            #     ExecutionRoleArn=self.config.get_runtime_execution_role_arn(),
            #     Environment={
            #         'BOT_ID': bot_id,
            #         'BOT_TABLE_NAME': os.getenv('TABLE_NAME', ''),
            #     }
            # )
            
            # Placeholder runtime ARN
            runtime_arn = f"arn:aws:bedrock-agentcore:us-east-1:123456789012:runtime/bedrock-chat-{bot_id}"
            
            # Store runtime mapping in DynamoDB
            runtime_metadata = {
                'BotId': bot_id,
                'RuntimeArn': runtime_arn,
                'Status': 'CREATING',
                'CreatedAt': int(time.time()),
                'UpdatedAt': int(time.time()),
                'ExpiresAt': int((datetime.now() + timedelta(days=30)).timestamp()),
                'BotConfig': bot_config,
                'ContainerImage': self.config.get_container_repository_uri() + ":latest",
            }
            
            self.table.put_item(Item=runtime_metadata)
            
            logger.info(f"Created runtime registry entry for bot {bot_id}")
            return runtime_metadata
            
        except Exception as e:
            logger.error(f"Failed to create runtime for bot {bot_id}: {e}")
            raise

    def get_runtime(self, bot_id: str) -> Optional[Dict[str, Any]]:
        """
        Get runtime metadata for a bot.
        
        Args:
            bot_id: Bot identifier
            
        Returns:
            Runtime metadata or None if not found
        """
        try:
            response = self.table.get_item(Key={'BotId': bot_id})
            
            if 'Item' in response:
                logger.info(f"Found runtime for bot {bot_id}")
                return response['Item']
            
            logger.info(f"No runtime found for bot {bot_id}")
            return None
            
        except ClientError as e:
            logger.error(f"Failed to get runtime for bot {bot_id}: {e}")
            raise

    def update_runtime_status(self, bot_id: str, status: str, metadata: Dict[str, Any] = None) -> bool:
        """
        Update runtime status and metadata.
        
        Args:
            bot_id: Bot identifier
            status: New runtime status
            metadata: Optional additional metadata
            
        Returns:
            True if update successful
        """
        try:
            update_expression = "SET #status = :status, UpdatedAt = :updated_at"
            expression_values = {
                ':status': status,
                ':updated_at': int(time.time())
            }
            expression_names = {'#status': 'Status'}
            
            if metadata:
                for key, value in metadata.items():
                    update_expression += f", {key} = :{key.lower()}"
                    expression_values[f":{key.lower()}"] = value
            
            self.table.update_item(
                Key={'BotId': bot_id},
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_values,
                ExpressionAttributeNames=expression_names
            )
            
            logger.info(f"Updated runtime status for bot {bot_id} to {status}")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to update runtime status for bot {bot_id}: {e}")
            return False

    def delete_runtime(self, bot_id: str) -> bool:
        """
        Delete AgentCore runtime and registry entry.
        
        Args:
            bot_id: Bot identifier
            
        Returns:
            True if deletion successful
        """
        try:
            # Get runtime metadata
            runtime_metadata = self.get_runtime(bot_id)
            if not runtime_metadata:
                logger.warning(f"No runtime found for bot {bot_id} to delete")
                return True
            
            runtime_arn = runtime_metadata.get('RuntimeArn')
            
            # TODO: Implement when bedrock-agentcore is available
            # self.agentcore_client.delete_runtime(RuntimeArn=runtime_arn)
            
            # Delete from registry
            self.table.delete_item(Key={'BotId': bot_id})
            
            logger.info(f"Deleted runtime for bot {bot_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete runtime for bot {bot_id}: {e}")
            return False

    def list_runtimes(self, status_filter: str = None) -> List[Dict[str, Any]]:
        """
        List all runtime registrations.
        
        Args:
            status_filter: Optional status filter
            
        Returns:
            List of runtime metadata
        """
        try:
            if status_filter:
                response = self.table.scan(
                    FilterExpression='#status = :status',
                    ExpressionAttributeNames={'#status': 'Status'},
                    ExpressionAttributeValues={':status': status_filter}
                )
            else:
                response = self.table.scan()
            
            runtimes = response.get('Items', [])
            logger.info(f"Found {len(runtimes)} runtimes")
            
            return runtimes
            
        except ClientError as e:
            logger.error(f"Failed to list runtimes: {e}")
            return []

    def trigger_container_build(self, bot_id: str) -> bool:
        """
        Trigger CodeBuild to build and deploy container.
        
        Args:
            bot_id: Bot identifier
            
        Returns:
            True if build triggered successfully
        """
        try:
            codebuild = boto3.client('codebuild')
            
            build_response = codebuild.start_build(
                projectName=self.config.get_build_project_name(),
                environmentVariablesOverride=[
                    {
                        'name': 'BOT_ID',
                        'value': bot_id
                    },
                    {
                        'name': 'ECR_REPOSITORY_URI',
                        'value': self.config.get_container_repository_uri()
                    }
                ]
            )
            
            build_id = build_response['build']['id']
            logger.info(f"Triggered container build {build_id} for bot {bot_id}")
            
            # Update runtime status to building
            self.update_runtime_status(bot_id, 'BUILDING', {'BuildId': build_id})
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to trigger container build for bot {bot_id}: {e}")
            return False

    def cleanup_expired_runtimes(self) -> int:
        """
        Clean up expired runtime entries.
        
        Returns:
            Number of cleaned up runtimes
        """
        try:
            current_time = int(time.time())
            
            # Scan for expired entries
            response = self.table.scan(
                FilterExpression='ExpiresAt < :current_time',
                ExpressionAttributeValues={':current_time': current_time}
            )
            
            expired_runtimes = response.get('Items', [])
            cleanup_count = 0
            
            for runtime in expired_runtimes:
                bot_id = runtime['BotId']
                if self.delete_runtime(bot_id):
                    cleanup_count += 1
            
            logger.info(f"Cleaned up {cleanup_count} expired runtimes")
            return cleanup_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup expired runtimes: {e}")
            return 0


# Global registry instance
_registry: Optional[AgentCoreRuntimeRegistry] = None


def get_runtime_registry() -> AgentCoreRuntimeRegistry:
    """
    Get the global runtime registry instance.
    
    Returns:
        AgentCoreRuntimeRegistry instance (singleton)
    """
    global _registry
    if _registry is None:
        _registry = AgentCoreRuntimeRegistry()
    return _registry
