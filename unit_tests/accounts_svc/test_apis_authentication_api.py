import unittest
import json
import logging
from unittest.mock import patch, MagicMock
from quart import Response
from apis.authentication_api_view import AuthenticationApiView

def _undecorated(method):
    """Return the original function if it's wrapped by a decorator."""
    return getattr(method, "__wrapped__", method)


class TestAuthenticationApiView(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        # Mock dependencies
        self.mock_logger = MagicMock(spec=logging.Logger)
        self.mock_child_logger = MagicMock(spec=logging.Logger)
        self.mock_logger.getChild.return_value = self.mock_child_logger

        self.mock_service_state = MagicMock()

        # Patch UserDataAccessLayer and AuthenticationService
        user_dal_patch = patch("apis.authentication_api_view.UserDataAccessLayer", autospec=True)
        auth_service_patch = patch("apis.authentication_api_view.AuthenticationService", autospec=True)
        self.addCleanup(user_dal_patch.stop)
        self.addCleanup(auth_service_patch.stop)
        self.mock_user_dal_cls = user_dal_patch.start()
        self.mock_auth_service_cls = auth_service_patch.start()

        self.mock_auth_service_instance = MagicMock()
        self.mock_auth_service_cls.return_value = self.mock_auth_service_instance

        # Create instance
        self.view = AuthenticationApiView(self.mock_logger, self.mock_service_state)

    async def test_init_creates_auth_service_and_user_dal(self):
        self.mock_logger.getChild.assert_called_once_with("apis.authentication_api_view")
        self.mock_user_dal_cls.assert_called_once_with(self.mock_service_state, self.mock_logger)
        self.mock_auth_service_cls.assert_called_once()
        self.assertIsInstance(self.view._auth_service, MagicMock)

    async def test_authenticate_basic_returns_expected_response(self):
        expected_status = 200
        expected_json = {"status": 1, "error": ""}
        self.mock_auth_service_instance.authenticate_basic.return_value = (
            expected_status,
            expected_json,
        )

        mock_request_msg = MagicMock()
        mock_request_msg.body.email_address = "user@example.com"
        mock_request_msg.body.password = "password"

        target = _undecorated(self.view.authenticate_basic)
        resp: Response = await target(self.view, mock_request_msg)

        self.mock_auth_service_instance.authenticate_basic.assert_called_once_with(
            email="user@example.com", password="password"
        )

        self.assertIsInstance(resp, Response)
        self.assertEqual(resp.status_code, expected_status)
        self.assertEqual(resp.content_type, "application/json")

        body_bytes = await resp.get_data()
        self.assertEqual(json.loads(body_bytes), expected_json)

    async def test_authenticate_basic_handles_different_response(self):
        self.mock_auth_service_instance.authenticate_basic.return_value = (
            401,
            {"status": 0, "error": "Invalid credentials"},
        )

        mock_request_msg = MagicMock()
        mock_request_msg.body.email_address = "bad@example.com"
        mock_request_msg.body.password = "wrong"

        target = _undecorated(self.view.authenticate_basic)
        resp: Response = await target(self.view, mock_request_msg)

        self.assertEqual(resp.status_code, 401)
        body_bytes = await resp.get_data()
        body_json = json.loads(body_bytes)
        self.assertEqual(body_json["error"], "Invalid credentials")
