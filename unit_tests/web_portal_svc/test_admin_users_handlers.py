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


if __name__ == "__main__":
    unittest.main()
