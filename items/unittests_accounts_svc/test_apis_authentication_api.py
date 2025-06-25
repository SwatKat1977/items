import unittest
from unittest.mock import MagicMock
from http import HTTPStatus
from quart import Quart
from base_view import ApiResponse
from apis.basic_authentication_api_view import BasicAuthenticationApiView as View

class TestBasicAuthAPI(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        """Set up Quart test client and mock dependencies."""
        self.app = Quart(__name__)

        # Mock dependencies
        self.sql_interface = MagicMock()
        self.logger = MagicMock()

        # Create the View instance
        self.view = View(self.sql_interface, self.logger)

        self.client = self.app.test_client()

        # Register route for testing
        self.app.add_url_rule('/basic_auth/authenticate', view_func=self.view.authenticate, methods=['POST'])

    async def test_authenticate_validation_fails(self):
        """Test authenticate() when JSON validation fails."""

        # Mock _validate_json_body to return an error response
        self.view._validate_json_body = MagicMock(return_value=ApiResponse(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            exception_msg="Validation error"
        ))

        async with self.client as client:
            response = await client.post('/basic_auth/authenticate', json={})

            # Validate the response
            self.assertEqual(response.status_code, HTTPStatus.INTERNAL_SERVER_ERROR)

            data = await response.get_json()
            self.assertEqual(data["status"], 0)
            self.assertEqual(data['error'], "Validation error")

    async def test_authenticate_validate_user_login_internal_error(self):
        """Test authenticate() when valid_user_to_logon returns None."""

        self.view._validate_json_body = MagicMock()
        self.view._validate_json_body.return_value = ApiResponse(
            status_code=HTTPStatus.OK,
            body=MagicMock(email_address="test@example.com")
        )

        # Mock valid_user_to_logon to return None
        self.view._sql_interface.valid_user_to_logon.return_value = None

        async with self.client as client:
            response = await client.post('/basic_auth/authenticate', json={"email_address": "test@example.com"})

            # Debugging: Print raw response text if data is None
            data = await response.get_json()
            if data is None:
                print(f"RAW RESPONSE: {await response.get_data(as_text=True)}")

            # Validate response status
            self.assertEqual(response.status_code, HTTPStatus.INTERNAL_SERVER_ERROR)

            # Ensure response contains JSON
            self.assertIsNotNone(data, "Response JSON is None!")

            # Validate response JSON structure
            self.assertEqual(data['status'], 0)
            self.assertEqual(data['error'], "Internal server error")

    async def test_authenticate_invalid_user_id(self):
        """Test authenticate() when valid_user_to_logon() returns an invalid user_id."""

        # Mock `_validate_json_body` to return valid data
        self.view._validate_json_body = MagicMock()
        self.view._validate_json_body.return_value = ApiResponse(
            status_code=HTTPStatus.OK,
            body=MagicMock(email_address="test@example.com", password="password123")
        )

        # Mock `_sql_interface.valid_user_to_logon()` to return (None, "User not found")
        self.view._sql_interface.valid_user_to_logon.return_value = (None, "User not found")

        async with self.client as client:
            response = await client.post('/basic_auth/authenticate',
                                         json={"email_address": "test@example.com", "password": "password123"})

            # Check response status
            self.assertEqual(response.status_code, HTTPStatus.OK)

            # Check response JSON
            data = await response.get_json()
            self.assertEqual(data['status'], 0)
            self.assertEqual(data['error'], "User not found")

    async def test_authenticate_wrong_password(self):
        """Test authenticate() when user exists but authentication fails (wrong password)."""

        # Mock `_validate_json_body` to return valid data
        self.view._validate_json_body = MagicMock()
        self.view._validate_json_body.return_value = ApiResponse(
            status_code=HTTPStatus.OK,
            body=MagicMock(email_address="test@example.com", password="wrongpassword")
        )

        # Mock `_sql_interface.valid_user_to_logon()` to return a valid user ID
        self.view._sql_interface.valid_user_to_logon.return_value = (123, None)

        # Mock `_sql_interface.basic_user_authenticate()` to return failure
        self.view._sql_interface.basic_user_authenticate.return_value = (False, "Invalid credentials")

        async with self.client as client:
            response = await client.post('/basic_auth/authenticate',
                                         json={"email_address": "test@example.com", "password": "wrongpassword"})

            # Check response status
            self.assertEqual(response.status_code, HTTPStatus.OK)

            # Check response JSON
            data = await response.get_json()
            self.assertEqual(data['status'], 0)
            self.assertEqual(data['error'], "Invalid credentials")

    async def test_authenticate_success(self):
        """Test authenticate() when user exists and authentication succeeds."""

        # Mock `_validate_json_body` to return valid data
        self.view._validate_json_body = MagicMock()
        self.view._validate_json_body.return_value = ApiResponse(
            status_code=HTTPStatus.OK,
            body=MagicMock(email_address="test@example.com", password="correctpassword")
        )

        # Mock `_sql_interface.valid_user_to_logon()` to return a valid user ID
        self.view._sql_interface.valid_user_to_logon.return_value = (123, None)

        # Mock `_sql_interface.basic_user_authenticate()` to return success
        self.view._sql_interface.basic_user_authenticate.return_value = (True, "")

        async with self.client as client:
            response = await client.post('/basic_auth/authenticate',
                                         json={"email_address": "test@example.com", "password": "correctpassword"})

            # Check response status
            self.assertEqual(response.status_code, HTTPStatus.OK)

            # Check response JSON
            data = await response.get_json()
            self.assertEqual(data['status'], 1)
            self.assertEqual(data['error'], "")
