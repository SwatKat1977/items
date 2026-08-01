import unittest
import json
import logging
from http import HTTPStatus
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

        repo_patch = patch(
            "routes.auth.authenticate_password_handler.UserRepository",
            autospec=True)
        auth_svc_patch = patch(
            "routes.auth.authenticate_password_handler.AuthenticationService",
            autospec=True)
        self.addCleanup(repo_patch.stop)
        self.addCleanup(auth_svc_patch.stop)
        self.mock_repo_cls = repo_patch.start()
        self.mock_auth_svc_cls = auth_svc_patch.start()

        self.mock_auth_svc = MagicMock()
        self.mock_auth_svc_cls.return_value = self.mock_auth_svc

        self.handler = AuthenticatePasswordHandler(
            self.mock_logger, self.mock_service_state, self.mock_config)

    def _request(self, email="admin@localhost", password="secret"):
        mock_request = MagicMock()
        mock_request.body = {"email_address": email, "password": password}
        return mock_request

    async def _call(self, success: bool, message: str,
                    email="admin@localhost", password="secret") -> Response:
        self.mock_auth_svc.authenticate_password = AsyncMock(
            return_value=(success, message))
        target = _undecorated(self.handler.authenticate_password)
        return await target(self.handler, self._request(email, password))

    async def test_init_creates_repo_and_auth_service(self):
        self.mock_repo_cls.assert_called_once_with(
            self.mock_child_logger, self.mock_config)
        self.mock_auth_svc_cls.assert_called_once()

    async def test_success_returns_200(self):
        resp: Response = await self._call(True, "ok")
        self.assertEqual(resp.status_code, HTTPStatus.OK)

    async def test_failure_returns_401(self):
        resp: Response = await self._call(False, "Username/password don't match")
        self.assertEqual(resp.status_code, HTTPStatus.UNAUTHORIZED)

    async def test_success_body_contains_success_true(self):
        resp: Response = await self._call(True, "ok")
        body = json.loads(await resp.get_data())
        self.assertTrue(body["success"])

    async def test_failure_body_contains_success_false(self):
        resp: Response = await self._call(False, "bad credentials")
        body = json.loads(await resp.get_data())
        self.assertFalse(body["success"])

    async def test_message_passed_through_to_response(self):
        resp: Response = await self._call(False, "Username/password don't match")
        body = json.loads(await resp.get_data())
        self.assertEqual(body["message"], "Username/password don't match")

    async def test_credentials_forwarded_to_service(self):
        await self._call(True, "ok",
                         email="someone@example.com", password="mypass")
        self.mock_auth_svc.authenticate_password.assert_awaited_once_with(
            email="someone@example.com", password="mypass")

    async def test_response_is_json(self):
        resp: Response = await self._call(True, "ok")
        self.assertEqual(resp.content_type, "application/json")
