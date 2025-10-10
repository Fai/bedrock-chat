import sys
import unittest
from unittest.mock import MagicMock, patch

sys.path.append(".")

from pprint import pprint

from app.repositories.usage_analysis import (
    _find_cognito_user_by_id,
    _find_cognito_users_by_ids,
    find_bots_sorted_by_price,
    find_users_sorted_by_price,
)


class TestUsageAnalysis(unittest.IsolatedAsyncioTestCase):
    async def test_find_bots_sorted_by_price(self):
        bots = await find_bots_sorted_by_price(
            limit=10, from_="2024010100", to_="2024120100"
        )
        pprint([bot.model_dump() for bot in bots])

    async def test_find_users_sorted_by_price(self):
        users = await find_users_sorted_by_price(
            limit=10, from_="2024010100", to_="2024120100"
        )
        pprint([user.model_dump() for user in users])


class TestCognitoUser(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.patcher = patch("boto3.client")
        self.mock_boto_client = self.patcher.start()

        # Mock Cognito client
        mock_cognito = MagicMock()
        mock_cognito.admin_get_user.return_value = {
            'Username': '07645ad8-b041-702e-9852-98b169c9f1b1',
            'UserAttributes': [
                {'Name': 'email', 'Value': 'test@example.com'},
                {'Name': 'given_name', 'Value': 'Test'},
                {'Name': 'family_name', 'Value': 'User'}
            ],
            'UserCreateDate': 1627984879.0,
            'UserLastModifiedDate': 1627984879.0,
            'Enabled': True,
            'UserStatus': 'CONFIRMED'
        }

        def mock_client(service_name):
            if service_name == "cognito-idp":
                return mock_cognito
            return MagicMock()

        self.mock_boto_client.side_effect = mock_client

    def tearDown(self):
        self.patcher.stop()

    async def test_find_cognito_user_by_id(self):
        user = _find_cognito_user_by_id("07645ad8-b041-702e-9852-98b169c9f1b1")
        pprint(user)

    async def test_find_cognito_users_by_ids(self):
        users = await _find_cognito_users_by_ids(
            [
                "07645ad8-b041-702e-9852-98b169c9f1b1",
                "c7345a28-00b1-70f1-632f-dcef9f455949",
            ]
        )
        pprint(users)


if __name__ == "__main__":
    unittest.main()
