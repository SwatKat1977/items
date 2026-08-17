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
_ROLES_LIST_OK = ApiResponse(
    status_code=HTTPStatus.OK, body={"roles": [{"id": 1, "name": "Tester"}]})
_ROLE_DETAIL_OK = ApiResponse(
    status_code=HTTPStatus.OK,
    body={"id": 1, "name": "Tester", "permissions": [
        {"area": "test_cases", "can_read": True, "can_add_modify": True,
         "can_delete": False}]})
_ROLES_EMPTY = ApiResponse(status_code=HTTPStatus.OK, body={"roles": []})


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

    async def test_success_confirms_the_invitation(self):
        self.mock_rest_client.post.side_effect = [
            _SESSION_VALID, ApiResponse(status_code=HTTPStatus.CREATED)]

        response = await self._post({"email_address": "new@b.com"})
        text = await response.get_data(as_text=True)

        self.assertIn("alert-success", text)
        self.assertIn("sent to new@b.com", text)

    async def test_invite_banner_uses_the_default_dismiss_delay(self):
        self.mock_rest_client.post.side_effect = [
            _SESSION_VALID, ApiResponse(status_code=HTTPStatus.CREATED)]

        response = await self._post({"email_address": "new@b.com"})
        text = await response.get_data(as_text=True)

        self.assertIn('data-auto-dismiss-ms="10000"', text)

    async def test_success_stays_on_the_users_tab(self):
        """A non-role write shouldn't jump the admin over to Roles."""
        self.mock_rest_client.post.side_effect = [
            _SESSION_VALID, ApiResponse(status_code=HTTPStatus.CREATED)]

        response = await self._post({"email_address": "new@b.com"})
        text = await response.get_data(as_text=True)

        self.assertIn(
            'tab-pane fade show active" id="users-tab-pane"', text)


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

    async def test_success_confirms_the_resend(self):
        """Without this the page looks identical to having done nothing."""
        self.mock_rest_client.post.side_effect = [
            _SESSION_VALID, ApiResponse(status_code=HTTPStatus.OK)]

        response = await self._post({"email_address": "new@b.com"})
        text = await response.get_data(as_text=True)

        self.assertIn("alert-success", text)
        self.assertIn("resent to new@b.com", text)

    async def test_success_warns_the_previous_link_is_dead(self):
        """Resending regenerates the token, invalidating any earlier link."""
        self.mock_rest_client.post.side_effect = [
            _SESSION_VALID, ApiResponse(status_code=HTTPStatus.OK)]

        response = await self._post({"email_address": "new@b.com"})
        text = await response.get_data(as_text=True)

        self.assertIn("no longer valid", text)

    async def test_failure_shows_no_success_banner(self):
        self.mock_rest_client.post.side_effect = [
            _SESSION_VALID,
            ApiResponse(status_code=HTTPStatus.NOT_FOUND,
                       body={"error": "No pending invite found"})]

        response = await self._post({"email_address": "new@b.com"})
        text = await response.get_data(as_text=True)

        self.assertIn("alert-danger", text)
        self.assertNotIn("alert-success", text)

    async def test_resend_banner_stays_longer_than_the_default(self):
        """It reports the previous link is dead, so it needs reading time."""
        self.mock_rest_client.post.side_effect = [
            _SESSION_VALID, ApiResponse(status_code=HTTPStatus.OK)]

        response = await self._post({"email_address": "new@b.com"})
        text = await response.get_data(as_text=True)

        self.assertIn('data-auto-dismiss-ms="20000"', text)

    async def test_error_banner_has_no_auto_dismiss(self):
        """A missed error is worse than a missed confirmation."""
        self.mock_rest_client.post.side_effect = [
            _SESSION_VALID,
            ApiResponse(status_code=HTTPStatus.NOT_FOUND,
                       body={"error": "No pending invite found"})]

        response = await self._post({"email_address": "new@b.com"})
        text = await response.get_data(as_text=True)

        # The attribute drives auto-dismissal; errors must not carry it.
        self.assertNotIn("data-auto-dismiss-ms", text)


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

    async def test_success_confirms_the_cancellation(self):
        self.mock_rest_client.post.side_effect = [
            _SESSION_VALID, ApiResponse(status_code=HTTPStatus.OK)]

        response = await self._post({"email_address": "new@b.com"})
        text = await response.get_data(as_text=True)

        self.assertIn("alert-success", text)
        self.assertIn("new@b.com", text)
        self.assertIn("cancelled", text)

    async def test_no_pending_invite_shows_error(self):
        self.mock_rest_client.post.side_effect = [
            _SESSION_VALID,
            ApiResponse(status_code=HTTPStatus.NOT_FOUND,
                       body={"error": "No pending invite found"})]
        response = await self._post({"email_address": "new@b.com"})
        text = await response.get_data(as_text=True)
        self.assertIn("No pending invite found", text)


