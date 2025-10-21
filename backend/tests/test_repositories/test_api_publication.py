import sys
import unittest
from unittest.mock import MagicMock, patch
from pprint import pprint
from datetime import datetime

sys.path.append(".")

from app.repositories.api_publication import (
    create_api_key,
    delete_api_key,
    find_api_key_by_id,
    find_stack_by_bot_id,
    find_usage_plan_by_id,
)

# Edit before running (Need to create a api stack. To do so, run codebuild project).
usage_plan_id = "jukuef"
bot_id = "01HRA01CB4H6GQPAG78YG49CQ4"


class TestApiGateway(unittest.TestCase):
    def setUp(self):
        self.patcher = patch("boto3.client")
        self.mock_boto_client = self.patcher.start()

        # Mock API Gateway client
        mock_api = MagicMock()
        mock_api.get_usage_plan.return_value = {
            'id': usage_plan_id,
            'name': 'test-plan',
            'apiStages': [],
            'throttle': {'rateLimit': 1000, 'burstLimit': 2000}
        }
        mock_api.get_api_key.return_value = {
            'id': 'new-key-id',  # Match the created key ID
            'name': 'test-key',
            'value': 'test-key-value',
            'enabled': True,
            'createdDate': datetime.fromtimestamp(1627984879.0),
            'description': 'description'  # Match the test description
        }
        mock_api.create_api_key.return_value = {
            'id': 'new-key-id',
            'name': 'new-key',
            'enabled': True,
            'createdDate': datetime.fromtimestamp(1627984879.0)
        }
        mock_api.create_usage_plan_key.return_value = {
            'id': 'new-key-id',
            'type': 'API_KEY'
        }
        mock_api.delete_api_key.return_value = {}

        def mock_client(service_name):
            if service_name == "apigateway":
                return mock_api
            elif service_name == "cloudformation":
                mock_cf = MagicMock()
                mock_cf.describe_stacks.return_value = {
                    'Stacks': [{
                        'StackName': f'ApiPublishmentStack{bot_id}',
                        'StackStatus': 'CREATE_COMPLETE',
                        'Outputs': []
                    }]
                }
                return mock_cf
            return MagicMock()

        self.mock_boto_client.side_effect = mock_client

    def tearDown(self):
        self.patcher.stop()

    def test_find_usage_plan_by_id(self):
        plan = find_usage_plan_by_id(usage_plan_id)
        pprint(plan)
        self.assertTrue(plan is not None)

    def test_find_api_key_by_id(self):
        # Use the mock key ID that matches our mock response
        key_id = "new-key-id"
        key = find_api_key_by_id(key_id, include_value=True)
        pprint(key)
        self.assertTrue(key is not None)
        self.assertEqual(key.id, key_id)
        self.assertEqual(key.enabled, True)

    def test_create_delete_api_key(self):
        res = create_api_key(usage_plan_id, "description")
        key = find_api_key_by_id(res.id, include_value=True)
        self.assertEqual(key.id, res.id)
        self.assertEqual(key.enabled, True)
        self.assertEqual(key.description, "description")
        delete_api_key(key.id)


class TestCloudformation(unittest.TestCase):
    def setUp(self):
        self.patcher = patch("boto3.client")
        self.mock_boto_client = self.patcher.start()

        # Mock CloudFormation client  
        mock_cf = MagicMock()
        mock_cf.describe_stacks.return_value = {
            'Stacks': [{
                'StackName': f'ApiPublishmentStack{bot_id}',
                'StackId': f'arn:aws:cloudformation:us-east-1:123456789012:stack/ApiPublishmentStack{bot_id}/12345',
                'StackStatus': 'CREATE_COMPLETE',
                'CreationTime': datetime.fromtimestamp(1627984879.0),
                'Outputs': [
                    {'OutputKey': 'ApiId', 'OutputValue': 'test-api-id'},
                    {'OutputKey': 'ApiName', 'OutputValue': 'test-api-name'},
                    {'OutputKey': 'ApiUsagePlanId', 'OutputValue': 'test-usage-plan-id'},
                    {'OutputKey': 'AllowedOrigins', 'OutputValue': 'https://example.com,https://test.com'},
                    {'OutputKey': 'DeploymentStage', 'OutputValue': 'prod'}
                ]
            }]
        }
        self.mock_boto_client.return_value = mock_cf

    def tearDown(self):
        self.patcher.stop()

    def test_find_stack_by_bot_id(self):
        stack = find_stack_by_bot_id(bot_id)
        pprint(stack)
        self.assertTrue(stack is not None)


if __name__ == "__main__":
    unittest.main()
