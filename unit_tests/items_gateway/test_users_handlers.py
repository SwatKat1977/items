"""
Unit tests for gateway user management route handlers:
  GET  /users              - ListUsersHandler
  GET  /users/<uuid>       - GetUserHandler
  POST /users              - CreateUserHandler
  PATCH /users/<uuid>      - ModifyUserHandler
  POST /users/<uuid>/password - ResetPasswordHandler
"""
import json
import unittest
from unittest.mock import AsyncMock, MagicMock
from quart import Quart
from weaver_framework.microservice.api_response import ApiResponse
from items.services.items_gateway.routes.web.users.list_users_handler import (
    ListUsersHandler)
from items.services.items_gateway.routes.web.users.get_user_handler import (
    GetUserHandler)
from items.services.items_gateway.routes.web.users.create_user_handler import (
    CreateUserHandler)
from items.services.items_gateway.routes.web.users.modify_user_handler import (
    ModifyUserHandler)
from items.services.items_gateway.routes.web.users.reset_password_handler import (
    ResetPasswordHandler)
from items.services.items_gateway.services.email_service import EmailServiceError

_LOGGER = MagicMock()
_UUID = "550e8400-e29b-41d4-a716-446655440000"
_UUID2 = "660e8400-e29b-41d4-a716-446655440000"
_USER = {
    "id": _UUID,
    "email_address": "a@b.com",
    "full_name": "Full",
    "display_name": "Display",
    "account_status": 1,
    "logon_type": 0,
    "is_administrator": True,
}


def _config():
    cfg = MagicMock()
    cfg.apis_identity_svc = "http://identity/"
    cfg.apis_web_portal_svc = "http://portal/"
    return cfg


def _ok(body):
    return ApiResponse(status_code=200, body=body)


def _err(body, status=500):
    return ApiResponse(status_code=status, body=body)


def _conn_err():
    r = ApiResponse(status_code=0, body=None)
    r.exception_msg = "connection refused"
    return r


# ---------------------------------------------------------------------------
# ListUsersHandler
# ---------------------------------------------------------------------------