class TestUsersAndRolesReadRoles(unittest.IsolatedAsyncioTestCase):
    """GET /admin/users_roles - the Roles section."""

    async def asyncSetUp(self):
        self.mock_rest_client = AsyncMock()
        self.mock_rest_client.post.return_value = _SESSION_VALID
        self.mock_rest_client.get.side_effect = [
            _USERS_OK, _INVITES_OK, _ROLES_LIST_OK, _ROLE_DETAIL_OK]
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

    async def test_renders_page_with_roles(self):
        response = await self._get()
        self.assertEqual(response.status_code, 200)
        text = await response.get_data(as_text=True)
        self.assertIn("Tester", text)

    async def test_no_roles_shows_placeholder(self):
        self.mock_rest_client.get.side_effect = [
            _USERS_OK, _INVITES_OK, _ROLES_EMPTY]
        response = await self._get()
        text = await response.get_data(as_text=True)
        self.assertIn("No roles defined yet", text)

    async def test_roles_fetch_failure_is_non_fatal(self):
        self.mock_rest_client.get.side_effect = [
            _USERS_OK, _INVITES_OK,
            ApiResponse(status_code=HTTPStatus.SERVICE_UNAVAILABLE, body={})]
        response = await self._get()
        self.assertEqual(response.status_code, 200)
        text = await response.get_data(as_text=True)
        self.assertIn("No roles defined yet", text)

    async def test_roles_fetch_exception_is_non_fatal(self):
        self.mock_rest_client.get.side_effect = [
            _USERS_OK, _INVITES_OK, RuntimeError("boom")]
        response = await self._get()
        self.assertEqual(response.status_code, 200)
        text = await response.get_data(as_text=True)
        self.assertIn("No roles defined yet", text)

    async def test_role_detail_failure_still_lists_the_role(self):
        """A bad detail fetch for one role doesn't drop it from the table -
        it's shown with an empty grid instead."""
        self.mock_rest_client.get.side_effect = [
            _USERS_OK, _INVITES_OK, _ROLES_LIST_OK,
            ApiResponse(status_code=HTTPStatus.SERVICE_UNAVAILABLE, body={})]
        response = await self._get()
        text = await response.get_data(as_text=True)
        self.assertIn("Tester", text)

    async def test_permissions_embedded_for_the_edit_modal(self):
        response = await self._get()
        text = await response.get_data(as_text=True)
        self.assertIn("data-permissions=", text)
        self.assertIn("test_cases", text)

    async def test_role_detail_fetch_exception_still_lists_the_role(self):
        """A raised exception fetching one role's grid (as opposed to a
        plain error status) is caught the same way - the role stays listed
        with an empty grid rather than taking the whole page down."""
        self.mock_rest_client.get.side_effect = [
            _USERS_OK, _INVITES_OK, _ROLES_LIST_OK, RuntimeError("boom")]
        response = await self._get()
        self.assertEqual(response.status_code, 200)
        text = await response.get_data(as_text=True)
        self.assertIn("Tester", text)


