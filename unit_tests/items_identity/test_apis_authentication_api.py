import unittest
import json
import logging
from unittest.mock import patch, MagicMock, AsyncMock
from quart import Response
from routes.auth.authenticate_password_handler import AuthenticatePasswordHandler


def _undecorated(method):
    """Return the original function if it's wrapped by a decorator."""
    return getattr(method, "__wrapped__", method)


class TestAuthenticatePasswordHandler(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.mock_logger = MagicMock(spec=logging.Logger)
        self.mock_child_logger = MagicMock(spec=logging.Logger)
        self.mock_logger.getChild.return_value = self.mock_child_logger
        self.mock_service_state = MagicMock()
        self.mock_config = MagicMock()

        user_repo_patch = patch(
            "routes.auth.authenticate_password_handler.UserRepository",
            autospec=True)
        auth_svc_patch = patch(
            "routes.auth.authenticate_password_handler.AuthenticationService",
            autospec=True)
        self.addCleanup(user_repo_patch.stop)
        self.addCleanup(auth_svc_patch.stop)
        self.mock_user_repo_cls = user_repo_patch.start()
        self.mock_auth_svc_cls = auth_svc_patch.start()

        self.mock_auth_svc_instance = MagicMock()
        self.mock_auth_svc_cls.return_value = self.mock_auth_svc_instance

        self.handler = AuthenticatePasswordHandler(
            self.mock_logger, self.mock_service_state, self.mock_config)

    async def test_init_creates_auth_service_and_user_repo(self):
        self.mock_logger.getChild.assert_called_once_with(
            "routes.auth.authenticate_password_handler")
        self.mock_user_repo_cls.assert_called_once_with(
            self.mock_child_logger, self.mock_config)
        self.mock_auth_svc_cls.assert_called_once()
        self.assertIsInstance(self.handler._auth_service, MagicMock)

    async def test_authenticate_password_success(self):
        self.mock_auth_svc_instance.authenticate_password = AsyncMock(
            return_value=(True, "Authentication successful"))

        mock_request = MagicMock()
        mock_request.body = {
            'email_address': 'user@example.com',
            'password': 'password'
        }

        target = _undecorated(self.handler.authenticate_password)
        resp: Response = await target(self.handler, mock_request)

        self.mock_auth_svc_instance.authenticate_password.assert_called_once_with(
            email="user@example.com", password="password")

        self.assertIsInstance(resp, Response)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, "application/json")

        body = json.loads(await resp.get_data())
        self.assertEqual(body, {"success": True, "message": "Authentication successful"})

    async def test_authenticate_password_failure(self):
        self.mock_auth_svc_instance.authenticate_password = AsyncMock(
            return_value=(False, "Username/password don't match"))

        mock_request = MagicMock()
        mock_request.body = {
            'email_address': 'bad@example.com',
            'password': 'wrong'
        }

        target = _undecorated(self.handler.authenticate_password)
        resp: Response = await target(self.handler, mock_request)

        self.assertEqual(resp.status_code, 401)
        body = json.loads(await resp.get_data())
        self.assertFalse(body["success"])
        self.assertEqual(body["message"], "Username/password don't match")
