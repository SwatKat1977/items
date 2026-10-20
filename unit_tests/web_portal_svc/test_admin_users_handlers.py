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
import re
import unittest
from unittest.mock import AsyncMock, MagicMock
from http import HTTPStatus
from weaver_framework.microservice.api_response import ApiResponse
from _test_utils import make_app
from items.services.items_web_portal.page_handlers.admin.users.\
    admin_add_user_page_handler import AdminAddUserPageHandler
from items.services.items_web_portal.page_handlers.admin.users.\
    admin_modify_user_page_handler import AdminModifyUserPageHandler
from items.services.items_web_portal.page_handlers.admin.users.\
    admin_reset_password_page_handler import AdminResetPasswordPageHandler

_LOGGER = MagicMock()
_AUTH_HEADERS = {"Cookie": "items_token=abc; items_user=bob"}
_UUID = "550e8400-e29b-41d4-a716-446655440000"

_SESSION_VALID = ApiResponse(
    status_code=HTTPStatus.OK,
    body={"status": "VALID", "is_administrator": True})

_USER = {
    "id": _UUID,
    "full_name": "Alice Smith",
    "display_name": "Alice",
    "email_address": "alice@localhost",
    "account_status": 1,
    "is_administrator": False,
}

_VALID_ADD_FORM = {
    "full_name": "Alice Smith",
    "display_name": "Alice",
    "email_address": "alice@localhost",
    "password": "securepass",
    "password_mode": "manual",
}

_VALID_MODIFY_FORM = {
    "full_name": "Alice Smith",
    "display_name": "Alice",
    "account_status": "1",
}

_PROJECTS_OK = ApiResponse(
    status_code=HTTPStatus.OK,
    body={"projects": [{"id": 5, "name": "Alpha"}, {"id": 7, "name": "Beta"}]})
_ROLES_OK = ApiResponse(
    status_code=HTTPStatus.OK,
    body={"roles": [{"id": 2, "name": "Tester"}, {"id": 3, "name": "Lead"}]})
_MEMBERSHIPS_OK = ApiResponse(
    status_code=HTTPStatus.OK,
    body={"memberships": [{"project_id": 5, "role_id": 2, "role_name": "Tester"}]})
_MEMBERSHIPS_EMPTY = ApiResponse(
    status_code=HTTPStatus.OK, body={"memberships": []})
_USER_OK = ApiResponse(status_code=HTTPStatus.OK, body=_USER)


def _get_side_effect(user=None, memberships=None, roles=None):
    """Build a get() side_effect list matching _render()'s call order:
    user (if fetched fresh), then projects, then memberships, then roles.
    """
    calls = []
    if user is not None:
        calls.append(user)
    calls.append(_PROJECTS_OK)
    calls.append(memberships if memberships is not None else _MEMBERSHIPS_EMPTY)
    calls.append(roles if roles is not None else _ROLES_OK)
    return calls


def _config():
    cfg = MagicMock()
    cfg.apis_gateway_svc = "http://gateway/"
    return cfg


def _metadata():
    m = MagicMock()
    m.instance_name = "INSTANCE"
    return m


# ---------------------------------------------------------------------------
# AdminAddUserPageHandler
# ---------------------------------------------------------------------------

