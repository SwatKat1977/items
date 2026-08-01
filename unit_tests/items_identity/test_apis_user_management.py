"""
Handler-level tests for the user management API endpoints:
  GET  /users               - ListUsersHandler
  GET  /users/<id>          - GetUserHandler
  POST /users               - CreateUserHandler
  PATCH /users/<id>         - ModifyUserHandler
  POST /users/<id>/password - ResetPasswordHandler
  POST /users/me/password   - ChangePasswordHandler
"""
import unittest
import json
import logging
from http import HTTPStatus
from unittest.mock import patch, MagicMock, AsyncMock
from quart import Response
from routes.users.list_users_handler import ListUsersHandler
from routes.users.get_user_handler import GetUserHandler
from routes.users.create_user_handler import CreateUserHandler
from routes.users.modify_user_handler import ModifyUserHandler
from routes.users.reset_password_handler import ResetPasswordHandler
from routes.users.change_password_handler import ChangePasswordHandler
from services.user_management_service import (
    UserListResult,
    UserLookupResult,
    UserCreateResult,
    UserUpdateResult,
    PasswordResult,
)

_USER_DICT = {
    "id": 1,
    "email_address": "a@b.com",
    "full_name": "Full Name",
    "display_name": "Display",
    "account_status": 1,
    "logon_type": 0,
    "is_administrator": True,
}


def _undecorated(method):
    """Return the original function if it's wrapped by a decorator."""
    return getattr(method, "__wrapped__", method)


def _make_handler_setup(handler_cls):
    """Return an asyncSetUp that wires up a handler with mocked service."""
    async def asyncSetUp(self):
        self.mock_logger = MagicMock(spec=logging.Logger)
        self.mock_logger.getChild.return_value = MagicMock(spec=logging.Logger)
        self.mock_state = MagicMock()
        self.mock_config = MagicMock()

        repo_patch = patch(
            f"routes.users.{handler_cls.__module__.split('.')[-1]}.UserRepository",
            autospec=True)
        svc_patch = patch(
            f"routes.users.{handler_cls.__module__.split('.')[-1]}.UserManagementService",
            autospec=True)
        self.addCleanup(repo_patch.stop)
        self.addCleanup(svc_patch.stop)
        repo_patch.start()
        self.mock_svc_cls = svc_patch.start()

        self.mock_svc = MagicMock()
        self.mock_svc_cls.return_value = self.mock_svc

        self.handler = handler_cls(
            self.mock_logger, self.mock_state, self.mock_config)

    return asyncSetUp


# ---------------------------------------------------------------------------
# ListUsersHandler
# ---------------------------------------------------------------------------

class TestListUsersHandler(unittest.IsolatedAsyncioTestCase):

    asyncSetUp = _make_handler_setup(ListUsersHandler)

    async def _call(self, result: UserListResult) -> Response:
        self.mock_svc.get_all_users = AsyncMock(return_value=result)
        return await self.handler.list_users()

    async def test_success_returns_200_with_users(self):
        resp = await self._call(UserListResult(users=[_USER_DICT]))
        self.assertEqual(resp.status_code, HTTPStatus.OK)
        body = json.loads(await resp.get_data())
        self.assertEqual(body["users"], [_USER_DICT])

    async def test_empty_list_returns_200(self):
        resp = await self._call(UserListResult(users=[]))
        self.assertEqual(resp.status_code, HTTPStatus.OK)
        body = json.loads(await resp.get_data())
        self.assertEqual(body["users"], [])

    async def test_unavailable_returns_503(self):
        resp = await self._call(UserListResult(available=False))
        self.assertEqual(resp.status_code, HTTPStatus.SERVICE_UNAVAILABLE)
        body = json.loads(await resp.get_data())
        self.assertIn("error", body)

    async def test_response_is_json(self):
        resp = await self._call(UserListResult(users=[]))
        self.assertEqual(resp.content_type, "application/json")


# ---------------------------------------------------------------------------
# GetUserHandler
# ---------------------------------------------------------------------------