class TestRoleAdd(unittest.IsolatedAsyncioTestCase):
    """POST /admin/users_roles/roles"""

    async def asyncSetUp(self):
        self.mock_rest_client = AsyncMock()
        self.mock_rest_client.post.return_value = _SESSION_VALID
        self.mock_rest_client.get.return_value = ApiResponse(
            status_code=HTTPStatus.OK, body={"users": [], "invites": []})
        handler = AdminUsersAndRolesPageHandler(
            _LOGGER, _config(), self.mock_rest_client, _metadata())

        app = make_app()

        @app.route("/admin/users_roles/roles", methods=["POST"])
        async def route():
            return await handler.role_add()

        self.client = app.test_client()

    async def _post(self, form):
        async with self.client as c:
            return await c.post(
                "/admin/users_roles/roles", form=form, headers=_AUTH_HEADERS)

    async def test_missing_name_renders_error(self):
        response = await self._post({})
        self.assertEqual(response.status_code, 200)
        text = await response.get_data(as_text=True)
        self.assertIn("Role name is required", text)
        self.mock_rest_client.post.assert_called_once()  # only session check

    async def test_success_rerenders_page(self):
        self.mock_rest_client.post.side_effect = [
            _SESSION_VALID,
            ApiResponse(status_code=HTTPStatus.CREATED, body={"id": 1})]
        response = await self._post({"name": "Tester"})
        self.assertEqual(response.status_code, 200)

    async def test_name_and_permissions_forwarded_to_gateway(self):
        self.mock_rest_client.post.side_effect = [
            _SESSION_VALID,
            ApiResponse(status_code=HTTPStatus.CREATED, body={"id": 1})]
        await self._post({
            "name": "Tester",
            "perm_test_cases_read": "on",
            "perm_test_cases_add_modify": "on",
        })
        call = self.mock_rest_client.post.call_args_list[1]
        self.assertEqual(call[0][0], "http://gateway/web/roles")
        self.assertEqual(call[1]["json_data"], {
            "name": "Tester",
            "permissions": [{
                "area": "test_cases", "can_read": True,
                "can_add_modify": True, "can_delete": False,
            }],
        })

    async def test_unticked_area_omitted_from_permissions(self):
        self.mock_rest_client.post.side_effect = [
            _SESSION_VALID,
            ApiResponse(status_code=HTTPStatus.CREATED, body={"id": 1})]
        await self._post({"name": "Tester"})
        call = self.mock_rest_client.post.call_args_list[1]
        self.assertEqual(call[1]["json_data"]["permissions"], [])

    async def test_duplicate_name_shows_error(self):
        self.mock_rest_client.post.side_effect = [
            _SESSION_VALID,
            ApiResponse(status_code=HTTPStatus.CONFLICT,
                       body={"error": "Role name already in use"})]
        response = await self._post({"name": "Tester"})
        text = await response.get_data(as_text=True)
        self.assertIn("Role name already in use", text)

    async def test_success_confirms_the_role(self):
        self.mock_rest_client.post.side_effect = [
            _SESSION_VALID,
            ApiResponse(status_code=HTTPStatus.CREATED, body={"id": 1})]
        response = await self._post({"name": "Tester"})
        text = await response.get_data(as_text=True)
        self.assertIn("alert-success", text)
        self.assertIn("Tester", text)
        self.assertIn("created", text)

    async def test_success_returns_to_the_roles_tab(self):
        self.mock_rest_client.post.side_effect = [
            _SESSION_VALID,
            ApiResponse(status_code=HTTPStatus.CREATED, body={"id": 1})]
        response = await self._post({"name": "Tester"})
        text = await response.get_data(as_text=True)
        self.assertIn(
            'tab-pane fade show active" id="roles-tab-pane"', text)

    async def test_validation_error_stays_on_the_roles_tab(self):
        """A missing-name resubmit shouldn't bounce the admin back to the
        Users tab, away from the form they were just filling in."""
        response = await self._post({})
        text = await response.get_data(as_text=True)
        self.assertIn(
            'tab-pane fade show active" id="roles-tab-pane"', text)

    async def test_gateway_error_stays_on_the_roles_tab(self):
        self.mock_rest_client.post.side_effect = [
            _SESSION_VALID,
            ApiResponse(status_code=HTTPStatus.CONFLICT,
                       body={"error": "Role name already in use"})]
        response = await self._post({"name": "Tester"})
        text = await response.get_data(as_text=True)
        self.assertIn(
            'tab-pane fade show active" id="roles-tab-pane"', text)


