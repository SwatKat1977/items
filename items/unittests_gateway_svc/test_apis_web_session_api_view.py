import unittest
from unittest.mock import AsyncMock, MagicMock, patch
import logging
import requests
from http import HTTPStatus
from quart import Quart
from sessions import Sessions
from base_view import ApiResponse
from apis.web.session_api_view import SessionApiView
from configuration.configuration_manager import ConfigurationManager

class TestHandshakeApiView(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.mock_logger = MagicMock(spec=logging.Logger)
        self.mock_sessions = MagicMock(spec=Sessions)
        self.view = HandshakeApiView(self.mock_logger, self.mock_sessions)

        # Set up Quart test client and mock dependencies.
        self.app = Quart(__name__)
        self.client = self.app.test_client()

        # Register route for testing
        self.app.add_url_rule('/handshake/basic_authenticate', view_func=self.view.basic_authenticate, methods=['POST'])
        self.app.add_url_rule('/handshake/logout', view_func=self.view.logout_user, methods=['POST'])
        self.app.add_url_rule('/handshake/is_token_valid', view_func=self.view.is_token_valid, methods=['POST'])

    @patch.object(ConfigurationManager, 'get_entry')
    async def test_basic_authenticate_invalid_status_from_accounts(self, mock_get_entry):

        mock_get_entry.return_value = "http://test:8080"

        # Mock `_validate_json_body` to return valid data
        self.view._validate_json_body = MagicMock()
        self.view._validate_json_body.return_value = ApiResponse(
            status_code=HTTPStatus.OK,
            body=MagicMock(email_address="test@example.com", password="mysecretpassword")
        )

        # Mock the response of `_call_api_post`
        mock_call_api_post = AsyncMock()
        mock_call_api_post.return_value = MagicMock(status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                                                    body={"status": True})
        self.view._call_api_post = mock_call_api_post

        async with self.client as client:
            response = await client.post('/handshake/basic_authenticate',
                                         json={"email_address": "test@example.com",
                                               "password": "mysecretpassword"})

            # Check response status
            self.assertEqual(response.status_code, HTTPStatus.INTERNAL_SERVER_ERROR)

            # Check response JSON
            data = await response.get_json()
            self.assertEqual(data['status'], 0)
            self.assertFalse("token" in data)

    @patch.object(ConfigurationManager, 'get_entry')
    async def test_basic_authenticate_invalid_login(self, mock_get_entry):

        mock_get_entry.return_value = "http://test:8080"

        # Mock `_validate_json_body` to return valid data
        self.view._validate_json_body = MagicMock()
        self.view._validate_json_body.return_value = ApiResponse(
            status_code=HTTPStatus.OK,
            body=MagicMock(email_address="test@example.com", password="mysecretpassword")
        )

        # Mock the response of `_call_api_post`
        mock_call_api_post = AsyncMock()
        mock_call_api_post.return_value = MagicMock(status_code=HTTPStatus.OK,
                                                    body={"status": 0})
        self.view._call_api_post = mock_call_api_post

        async with self.client as client:
            response = await client.post('/handshake/basic_authenticate',
                                         json={"email_address": "test@example.com",
                                               "password": "mysecretpassword"})

            # Check response status
            self.assertEqual(response.status_code, HTTPStatus.OK)

            # Check response JSON
            data = await response.get_json()
            self.assertEqual(data['status'], 0)
            self.assertFalse("token" in data)

    @patch.object(ConfigurationManager, 'get_entry')
    async def test_basic_authenticate_accounts_connection_error(self, mock_get_entry):

        mock_get_entry.return_value = "http://test:8080"

        # Mock `_validate_json_body` to return valid data
        self.view._validate_json_body = MagicMock()
        self.view._validate_json_body.return_value = ApiResponse(
            status_code=HTTPStatus.OK,
            body=MagicMock(email_address="test@example.com", password="mysecretpassword")
        )

        # Mock the response of `_call_api_post`
        mock_call_api_post = AsyncMock()
        mock_call_api_post = AsyncMock(
            side_effect=requests.exceptions.ConnectionError("Simulated connection error")
        )
        self.view._call_api_post = mock_call_api_post

        async with self.client as client:
            response = await client.post('/handshake/basic_authenticate',
                                         json={"email_address": "test@example.com",
                                               "password": "mysecretpassword"})

            # Check response status
            self.assertEqual(response.status_code, HTTPStatus.INTERNAL_SERVER_ERROR)

            # Check response JSON
            data = await response.get_json()
            self.assertEqual(data['status'], 0)
            self.assertFalse("token" in data)

    async def test_basic_authenticate_invalid_json(self):

        # Mock _validate_json_body to return an error response
        self.view._validate_json_body = MagicMock(return_value=ApiResponse(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            exception_msg="Validation error"
        ))

        async with self.client as client:
            response = await client.post('/handshake/basic_authenticate', json={})

            # Validate the response
            self.assertEqual(response.status_code, HTTPStatus.INTERNAL_SERVER_ERROR)

            data = await response.get_json()
            self.assertEqual(data["status"], 0)
            self.assertEqual(data['error'], "Validation error")

    @patch.object(ConfigurationManager, 'get_entry')
    async def test_basic_authenticate_success(self, mock_get_entry):

        mock_get_entry.return_value = "http://test:8080"

        # Mock `_validate_json_body` to return valid data
        self.view._validate_json_body = MagicMock()
        self.view._validate_json_body.return_value = ApiResponse(
            status_code=HTTPStatus.OK,
            body=MagicMock(email_address="test@example.com", password="mysecretpassword")
        )

        # Mock the response of `_call_api_post`
        mock_call_api_post = AsyncMock()
        mock_call_api_post.return_value = MagicMock(status_code=HTTPStatus.OK,
                                                    body={"status": True})
        self.view._call_api_post = mock_call_api_post

        async with self.client as client:
            response = await client.post('/handshake/basic_authenticate',
                                         json={"email_address": "test@example.com",
                                               "password": "mysecretpassword"})

            # Check response status
            self.assertEqual(response.status_code, HTTPStatus.OK)

            # Check response JSON
            data = await response.get_json()
            self.assertEqual(data['status'], 1)
            self.assertTrue("token" in data)

    @patch.object(ConfigurationManager, 'get_entry')
    async def test_logout_user_valid_session(self, mock_get_entry):

        mock_get_entry.return_value = "http://test:8080"

        self.view._sessions = MagicMock()
        # Simulate a valid session
        self.view._sessions.is_valid_session.return_value = True

        async with self.client as client:
            response = await client.post('/handshake/logout',
                                         json={"email_address": "test@example.com",
                                               "token": "TestTokens"})

            # Check response status
            self.assertEqual(response.status_code, HTTPStatus.OK)

            # Check response JSON
            data = await response.get_data()
            self.assertEqual(data.decode('utf-8'), 'OK')

    @patch.object(ConfigurationManager, 'get_entry')
    async def test_logout_user_invalid_session(self, mock_get_entry):

        mock_get_entry.return_value = "http://test:8080"

        self.view._sessions = MagicMock()
        # Simulate a valid session
        self.view._sessions.is_valid_session.return_value = False

        async with self.client as client:
            response = await client.post('/handshake/logout',
                                         json={"email_address": "test@example.com",
                                               "token": "TestTokens"})

            # Check response status
            self.assertEqual(response.status_code, HTTPStatus.OK)

            # Check response JSON
            data = await response.get_data()
            self.assertEqual(data.decode('utf-8'), 'OK')

    @patch.object(ConfigurationManager, 'get_entry')
    async def test_logout_user_error_status_code(self, mock_get_entry):

        # Mock _validate_json_body to return an error response
        self.view._validate_json_body = MagicMock(return_value=ApiResponse(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            exception_msg="Validation error"
        ))

        async with self.client as client:
            response = await client.post('/handshake/logout', json={})

            # Validate the response
            self.assertEqual(response.status_code, HTTPStatus.INTERNAL_SERVER_ERROR)

            data = await response.get_json()
            self.assertEqual(data["status"], 0)
            self.assertEqual(data['error'], "Validation error")

    @patch("sessions.Sessions.is_valid_session")
    async def test_is_token_valid_valid(self, mock_is_valid_session):

        # Mock `_validate_json_body` to return valid data
        self.view._validate_json_body = MagicMock()
        self.view._validate_json_body.return_value = ApiResponse(
            status_code=HTTPStatus.OK,
            body=MagicMock(email_address="test@example.com", token="TestToken")
        )

        #     "required": ["email_address", "token"],
        async with self.client as client:
            response = await client.post('/handshake/is_token_valid',
                                         json={"email_address": "test@example.com",
                                               "token": "TestTokens"})

            # Check response status
            self.assertEqual(response.status_code, HTTPStatus.OK)

            # Check response JSON
            data = await response.get_json()
            self.assertEqual(data['status'], 'VALID')

    @patch("sessions.Sessions.is_valid_session")
    async def test_is_token_internal_error(self, mock_is_valid_session):

        # Mock `_validate_json_body` to return valid data
        self.view._validate_json_body = MagicMock()
        self.view._validate_json_body.return_value = ApiResponse(
            status_code=HTTPStatus.IM_A_TEAPOT,
            body=MagicMock(email_address="test@example.com", token="TestToken")
        )

        #     "required": ["email_address", "token"],
        async with self.client as client:
            response = await client.post('/handshake/is_token_valid',
                                         json={"email_address": "test@example.com",
                                               "token": "TestTokens"})

            # Check response status
            self.assertEqual(response.status_code, HTTPStatus.INTERNAL_SERVER_ERROR)

            # Check response JSON
            data = await response.get_json()
            self.assertEqual(data['status'], 'BAD REQUEST')
