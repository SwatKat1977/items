import unittest
import json
import logging
from http import HTTPStatus
from unittest.mock import patch, MagicMock, AsyncMock
from quart import Response
from routes.users.user_management_handler import UserManagementHandler
from services.user_management_service import UserManagementResult

USER = {
    "id": 2,
    "email_address": "gemma@localhost",
    "full_name": "Gemma",
    "display_name": "Gemma",
    "insertion_date": 1700000001,
    "account_status": 1,
    "logon_type": 0,
    "is_administrator": False,
}


def _undecorated(method):
    """Return the original function if it's wrapped by a decorator."""
    return getattr(method, "__wrapped__", method)


class TestUserManagementHandler(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.mock_logger = MagicMock(spec=logging.Logger)
        self.mock_child_logger = MagicMock(spec=logging.Logger)
        self.mock_logger.getChild.return_value = self.mock_child_logger
        self.mock_service_state = MagicMock()
        self.mock_config = MagicMock()

        repo_patch = patch(
            "routes.users.user_management_handler.UserRepository",
            autospec=True)
        svc_patch = patch(
            "routes.users.user_management_handler.UserManagementService",
            autospec=True)
        self.addCleanup(repo_patch.stop)
        self.addCleanup(svc_patch.stop)
        repo_patch.start()
        self.mock_svc_cls = svc_patch.start()

        self.svc = MagicMock()
        self.mock_svc_cls.return_value = self.svc

        self.handler = UserManagementHandler(
            self.mock_logger, self.mock_service_state, self.mock_config)

    @staticmethod
    def _request(body):
        msg = MagicMock()
        msg.body = body
        return msg

    @staticmethod
    async def _body(resp: Response):
        return json.loads(await resp.get_data())

    # ------------------------------------------------------------------
    # List / get
    # ------------------------------------------------------------------

    async def test_list_users_success(self):
        self.svc.list_users = AsyncMock(
            return_value=UserManagementResult(users=[USER]))

        resp = await self.handler.list_users()

        self.assertEqual(resp.status_code, HTTPStatus.OK)
        self.assertEqual((await self._body(resp))["users"], [USER])

    async def test_list_users_unavailable(self):
        self.svc.list_users = AsyncMock(
            return_value=UserManagementResult(available=False))

        resp = await self.handler.list_users()

        self.assertEqual(resp.status_code, HTTPStatus.SERVICE_UNAVAILABLE)

    async def test_get_user_success(self):
        self.svc.get_user = AsyncMock(
            return_value=UserManagementResult(user=USER))

        resp = await self.handler.get_user(2)

        self.assertEqual(resp.status_code, HTTPStatus.OK)
        self.assertEqual(await self._body(resp), USER)

    async def test_get_user_not_found(self):
        self.svc.get_user = AsyncMock(
            return_value=UserManagementResult(found=False))

        resp = await self.handler.get_user(99)

        self.assertEqual(resp.status_code, HTTPStatus.NOT_FOUND)

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    async def test_create_returns_201_and_the_user(self):
        self.svc.create_user = AsyncMock(
            return_value=UserManagementResult(user=USER))

        target = _undecorated(self.handler.create_user)
        resp = await target(self.handler, self._request({
            "email_address": "gemma@localhost",
            "full_name": "Gemma",
            "display_name": "Gemma"}))

        self.assertEqual(resp.status_code, HTTPStatus.CREATED)
        self.assertEqual(await self._body(resp), USER)

    async def test_create_includes_generated_password_when_present(self):
        self.svc.create_user = AsyncMock(
            return_value=UserManagementResult(user=USER,
                                              generated_password="s3cr3t!"))

        target = _undecorated(self.handler.create_user)
        resp = await target(self.handler, self._request({
            "email_address": "g@l", "full_name": "G", "display_name": "G"}))

        self.assertEqual((await self._body(resp))["generated_password"],
                         "s3cr3t!")

    async def test_create_omits_generated_password_when_absent(self):
        self.svc.create_user = AsyncMock(
            return_value=UserManagementResult(user=USER))

        target = _undecorated(self.handler.create_user)
        resp = await target(self.handler, self._request({
            "email_address": "g@l", "full_name": "G", "display_name": "G"}))

        self.assertNotIn("generated_password", await self._body(resp))

    async def test_create_conflict_returns_409(self):
        self.svc.create_user = AsyncMock(
            return_value=UserManagementResult(conflict="already in use"))

        target = _undecorated(self.handler.create_user)
        resp = await target(self.handler, self._request({
            "email_address": "g@l", "full_name": "G", "display_name": "G"}))

        self.assertEqual(resp.status_code, HTTPStatus.CONFLICT)
        self.assertIn("already in use", (await self._body(resp))["error"])

    async def test_create_defaults_are_passed_through(self):
        self.svc.create_user = AsyncMock(
            return_value=UserManagementResult(user=USER))

        target = _undecorated(self.handler.create_user)
        await target(self.handler, self._request({
            "email_address": "g@l", "full_name": "G", "display_name": "G"}))

        kwargs = self.svc.create_user.call_args.kwargs
        self.assertFalse(kwargs["is_administrator"])
        self.assertTrue(kwargs["enabled"])
        self.assertIsNone(kwargs["password"])

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    async def test_update_success(self):
        self.svc.update_user = AsyncMock(
            return_value=UserManagementResult(user=USER))

        target = _undecorated(self.handler.update_user)
        resp = await target(self.handler, self._request({"full_name": "X"}), 2)

        self.assertEqual(resp.status_code, HTTPStatus.OK)

    async def test_update_passes_none_for_omitted_fields(self):
        """Omitted fields must arrive as None so they are left unchanged."""
        self.svc.update_user = AsyncMock(
            return_value=UserManagementResult(user=USER))

        target = _undecorated(self.handler.update_user)
        await target(self.handler, self._request({"full_name": "X"}), 2)

        kwargs = self.svc.update_user.call_args.kwargs
        self.assertEqual(kwargs["full_name"], "X")
        self.assertIsNone(kwargs["email"])
        self.assertIsNone(kwargs["display_name"])
        self.assertIsNone(kwargs["is_administrator"])
        self.assertIsNone(kwargs["enabled"])

    async def test_update_last_administrator_conflict_returns_409(self):
        self.svc.update_user = AsyncMock(
            return_value=UserManagementResult(
                conflict="would leave no active administrator"))

        target = _undecorated(self.handler.update_user)
        resp = await target(self.handler,
                            self._request({"is_administrator": False}), 1)

        self.assertEqual(resp.status_code, HTTPStatus.CONFLICT)
        self.assertIn("administrator", (await self._body(resp))["error"])

    async def test_update_not_found(self):
        self.svc.update_user = AsyncMock(
            return_value=UserManagementResult(found=False))

        target = _undecorated(self.handler.update_user)
        resp = await target(self.handler, self._request({"full_name": "X"}), 99)

        self.assertEqual(resp.status_code, HTTPStatus.NOT_FOUND)

    # ------------------------------------------------------------------
    # Password
    # ------------------------------------------------------------------

    async def test_set_password_success(self):
        self.svc.set_password = AsyncMock(
            return_value=UserManagementResult(user=USER))

        target = _undecorated(self.handler.set_password)
        resp = await target(self.handler,
                            self._request({"password": "long-enough"}), 2)

        self.assertEqual(resp.status_code, HTTPStatus.OK)
        self.svc.set_password.assert_awaited_once_with(
            user_id=2, password="long-enough")

    async def test_set_password_generated_when_omitted(self):
        self.svc.set_password = AsyncMock(
            return_value=UserManagementResult(user=USER,
                                              generated_password="gen"))

        target = _undecorated(self.handler.set_password)
        resp = await target(self.handler, self._request({}), 2)

        self.assertEqual((await self._body(resp))["generated_password"], "gen")
        self.assertIsNone(self.svc.set_password.call_args.kwargs["password"])

    # ------------------------------------------------------------------
    # Failure precedence
    # ------------------------------------------------------------------

    async def test_unavailable_takes_precedence_over_not_found(self):
        self.svc.get_user = AsyncMock(
            return_value=UserManagementResult(available=False, found=False))

        resp = await self.handler.get_user(2)

        self.assertEqual(resp.status_code, HTTPStatus.SERVICE_UNAVAILABLE)

    async def test_not_found_takes_precedence_over_conflict(self):
        self.svc.update_user = AsyncMock(
            return_value=UserManagementResult(found=False, conflict="x"))

        target = _undecorated(self.handler.update_user)
        resp = await target(self.handler, self._request({"full_name": "X"}), 9)

        self.assertEqual(resp.status_code, HTTPStatus.NOT_FOUND)