class TestRoleModify(unittest.IsolatedAsyncioTestCase):
    """POST /admin/users_roles/roles/<id>/modify"""

    async def asyncSetUp(self):
        self.mock_rest_client = AsyncMock()
        self.mock_rest_client.post.return_value = _SESSION_VALID
        self.mock_rest_client.get.return_value = ApiResponse(
            status_code=HTTPStatus.OK, body={"users": [], "invites": []})
        handler = AdminUsersAndRolesPageHandler(
            _LOGGER, _config(), self.mock_rest_client, _metadata())

        app = make_app()

        @app.route("/admin/users_roles/roles/<int:role_id>/modify",
                  methods=["POST"])
        async def route(role_id: int):
            return await handler.role_modify(role_id)

        self.client = app.test_client()

    async def _post(self, form, role_id=1):
        async with self.client as c:
            return await c.post(
                f"/admin/users_roles/roles/{role_id}/modify", form=form,
                headers=_AUTH_HEADERS)

    async def test_missing_name_renders_error(self):
        response = await self._post({})
        text = await response.get_data(as_text=True)
        self.assertIn("Role name is required", text)

    async def test_success_rerenders_page(self):
        self.mock_rest_client.patch.return_value = ApiResponse(
            status_code=HTTPStatus.OK)
        response = await self._post({"name": "Lead"})
        self.assertEqual(response.status_code, 200)

    async def test_url_and_body_forwarded_to_gateway(self):
        self.mock_rest_client.patch.return_value = ApiResponse(
            status_code=HTTPStatus.OK)
        await self._post({
            "name": "Lead",
            "perm_test_cases_delete": "on",
        }, role_id=9)
        call = self.mock_rest_client.patch.call_args
        self.assertEqual(call[0][0], "http://gateway/web/roles/9")
        self.assertEqual(call[1]["json_data"], {
            "name": "Lead",
            "permissions": [{
                "area": "test_cases", "can_read": False,
                "can_add_modify": False, "can_delete": True,
            }],
        })

    async def test_not_found_shows_error(self):
        self.mock_rest_client.patch.return_value = ApiResponse(
            status_code=HTTPStatus.NOT_FOUND,
            body={"error": "Role not found"})
        response = await self._post({"name": "Lead"})
        text = await response.get_data(as_text=True)
        self.assertIn("Role not found", text)

    async def test_success_confirms_the_update(self):
        self.mock_rest_client.patch.return_value = ApiResponse(
            status_code=HTTPStatus.OK)
        response = await self._post({"name": "Lead"})
        text = await response.get_data(as_text=True)
        self.assertIn("alert-success", text)
        self.assertIn("Lead", text)
        self.assertIn("updated", text)

    async def test_success_returns_to_the_roles_tab(self):
        self.mock_rest_client.patch.return_value = ApiResponse(
            status_code=HTTPStatus.OK)
        response = await self._post({"name": "Lead"})
        text = await response.get_data(as_text=True)
        self.assertIn(
            'tab-pane fade show active" id="roles-tab-pane"', text)