class TestGetUserHandler(unittest.IsolatedAsyncioTestCase):

    asyncSetUp = _make_handler_setup(GetUserHandler)

    async def _call(self, result: UserLookupResult, user_id: int = 1) -> Response:
        self.mock_svc.get_user_by_id = AsyncMock(return_value=result)
        return await self.handler.get_user(user_id)

    async def test_success_returns_200_with_user(self):
        resp = await self._call(UserLookupResult(user=_USER_DICT))
        self.assertEqual(resp.status_code, HTTPStatus.OK)
        body = json.loads(await resp.get_data())
        self.assertEqual(body, _USER_DICT)

    async def test_not_found_returns_404(self):
        resp = await self._call(UserLookupResult(found=False))
        self.assertEqual(resp.status_code, HTTPStatus.NOT_FOUND)
        body = json.loads(await resp.get_data())
        self.assertIn("error", body)

    async def test_unavailable_returns_503(self):
        resp = await self._call(UserLookupResult(available=False))
        self.assertEqual(resp.status_code, HTTPStatus.SERVICE_UNAVAILABLE)

    async def test_unavailable_takes_precedence_over_not_found(self):
        resp = await self._call(UserLookupResult(available=False, found=False))
        self.assertEqual(resp.status_code, HTTPStatus.SERVICE_UNAVAILABLE)

    async def test_user_id_passed_to_service(self):
        self.mock_svc.get_user_by_id = AsyncMock(
            return_value=UserLookupResult(user=_USER_DICT))
        await self.handler.get_user(42)
        self.mock_svc.get_user_by_id.assert_awaited_once_with(42)

    async def test_response_is_json(self):
        resp = await self._call(UserLookupResult(user=_USER_DICT))
        self.assertEqual(resp.content_type, "application/json")


# ---------------------------------------------------------------------------
# CreateUserHandler
# ---------------------------------------------------------------------------

class TestCreateUserHandler(unittest.IsolatedAsyncioTestCase):

    asyncSetUp = _make_handler_setup(CreateUserHandler)

    def _request(self, **overrides):
        body = {
            "email_address": "new@example.com",
            "full_name": "New User",
            "display_name": "New",
        }
        body.update(overrides)
        mock_req = MagicMock()
        mock_req.body = body
        return mock_req

    async def _call(self, result: UserCreateResult, **body_overrides) -> Response:
        self.mock_svc.create_user = AsyncMock(return_value=result)
        target = _undecorated(self.handler.create_user)
        return await target(self.handler, self._request(**body_overrides))

    async def test_success_returns_201_with_id(self):
        resp = await self._call(UserCreateResult(user_id=5))
        self.assertEqual(resp.status_code, HTTPStatus.CREATED)
        body = json.loads(await resp.get_data())
        self.assertEqual(body["id"], 5)

    async def test_conflict_returns_409(self):
        resp = await self._call(UserCreateResult(conflict=True))
        self.assertEqual(resp.status_code, HTTPStatus.CONFLICT)
        body = json.loads(await resp.get_data())
        self.assertIn("error", body)

    async def test_unavailable_returns_503(self):
        resp = await self._call(UserCreateResult(available=False))
        self.assertEqual(resp.status_code, HTTPStatus.SERVICE_UNAVAILABLE)

    async def test_is_administrator_defaults_to_false_when_absent(self):
        await self._call(UserCreateResult(user_id=1))
        kwargs = self.mock_svc.create_user.call_args[1]
        self.assertFalse(kwargs.get("is_administrator", False))

    async def test_is_administrator_passed_when_provided(self):
        await self._call(UserCreateResult(user_id=1), is_administrator=True)
        kwargs = self.mock_svc.create_user.call_args[1]
        self.assertTrue(kwargs["is_administrator"])

    async def test_password_none_when_not_in_body(self):
        """No password in body → service called with password=None."""
        await self._call(UserCreateResult(user_id=1))
        kwargs = self.mock_svc.create_user.call_args[1]
        self.assertIsNone(kwargs["password"])

    async def test_password_passed_when_in_body(self):
        """Explicit password in body → passed through to service."""
        await self._call(UserCreateResult(user_id=1), password="mypassword")
        kwargs = self.mock_svc.create_user.call_args[1]
        self.assertEqual(kwargs["password"], "mypassword")

    async def test_generated_password_included_in_201_when_set(self):
        resp = await self._call(
            UserCreateResult(user_id=3, generated_password="abc123!@#XYZ"))
        body = json.loads(await resp.get_data())
        self.assertEqual(body["generated_password"], "abc123!@#XYZ")

    async def test_generated_password_absent_from_201_when_not_set(self):
        resp = await self._call(UserCreateResult(user_id=3))
        body = json.loads(await resp.get_data())
        self.assertNotIn("generated_password", body)

    async def test_response_is_json(self):
        resp = await self._call(UserCreateResult(user_id=1))
        self.assertEqual(resp.content_type, "application/json")