class TestAdminAddUserPageHandler(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.mock_rest_client = AsyncMock()
        handler = AdminAddUserPageHandler(
            _LOGGER, _config(), self.mock_rest_client, _metadata())

        app = make_app()

        @app.route("/admin/users_roles/add", methods=["GET"])
        async def get_route():
            return await handler.add_user_get()

        @app.route("/admin/users_roles/add", methods=["POST"])
        async def post_route():
            return await handler.add_user_post()

        self.client = app.test_client()

    async def _get(self):
        async with self.client as c:
            return await c.get("/admin/users_roles/add", headers=_AUTH_HEADERS)

    async def _post(self, form):
        async with self.client as c:
            return await c.post("/admin/users_roles/add", form=form,
                                headers=_AUTH_HEADERS)

    async def test_get_renders_blank_form(self):
        self.mock_rest_client.post.return_value = _SESSION_VALID
        response = await self._get()
        self.assertEqual(response.status_code, 200)
        text = await response.get_data(as_text=True)
        self.assertNotIn("Refresh", text)

    async def test_post_missing_full_name_renders_error(self):
        self.mock_rest_client.post.return_value = _SESSION_VALID
        form = dict(_VALID_ADD_FORM)
        del form["full_name"]
        response = await self._post(form)
        self.assertEqual(response.status_code, 200)
        text = await response.get_data(as_text=True)
        self.assertIn("required", text)
        self.mock_rest_client.post.assert_called_once()

    async def test_post_missing_display_name_renders_error(self):
        self.mock_rest_client.post.return_value = _SESSION_VALID
        form = dict(_VALID_ADD_FORM)
        del form["display_name"]
        response = await self._post(form)
        self.assertEqual(response.status_code, 200)
        self.mock_rest_client.post.assert_called_once()

    async def test_post_missing_email_renders_error(self):
        self.mock_rest_client.post.return_value = _SESSION_VALID
        form = dict(_VALID_ADD_FORM)
        del form["email_address"]
        response = await self._post(form)
        self.assertEqual(response.status_code, 200)
        self.mock_rest_client.post.assert_called_once()

    async def test_post_short_password_renders_error(self):
        self.mock_rest_client.post.return_value = _SESSION_VALID
        form = dict(_VALID_ADD_FORM)
        form["password"] = "short"
        response = await self._post(form)
        self.assertEqual(response.status_code, 200)
        text = await response.get_data(as_text=True)
        self.assertIn("8 characters", text)
        self.mock_rest_client.post.assert_called_once()

    async def test_post_conflict_renders_email_error(self):
        self.mock_rest_client.post.side_effect = [
            _SESSION_VALID,
            ApiResponse(status_code=HTTPStatus.CONFLICT, body={}),
        ]
        response = await self._post(_VALID_ADD_FORM)
        self.assertEqual(response.status_code, 200)
        text = await response.get_data(as_text=True)
        self.assertIn("already registered", text)

    async def test_post_gateway_error_renders_unexpected_error(self):
        self.mock_rest_client.post.side_effect = [
            _SESSION_VALID,
            ApiResponse(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, body={}),
        ]
        response = await self._post(_VALID_ADD_FORM)
        self.assertEqual(response.status_code, 200)
        text = await response.get_data(as_text=True)
        self.assertIn("unexpected error", text)

    async def test_post_success_redirects(self):
        self.mock_rest_client.post.side_effect = [
            _SESSION_VALID,
            ApiResponse(status_code=HTTPStatus.CREATED, body={"id": 2}),
        ]
        response = await self._post(_VALID_ADD_FORM)
        self.assertEqual(response.status_code, 200)
        text = await response.get_data(as_text=True)
        self.assertIn("Refresh", text)

    async def test_redirects_when_not_authenticated(self):
        async with self.client as c:
            response = await c.get("/admin/users_roles/add")
        text = await response.get_data(as_text=True)
        self.assertIn("Refresh", text)

    async def test_post_is_administrator_checked_is_sent_to_gateway(self):
        self.mock_rest_client.post.side_effect = [
            _SESSION_VALID,
            ApiResponse(status_code=HTTPStatus.CREATED, body={"id": 2}),
        ]
        form = dict(_VALID_ADD_FORM)
        form["is_administrator"] = "1"
        await self._post(form)
        create_call = self.mock_rest_client.post.await_args_list[1]
        self.assertTrue(create_call.kwargs["json_data"]["is_administrator"])

    async def test_post_is_administrator_unchecked_is_sent_as_false(self):
        self.mock_rest_client.post.side_effect = [
            _SESSION_VALID,
            ApiResponse(status_code=HTTPStatus.CREATED, body={"id": 2}),
        ]
        await self._post(_VALID_ADD_FORM)
        create_call = self.mock_rest_client.post.await_args_list[1]
        self.assertFalse(create_call.kwargs["json_data"]["is_administrator"])

    async def test_post_validation_error_re_populates_is_administrator(self):
        self.mock_rest_client.post.return_value = _SESSION_VALID
        form = dict(_VALID_ADD_FORM)
        form["is_administrator"] = "1"
        del form["full_name"]
        response = await self._post(form)
        text = await response.get_data(as_text=True)
        checkbox_start = text.index('id="is_administrator"')
        checkbox_tag = text[checkbox_start:text.index(">", checkbox_start)]
        self.assertIn("checked", checkbox_tag)


# ---------------------------------------------------------------------------
# AdminModifyUserPageHandler
# ---------------------------------------------------------------------------

class TestAdminModifyUserPageHandler(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.mock_rest_client = AsyncMock()
        self.mock_rest_client.post.return_value = _SESSION_VALID
        handler = AdminModifyUserPageHandler(
            _LOGGER, _config(), self.mock_rest_client, _metadata())

        app = make_app()

        @app.route("/admin/users_roles/<string:user_id>/modify", methods=["GET"])
        async def get_route(user_id: str):
            return await handler.modify_user_get(user_id)

        @app.route("/admin/users_roles/<string:user_id>/modify", methods=["POST"])
        async def post_route(user_id: str):
            return await handler.modify_user_post(user_id)

        self.client = app.test_client()

    async def _get(self, user_id=_UUID):
        async with self.client as c:
            return await c.get(f"/admin/users_roles/{user_id}/modify",
                               headers=_AUTH_HEADERS)

    async def _post(self, form, user_id=_UUID):
        async with self.client as c:
            return await c.post(f"/admin/users_roles/{user_id}/modify",
                                form=form, headers=_AUTH_HEADERS)

    async def test_get_success_pre_populates_form(self):
        self.mock_rest_client.get.return_value = ApiResponse(
            status_code=HTTPStatus.OK, body=_USER)
        response = await self._get()
        self.assertEqual(response.status_code, 200)
        text = await response.get_data(as_text=True)
        self.assertIn("Alice Smith", text)

    async def test_get_not_found_renders_error(self):
        self.mock_rest_client.get.return_value = ApiResponse(
            status_code=HTTPStatus.NOT_FOUND, body={})
        response = await self._get()
        self.assertEqual(response.status_code, 200)
        text = await response.get_data(as_text=True)
        self.assertIn("not found", text)

    async def test_get_gateway_error_renders_error(self):
        self.mock_rest_client.get.return_value = ApiResponse(
            status_code=HTTPStatus.SERVICE_UNAVAILABLE, body={})
        response = await self._get()
        self.assertEqual(response.status_code, 200)
        text = await response.get_data(as_text=True)
        self.assertIn("Could not load", text)

    async def test_post_missing_full_name_renders_error(self):
        form = dict(_VALID_MODIFY_FORM)
        del form["full_name"]
        response = await self._post(form)
        self.assertEqual(response.status_code, 200)
        text = await response.get_data(as_text=True)
        self.assertIn("required", text)
        self.mock_rest_client.patch.assert_not_called()

    async def test_post_missing_display_name_renders_error(self):
        form = dict(_VALID_MODIFY_FORM)
        del form["display_name"]
        response = await self._post(form)
        self.assertEqual(response.status_code, 200)
        self.mock_rest_client.patch.assert_not_called()

    async def test_post_forbidden_renders_last_admin_error(self):
        self.mock_rest_client.patch.return_value = ApiResponse(
            status_code=HTTPStatus.FORBIDDEN, body={})
        response = await self._post(_VALID_MODIFY_FORM)
        self.assertEqual(response.status_code, 200)
        text = await response.get_data(as_text=True)
        self.assertIn("no active administrator", text)

    async def test_post_not_found_renders_error(self):
        self.mock_rest_client.patch.return_value = ApiResponse(
            status_code=HTTPStatus.NOT_FOUND, body={})
        response = await self._post(_VALID_MODIFY_FORM)
        self.assertEqual(response.status_code, 200)
        text = await response.get_data(as_text=True)
        self.assertIn("not found", text)

    async def test_post_gateway_error_renders_unexpected_error(self):
        self.mock_rest_client.patch.return_value = ApiResponse(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR, body={})
        response = await self._post(_VALID_MODIFY_FORM)
        self.assertEqual(response.status_code, 200)
        text = await response.get_data(as_text=True)
        self.assertIn("unexpected error", text)

    async def test_post_success_redirects(self):
        self.mock_rest_client.patch.return_value = ApiResponse(
            status_code=HTTPStatus.OK, body={})
        response = await self._post(_VALID_MODIFY_FORM)
        self.assertEqual(response.status_code, 200)
        text = await response.get_data(as_text=True)
        self.assertIn("Refresh", text)

    async def test_redirects_when_not_authenticated(self):
        async with self.client as c:
            response = await c.get(f"/admin/users_roles/{_UUID}/modify")
        text = await response.get_data(as_text=True)
        self.assertIn("Refresh", text)

    async def test_get_pre_populates_is_administrator_when_true(self):
        admin_user = dict(_USER, is_administrator=True)
        self.mock_rest_client.get.return_value = ApiResponse(
            status_code=HTTPStatus.OK, body=admin_user)
        response = await self._get()
        text = await response.get_data(as_text=True)
        checkbox_start = text.index('id="is_administrator"')
        checkbox_tag = text[checkbox_start:text.index(">", checkbox_start)]
        self.assertIn("checked", checkbox_tag)

    async def test_get_does_not_pre_populate_is_administrator_when_false(self):
        self.mock_rest_client.get.return_value = ApiResponse(
            status_code=HTTPStatus.OK, body=_USER)
        response = await self._get()
        text = await response.get_data(as_text=True)
        checkbox_start = text.index('id="is_administrator"')
        checkbox_tag = text[checkbox_start:text.index(">", checkbox_start)]
        self.assertNotIn("checked", checkbox_tag)

    async def test_post_is_administrator_checked_is_sent_to_gateway(self):
        self.mock_rest_client.patch.return_value = ApiResponse(
            status_code=HTTPStatus.OK, body={})
        form = dict(_VALID_MODIFY_FORM)
        form["is_administrator"] = "1"
        await self._post(form)
        patch_call = self.mock_rest_client.patch.await_args
        self.assertTrue(patch_call.kwargs["json_data"]["is_administrator"])

    async def test_post_is_administrator_unchecked_is_sent_as_false(self):
        self.mock_rest_client.patch.return_value = ApiResponse(
            status_code=HTTPStatus.OK, body={})
        await self._post(_VALID_MODIFY_FORM)
        patch_call = self.mock_rest_client.patch.await_args
        self.assertFalse(patch_call.kwargs["json_data"]["is_administrator"])

    # -- Projects tab rendering ---------------------------------------

    async def test_get_shows_membership_with_joined_project_name(self):
        self.mock_rest_client.get.side_effect = _get_side_effect(
            user=_USER_OK, memberships=_MEMBERSHIPS_OK)
        response = await self._get()
        text = await response.get_data(as_text=True)
        self.assertIn("Alpha", text)
        self.assertIn("Tester", text)

    async def test_get_no_memberships_shows_placeholder(self):
        self.mock_rest_client.get.side_effect = _get_side_effect(
            user=_USER_OK, memberships=_MEMBERSHIPS_EMPTY)
        response = await self._get()
        text = await response.get_data(as_text=True)
        self.assertIn("Not a member of any projects", text)

    async def test_get_add_project_excludes_assigned_projects(self):
        """Alpha (id 5) is already assigned - only Beta should be offered."""
        self.mock_rest_client.get.side_effect = _get_side_effect(
            user=_USER_OK, memberships=_MEMBERSHIPS_OK)
        response = await self._get()
        text = await response.get_data(as_text=True)
        add_modal_start = text.index('id="addProjectModal"')
        add_modal_text = text[add_modal_start:add_modal_start + 2000]
        self.assertIn("Beta", add_modal_text)
        self.assertNotIn("Alpha", add_modal_text)

    async def test_get_member_of_every_project_disables_add_button(self):
        all_assigned = ApiResponse(
            status_code=HTTPStatus.OK,
            body={"memberships": [
                {"project_id": 5, "role_id": 2, "role_name": "Tester"},
                {"project_id": 7, "role_id": None, "role_name": None}]})
        self.mock_rest_client.get.side_effect = _get_side_effect(
            user=_USER_OK, memberships=all_assigned)
        response = await self._get()
        text = await response.get_data(as_text=True)
        self.assertIn("Already a member of every project", text)

    async def test_get_defaults_to_the_user_tab(self):
        self.mock_rest_client.get.side_effect = _get_side_effect(user=_USER_OK)
        response = await self._get()
        text = await response.get_data(as_text=True)
        self.assertIn('nav-link active" data-bs-toggle="tab" href="#tab-user"', text)

    async def test_projects_fetch_failure_is_non_fatal(self):
        self.mock_rest_client.get.side_effect = [
            _USER_OK,
            ApiResponse(status_code=HTTPStatus.SERVICE_UNAVAILABLE, body={}),
            _MEMBERSHIPS_EMPTY, _ROLES_OK]
        response = await self._get()
        self.assertEqual(response.status_code, 200)

    async def test_roles_fetch_exception_is_non_fatal(self):
        self.mock_rest_client.get.side_effect = [
            _USER_OK, _PROJECTS_OK, _MEMBERSHIPS_EMPTY, RuntimeError("boom")]
        response = await self._get()
        self.assertEqual(response.status_code, 200)

    async def test_projects_fetch_exception_is_non_fatal(self):
        self.mock_rest_client.get.side_effect = [
            _USER_OK, RuntimeError("boom"), _MEMBERSHIPS_EMPTY, _ROLES_OK]
        response = await self._get()
        self.assertEqual(response.status_code, 200)

    async def test_memberships_fetch_exception_is_non_fatal(self):
        self.mock_rest_client.get.side_effect = [
            _USER_OK, _PROJECTS_OK, RuntimeError("boom"), _ROLES_OK]
        response = await self._get()
        self.assertEqual(response.status_code, 200)


# ---------------------------------------------------------------------------
# Project membership actions (Projects tab)
# ---------------------------------------------------------------------------

class TestAddUserProject(unittest.IsolatedAsyncioTestCase):
    """POST /admin/users_roles/<id>/projects"""

    async def asyncSetUp(self):
        self.mock_rest_client = AsyncMock()
        self.mock_rest_client.post.return_value = _SESSION_VALID
        handler = AdminModifyUserPageHandler(
            _LOGGER, _config(), self.mock_rest_client, _metadata())

        app = make_app()

        @app.route("/admin/users_roles/<string:user_id>/projects",
                  methods=["POST"])
        async def route(user_id: str):
            return await handler.add_user_project(user_id)

        self.client = app.test_client()

    async def _post(self, form, user_id=_UUID):
        async with self.client as c:
            return await c.post(f"/admin/users_roles/{user_id}/projects",
                                form=form, headers=_AUTH_HEADERS)

    async def test_missing_project_id_renders_error(self):
        self.mock_rest_client.get.side_effect = _get_side_effect(user=_USER_OK)
        response = await self._post({})
        self.assertEqual(response.status_code, 200)
        text = await response.get_data(as_text=True)
        self.assertIn("Select a project", text)
        self.mock_rest_client.post.assert_called_once()  # only session check

    async def test_non_integer_project_id_renders_error(self):
        self.mock_rest_client.get.side_effect = _get_side_effect(user=_USER_OK)
        response = await self._post({"project_id": "abc"})
        text = await response.get_data(as_text=True)
        self.assertIn("Invalid project", text)

    async def test_non_integer_role_id_renders_error(self):
        self.mock_rest_client.get.side_effect = _get_side_effect(user=_USER_OK)
        response = await self._post({"project_id": "5", "role_id": "abc"})
        text = await response.get_data(as_text=True)
        self.assertIn("Invalid role", text)

    async def test_success_forwards_project_and_role_to_gateway(self):
        self.mock_rest_client.post.side_effect = [
            _SESSION_VALID, ApiResponse(status_code=HTTPStatus.CREATED)]
        self.mock_rest_client.get.side_effect = _get_side_effect(user=_USER_OK)
        await self._post({"project_id": "5", "role_id": "2"})
        call = self.mock_rest_client.post.call_args_list[1]
        self.assertEqual(call[0][0], "http://gateway/web/users/" + _UUID + "/projects")
        self.assertEqual(call[1]["json_data"], {"project_id": 5, "role_id": 2})

    async def test_no_role_selected_omits_role_id(self):
        self.mock_rest_client.post.side_effect = [
            _SESSION_VALID, ApiResponse(status_code=HTTPStatus.CREATED)]
        self.mock_rest_client.get.side_effect = _get_side_effect(user=_USER_OK)
        await self._post({"project_id": "5"})
        call = self.mock_rest_client.post.call_args_list[1]
        self.assertEqual(call[1]["json_data"], {"project_id": 5})

    async def test_gateway_conflict_shows_error(self):
        self.mock_rest_client.post.side_effect = [
            _SESSION_VALID,
            ApiResponse(status_code=HTTPStatus.CONFLICT,
                       body={"error": "User is already a member of this project"})]
        self.mock_rest_client.get.side_effect = _get_side_effect(user=_USER_OK)
        response = await self._post({"project_id": "5"})
        text = await response.get_data(as_text=True)
        self.assertIn("already a member", text)

    async def test_success_confirms_and_returns_to_projects_tab(self):
        self.mock_rest_client.post.side_effect = [
            _SESSION_VALID, ApiResponse(status_code=HTTPStatus.CREATED)]
        self.mock_rest_client.get.side_effect = _get_side_effect(user=_USER_OK)
        response = await self._post({"project_id": "5"})
        text = await response.get_data(as_text=True)
        self.assertIn("Project access added", text)
        self.assertIn('nav-link active" data-bs-toggle="tab" href="#tab-projects"', text)

    async def test_error_without_body_uses_fallback_message(self):
        self.mock_rest_client.post.side_effect = [
            _SESSION_VALID,
            ApiResponse(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, body={})]
        self.mock_rest_client.get.side_effect = _get_side_effect(user=_USER_OK)
        response = await self._post({"project_id": "5"})
        text = await response.get_data(as_text=True)
        self.assertIn("could not be completed", text)

    async def test_stale_user_fetch_failure_shows_a_notice_not_a_form(self):
        """A failed re-fetch of the user's core fields after a successful
        project write shouldn't fail the whole page, but it must not draw a
        blank form either: that form has both the active and the
        administrator switches off, and saving it would deactivate the user
        and remove their administrator rights. The project write is still
        confirmed, and the Projects tab still works."""
        self.mock_rest_client.post.side_effect = [
            _SESSION_VALID, ApiResponse(status_code=HTTPStatus.CREATED)]
        self.mock_rest_client.get.side_effect = [
            ApiResponse(status_code=HTTPStatus.SERVICE_UNAVAILABLE, body={}),
            _PROJECTS_OK, _MEMBERSHIPS_EMPTY, _ROLES_OK]
        response = await self._post({"project_id": "5"})
        self.assertEqual(response.status_code, 200)
        text = await response.get_data(as_text=True)
        self.assertIn("Project access added", text)
        self.assertIn("details could not be loaded", text)
        self.assertNotIn('id="modifyUserForm"', text)
        self.assertNotIn('id="account_status"', text)
        self.assertNotIn('id="is_administrator"', text)
        self.assertNotIn("Save User", text)
        self.assertIn("Add Project", text)  # the Projects tab still works


class TestModifyUserProject(unittest.IsolatedAsyncioTestCase):
    """POST /admin/users_roles/<id>/projects/<project_id>/modify"""

    async def asyncSetUp(self):
        self.mock_rest_client = AsyncMock()
        self.mock_rest_client.post.return_value = _SESSION_VALID
        handler = AdminModifyUserPageHandler(
            _LOGGER, _config(), self.mock_rest_client, _metadata())

        app = make_app()

        @app.route(
            "/admin/users_roles/<string:user_id>/projects/<int:project_id>/modify",
            methods=["POST"])
        async def route(user_id: str, project_id: int):
            return await handler.modify_user_project(user_id, project_id)

        self.client = app.test_client()

    async def _post(self, form, user_id=_UUID, project_id=5):
        async with self.client as c:
            return await c.post(
                f"/admin/users_roles/{user_id}/projects/{project_id}/modify",
                form=form, headers=_AUTH_HEADERS)

    async def test_success_forwards_role_id_to_gateway(self):
        self.mock_rest_client.patch.return_value = ApiResponse(status_code=HTTPStatus.OK)
        self.mock_rest_client.get.side_effect = _get_side_effect(user=_USER_OK)
        await self._post({"role_id": "3"}, project_id=9)
        self.mock_rest_client.patch.assert_called_once_with(
            "http://gateway/web/users/" + _UUID + "/projects/9",
            json_data={"role_id": 3})

    async def test_unassigned_selection_sends_null_role(self):
        self.mock_rest_client.patch.return_value = ApiResponse(status_code=HTTPStatus.OK)
        self.mock_rest_client.get.side_effect = _get_side_effect(user=_USER_OK)
        await self._post({"role_id": ""})
        self.mock_rest_client.patch.assert_called_once_with(
            "http://gateway/web/users/" + _UUID + "/projects/5",
            json_data={"role_id": None})

    async def test_non_integer_role_id_renders_error_without_calling_gateway(self):
        self.mock_rest_client.get.side_effect = _get_side_effect(user=_USER_OK)
        response = await self._post({"role_id": "abc"})
        text = await response.get_data(as_text=True)
        self.assertIn("Invalid role", text)
        self.mock_rest_client.patch.assert_not_called()

    async def test_not_a_member_shows_error(self):
        self.mock_rest_client.patch.return_value = ApiResponse(
            status_code=HTTPStatus.NOT_FOUND,
            body={"error": "User is not a member of this project"})
        self.mock_rest_client.get.side_effect = _get_side_effect(user=_USER_OK)
        response = await self._post({"role_id": "3"})
        text = await response.get_data(as_text=True)
        self.assertIn("not a member", text)

    async def test_success_confirms_and_returns_to_projects_tab(self):
        self.mock_rest_client.patch.return_value = ApiResponse(status_code=HTTPStatus.OK)
        self.mock_rest_client.get.side_effect = _get_side_effect(user=_USER_OK)
        response = await self._post({"role_id": "3"})
        text = await response.get_data(as_text=True)
        self.assertIn("Role updated", text)
        self.assertIn('nav-link active" data-bs-toggle="tab" href="#tab-projects"', text)


class TestRemoveUserProject(unittest.IsolatedAsyncioTestCase):
    """POST /admin/users_roles/<id>/projects/<project_id>/delete"""

    async def asyncSetUp(self):
        self.mock_rest_client = AsyncMock()
        self.mock_rest_client.post.return_value = _SESSION_VALID
        handler = AdminModifyUserPageHandler(
            _LOGGER, _config(), self.mock_rest_client, _metadata())

        app = make_app()

        @app.route(
            "/admin/users_roles/<string:user_id>/projects/<int:project_id>/delete",
            methods=["POST"])
        async def route(user_id: str, project_id: int):
            return await handler.remove_user_project(user_id, project_id)

        self.client = app.test_client()

    async def _post(self, user_id=_UUID, project_id=5):
        async with self.client as c:
            return await c.post(
                f"/admin/users_roles/{user_id}/projects/{project_id}/delete",
                headers=_AUTH_HEADERS)

    async def test_success_calls_gateway_delete(self):
        self.mock_rest_client.delete.return_value = ApiResponse(status_code=HTTPStatus.OK)
        self.mock_rest_client.get.side_effect = _get_side_effect(user=_USER_OK)
        await self._post(project_id=9)
        self.mock_rest_client.delete.assert_called_once_with(
            "http://gateway/web/users/" + _UUID + "/projects/9")

    async def test_not_a_member_shows_error(self):
        self.mock_rest_client.delete.return_value = ApiResponse(
            status_code=HTTPStatus.NOT_FOUND,
            body={"error": "User is not a member of this project"})
        self.mock_rest_client.get.side_effect = _get_side_effect(user=_USER_OK)
        response = await self._post()
        text = await response.get_data(as_text=True)
        self.assertIn("not a member", text)

    async def test_success_confirms_and_returns_to_projects_tab(self):
        self.mock_rest_client.delete.return_value = ApiResponse(status_code=HTTPStatus.OK)
        self.mock_rest_client.get.side_effect = _get_side_effect(user=_USER_OK)
        response = await self._post()
        text = await response.get_data(as_text=True)
        self.assertIn("Project access removed", text)
        self.assertIn('nav-link active" data-bs-toggle="tab" href="#tab-projects"', text)


# ---------------------------------------------------------------------------
# AdminResetPasswordPageHandler
# ---------------------------------------------------------------------------

class TestAdminResetPasswordPageHandler(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.mock_rest_client = AsyncMock()
        self.mock_rest_client.post.return_value = _SESSION_VALID
        handler = AdminResetPasswordPageHandler(
            _LOGGER, _config(), self.mock_rest_client, _metadata())

        app = make_app()

        @app.route("/admin/users_roles/<string:user_id>/reset_password",
                   methods=["GET"])
        async def get_route(user_id: str):
            return await handler.reset_password_get(user_id)

        @app.route("/admin/users_roles/<string:user_id>/reset_password",
                   methods=["POST"])
        async def post_route(user_id: str):
            return await handler.reset_password_post(user_id)

        self.client = app.test_client()

    async def _get(self, user_id=_UUID):
        async with self.client as c:
            return await c.get(
                f"/admin/users_roles/{user_id}/reset_password",
                headers=_AUTH_HEADERS)

    async def _post(self, form, user_id=_UUID):
        async with self.client as c:
            return await c.post(
                f"/admin/users_roles/{user_id}/reset_password",
                form=form, headers=_AUTH_HEADERS)

    async def test_get_success_shows_user_context(self):
        self.mock_rest_client.get.return_value = ApiResponse(
            status_code=HTTPStatus.OK, body=_USER)
        response = await self._get()
        self.assertEqual(response.status_code, 200)
        text = await response.get_data(as_text=True)
        self.assertIn("Alice Smith", text)
        self.assertIn("alice@localhost", text)

    async def test_get_user_not_found_renders_error(self):
        self.mock_rest_client.get.return_value = ApiResponse(
            status_code=HTTPStatus.NOT_FOUND, body={})
        response = await self._get()
        self.assertEqual(response.status_code, 200)
        text = await response.get_data(as_text=True)
        self.assertIn("not found", text)

    async def test_post_passwords_do_not_match_renders_error(self):
        self.mock_rest_client.get.return_value = ApiResponse(
            status_code=HTTPStatus.OK, body=_USER)
        response = await self._post({
            "new_password": "password1",
            "confirm_password": "password2"})
        self.assertEqual(response.status_code, 200)
        text = await response.get_data(as_text=True)
        self.assertIn("do not match", text)
        self.mock_rest_client.post.assert_called_once()  # only session validate

    async def test_post_password_too_short_renders_error(self):
        self.mock_rest_client.get.return_value = ApiResponse(
            status_code=HTTPStatus.OK, body=_USER)
        response = await self._post({
            "new_password": "short",
            "confirm_password": "short"})
        self.assertEqual(response.status_code, 200)
        text = await response.get_data(as_text=True)
        self.assertIn("8 characters", text)

    async def test_post_not_found_renders_error(self):
        self.mock_rest_client.get.return_value = ApiResponse(
            status_code=HTTPStatus.OK, body=_USER)
        self.mock_rest_client.post.side_effect = [
            _SESSION_VALID,
            ApiResponse(status_code=HTTPStatus.NOT_FOUND, body={}),
        ]
        response = await self._post({
            "new_password": "newpassword1",
            "confirm_password": "newpassword1"})
        self.assertEqual(response.status_code, 200)
        text = await response.get_data(as_text=True)
        self.assertIn("not found", text)

    async def test_post_gateway_error_renders_unexpected_error(self):
        self.mock_rest_client.get.return_value = ApiResponse(
            status_code=HTTPStatus.OK, body=_USER)
        self.mock_rest_client.post.side_effect = [
            _SESSION_VALID,
            ApiResponse(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, body={}),
        ]
        response = await self._post({
            "new_password": "newpassword1",
            "confirm_password": "newpassword1"})
        self.assertEqual(response.status_code, 200)
        text = await response.get_data(as_text=True)
        self.assertIn("unexpected error", text)

    async def test_post_success_redirects(self):
        self.mock_rest_client.get.return_value = ApiResponse(
            status_code=HTTPStatus.OK, body=_USER)
        self.mock_rest_client.post.side_effect = [
            _SESSION_VALID,
            ApiResponse(status_code=HTTPStatus.OK, body={}),
        ]
        response = await self._post({
            "new_password": "newpassword1",
            "confirm_password": "newpassword1"})
        self.assertEqual(response.status_code, 200)
        text = await response.get_data(as_text=True)
        self.assertIn("Refresh", text)

    async def test_redirects_when_not_authenticated(self):
        async with self.client as c:
            response = await c.get(f"/admin/users_roles/{_UUID}/reset_password")
        text = await response.get_data(as_text=True)
        self.assertIn("Refresh", text)


# ---------------------------------------------------------------------------
# The Edit User page itself: tabs, Save, role rows, missing details
# ---------------------------------------------------------------------------

def _tag(text: str, element_id: str) -> str:
    """The whole opening tag with this id, as rendered."""
    match = re.search(rf'<[a-z]+[^>]*id="{element_id}"[^>]*>', text)
    assert match, f"nothing with id {element_id!r} on the page"
    return match.group(0)


class TestEditUserPage(unittest.IsolatedAsyncioTestCase):
    """What the Edit User page offers, and what it refuses to draw."""

    async def asyncSetUp(self):
        self.mock_rest_client = AsyncMock()
        self.mock_rest_client.post.return_value = _SESSION_VALID
        handler = AdminModifyUserPageHandler(
            _LOGGER, _config(), self.mock_rest_client, _metadata())

        app = make_app()

        @app.route("/admin/users_roles/<string:user_id>/modify",
                   methods=["GET"])
        async def get_route(user_id: str):
            return await handler.modify_user_get(user_id)

        @app.route("/admin/users_roles/<string:user_id>/projects",
                   methods=["POST"])
        async def add_route(user_id: str):
            return await handler.add_user_project(user_id)

        @app.route("/admin/users_roles/<string:user_id>/projects/"
                   "<int:project_id>/modify", methods=["POST"])
        async def role_route(user_id: str, project_id: int):
            return await handler.modify_user_project(user_id, project_id)

        @app.route("/admin/users_roles/<string:user_id>/projects/"
                   "<int:project_id>/delete", methods=["POST"])
        async def remove_route(user_id: str, project_id: int):
            return await handler.remove_user_project(user_id, project_id)

        self.client = app.test_client()

    async def _page(self, user=_USER_OK, memberships=_MEMBERSHIPS_OK):
        self.mock_rest_client.get.side_effect = _get_side_effect(
            user=user, memberships=memberships)
        async with self.client as c:
            response = await c.get(f"/admin/users_roles/{_UUID}/modify",
                                   headers=_AUTH_HEADERS)
        self.assertEqual(response.status_code, 200)
        return await response.get_data(as_text=True)

    async def _after(self, method_path, form, post_response, user):
        """The page as it comes back after a project action."""
        self.mock_rest_client.post.side_effect = [
            _SESSION_VALID, post_response]
        self.mock_rest_client.patch.return_value = post_response
        self.mock_rest_client.delete.return_value = post_response
        self.mock_rest_client.get.side_effect = _get_side_effect(
            user=user, memberships=_MEMBERSHIPS_OK)
        async with self.client as c:
            response = await c.post(method_path, form=form,
                                    headers=_AUTH_HEADERS)
        self.assertEqual(response.status_code, 200)
        return await response.get_data(as_text=True)

    # --- Save User and Back to users ------------------------------------

    async def test_the_user_tab_offers_save_and_cancel(self):
        text = await self._page()
        self.assertIn("Save User", text)
        self.assertNotIn("d-none", _tag(text, "user-save-row"))

    async def test_save_is_not_shown_when_the_page_opens_on_projects(self):
        """After a project action the page lands on the Projects tab, where
        Save User would only suggest there is something left to save."""
        text = await self._after(
            f"/admin/users_roles/{_UUID}/projects", {"project_id": "7"},
            ApiResponse(status_code=HTTPStatus.CREATED), _USER_OK)
        self.assertIn("d-none", _tag(text, "user-save-row"))

    async def test_the_projects_tab_has_a_back_to_users_button(self):
        text = await self._page()
        self.assertIn('href="/admin/users_roles"',
                      _tag(text, "back-to-users-btn"))
        self.assertIn("Back to users", text)

    async def test_back_to_users_shares_a_row_with_add_project(self):
        """Not a lone button on a line of its own: nothing closes between
        the two, so they sit in the same row."""
        text = await self._page()
        between = text[text.index('id="add-project-btn"'):
                       text.index('id="back-to-users-btn"')]
        self.assertNotIn("</div>", between)

    async def test_the_every_project_note_stays_when_there_is_nothing_to_add(
            self):
        """With no projects left to add, Add Project is disabled and says
        why; Back to users is still there."""
        self.mock_rest_client.get.side_effect = _get_side_effect(
            user=_USER_OK, memberships=ApiResponse(
                status_code=HTTPStatus.OK, body={"memberships": [
                    {"project_id": 5, "role_id": 2, "role_name": "Tester"},
                    {"project_id": 7, "role_id": 3, "role_name": "Lead"}]}))
        async with self.client as c:
            response = await c.get(f"/admin/users_roles/{_UUID}/modify",
                                   headers=_AUTH_HEADERS)
        text = await response.get_data(as_text=True)
        self.assertIn("Already a member of every project.", text)
        self.assertIn("disabled", _tag(text, "add-project-btn"))
        self.assertIn('href="/admin/users_roles"',
                      _tag(text, "back-to-users-btn"))

    async def test_the_error_is_shown_once_not_twice(self):
        self.mock_rest_client.get.return_value = ApiResponse(
            status_code=HTTPStatus.NOT_FOUND, body={})
        async with self.client as c:
            response = await c.get(f"/admin/users_roles/{_UUID}/modify",
                                   headers=_AUTH_HEADERS)
        text = await response.get_data(as_text=True)
        self.assertEqual(text.count('id="error_msg"'), 1)
        self.assertEqual(text.count("User not found."), 1)

    # --- role rows ---------------------------------------------------------

    async def test_a_role_row_has_a_labelled_save_button(self):
        text = await self._page()
        match = re.search(
            r'<button[^>]*class="[^"]*role-save-btn[^"]*"[^>]*>\s*Save\s*'
            r'</button>', text)
        self.assertTrue(match, "no labelled Save button on the role row")
        self.assertNotIn("bi-check-lg", text)  # no icon-only tick

    async def test_a_role_row_knows_the_saved_role(self):
        """The script enables Save only when the dropdown differs from this."""
        text = await self._page(memberships=_MEMBERSHIPS_OK)
        self.assertIn('data-saved-role="2"', text)

    async def test_a_member_with_no_role_has_an_empty_saved_role(self):
        memberships = ApiResponse(status_code=HTTPStatus.OK, body={
            "memberships": [
                {"project_id": 5, "role_id": None, "role_name": None}]})
        text = await self._page(memberships=memberships)
        self.assertIn('data-saved-role=""', text)

    async def test_the_saved_role_is_the_selected_one(self):
        text = await self._page()
        self.assertRegex(text, r'<option value="2" selected>Tester</option>')

    async def test_the_role_dropdown_is_labelled_for_its_project(self):
        text = await self._page()
        self.assertIn('aria-label="Role on Alpha"', text)

    # --- the User and Access tabs: drawn only from real data ---------------

    async def test_with_the_users_details_the_form_reflects_them(self):
        text = await self._page()
        self.assertIn('id="modifyUserForm"', text)
        self.assertIn('value="Alice Smith"', text)
        self.assertIn("checked", _tag(text, "account_status"))
        self.assertNotIn("checked", _tag(text, "is_administrator"))

    async def test_an_administrator_is_drawn_as_one(self):
        admin = ApiResponse(status_code=HTTPStatus.OK,
                            body={**_USER, "is_administrator": True})
        text = await self._page(user=admin)
        self.assertIn("checked", _tag(text, "is_administrator"))

    async def test_an_unloadable_user_gets_a_notice_not_a_blank_form(self):
        """The dangerous case: a blank form has both switches off, and
        saving it would deactivate the user and remove their administrator
        rights."""
        for status in (HTTPStatus.SERVICE_UNAVAILABLE,
                       HTTPStatus.INTERNAL_SERVER_ERROR,
                       HTTPStatus.NOT_FOUND):
            with self.subTest(status=status):
                self.mock_rest_client.get.side_effect = [
                    ApiResponse(status_code=status, body={}),
                    _PROJECTS_OK, _MEMBERSHIPS_OK, _ROLES_OK]
                async with self.client as c:
                    response = await c.get(
                        f"/admin/users_roles/{_UUID}/modify",
                        headers=_AUTH_HEADERS)
                text = await response.get_data(as_text=True)
                self.assertIn("details could not be loaded", text)
                self.assertNotIn('id="modifyUserForm"', text)
                self.assertNotIn('id="account_status"', text)
                self.assertNotIn('id="is_administrator"', text)
                self.assertNotIn("Save User", text)
                self.assertNotIn('name="full_name"', text)
                self.assertIn(f'href="/admin/users_roles/{_UUID}/modify"',
                              _tag(text, "reload-user-btn"))
                self.assertIn("Back to users", text)

    async def test_the_projects_tab_still_works_without_the_details(self):
        self.mock_rest_client.get.side_effect = [
            ApiResponse(status_code=HTTPStatus.SERVICE_UNAVAILABLE, body={}),
            _PROJECTS_OK, _MEMBERSHIPS_OK, _ROLES_OK]
        async with self.client as c:
            response = await c.get(f"/admin/users_roles/{_UUID}/modify",
                                   headers=_AUTH_HEADERS)
        text = await response.get_data(as_text=True)
        self.assertIn("Alpha", text)           # the membership row
        self.assertIn("role-save-btn", text)
        self.assertIn("Add Project", text)

    async def test_every_project_action_refuses_to_draw_a_blank_form(self):
        """Add, change a role, remove: each re-fetches the user, and if that
        fails each shows the notice (and still confirms what it did)."""
        broken_user = ApiResponse(
            status_code=HTTPStatus.SERVICE_UNAVAILABLE, body={})
        actions = {
            "add": (f"/admin/users_roles/{_UUID}/projects",
                    {"project_id": "7"},
                    ApiResponse(status_code=HTTPStatus.CREATED),
                    "Project access added"),
            "role": (f"/admin/users_roles/{_UUID}/projects/5/modify",
                     {"role_id": "3"},
                     ApiResponse(status_code=HTTPStatus.OK),
                     "Role updated"),
            "remove": (f"/admin/users_roles/{_UUID}/projects/5/delete",
                       {}, ApiResponse(status_code=HTTPStatus.OK),
                       "Project access removed"),
        }
        for label, (path, form, response, confirmation) in actions.items():
            with self.subTest(label):
                text = await self._after(path, form, response, broken_user)
                self.assertIn(confirmation, text)
                self.assertIn("details could not be loaded", text)
                self.assertNotIn('id="modifyUserForm"', text)
                self.assertNotIn('id="account_status"', text)

    async def test_an_odd_reply_when_reloading_the_user_is_also_unavailable(
            self):
        odd = ApiResponse(status_code=HTTPStatus.OK, body=["not", "a", "user"])
        text = await self._after(
            f"/admin/users_roles/{_UUID}/projects", {"project_id": "7"},
            ApiResponse(status_code=HTTPStatus.CREATED), odd)
        self.assertIn("details could not be loaded", text)
        self.assertNotIn('id="modifyUserForm"', text)

    async def test_a_working_reload_still_draws_the_real_form(self):
        text = await self._after(
            f"/admin/users_roles/{_UUID}/projects", {"project_id": "7"},
            ApiResponse(status_code=HTTPStatus.CREATED), _USER_OK)
        self.assertIn('id="modifyUserForm"', text)
        self.assertIn('value="Alice Smith"', text)
        self.assertNotIn("details could not be loaded", text)


if __name__ == "__main__":
    unittest.main()
