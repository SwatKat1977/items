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
from items.services.items_web_portal.page_handlers.admin.projects.\
    admin_projects_page_handlers import AdminProjectsPageHandlers
from items.services.items_web_portal.page_handlers.admin.projects.\
    admin_add_project_page_handlers import AdminAddProjectPageHandlers
from items.services.items_web_portal.page_handlers.admin.projects.\
    admin_modify_project_page_handlers import AdminModifyProjectPageHandlers

_LOGGER = MagicMock()

_VALID_ADD_FORM = {"project_name": "Project X", "announcement": ""}
_AUTH_HEADERS = {"Cookie": "items_token=abc; items_user=bob"}
_SESSION_VALID = ApiResponse(status_code=HTTPStatus.OK, body={"status": "VALID"})


def _config():
    config = MagicMock()
    config.apis_gateway_svc = "http://gateway/"
    return config


def _metadata():
    metadata = MagicMock()
    metadata.instance_name = "INSTANCE"
    return metadata


# ------------------------------------------------------------------
# AdminProjectsPageHandlers
# ------------------------------------------------------------------
# projects_read/projects_post use .get()/.delete() for their own logic, so
# session validation (.post()) never collides with them - a single blanket
# post.return_value covers every test in this class.

class TestAdminProjectsPageHandlers(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.mock_rest_client = AsyncMock()
        self.mock_rest_client.post.return_value = _SESSION_VALID
        handler = AdminProjectsPageHandlers(
            _LOGGER, _config(), self.mock_rest_client, _metadata())

        app = make_app()

        @app.route("/admin/projects", methods=["GET"])
        async def get_route():
            return await handler.projects_read()

        @app.route("/admin/projects", methods=["POST"])
        async def post_route():
            return await handler.projects_post()

        self.client = app.test_client()

    async def _get(self):
        async with self.client as c:
            return await c.get("/admin/projects", headers=_AUTH_HEADERS)

    async def _post(self, form):
        async with self.client as c:
            return await c.post("/admin/projects", form=form,
                               headers=_AUTH_HEADERS)

    async def test_read_success(self):
        self.mock_rest_client.get.return_value = ApiResponse(
            status_code=HTTPStatus.OK, body={"projects": [{"id": 1}]})
        response = await self._get()
        self.assertEqual(response.status_code, 200)

    async def test_read_failure_renders_internal_error(self):
        self.mock_rest_client.get.return_value = ApiResponse(status_code=503)
        response = await self._get()
        self.assertEqual(response.status_code, 200)

    async def test_post_delete_success_renders_list(self):
        self.mock_rest_client.delete.return_value = ApiResponse(
            status_code=HTTPStatus.OK)
        self.mock_rest_client.get.return_value = ApiResponse(
            status_code=HTTPStatus.OK, body={"projects": []})
        response = await self._post({"projectId": "1"})
        self.assertEqual(response.status_code, 200)
        self.mock_rest_client.get.assert_called_once()

    async def test_post_delete_failure_renders_internal_error(self):
        self.mock_rest_client.delete.return_value = ApiResponse(status_code=503)
        response = await self._post({"projectId": "1"})
        self.assertEqual(response.status_code, 200)
        self.mock_rest_client.get.assert_not_called()


# ------------------------------------------------------------------
# AdminAddProjectPageHandlers
# ------------------------------------------------------------------
# add_project_get/add_project_post both go through @require_session (which
# itself calls .post() to validate the session) AND add_project_post makes
# its own .post() call to submit to CMS - so the session-validation call and
# the CMS call share the same mocked method. side_effect lists the session
# validation response first, then whatever the test wants the CMS call to
# return.

class TestAdminAddProjectPageHandlers(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.mock_rest_client = AsyncMock()
        handler = AdminAddProjectPageHandlers(
            _LOGGER, _config(), self.mock_rest_client, _metadata())

        app = make_app()

        @app.route("/admin/add_project", methods=["GET"])
        async def get_route():
            return await handler.add_project_get()

        @app.route("/admin/add_project", methods=["POST"])
        async def post_route():
            return await handler.add_project_post()

        self.client = app.test_client()

    async def _get(self):
        async with self.client as c:
            return await c.get("/admin/add_project", headers=_AUTH_HEADERS)

    async def _post(self, form):
        async with self.client as c:
            return await c.post("/admin/add_project", form=form,
                               headers=_AUTH_HEADERS)

    async def test_get_renders_blank_form(self):
        self.mock_rest_client.post.return_value = _SESSION_VALID
        response = await self._get()
        self.assertEqual(response.status_code, 200)

    async def test_post_missing_project_name_renders_error(self):
        self.mock_rest_client.post.return_value = _SESSION_VALID
        response = await self._post({"announcement": ""})
        self.assertEqual(response.status_code, 200)
        text = await response.get_data(as_text=True)
        self.assertIn("required", text)
        # Only the session-validation call happened - never reached CMS.
        self.mock_rest_client.post.assert_called_once()

    async def test_post_missing_announcement_renders_error(self):
        self.mock_rest_client.post.return_value = _SESSION_VALID
        response = await self._post({"project_name": "X"})
        self.assertEqual(response.status_code, 200)
        self.mock_rest_client.post.assert_called_once()

    async def test_post_gateway_error_status_renders_internal_error(self):
        self.mock_rest_client.post.side_effect = [
            _SESSION_VALID,
            ApiResponse(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, body={}),
        ]
        response = await self._post(_VALID_ADD_FORM)
        self.assertEqual(response.status_code, 200)
        text = await response.get_data(as_text=True)
        self.assertIn("Internal server error", text)

    async def test_post_not_found_renders_internal_error(self):
        self.mock_rest_client.post.side_effect = [
            _SESSION_VALID,
            ApiResponse(status_code=HTTPStatus.NOT_FOUND, body={}),
        ]
        response = await self._post(_VALID_ADD_FORM)
        self.assertEqual(response.status_code, 200)

    async def test_post_bad_request_with_status_uses_body_error(self):
        self.mock_rest_client.post.side_effect = [
            _SESSION_VALID,
            ApiResponse(status_code=HTTPStatus.BAD_REQUEST,
                       body={"status": 0, "error": "duplicate name"}),
        ]
        response = await self._post(_VALID_ADD_FORM)
        self.assertEqual(response.status_code, 200)
        text = await response.get_data(as_text=True)
        self.assertIn("duplicate name", text)

    async def test_post_bad_request_without_status_uses_fallback(self):
        self.mock_rest_client.post.side_effect = [
            _SESSION_VALID,
            ApiResponse(status_code=HTTPStatus.BAD_REQUEST, body={}),
        ]
        response = await self._post(_VALID_ADD_FORM)
        self.assertEqual(response.status_code, 200)
        text = await response.get_data(as_text=True)
        self.assertIn("Internal ITEMS error", text)

    async def test_post_success_redirects(self):
        self.mock_rest_client.post.side_effect = [
            _SESSION_VALID,
            ApiResponse(status_code=HTTPStatus.OK, body={"status": 1}),
        ]
        response = await self._post(_VALID_ADD_FORM)
        self.assertEqual(response.status_code, 200)
        text = await response.get_data(as_text=True)
        self.assertIn("Refresh", text)


# ------------------------------------------------------------------
# AdminModifyProjectPageHandlers
# ------------------------------------------------------------------
# Both modify_project_get and modify_project_post are wrapped in
# @require_session, which validates the session via .post() - separate from
# .get()/.patch() used by the handlers' own logic, so no side_effect
# ordering is needed, just a blanket post.return_value plus auth cookies.

class TestAdminModifyProjectPageHandlers(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.mock_rest_client = AsyncMock()
        self.mock_rest_client.post.return_value = _SESSION_VALID
        handler = AdminModifyProjectPageHandlers(
            _LOGGER, _config(), self.mock_rest_client, _metadata())

        app = make_app()

        @app.route("/admin/<project_id>/modify_project", methods=["GET"])
        async def get_route(project_id):
            return await handler.modify_project_get(project_id)

        @app.route("/admin/<project_id>/modify_project", methods=["POST"])
        async def post_route(project_id):
            return await handler.modify_project_post(project_id)

        self.client = app.test_client()

    async def _get(self):
        async with self.client as c:
            return await c.get("/admin/1/modify_project", headers=_AUTH_HEADERS)

    async def _post(self, form):
        async with self.client as c:
            return await c.post("/admin/1/modify_project", form=form,
                               headers=_AUTH_HEADERS)

    async def test_get_failure_redirects(self):
        self.mock_rest_client.get.return_value = ApiResponse(status_code=503)
        response = await self._get()
        self.assertEqual(response.status_code, 200)
        text = await response.get_data(as_text=True)
        self.assertIn("Refresh", text)

    async def test_get_success_renders_form(self):
        self.mock_rest_client.get.return_value = ApiResponse(
            status_code=HTTPStatus.OK,
            body={"name": "Project X", "announcement": "hello  ",
                 "show_announcement_on_overview": True})
        response = await self._get()
        self.assertEqual(response.status_code, 200)
        text = await response.get_data(as_text=True)
        self.assertIn("Project X", text)

    async def test_post_failure_with_error_renders_form_with_message(self):
        self.mock_rest_client.patch.return_value = ApiResponse(
            status_code=HTTPStatus.BAD_REQUEST, body={"error": "bad name"})
        response = await self._post(_VALID_ADD_FORM)
        self.assertEqual(response.status_code, 200)
        text = await response.get_data(as_text=True)
        self.assertIn("Internal error modifying project", text)

    async def test_post_failure_without_error_key(self):
        self.mock_rest_client.patch.return_value = ApiResponse(
            status_code=HTTPStatus.BAD_REQUEST, body={})
        response = await self._post(_VALID_ADD_FORM)
        self.assertEqual(response.status_code, 200)

    async def test_post_success_redirects(self):
        self.mock_rest_client.patch.return_value = ApiResponse(
            status_code=HTTPStatus.OK)
        response = await self._post(_VALID_ADD_FORM)
        self.assertEqual(response.status_code, 200)
        text = await response.get_data(as_text=True)
        self.assertIn("Refresh", text)


if __name__ == "__main__":
    unittest.main()
