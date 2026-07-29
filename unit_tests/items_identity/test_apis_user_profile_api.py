import unittest
import json
import logging
from http import HTTPStatus
from unittest.mock import patch, MagicMock, AsyncMock
from quart import Response
from routes.users.get_user_profile_handler import GetUserProfileHandler
from services.user_profile_service import UserProfileResult

ADMIN_PROFILE = {
    "id": 1,
    "email_address": "admin@localhost",
    "full_name": "Local Admin",
    "display_name": "Local Admin",
    "account_status": 1,
    "logon_type": 0,
    "is_administrator": True,
}


def _undecorated(method):
    """Return the original function if it's wrapped by a decorator."""
    return getattr(method, "__wrapped__", method)


class TestGetUserProfileHandler(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.mock_logger = MagicMock(spec=logging.Logger)
        self.mock_child_logger = MagicMock(spec=logging.Logger)
        self.mock_logger.getChild.return_value = self.mock_child_logger
        self.mock_service_state = MagicMock()
        self.mock_config = MagicMock()

        user_repo_patch = patch(
            "routes.users.get_user_profile_handler.UserRepository",
            autospec=True)
        profile_svc_patch = patch(
            "routes.users.get_user_profile_handler.UserProfileService",
            autospec=True)
        self.addCleanup(user_repo_patch.stop)
        self.addCleanup(profile_svc_patch.stop)
        self.mock_user_repo_cls = user_repo_patch.start()
        self.mock_profile_svc_cls = profile_svc_patch.start()

        self.mock_profile_svc_instance = MagicMock()
        self.mock_profile_svc_cls.return_value = self.mock_profile_svc_instance

        self.handler = GetUserProfileHandler(
            self.mock_logger, self.mock_service_state, self.mock_config)

    def _request(self, email="admin@localhost"):
        mock_request = MagicMock()
        mock_request.body = {"email_address": email}
        return mock_request

    async def _call(self, result: UserProfileResult, email="admin@localhost"):
        self.mock_profile_svc_instance.get_profile_by_email = AsyncMock(
            return_value=result)
        target = _undecorated(self.handler.get_user_profile)
        return await target(self.handler, self._request(email))

    async def test_init_creates_profile_service_and_user_repo(self):
        self.mock_user_repo_cls.assert_called_once_with(
            self.mock_child_logger, self.mock_config)
        self.mock_profile_svc_cls.assert_called_once()

    async def test_success_returns_profile(self):
        resp: Response = await self._call(
            UserProfileResult(profile=ADMIN_PROFILE))

        self.assertEqual(resp.status_code, HTTPStatus.OK)
        body = json.loads(await resp.get_data())
        self.assertEqual(body, ADMIN_PROFILE)
        self.assertTrue(body["is_administrator"])

    async def test_not_found_returns_404(self):
        resp: Response = await self._call(UserProfileResult(found=False))

        self.assertEqual(resp.status_code, HTTPStatus.NOT_FOUND)
        body = json.loads(await resp.get_data())
        self.assertIn("error", body)

    async def test_unavailable_returns_503(self):
        resp: Response = await self._call(UserProfileResult(available=False))

        self.assertEqual(resp.status_code, HTTPStatus.SERVICE_UNAVAILABLE)
        body = json.loads(await resp.get_data())
        self.assertIn("error", body)

    async def test_unavailable_takes_precedence_over_not_found(self):
        """An outage must not be reported to the caller as a 404."""
        resp: Response = await self._call(
            UserProfileResult(available=False, found=False))

        self.assertEqual(resp.status_code, HTTPStatus.SERVICE_UNAVAILABLE)

    async def test_email_from_request_is_passed_to_service(self):
        await self._call(UserProfileResult(profile=ADMIN_PROFILE),
                         email="someone@example.com")

        self.mock_profile_svc_instance.get_profile_by_email \
            .assert_called_once_with("someone@example.com")

    async def test_response_is_json(self):
        resp: Response = await self._call(
            UserProfileResult(profile=ADMIN_PROFILE))

        self.assertEqual(resp.content_type, "application/json")
