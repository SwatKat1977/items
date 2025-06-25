import unittest
from unittest.mock import MagicMock, patch
from http import HTTPStatus
from quart import Quart
from base_view import ApiResponse
from apis.authentication_api_view import AuthenticationApiView as View
from threadsafe_configuration import ThreadSafeConfiguration

class TestAuthenticationAPI(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        """Set up Quart test client and mock dependencies."""
        self.app = Quart(__name__)

        # Patch configuration
        patcher = patch.object(
            ThreadSafeConfiguration,
            'get_entry',
            return_value=":memory:"
        )
        self.mock_get_entry = patcher.start()
        self.addCleanup(patcher.stop)

        # Mock dependencies
        self.sql_interface = MagicMock()
        self.logger = MagicMock()

        self.client = self.app.test_client()

    @patch('apis.authentication_api_view.SqliteInterface')
    async def test_authenticate_validate_user_login_internal_error(self, mock_sql_interface):
        """Test authenticate() when valid_user_to_logon returns None."""
        mock_db = MagicMock()
        mock_db.valid_user_to_logon.return_value = (None, 'Internal error')
        mock_sql_interface.return_value = mock_db

        # Create the View instance
        view = View(self.sql_interface, self.logger)

        # Register route for testing
        self.app.add_url_rule('/authentication/basic',
                              view_func=view.authenticate_basic,
                              methods=['POST'])

        async with self.client as client:
            response = await client.post('/authentication/basic',
                                         json={"email_address": "test@example.com", "password": "1"})

            # Debugging: Print raw response text if data is None
            data = await response.get_json()

            # Validate response status
            self.assertEqual(response.status_code, HTTPStatus.INTERNAL_SERVER_ERROR)

            # Ensure response contains JSON
            self.assertIsNotNone(data, "Response JSON is None!")

            # Validate response JSON structure
            self.assertEqual(data['status'], 0)
            self.assertEqual(data['error'], "Internal server error")

    @patch('apis.authentication_api_view.SqliteInterface')
    async def test_authenticate_invalid_user_id(self, mock_sql_interface):
        """Test authenticate() when valid_user_to_logon() returns an invalid user_id."""
        mock_db = MagicMock()

        # Mock valid_user_to_logon() to return a valid user ID
        mock_db.valid_user_to_logon.return_value = (False, 'Invalid user id')

        mock_sql_interface.return_value = mock_db

        # Create the View instance
        view = View(self.sql_interface, self.logger)

        # Register route for testing
        self.app.add_url_rule('/authentication/basic',
                              view_func=view.authenticate_basic,
                              methods=['POST'])

        async with self.client as client:
            response = await client.post('/authentication/basic',
                                         json={"email_address": "test@example.com", "password": "password123"})
            data = await response.get_json()
            # Check response status
            self.assertEqual(response.status_code, HTTPStatus.OK)

            # Check response JSON
            data = await response.get_json()
            self.assertEqual(data['status'], 0)
            self.assertEqual(data['error'], "Invalid user id")

    '''
    @patch('apis.authentication_api_view.SqliteInterface')
    async def test_authenticate_wrong_password(self, mock_sql_interface):
        """Test authenticate() when user exists but authentication fails (wrong password)."""
        mock_db = MagicMock()

        # Mock valid_user_to_logon() to return a valid user ID
        mock_db.valid_user_to_logon.return_value = (123, None)

        # Mock basic_user_authenticate() to return failed password match
        mock_db.basic_user_authenticate.return_value = (0, "Invalid credentials")
        mock_sql_interface.return_value = mock_db

        # Create the View instance
        view = View(self.sql_interface, self.logger)

        # Register route for testing
        self.app.add_url_rule('/authentication/basic',
                              view_func=view.authenticate_basic,
                              methods=['POST'])

        async with self.client as client:
            response = await client.post('/authentication/basic',
                                         json={"email_address": "test@example.com", "password": "wrongpassword"})
            # Check response status
            self.assertEqual(response.status_code, HTTPStatus.OK)

            # Check response JSON
            data = await response.get_json()
            self.assertEqual(data['status'], 0)
            self.assertEqual(data['error'], "Invalid credentials")
    '''

    @patch('apis.authentication_api_view.SqliteInterface')
    async def test_authenticate_success(self, mock_sql_interface):
        """Test authenticate() when user exists and authentication succeeds."""
        mock_db = MagicMock()

        # Mock valid_user_to_logon() to return a valid user ID
        mock_db.valid_user_to_logon.return_value = (123, None)

        # Mock basic_user_authenticate() to return success
        mock_db.basic_user_authenticate.return_value = (True, "")
        mock_sql_interface.return_value = mock_db

        # Create the View instance
        view = View(self.sql_interface, self.logger)

        # Register route for testing
        self.app.add_url_rule('/authentication/basic',
                              view_func=view.authenticate_basic,
                              methods=['POST'])

        async with self.client as client:
            response = await client.post('/authentication/basic',
                                         json={"email_address": "test@example.com", "password": "correctpassword"})
            # Check response status
            self.assertEqual(response.status_code, HTTPStatus.OK)

            # Check response JSON
            data = await response.get_json()
            self.assertEqual(data['status'], 1)
            self.assertEqual(data['error'], "")
