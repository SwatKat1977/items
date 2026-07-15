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
from quart import Quart
from weaver_framework.microservice.api_response import ApiResponse
from items.services.items_gateway.routes.web.projects.add_project_handler \
    import AddProjectHandler
from items.services.items_gateway.routes.web.projects.delete_project_handler \
    import DeleteProjectHandler
from items.services.items_gateway.routes.web.projects.get_all_projects_handler \
    import GetAllProjectsHandler
from items.services.items_gateway.routes.web.projects.get_project_handler \
    import GetProjectHandler
from items.services.items_gateway.routes.web.projects.update_project_handler \
    import UpdateProjectHandler

_LOGGER = MagicMock()

_VALID_PROJECT_BODY = {
    "name": "Project X",
    "announcement": "",
    "announcement_on_overview": False,
}


def _config():
    config = MagicMock()
    config.apis_cms_svc = "http://cms/"
    return config


# ------------------------------------------------------------------
# AddProjectHandler
# ------------------------------------------------------------------

class TestAddProjectHandler(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.mock_rest_client = AsyncMock()
        handler = AddProjectHandler(_LOGGER, _config(), self.mock_rest_client)

        app = Quart(__name__)

        @app.route("/projects", methods=["POST"])
        async def add_project():
            return await handler.add_project()

        self.client = app.test_client()

    async def _post(self, body):
        async with self.client as c:
            return await c.post("/projects", json=body)

    async def test_missing_field_returns_400(self):
        response = await self._post({"name": "X"})
        self.assertEqual(response.status_code, 400)
        self.mock_rest_client.post.assert_not_called()

    async def test_connection_failure_returns_500(self):
        self.mock_rest_client.post.return_value = ApiResponse(
            status_code=None, exception_msg="boom")
        response = await self._post(_VALID_PROJECT_BODY)
        self.assertEqual(response.status_code, 500)

    async def test_cms_bad_request_returns_400(self):
        self.mock_rest_client.post.return_value = ApiResponse(
            status_code=400, body={"error": "duplicate name"})
        response = await self._post(_VALID_PROJECT_BODY)
        self.assertEqual(response.status_code, 400)
        data = await response.get_json()
        self.assertEqual(data["error"], "duplicate name")

    async def test_cms_other_error_returns_500(self):
        self.mock_rest_client.post.return_value = ApiResponse(status_code=503)
        response = await self._post(_VALID_PROJECT_BODY)
        self.assertEqual(response.status_code, 500)

    async def test_success_returns_200(self):
        self.mock_rest_client.post.return_value = ApiResponse(status_code=200)
        response = await self._post(_VALID_PROJECT_BODY)
        self.assertEqual(response.status_code, 200)
        data = await response.get_json()
        self.assertEqual(data["status"], 1)


# ------------------------------------------------------------------
# DeleteProjectHandler
# ------------------------------------------------------------------

class TestDeleteProjectHandler(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.mock_rest_client = AsyncMock()
        handler = DeleteProjectHandler(_LOGGER, _config(), self.mock_rest_client)

        app = Quart(__name__)

        @app.route("/projects/<int:project_id>", methods=["DELETE"])
        async def delete_project(project_id):
            return await handler.delete_project(project_id)

        self.client = app.test_client()

    async def _delete(self, qs=""):
        async with self.client as c:
            return await c.delete(f"/projects/1{qs}")

    async def test_default_soft_delete(self):
        self.mock_rest_client.delete.return_value = ApiResponse(
            status_code=200, body={})
        response = await self._delete()
        self.assertEqual(response.status_code, 200)
        called_url = self.mock_rest_client.delete.call_args[0][0]
        self.assertIn("hard_delete=false", called_url)

    async def test_invalid_hard_delete_value_returns_500(self):
        response = await self._delete("?hard_delete=maybe")
        self.assertEqual(response.status_code, 500)
        self.mock_rest_client.delete.assert_not_called()

    async def test_hard_delete_true(self):
        self.mock_rest_client.delete.return_value = ApiResponse(
            status_code=200, body={})
        response = await self._delete("?hard_delete=true")
        self.assertEqual(response.status_code, 200)
        called_url = self.mock_rest_client.delete.call_args[0][0]
        self.assertIn("hard_delete=True", called_url)

    async def test_not_found_propagates_404(self):
        self.mock_rest_client.delete.return_value = ApiResponse(
            status_code=404, body={"error": "no such project"})
        response = await self._delete()
        self.assertEqual(response.status_code, 404)

    async def test_other_error_returns_500(self):
        self.mock_rest_client.delete.return_value = ApiResponse(status_code=503)
        response = await self._delete()
        self.assertEqual(response.status_code, 500)

    async def test_success_returns_200(self):
        self.mock_rest_client.delete.return_value = ApiResponse(
            status_code=200, body={"status": 1})
        response = await self._delete()
        self.assertEqual(response.status_code, 200)


# ------------------------------------------------------------------
# GetAllProjectsHandler
# ------------------------------------------------------------------

class TestGetAllProjectsHandler(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.mock_rest_client = AsyncMock()
        handler = GetAllProjectsHandler(_LOGGER, _config(), self.mock_rest_client)

        app = Quart(__name__)

        @app.route("/projects", methods=["GET"])
        async def list_projects():
            return await handler.list_all_projects()

        self.client = app.test_client()

    async def _get(self, qs=""):
        async with self.client as c:
            return await c.get(f"/projects{qs}")

    async def test_no_query_params(self):
        self.mock_rest_client.get.return_value = ApiResponse(
            status_code=200, body={"projects": []})
        response = await self._get()
        self.assertEqual(response.status_code, 200)

    async def test_value_fields_only(self):
        self.mock_rest_client.get.return_value = ApiResponse(
            status_code=200, body={})
        response = await self._get("?value_fields=name")
        self.assertEqual(response.status_code, 200)
        called_url = self.mock_rest_client.get.call_args[0][0]
        self.assertIn("value_fields=name", called_url)

    async def test_count_fields_only(self):
        self.mock_rest_client.get.return_value = ApiResponse(
            status_code=200, body={})
        response = await self._get("?count_fields=testcases")
        self.assertEqual(response.status_code, 200)
        called_url = self.mock_rest_client.get.call_args[0][0]
        self.assertIn("count_fields=testcases", called_url)

    async def test_both_value_and_count_fields(self):
        self.mock_rest_client.get.return_value = ApiResponse(
            status_code=200, body={})
        response = await self._get("?value_fields=name&count_fields=testcases")
        self.assertEqual(response.status_code, 200)
        called_url = self.mock_rest_client.get.call_args[0][0]
        self.assertIn("value_fields=name&count_fields=testcases", called_url)

    async def test_bad_request_returns_400(self):
        self.mock_rest_client.get.return_value = ApiResponse(
            status_code=400, body={"error": "bad field"})
        response = await self._get()
        self.assertEqual(response.status_code, 400)

    async def test_other_error_returns_500(self):
        self.mock_rest_client.get.return_value = ApiResponse(status_code=503)
        response = await self._get()
        self.assertEqual(response.status_code, 500)


# ------------------------------------------------------------------
# GetProjectHandler
# ------------------------------------------------------------------

class TestGetProjectHandler(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.mock_rest_client = AsyncMock()
        handler = GetProjectHandler(_LOGGER, _config(), self.mock_rest_client)

        app = Quart(__name__)

        @app.route("/projects/<int:project_id>", methods=["GET"])
        async def get_project(project_id):
            return await handler.get_project(project_id)

        self.client = app.test_client()

    async def _get(self):
        async with self.client as c:
            return await c.get("/projects/1")

    async def test_not_found_returns_404(self):
        self.mock_rest_client.get.return_value = ApiResponse(status_code=404)
        response = await self._get()
        self.assertEqual(response.status_code, 404)

    async def test_internal_server_error_returns_500(self):
        self.mock_rest_client.get.return_value = ApiResponse(
            status_code=500, body={"error": "db error"})
        response = await self._get()
        self.assertEqual(response.status_code, 500)

    async def test_other_error_returns_500(self):
        self.mock_rest_client.get.return_value = ApiResponse(status_code=503)
        response = await self._get()
        self.assertEqual(response.status_code, 500)

    async def test_success_returns_200(self):
        self.mock_rest_client.get.return_value = ApiResponse(
            status_code=200, body={"id": 1})
        response = await self._get()
        self.assertEqual(response.status_code, 200)


# ------------------------------------------------------------------
# UpdateProjectHandler
# ------------------------------------------------------------------

class TestUpdateProjectHandler(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.mock_rest_client = AsyncMock()
        handler = UpdateProjectHandler(_LOGGER, _config(), self.mock_rest_client)

        app = Quart(__name__)

        @app.route("/projects/<int:project_id>", methods=["PATCH"])
        async def update_project(project_id):
            return await handler.update_project(project_id)

        self.client = app.test_client()

    async def _patch(self, body):
        async with self.client as c:
            return await c.patch("/projects/1", json=body)

    async def test_missing_field_returns_400(self):
        response = await self._patch({"name": "X"})
        self.assertEqual(response.status_code, 400)
        self.mock_rest_client.patch.assert_not_called()

    async def test_not_found_returns_404(self):
        self.mock_rest_client.patch.return_value = ApiResponse(status_code=404)
        response = await self._patch(_VALID_PROJECT_BODY)
        self.assertEqual(response.status_code, 404)

    async def test_bad_request_returns_400(self):
        self.mock_rest_client.patch.return_value = ApiResponse(
            status_code=400, body={"error": "duplicate name"})
        response = await self._patch(_VALID_PROJECT_BODY)
        self.assertEqual(response.status_code, 400)

    async def test_internal_server_error_returns_500(self):
        self.mock_rest_client.patch.return_value = ApiResponse(
            status_code=500, exception_msg="db error")
        response = await self._patch(_VALID_PROJECT_BODY)
        self.assertEqual(response.status_code, 500)

    async def test_unexpected_status_returns_500(self):
        self.mock_rest_client.patch.return_value = ApiResponse(status_code=503)
        response = await self._patch(_VALID_PROJECT_BODY)
        self.assertEqual(response.status_code, 500)
        data = await response.get_json()
        self.assertEqual(data["status"], 0)

    async def test_success_returns_200(self):
        self.mock_rest_client.patch.return_value = ApiResponse(status_code=200)
        response = await self._patch(_VALID_PROJECT_BODY)
        self.assertEqual(response.status_code, 200)
        data = await response.get_json()
        self.assertEqual(data["status"], 1)


if __name__ == "__main__":
    unittest.main()
