import time
import logging
from typing import Optional, Dict, Any
from contextlib import contextmanager
import boto3
from botocore.exceptions import ClientError
from app.routes.schemas.conversation import type_model_name

logger = logging.getLogger(__name__)

class BedrockMetrics:
    def __init__(self):
        try:
            self.cloudwatch = boto3.client('cloudwatch')
        except Exception as e:
            logger.warning(f"CloudWatch client initialization failed: {e}")
            self.cloudwatch = None
    
    def put_api_metrics(self, model: type_model_name, latency_ms: float, 
                       success: bool, error_type: Optional[str] = None):
        """Send API performance metrics to CloudWatch."""
        if not self.cloudwatch:
            return
            
        try:
            metric_data = [
                {
                    'MetricName': 'APILatency',
                    'Dimensions': [
                        {'Name': 'Model', 'Value': str(model)},
                        {'Name': 'Success', 'Value': str(success)}
                    ],
                    'Value': latency_ms,
                    'Unit': 'Milliseconds'
                },
                {
                    'MetricName': 'APICallCount',
                    'Dimensions': [{'Name': 'Model', 'Value': str(model)}],
                    'Value': 1,
                    'Unit': 'Count'
                }
            ]
            
            if not success and error_type:
                metric_data.append({
                    'MetricName': 'APIErrors',
                    'Dimensions': [
                        {'Name': 'Model', 'Value': str(model)},
                        {'Name': 'ErrorType', 'Value': error_type}
                    ],
                    'Value': 1,
                    'Unit': 'Count'
                })
            
            self.cloudwatch.put_metric_data(
                Namespace='BedrockChat/API',
                MetricData=metric_data
            )
            
        except Exception as e:
            logger.error(f"Failed to send metrics: {e}")
    
    def put_token_metrics(self, model: type_model_name, input_tokens: int, 
                         output_tokens: int, cache_read: int = 0, cache_write: int = 0):
        """Send token usage metrics to CloudWatch."""
        if not self.cloudwatch:
            return
            
        try:
            metric_data = [
                {
                    'MetricName': 'InputTokens',
                    'Dimensions': [{'Name': 'Model', 'Value': str(model)}],
                    'Value': input_tokens,
                    'Unit': 'Count'
                },
                {
                    'MetricName': 'OutputTokens',
                    'Dimensions': [{'Name': 'Model', 'Value': str(model)}],
                    'Value': output_tokens,
                    'Unit': 'Count'
                }
            ]
            
            if cache_read > 0:
                metric_data.append({
                    'MetricName': 'CacheReadTokens',
                    'Dimensions': [{'Name': 'Model', 'Value': str(model)}],
                    'Value': cache_read,
                    'Unit': 'Count'
                })
                
            if cache_write > 0:
                metric_data.append({
                    'MetricName': 'CacheWriteTokens',
                    'Dimensions': [{'Name': 'Model', 'Value': str(model)}],
                    'Value': cache_write,
                    'Unit': 'Count'
                })
            
            self.cloudwatch.put_metric_data(
                Namespace='BedrockChat/Tokens',
                MetricData=metric_data
            )
            
        except Exception as e:
            logger.error(f"Failed to send token metrics: {e}")

# Global metrics instance
metrics = BedrockMetrics()

@contextmanager
def track_bedrock_call(model: type_model_name):
    """Context manager to track Bedrock API call performance."""
    start_time = time.time()
    success = False
    error_type = None
    
    try:
        yield
        success = True
    except ClientError as e:
        error_type = e.response.get('Error', {}).get('Code', 'Unknown')
        raise
    except Exception as e:
        error_type = type(e).__name__
        raise
    finally:
        latency_ms = (time.time() - start_time) * 1000
        metrics.put_api_metrics(model, latency_ms, success, error_type)

def track_token_usage(model: type_model_name, usage_data: Dict[str, Any]):
    """Track token usage from Bedrock response."""
    input_tokens = usage_data.get('inputTokens', 0)
    output_tokens = usage_data.get('outputTokens', 0)
    cache_read = usage_data.get('cacheReadInputTokens', 0)
    cache_write = usage_data.get('cacheCreationInputTokens', 0)
    
    metrics.put_token_metrics(model, input_tokens, output_tokens, cache_read, cache_write)