class TestListUsersHandler(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.mock_rc = AsyncMock()
        handler = ListUsersHandler(_LOGGER, _config(), self.mock_rc)
        app = Quart(__name__)

        @app.route("/users", methods=["GET"])
        async def route():
            return await handler.list_users()

        self.client = app.test_client()

    async def _get(self):
        async with self.client as c:
            return await c.get("/users")

    async def test_success_returns_200_with_body(self):
        self.mock_rc.get.return_value = _ok({"users": [_USER]})
        resp = await self._get()
        self.assertEqual(resp.status_code, 200)
        body = json.loads(await resp.get_data())
        self.assertEqual(body["users"], [_USER])

    async def test_identity_url_is_correct(self):
        self.mock_rc.get.return_value = _ok({"users": []})
        await self._get()
        self.mock_rc.get.assert_called_once_with("http://identity/users")

    async def test_identity_503_is_propagated(self):
        self.mock_rc.get.return_value = _err({"error": "unavailable"}, 503)
        resp = await self._get()
        self.assertEqual(resp.status_code, 503)

    async def test_connection_error_returns_500(self):
        self.mock_rc.get.return_value = _conn_err()
        resp = await self._get()
        self.assertEqual(resp.status_code, 500)

    async def test_response_is_json(self):
        self.mock_rc.get.return_value = _ok({"users": []})
        resp = await self._get()
        self.assertEqual(resp.content_type, "application/json")


# ---------------------------------------------------------------------------
# GetUserHandler
# ---------------------------------------------------------------------------

class TestGetUserHandler(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.mock_rc = AsyncMock()
        handler = GetUserHandler(_LOGGER, _config(), self.mock_rc)
        app = Quart(__name__)

        @app.route("/users/<string:user_id>", methods=["GET"])
        async def route(user_id: str):
            return await handler.get_user(user_id)

        self.client = app.test_client()

    async def _get(self, user_id=_UUID):
        async with self.client as c:
            return await c.get(f"/users/{user_id}")

    async def test_success_returns_200_with_user(self):
        self.mock_rc.get.return_value = _ok(_USER)
        resp = await self._get(_UUID)
        self.assertEqual(resp.status_code, 200)
        body = json.loads(await resp.get_data())
        self.assertEqual(body, _USER)

    async def test_uuid_included_in_url(self):
        self.mock_rc.get.return_value = _ok(_USER)
        await self._get(_UUID2)
        self.mock_rc.get.assert_called_once_with(
            f"http://identity/users/{_UUID2}")

    async def test_identity_404_is_propagated(self):
        self.mock_rc.get.return_value = _err({"error": "User not found"}, 404)
        resp = await self._get(_UUID)
        self.assertEqual(resp.status_code, 404)

    async def test_connection_error_returns_500(self):
        self.mock_rc.get.return_value = _conn_err()
        resp = await self._get()
        self.assertEqual(resp.status_code, 500)

    async def test_response_is_json(self):
        self.mock_rc.get.return_value = _ok(_USER)
        resp = await self._get()
        self.assertEqual(resp.content_type, "application/json")

    async def test_id_in_response_is_uuid_string(self):
        self.mock_rc.get.return_value = _ok(_USER)
        resp = await self._get()
        body = json.loads(await resp.get_data())
        self.assertIsInstance(body["id"], str)


# ---------------------------------------------------------------------------
# CreateUserHandler
# ---------------------------------------------------------------------------

class TestCreateUserHandler(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.mock_rc = AsyncMock()
        handler = CreateUserHandler(_LOGGER, _config(), self.mock_rc)
        app = Quart(__name__)

        @app.route("/users", methods=["POST"])
        async def route():
            return await handler.create_user()

        self.client = app.test_client()

    async def _post(self, body):
        async with self.client as c:
            return await c.post("/users", json=body)

    async def test_success_returns_201_with_uuid(self):
        self.mock_rc.post.return_value = ApiResponse(
            status_code=201, body={"id": _UUID})
        resp = await self._post({"email_address": "a@b.com",
                                  "full_name": "A", "display_name": "A"})
        self.assertEqual(resp.status_code, 201)
        body = json.loads(await resp.get_data())
        self.assertEqual(body["id"], _UUID)

    async def test_id_in_response_is_uuid_string(self):
        self.mock_rc.post.return_value = ApiResponse(
            status_code=201, body={"id": _UUID})
        resp = await self._post({"email_address": "a@b.com",
                                  "full_name": "A", "display_name": "A"})
        body = json.loads(await resp.get_data())
        self.assertIsInstance(body["id"], str)

    async def test_generated_password_propagated(self):
        self.mock_rc.post.return_value = ApiResponse(
            status_code=201, body={"id": _UUID, "generated_password": "xyz"})
        resp = await self._post({"email_address": "a@b.com",
                                  "full_name": "A", "display_name": "A"})
        body = json.loads(await resp.get_data())
        self.assertEqual(body["generated_password"], "xyz")

    async def test_body_forwarded_to_identity(self):
        self.mock_rc.post.return_value = ApiResponse(
            status_code=201, body={"id": _UUID})
        payload = {"email_address": "a@b.com",
                   "full_name": "A", "display_name": "A"}
        await self._post(payload)
        _, kwargs = self.mock_rc.post.call_args
        self.assertEqual(kwargs["json_data"], payload)

    async def test_identity_409_is_propagated(self):
        self.mock_rc.post.return_value = _err(
            {"error": "Email address already registered"}, 409)
        resp = await self._post({"email_address": "a@b.com",
                                  "full_name": "A", "display_name": "A"})
        self.assertEqual(resp.status_code, 409)

    async def test_missing_body_returns_400(self):
        async with self.client as c:
            resp = await c.post("/users", data="not json",
                                headers={"Content-Type": "text/plain"})
        self.assertEqual(resp.status_code, 400)
        self.mock_rc.post.assert_not_called()

    async def test_connection_error_returns_500(self):
        self.mock_rc.post.return_value = _conn_err()
        resp = await self._post({"email_address": "a@b.com",
                                  "full_name": "A", "display_name": "A"})
        self.assertEqual(resp.status_code, 500)

    async def test_response_is_json(self):
        self.mock_rc.post.return_value = ApiResponse(
            status_code=201, body={"id": _UUID})
        resp = await self._post({"email_address": "a@b.com",
                                  "full_name": "A", "display_name": "A"})
        self.assertEqual(resp.content_type, "application/json")


# ---------------------------------------------------------------------------
# ModifyUserHandler
# ---------------------------------------------------------------------------

class TestModifyUserHandler(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.mock_rc = AsyncMock()
        handler = ModifyUserHandler(_LOGGER, _config(), self.mock_rc)
        app = Quart(__name__)

        @app.route("/users/<string:user_id>", methods=["PATCH"])
        async def route(user_id: str):
            return await handler.modify_user(user_id)

        self.client = app.test_client()

    async def _patch(self, user_id=_UUID, body=None):
        async with self.client as c:
            return await c.patch(f"/users/{user_id}",
                                 json=body or {"display_name": "New"})

    async def test_success_returns_200(self):
        self.mock_rc.patch.return_value = _ok({"status": "ok"})
        resp = await self._patch()
        self.assertEqual(resp.status_code, 200)

    async def test_uuid_and_body_forwarded(self):
        self.mock_rc.patch.return_value = _ok({"status": "ok"})
        await self._patch(user_id=_UUID2, body={"full_name": "Changed"})
        call_args = self.mock_rc.patch.call_args
        self.assertIn(f"users/{_UUID2}", call_args[0][0])
        self.assertEqual(call_args[1]["json_data"], {"full_name": "Changed"})

    async def test_identity_403_is_propagated(self):
        self.mock_rc.patch.return_value = _err(
            {"error": "Cannot remove the last active administrator"}, 403)
        resp = await self._patch()
        self.assertEqual(resp.status_code, 403)

    async def test_identity_404_is_propagated(self):
        self.mock_rc.patch.return_value = _err({"error": "User not found"}, 404)
        resp = await self._patch()
        self.assertEqual(resp.status_code, 404)

    async def test_missing_body_returns_400(self):
        async with self.client as c:
            resp = await c.patch(f"/users/{_UUID}", data="not json",
                                 headers={"Content-Type": "text/plain"})
        self.assertEqual(resp.status_code, 400)
        self.mock_rc.patch.assert_not_called()

    async def test_connection_error_returns_500(self):
        self.mock_rc.patch.return_value = _conn_err()
        resp = await self._patch()
        self.assertEqual(resp.status_code, 500)

    async def test_response_is_json(self):
        self.mock_rc.patch.return_value = _ok({"status": "ok"})
        resp = await self._patch()
        self.assertEqual(resp.content_type, "application/json")


# ---------------------------------------------------------------------------
# ResetPasswordHandler
# ---------------------------------------------------------------------------

class TestResetPasswordHandler(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.mock_rc = AsyncMock()
        handler = ResetPasswordHandler(_LOGGER, _config(), self.mock_rc)
        app = Quart(__name__)

        @app.route("/users/<string:user_id>/password", methods=["POST"])
        async def route(user_id: str):
            return await handler.reset_password(user_id)

        self.client = app.test_client()

    async def _post(self, user_id=_UUID, body=None):
        async with self.client as c:
            return await c.post(f"/users/{user_id}/password",
                                json=body or {"new_password": "newpass123"})

    async def test_success_returns_200(self):
        self.mock_rc.post.return_value = _ok({"status": "ok"})
        resp = await self._post()
        self.assertEqual(resp.status_code, 200)

    async def test_uuid_and_body_forwarded(self):
        self.mock_rc.post.return_value = _ok({"status": "ok"})
        await self._post(user_id=_UUID2, body={"new_password": "abc"})
        call_args = self.mock_rc.post.call_args
        self.assertIn(f"users/{_UUID2}/password", call_args[0][0])
        self.assertEqual(call_args[1]["json_data"], {"new_password": "abc"})

    async def test_identity_404_is_propagated(self):
        self.mock_rc.post.return_value = _err({"error": "User not found"}, 404)
        resp = await self._post()
        self.assertEqual(resp.status_code, 404)

    async def test_missing_body_returns_400(self):
        async with self.client as c:
            resp = await c.post(f"/users/{_UUID}/password", data="not json",
                                headers={"Content-Type": "text/plain"})
        self.assertEqual(resp.status_code, 400)
        self.mock_rc.post.assert_not_called()

    async def test_connection_error_returns_500(self):
        self.mock_rc.post.return_value = _conn_err()
        resp = await self._post()
        self.assertEqual(resp.status_code, 500)

    async def test_response_is_json(self):
        self.mock_rc.post.return_value = _ok({"status": "ok"})
        resp = await self._post()
        self.assertEqual(resp.content_type, "application/json")


# ---------------------------------------------------------------------------
# ResetPasswordHandler — email notification behaviour
# ---------------------------------------------------------------------------

class TestResetPasswordHandlerEmail(unittest.IsolatedAsyncioTestCase):
    """Tests for the email notification sent after a successful password reset."""

    def _make_handler_and_app(self, email_service=None):
        mock_rc = AsyncMock()
        handler = ResetPasswordHandler(
            _LOGGER, _config(), mock_rc, email_service)
        app = Quart(__name__)

        @app.route("/users/<string:user_id>/password", methods=["POST"])
        async def route(user_id: str):
            return await handler.reset_password(user_id)

        return mock_rc, app

    async def test_email_sent_on_success(self):
        email_svc = AsyncMock()
        mock_rc, app = self._make_handler_and_app(email_svc)
        # POST /users/.../password → 200
        mock_rc.post.return_value = _ok({"status": "ok"})
        # GET /users/... → user with email
        mock_rc.get.return_value = _ok(_USER)

        async with app.test_client() as c:
            resp = await c.post(f"/users/{_UUID}/password",
                                json={"new_password": "newpass123"})
        self.assertEqual(resp.status_code, 200)
        email_svc.send.assert_awaited_once()
        _, kwargs = email_svc.send.call_args
        self.assertEqual(kwargs["to"], _USER["email_address"])

    async def test_email_body_contains_login_link(self):
        email_svc = AsyncMock()
        mock_rc, app = self._make_handler_and_app(email_svc)
        mock_rc.post.return_value = _ok({"status": "ok"})
        mock_rc.get.return_value = _ok(_USER)

        async with app.test_client() as c:
            await c.post(f"/users/{_UUID}/password",
                         json={"new_password": "newpass123"})
        _, kwargs = email_svc.send.call_args
        self.assertIn("http://portal/login", kwargs["body"])

    async def test_email_not_sent_on_404(self):
        email_svc = AsyncMock()
        mock_rc, app = self._make_handler_and_app(email_svc)
        mock_rc.post.return_value = _err({"error": "not found"}, 404)

        async with app.test_client() as c:
            resp = await c.post(f"/users/{_UUID}/password",
                                json={"new_password": "newpass123"})
        self.assertEqual(resp.status_code, 404)
        email_svc.send.assert_not_awaited()

    async def test_email_failure_does_not_affect_response(self):
        email_svc = AsyncMock()
        email_svc.send.side_effect = EmailServiceError("SMTP down")
        mock_rc, app = self._make_handler_and_app(email_svc)
        mock_rc.post.return_value = _ok({"status": "ok"})
        mock_rc.get.return_value = _ok(_USER)

        async with app.test_client() as c:
            resp = await c.post(f"/users/{_UUID}/password",
                                json={"new_password": "newpass123"})
        # Password was reset successfully; email failure must not flip status
        self.assertEqual(resp.status_code, 200)

    async def test_no_email_when_user_fetch_fails(self):
        email_svc = AsyncMock()
        mock_rc, app = self._make_handler_and_app(email_svc)
        mock_rc.post.return_value = _ok({"status": "ok"})
        mock_rc.get.return_value = _err({}, 404)

        async with app.test_client() as c:
            resp = await c.post(f"/users/{_UUID}/password",
                                json={"new_password": "newpass123"})
        self.assertEqual(resp.status_code, 200)
        email_svc.send.assert_not_awaited()

    async def test_no_email_when_user_has_no_email_address(self):
        email_svc = AsyncMock()
        mock_rc, app = self._make_handler_and_app(email_svc)
        mock_rc.post.return_value = _ok({"status": "ok"})
        # User fetched OK but email_address is absent from the body
        mock_rc.get.return_value = _ok({"id": _UUID, "full_name": "Alice"})

        async with app.test_client() as c:
            resp = await c.post(f"/users/{_UUID}/password",
                                json={"new_password": "newpass123"})
        self.assertEqual(resp.status_code, 200)
        email_svc.send.assert_not_awaited()

    async def test_no_email_when_email_service_is_none(self):
        mock_rc, app = self._make_handler_and_app(email_service=None)
        mock_rc.post.return_value = _ok({"status": "ok"})

        async with app.test_client() as c:
            resp = await c.post(f"/users/{_UUID}/password",
                                json={"new_password": "newpass123"})
        # Should succeed without attempting any email
        self.assertEqual(resp.status_code, 200)
        # get should not have been called (no user fetch without email service)
        mock_rc.get.assert_not_awaited()
