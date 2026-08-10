"""
Copyright 2025-2026 Integrated Test Management Suite Development Team

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
import unittest
from unittest.mock import AsyncMock, MagicMock
from http import HTTPStatus
from weaver_framework.microservice.api_response import ApiResponse
from _test_utils import make_app
from items.services.items_web_portal.page_handlers.admin.\
    admin_users_and_roles_page_handler import AdminUsersAndRolesPageHandler

_LOGGER = MagicMock()
_AUTH_HEADERS = {"Cookie": "items_token=abc; items_user=bob"}
_SESSION_VALID = ApiResponse(
    status_code=HTTPStatus.OK,
    body={"status": "VALID", "is_administrator": True})

_USERS_OK = ApiResponse(
    status_code=HTTPStatus.OK, body={"users": [{"id": 1, "full_name": "Alice"}]})
_INVITES_OK = ApiResponse(
    status_code=HTTPStatus.OK, body={"invites": [
        {"email_address": "new@b.com", "created_at": 1700000000,
         "expires_at": 1700172800}]})


def _config():
    config = MagicMock()
    config.apis_gateway_svc = "http://gateway/"
    return config


def _metadata():
    metadata = MagicMock()
    metadata.instance_name = "INSTANCE"
    return metadata


class TestUsersAndRolesRead(unittest.IsolatedAsyncioTestCase):
    """GET /admin/users_roles"""

    async def asyncSetUp(self):
        self.mock_rest_client = AsyncMock()
        self.mock_rest_client.post.return_value = _SESSION_VALID
        # Default happy path: a single dict body works for both the users
        # and invites GET calls, since each side only reads its own key.
        self.mock_rest_client.get.return_value = ApiResponse(
            status_code=HTTPStatus.OK,
            body={"users": _USERS_OK.body["users"],
                 "invites": _INVITES_OK.body["invites"]})
        handler = AdminUsersAndRolesPageHandler(
            _LOGGER, _config(), self.mock_rest_client, _metadata())

        app = make_app()

        @app.route("/admin/users_roles", methods=["GET"])
        async def route():
            return await handler.users_and_roles()

        self.client = app.test_client()

    async def _get(self, headers=_AUTH_HEADERS):
        async with self.client as c:
            return await c.get("/admin/users_roles", headers=headers)

    async def test_renders_page_with_users(self):
        response = await self._get()
        self.assertEqual(response.status_code, 200)
        text = await response.get_data(as_text=True)
        self.assertIn("Alice", text)

    async def test_renders_page_with_pending_invites(self):
        response = await self._get()
        text = await response.get_data(as_text=True)
        self.assertIn("new@b.com", text)
        self.assertIn("2023-11-14", text)  # formatted created_at

    async def test_no_pending_invites_shows_placeholder(self):
        self.mock_rest_client.get.side_effect = [
            _USERS_OK,
            ApiResponse(status_code=HTTPStatus.OK, body={"invites": []})]
        response = await self._get()
        text = await response.get_data(as_text=True)
        self.assertIn("No pending invites", text)

    async def test_users_gateway_failure_renders_error_message(self):
        self.mock_rest_client.get.side_effect = [
            ApiResponse(status_code=HTTPStatus.SERVICE_UNAVAILABLE, body={}),
            _INVITES_OK]
        response = await self._get()
        self.assertEqual(response.status_code, 200)
        text = await response.get_data(as_text=True)
        self.assertIn("Could not load users", text)

    async def test_invites_fetch_failure_is_non_fatal(self):
        self.mock_rest_client.get.side_effect = [
            _USERS_OK,
            ApiResponse(status_code=HTTPStatus.SERVICE_UNAVAILABLE, body={})]
        response = await self._get()
        self.assertEqual(response.status_code, 200)
        text = await response.get_data(as_text=True)
        self.assertIn("No pending invites", text)

    async def test_invites_fetch_exception_is_non_fatal(self):
        self.mock_rest_client.get.side_effect = [_USERS_OK, RuntimeError("boom")]
        response = await self._get()
        self.assertEqual(response.status_code, 200)
        text = await response.get_data(as_text=True)
        self.assertIn("No pending invites", text)

    async def test_redirects_when_not_authenticated(self):
        response = await self._get(headers={})
        text = await response.get_data(as_text=True)
        self.assertIn("Refresh", text)

    async def test_redirects_when_not_administrator(self):
        self.mock_rest_client.post.return_value = ApiResponse(
            status_code=HTTPStatus.OK,
            body={"status": "VALID", "is_administrator": False})
        response = await self._get()
        text = await response.get_data(as_text=True)
        self.assertIn("Refresh", text)


class TestInviteUser(unittest.IsolatedAsyncioTestCase):
    """POST /admin/users_roles/invite"""

    async def asyncSetUp(self):
        self.mock_rest_client = AsyncMock()
        self.mock_rest_client.post.return_value = _SESSION_VALID
        self.mock_rest_client.get.return_value = ApiResponse(
            status_code=HTTPStatus.OK, body={"users": [], "invites": []})
        handler = AdminUsersAndRolesPageHandler(
            _LOGGER, _config(), self.mock_rest_client, _metadata())

        app = make_app()

        @app.route("/admin/users_roles/invite", methods=["POST"])
        async def route():
            return await handler.invite_user()

        self.client = app.test_client()

    async def _post(self, form):
        async with self.client as c:
            return await c.post(
                "/admin/users_roles/invite", form=form, headers=_AUTH_HEADERS)

    async def test_missing_email_renders_error(self):
        response = await self._post({})
        self.assertEqual(response.status_code, 200)
        text = await response.get_data(as_text=True)
        self.assertIn("Email address is required", text)
        self.mock_rest_client.post.assert_called_once()  # only session check

    async def test_success_rerenders_page(self):
        self.mock_rest_client.post.side_effect = [
            _SESSION_VALID, ApiResponse(status_code=HTTPStatus.CREATED)]
        response = await self._post({"email_address": "new@b.com"})
        self.assertEqual(response.status_code, 200)

    async def test_email_forwarded_to_gateway(self):
        self.mock_rest_client.post.side_effect = [
            _SESSION_VALID, ApiResponse(status_code=HTTPStatus.CREATED)]
        await self._post({"email_address": "new@b.com"})
        url, kwargs = self.mock_rest_client.post.call_args_list[1][0][0], \
            self.mock_rest_client.post.call_args_list[1][1]
        self.assertEqual(url, "http://gateway/web/invites")
        self.assertEqual(kwargs["json_data"], {"email_address": "new@b.com"})

    async def test_already_invited_shows_error(self):
        self.mock_rest_client.post.side_effect = [
            _SESSION_VALID,
            ApiResponse(status_code=HTTPStatus.CONFLICT,
                       body={"error": "A pending invite already exists"})]
        response = await self._post({"email_address": "new@b.com"})
        text = await response.get_data(as_text=True)
        self.assertIn("A pending invite already exists", text)

    async def test_error_without_body_uses_fallback_message(self):
        self.mock_rest_client.post.side_effect = [
            _SESSION_VALID,
            ApiResponse(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, body={})]
        response = await self._post({"email_address": "new@b.com"})
        text = await response.get_data(as_text=True)
        self.assertIn("could not be completed", text)


class TestResendInvite(unittest.IsolatedAsyncioTestCase):
    """POST /admin/users_roles/invite/resend"""

    async def asyncSetUp(self):
        self.mock_rest_client = AsyncMock()
        self.mock_rest_client.post.return_value = _SESSION_VALID
        self.mock_rest_client.get.return_value = ApiResponse(
            status_code=HTTPStatus.OK, body={"users": [], "invites": []})
        handler = AdminUsersAndRolesPageHandler(
            _LOGGER, _config(), self.mock_rest_client, _metadata())

        app = make_app()

        @app.route("/admin/users_roles/invite/resend", methods=["POST"])
        async def route():
            return await handler.resend_invite()

        self.client = app.test_client()

    async def _post(self, form):
        async with self.client as c:
            return await c.post(
                "/admin/users_roles/invite/resend", form=form,
                headers=_AUTH_HEADERS)

    async def test_success_rerenders_page(self):
        self.mock_rest_client.post.side_effect = [
            _SESSION_VALID, ApiResponse(status_code=HTTPStatus.OK)]
        response = await self._post({"email_address": "new@b.com"})
        self.assertEqual(response.status_code, 200)

    async def test_no_pending_invite_shows_error(self):
        self.mock_rest_client.post.side_effect = [
            _SESSION_VALID,
            ApiResponse(status_code=HTTPStatus.NOT_FOUND,
                       body={"error": "No pending invite found"})]
        response = await self._post({"email_address": "new@b.com"})
        text = await response.get_data(as_text=True)
        self.assertIn("No pending invite found", text)


class TestUninvite(unittest.IsolatedAsyncioTestCase):
    """POST /admin/users_roles/invite/uninvite"""

    async def asyncSetUp(self):
        self.mock_rest_client = AsyncMock()
        self.mock_rest_client.post.return_value = _SESSION_VALID
        self.mock_rest_client.get.return_value = ApiResponse(
            status_code=HTTPStatus.OK, body={"users": [], "invites": []})
        handler = AdminUsersAndRolesPageHandler(
            _LOGGER, _config(), self.mock_rest_client, _metadata())

        app = make_app()

        @app.route("/admin/users_roles/invite/uninvite", methods=["POST"])
        async def route():
            return await handler.uninvite()

        self.client = app.test_client()

    async def _post(self, form):
        async with self.client as c:
            return await c.post(
                "/admin/users_roles/invite/uninvite", form=form,
                headers=_AUTH_HEADERS)

    async def test_success_rerenders_page(self):
        self.mock_rest_client.post.side_effect = [
            _SESSION_VALID, ApiResponse(status_code=HTTPStatus.OK)]
        response = await self._post({"email_address": "new@b.com"})
        self.assertEqual(response.status_code, 200)

    async def test_email_forwarded_to_gateway(self):
        self.mock_rest_client.post.side_effect = [
            _SESSION_VALID, ApiResponse(status_code=HTTPStatus.OK)]
        await self._post({"email_address": "new@b.com"})
        call = self.mock_rest_client.post.call_args_list[1]
        self.assertEqual(call[0][0], "http://gateway/web/invites/uninvite")
        self.assertEqual(call[1]["json_data"], {"email_address": "new@b.com"})

    async def test_no_pending_invite_shows_error(self):
        self.mock_rest_client.post.side_effect = [
            _SESSION_VALID,
            ApiResponse(status_code=HTTPStatus.NOT_FOUND,
                       body={"error": "No pending invite found"})]
        response = await self._post({"email_address": "new@b.com"})
        text = await response.get_data(as_text=True)
        self.assertIn("No pending invite found", text)


class TestFormatEpoch(unittest.TestCase):
    """Direct unit tests for the _format_epoch helper."""

    def test_none_returns_empty_string(self):
        self.assertEqual(
            AdminUsersAndRolesPageHandler._format_epoch(None), "")

    def test_formats_epoch_seconds(self):
        result = AdminUsersAndRolesPageHandler._format_epoch(1700000000)
        self.assertEqual(result, "2023-11-14 22:13 UTC")


if __name__ == "__main__":
    unittest.main()