# ---------------------------------------------------------------------------
# ModifyUserHandler
# ---------------------------------------------------------------------------

class TestModifyUserHandler(unittest.IsolatedAsyncioTestCase):

    asyncSetUp = _make_handler_setup(ModifyUserHandler)

    def _request(self, **overrides):
        # All fields optional (patch-style); default body is empty.
        mock_req = MagicMock()
        mock_req.body = overrides
        return mock_req

    async def _call(self, result: UserUpdateResult,
                    user_id: int = 1, **body_overrides) -> Response:
        self.mock_svc.update_user = AsyncMock(return_value=result)
        target = _undecorated(self.handler.modify_user)
        return await target(self.handler, self._request(**body_overrides),
                            user_id=user_id)

    async def test_success_returns_200(self):
        resp = await self._call(UserUpdateResult(success=True))
        self.assertEqual(resp.status_code, HTTPStatus.OK)

    async def test_not_found_returns_404(self):
        resp = await self._call(UserUpdateResult(found=False))
        self.assertEqual(resp.status_code, HTTPStatus.NOT_FOUND)
        body = json.loads(await resp.get_data())
        self.assertIn("error", body)

    async def test_forbidden_returns_403(self):
        resp = await self._call(UserUpdateResult(forbidden=True))
        self.assertEqual(resp.status_code, HTTPStatus.FORBIDDEN)
        body = json.loads(await resp.get_data())
        self.assertIn("error", body)

    async def test_forbidden_error_mentions_last_administrator(self):
        resp = await self._call(UserUpdateResult(forbidden=True))
        body = json.loads(await resp.get_data())
        self.assertIn("last", body["error"].lower())

    async def test_unavailable_returns_503(self):
        resp = await self._call(UserUpdateResult(available=False))
        self.assertEqual(resp.status_code, HTTPStatus.SERVICE_UNAVAILABLE)

    async def test_user_id_from_url_passed_to_service(self):
        self.mock_svc.update_user = AsyncMock(
            return_value=UserUpdateResult(success=True))
        target = _undecorated(self.handler.modify_user)
        await target(self.handler, self._request(), user_id=99)
        self.assertEqual(
            self.mock_svc.update_user.call_args[1]["user_id"], 99)

    async def test_supplied_fields_passed_to_service(self):
        """Fields present in body are forwarded; absent fields are None."""
        self.mock_svc.update_user = AsyncMock(
            return_value=UserUpdateResult(success=True))
        target = _undecorated(self.handler.modify_user)
        await target(self.handler,
                     self._request(full_name="Changed"), user_id=1)
        kwargs = self.mock_svc.update_user.call_args[1]
        self.assertEqual(kwargs["full_name"], "Changed")
        self.assertIsNone(kwargs["display_name"])
        self.assertIsNone(kwargs["account_status"])
        self.assertIsNone(kwargs["is_administrator"])

    async def test_response_is_json(self):
        resp = await self._call(UserUpdateResult(success=True))
        self.assertEqual(resp.content_type, "application/json")


# ---------------------------------------------------------------------------
# ResetPasswordHandler
# ---------------------------------------------------------------------------

