"""Global test configuration and fixtures."""
import os
import pytest
from unittest.mock import Mock, patch


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up test environment variables."""
    test_env = {
        # DynamoDB
        "CONVERSATION_TABLE_NAME": "test-conversation-table",
        "BOT_TABLE_NAME": "test-bot-table", 
        "BOT_ALIAS_TABLE_NAME": "test-bot-alias-table",
        "PUBLISHED_API_TABLE_NAME": "test-published-api-table",
        "USAGE_ANALYSIS_TABLE_NAME": "test-usage-analysis-table",
        "CONVERSATION_BUCKET_NAME": "test-bucket",
        "LARGE_MESSAGE_BUCKET": "test-large-message-bucket",
        
        # IAM Roles
        "CROSS_REGION_INFERENCE_ROLE_ARN": "arn:aws:iam::123456789012:role/test-cross-region-role",
        "BEDROCK_KB_ROLE_ARN": "arn:aws:iam::123456789012:role/test-bedrock-kb-role",
        
        # Cognito
        "USER_POOL_ID": "us-east-1_TEST123456",
        "USER_POOL_CLIENT_ID": "test-client-id",
        
        # OpenSearch
        "OPENSEARCH_DOMAIN_ENDPOINT": "https://test-domain.us-east-1.es.amazonaws.com",
        
        # Bedrock
        "BEDROCK_REGION": "us-east-1",
        
        # API Gateway
        "API_GATEWAY_ID": "test-api-gateway-id",
        
        # S3
        "DOCUMENT_BUCKET": "test-document-bucket",
        
        # Aurora
        "AURORA_CLUSTER_ARN": "arn:aws:rds:us-east-1:123456789012:cluster:test-aurora-cluster",
        "AURORA_SECRET_ARN": "arn:aws:secretsmanager:us-east-1:123456789012:secret:test-aurora-secret",
        "AURORA_DATABASE_NAME": "bedrock_kb",
    }
    
    # Set environment variables
    for key, value in test_env.items():
        os.environ[key] = value
    
    yield
    
    # Cleanup
    for key in test_env.keys():
        os.environ.pop(key, None)


@pytest.fixture
def mock_opensearch_client():
    """Mock OpenSearch client for tests that need it."""
    with patch('app.repositories.common.get_opensearch_client') as mock_client:
        mock_os_client = Mock()
        mock_os_client.search.return_value = {
            'hits': {
                'total': {'value': 0},
                'hits': []
            }
        }
        mock_os_client.index.return_value = {'result': 'created'}
        mock_os_client.delete.return_value = {'result': 'deleted'}
        mock_client.return_value = mock_os_client
        yield mock_os_client


@pytest.fixture
def mock_cognito_client():
    """Mock Cognito client for tests that need it."""
    with patch('app.repositories.user.get_cognito_client') as mock_client:
        mock_cognito = Mock()
        mock_cognito.list_users.return_value = {
            'Users': []
        }
        mock_cognito.admin_create_user.return_value = {
            'User': {
                'Username': 'test-user',
                'Attributes': []
            }
        }
        mock_cognito.create_group.return_value = {
            'Group': {
                'GroupName': 'test-group'
            }
        }
        mock_cognito.list_groups.return_value = {
            'Groups': []
        }
        mock_client.return_value = mock_cognito
        yield mock_cognito


@pytest.fixture(autouse=True)
def mock_aws_services():
    """Mock AWS services for all tests."""
    with patch('app.repositories.common._get_aws_resource') as mock_get_resource:
        mock_table = Mock()
        mock_table.put_item.return_value = {}
        mock_table.get_item.return_value = {'Item': {}}
        mock_table.query.return_value = {'Items': []}
        mock_table.scan.return_value = {'Items': []}
        mock_table.update_item.return_value = {}
        mock_table.delete_item.return_value = {}
        mock_get_resource.return_value = mock_table
        
        yield


@pytest.fixture
def mock_opensearch_client():
    """Mock OpenSearch client."""
    with patch('app.repositories.common.get_opensearch_client') as mock_client:
        mock_os_client = Mock()
        mock_os_client.search.return_value = {
            'hits': {
                'total': {'value': 0},
                'hits': []
            }
        }
        mock_os_client.index.return_value = {'result': 'created'}
        mock_os_client.delete.return_value = {'result': 'deleted'}
        mock_client.return_value = mock_os_client
        yield mock_os_client


@pytest.fixture
def mock_bedrock_client():
    """Mock Bedrock client."""
    with patch('app.repositories.common.get_bedrock_agent_client') as mock_client:
        mock_bedrock = Mock()
        mock_bedrock.create_knowledge_base.return_value = {
            'knowledgeBase': {'knowledgeBaseId': 'test-kb-123'}
        }
        mock_bedrock.create_data_source.return_value = {
            'dataSource': {'dataSourceId': 'test-ds-456'}
        }
        mock_bedrock.start_ingestion_job.return_value = {
            'ingestionJob': {'ingestionJobId': 'test-job-789'}
        }
        mock_bedrock.get_knowledge_base.return_value = {
            'knowledgeBase': {
                'knowledgeBaseId': 'test-kb-123',
                'status': 'ACTIVE'
            }
        }
        mock_bedrock.delete_knowledge_base.return_value = {}
        mock_bedrock.retrieve.return_value = {
            'retrievalResults': []
        }
        mock_client.return_value = mock_bedrock
        yield mock_bedrock


@pytest.fixture
def mock_cognito_client():
    """Mock Cognito client."""
    with patch('app.repositories.common.get_cognito_client') as mock_client:
        mock_cognito = Mock()
        mock_cognito.list_users.return_value = {
            'Users': []
        }
        mock_cognito.admin_create_user.return_value = {
            'User': {
                'Username': 'test-user',
                'Attributes': []
            }
        }
        mock_cognito.create_group.return_value = {
            'Group': {
                'GroupName': 'test-group'
            }
        }
        mock_cognito.list_groups.return_value = {
            'Groups': []
        }
        mock_client.return_value = mock_cognito
        yield mock_cognito