class TestRoleDelete(unittest.IsolatedAsyncioTestCase):
    """POST /admin/users_roles/roles/<id>/delete"""

    async def asyncSetUp(self):
        self.mock_rest_client = AsyncMock()
        self.mock_rest_client.post.return_value = _SESSION_VALID
        self.mock_rest_client.get.return_value = ApiResponse(
            status_code=HTTPStatus.OK, body={"users": [], "invites": []})
        handler = AdminUsersAndRolesPageHandler(
            _LOGGER, _config(), self.mock_rest_client, _metadata())

        app = make_app()

        @app.route("/admin/users_roles/roles/<int:role_id>/delete",
                  methods=["POST"])
        async def route(role_id: int):
            return await handler.role_delete(role_id)

        self.client = app.test_client()

    async def _post(self, form, role_id=1):
        async with self.client as c:
            return await c.post(
                f"/admin/users_roles/roles/{role_id}/delete", form=form,
                headers=_AUTH_HEADERS)

    async def test_success_rerenders_page(self):
        self.mock_rest_client.delete.return_value = ApiResponse(
            status_code=HTTPStatus.OK)
        response = await self._post({"name": "Tester"})
        self.assertEqual(response.status_code, 200)

    async def test_url_includes_role_id(self):
        self.mock_rest_client.delete.return_value = ApiResponse(
            status_code=HTTPStatus.OK)
        await self._post({"name": "Tester"}, role_id=7)
        self.mock_rest_client.delete.assert_called_once_with(
            "http://gateway/web/roles/7")

    async def test_not_found_shows_error(self):
        self.mock_rest_client.delete.return_value = ApiResponse(
            status_code=HTTPStatus.NOT_FOUND,
            body={"error": "Role not found"})
        response = await self._post({"name": "Tester"})
        text = await response.get_data(as_text=True)
        self.assertIn("Role not found", text)

    async def test_success_confirms_the_deletion(self):
        self.mock_rest_client.delete.return_value = ApiResponse(
            status_code=HTTPStatus.OK)
        response = await self._post({"name": "Tester"})
        text = await response.get_data(as_text=True)
        self.assertIn("alert-success", text)
        self.assertIn("Tester", text)
        self.assertIn("deleted", text)

    async def test_missing_name_falls_back_to_a_generic_label(self):
        """The delete form always carries a name (JS sets the hidden field
        before submitting), but a missing one still produces a sensible
        message rather than a KeyError or a blank subject."""
        self.mock_rest_client.delete.return_value = ApiResponse(
            status_code=HTTPStatus.OK)
        response = await self._post({})
        text = await response.get_data(as_text=True)
        self.assertIn("Role", text)
        self.assertIn("deleted", text)

    async def test_success_returns_to_the_roles_tab(self):
        self.mock_rest_client.delete.return_value = ApiResponse(
            status_code=HTTPStatus.OK)
        response = await self._post({"name": "Tester"})
        text = await response.get_data(as_text=True)
        self.assertIn(
            'tab-pane fade show active" id="roles-tab-pane"', text)


class TestParsePermissionsFromForm(unittest.TestCase):
    """Direct unit tests for the _parse_permissions_from_form helper."""

    def test_no_checkboxes_ticked_returns_empty_list(self):
        result = AdminUsersAndRolesPageHandler._parse_permissions_from_form({})
        self.assertEqual(result, [])

    def test_read_only_area_included(self):
        form = {"perm_test_cases_read": "on"}
        result = AdminUsersAndRolesPageHandler._parse_permissions_from_form(
            form)
        self.assertEqual(result, [{
            "area": "test_cases", "can_read": True,
            "can_add_modify": False, "can_delete": False,
        }])

    def test_multiple_areas_preserve_definition_order(self):
        form = {
            "perm_test_cases_read": "on",
            "perm_milestones_delete": "on",
        }
        result = AdminUsersAndRolesPageHandler._parse_permissions_from_form(
            form)
        self.assertEqual([p["area"] for p in result],
                         ["test_cases", "milestones"])


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