class TestResetPasswordHandler(unittest.IsolatedAsyncioTestCase):

    asyncSetUp = _make_handler_setup(ResetPasswordHandler)

    def _request(self, new_password="newpass123"):
        mock_req = MagicMock()
        mock_req.body = {"new_password": new_password}
        return mock_req

    async def _call(self, result: PasswordResult, user_id: int = 1) -> Response:
        self.mock_svc.reset_password = AsyncMock(return_value=result)
        target = _undecorated(self.handler.reset_password)
        return await target(self.handler, self._request(), user_id=user_id)

    async def test_success_returns_200(self):
        resp = await self._call(PasswordResult(success=True))
        self.assertEqual(resp.status_code, HTTPStatus.OK)

    async def test_not_found_returns_404(self):
        resp = await self._call(PasswordResult(found=False))
        self.assertEqual(resp.status_code, HTTPStatus.NOT_FOUND)
        body = json.loads(await resp.get_data())
        self.assertIn("error", body)

    async def test_unavailable_returns_503(self):
        resp = await self._call(PasswordResult(available=False))
        self.assertEqual(resp.status_code, HTTPStatus.SERVICE_UNAVAILABLE)

    async def test_user_id_passed_to_service(self):
        self.mock_svc.reset_password = AsyncMock(
            return_value=PasswordResult(success=True))
        target = _undecorated(self.handler.reset_password)
        await target(self.handler, self._request(), user_id=77)
        self.assertEqual(
            self.mock_svc.reset_password.call_args[1]["user_id"], 77)

    async def test_response_is_json(self):
        resp = await self._call(PasswordResult(success=True))
        self.assertEqual(resp.content_type, "application/json")


# ---------------------------------------------------------------------------
# ChangePasswordHandler
# ---------------------------------------------------------------------------

class TestChangePasswordHandler(unittest.IsolatedAsyncioTestCase):

    asyncSetUp = _make_handler_setup(ChangePasswordHandler)

    def _request(self, user_id=1, current_password="oldpass",
                 new_password="newpass123"):
        mock_req = MagicMock()
        mock_req.body = {
            "user_id": user_id,
            "current_password": current_password,
            "new_password": new_password,
        }
        return mock_req

    async def _call(self, result: PasswordResult,
                    user_id=1, current_password="old",
                    new_password="new123") -> Response:
        self.mock_svc.change_own_password = AsyncMock(return_value=result)
        target = _undecorated(self.handler.change_password)
        return await target(
            self.handler,
            self._request(user_id, current_password, new_password))

    async def test_success_returns_200(self):
        resp = await self._call(PasswordResult(success=True))
        self.assertEqual(resp.status_code, HTTPStatus.OK)

    async def test_wrong_password_returns_401(self):
        resp = await self._call(PasswordResult(wrong_password=True))
        self.assertEqual(resp.status_code, HTTPStatus.UNAUTHORIZED)
        body = json.loads(await resp.get_data())
        self.assertIn("error", body)

    async def test_not_found_returns_404(self):
        resp = await self._call(PasswordResult(found=False))
        self.assertEqual(resp.status_code, HTTPStatus.NOT_FOUND)

    async def test_unavailable_returns_503(self):
        resp = await self._call(PasswordResult(available=False))
        self.assertEqual(resp.status_code, HTTPStatus.SERVICE_UNAVAILABLE)

    async def test_unavailable_takes_precedence_over_not_found(self):
        resp = await self._call(PasswordResult(available=False, found=False))
        self.assertEqual(resp.status_code, HTTPStatus.SERVICE_UNAVAILABLE)

    async def test_credentials_passed_to_service(self):
        self.mock_svc.change_own_password = AsyncMock(
            return_value=PasswordResult(success=True))
        target = _undecorated(self.handler.change_password)
        await target(
            self.handler,
            self._request(user_id=5, current_password="old", new_password="new"))
        self.mock_svc.change_own_password.assert_awaited_once_with(
            user_id=5, current_password="old", new_password="new")

    async def test_response_is_json(self):
        resp = await self._call(PasswordResult(success=True))
        self.assertEqual(resp.content_type, "application/json")
