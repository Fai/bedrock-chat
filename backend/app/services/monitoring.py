"""
Monitoring service for AgentCore migration metrics.

Provides CloudWatch metrics collection for monitoring migration progress,
performance, and error rates during A/B testing and rollout.
"""

import logging
import time
from typing import Dict, Any, Optional
from contextlib import contextmanager

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class AgentCoreMonitoring:
    """
    Monitoring service for AgentCore migration metrics.
    """
    
    def __init__(self, namespace: str = "BedrockChat/AgentCore"):
        """
        Initialize monitoring service.
        
        Args:
            namespace: CloudWatch namespace for metrics
        """
        self.namespace = namespace
        self.cloudwatch = boto3.client('cloudwatch')
        
    def record_request(self, implementation: str, success: bool = True, duration: float = None):
        """
        Record a chat request.
        
        Args:
            implementation: "agentcore" or "legacy"
            success: Whether request was successful
            duration: Request duration in seconds
        """
        try:
            metrics = [
                {
                    'MetricName': 'RequestCount',
                    'Dimensions': [
                        {'Name': 'Implementation', 'Value': implementation}
                    ],
                    'Value': 1,
                    'Unit': 'Count'
                }
            ]
            
            if not success:
                metrics.append({
                    'MetricName': 'ErrorCount',
                    'Dimensions': [
                        {'Name': 'Implementation', 'Value': implementation}
                    ],
                    'Value': 1,
                    'Unit': 'Count'
                })
            
            if duration is not None:
                metrics.append({
                    'MetricName': 'Duration',
                    'Dimensions': [
                        {'Name': 'Implementation', 'Value': implementation}
                    ],
                    'Value': duration,
                    'Unit': 'Seconds'
                })
            
            self.cloudwatch.put_metric_data(
                Namespace=self.namespace,
                MetricData=metrics
            )
            
        except ClientError as e:
            logger.error(f"Failed to record metrics: {e}")
    
    def record_tool_usage(self, tool_name: str, success: bool = True, duration: float = None):
        """
        Record tool usage metrics.
        
        Args:
            tool_name: Name of the tool used
            success: Whether tool execution was successful
            duration: Tool execution duration
        """
        try:
            metrics = [
                {
                    'MetricName': 'ToolUsage',
                    'Dimensions': [
                        {'Name': 'ToolName', 'Value': tool_name}
                    ],
                    'Value': 1,
                    'Unit': 'Count'
                }
            ]
            
            if not success:
                metrics.append({
                    'MetricName': 'ToolErrors',
                    'Dimensions': [
                        {'Name': 'ToolName', 'Value': tool_name}
                    ],
                    'Value': 1,
                    'Unit': 'Count'
                })
            
            if duration is not None:
                metrics.append({
                    'MetricName': 'ToolDuration',
                    'Dimensions': [
                        {'Name': 'ToolName', 'Value': tool_name}
                    ],
                    'Value': duration,
                    'Unit': 'Seconds'
                })
            
            self.cloudwatch.put_metric_data(
                Namespace=self.namespace,
                MetricData=metrics
            )
            
        except ClientError as e:
            logger.error(f"Failed to record tool metrics: {e}")
    
    def record_multi_agent_metrics(self, pattern: str, agents_used: int, success: bool = True):
        """
        Record multi-agent orchestration metrics.
        
        Args:
            pattern: Orchestration pattern used
            agents_used: Number of agents involved
            success: Whether orchestration was successful
        """
        try:
            metrics = [
                {
                    'MetricName': 'MultiAgentUsage',
                    'Dimensions': [
                        {'Name': 'Pattern', 'Value': pattern}
                    ],
                    'Value': 1,
                    'Unit': 'Count'
                },
                {
                    'MetricName': 'AgentsUsed',
                    'Dimensions': [
                        {'Name': 'Pattern', 'Value': pattern}
                    ],
                    'Value': agents_used,
                    'Unit': 'Count'
                }
            ]
            
            if not success:
                metrics.append({
                    'MetricName': 'MultiAgentErrors',
                    'Dimensions': [
                        {'Name': 'Pattern', 'Value': pattern}
                    ],
                    'Value': 1,
                    'Unit': 'Count'
                })
            
            self.cloudwatch.put_metric_data(
                Namespace=self.namespace,
                MetricData=metrics
            )
            
        except ClientError as e:
            logger.error(f"Failed to record multi-agent metrics: {e}")
    
    @contextmanager
    def measure_duration(self, metric_name: str, dimensions: Dict[str, str] = None):
        """
        Context manager to measure operation duration.
        
        Args:
            metric_name: Name of the duration metric
            dimensions: Optional metric dimensions
        """
        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time
            try:
                metric_data = {
                    'MetricName': metric_name,
                    'Value': duration,
                    'Unit': 'Seconds'
                }
                
                if dimensions:
                    metric_data['Dimensions'] = [
                        {'Name': k, 'Value': v} for k, v in dimensions.items()
                    ]
                
                self.cloudwatch.put_metric_data(
                    Namespace=self.namespace,
                    MetricData=[metric_data]
                )
            except ClientError as e:
                logger.error(f"Failed to record duration metric: {e}")


# Global monitoring instance
_monitoring: Optional[AgentCoreMonitoring] = None


def get_monitoring() -> AgentCoreMonitoring:
    """
    Get the global monitoring instance.
    
    Returns:
        AgentCoreMonitoring instance (singleton)
    """
    global _monitoring
    if _monitoring is None:
        _monitoring = AgentCoreMonitoring()
    return _monitoring


def record_chat_request(implementation: str, success: bool = True, duration: float = None):
    """
    Convenience function to record chat request.
    
    Args:
        implementation: "agentcore" or "legacy"
        success: Whether request was successful
        duration: Request duration in seconds
    """
    get_monitoring().record_request(implementation, success, duration)


def record_tool_usage(tool_name: str, success: bool = True, duration: float = None):
    """
    Convenience function to record tool usage.
    
    Args:
        tool_name: Name of the tool used
        success: Whether tool execution was successful
        duration: Tool execution duration
    """
    get_monitoring().record_tool_usage(tool_name, success, duration)
