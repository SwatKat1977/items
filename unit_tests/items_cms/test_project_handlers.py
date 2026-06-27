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
from items.services.items_cms.routes.projects.get_project_handler import (
    GetProjectHandler,
)
from items.services.items_cms.routes.projects.list_projects_handler import (
    ListProjectsHandler,
)
from items.services.items_cms.routes.projects.create_project_handler import (
    CreateProjectHandler,
)
from items.services.items_cms.routes.projects.modify_project_handler import (
    ModifyProjectHandler,
)
from items.services.items_cms.routes.projects.delete_project_handler import (
    DeleteProjectHandler,
)
from items.services.items_cms.services.project_service import (
    ProjectService,
    ProjectResult,
)

_LOGGER = MagicMock()


def _ok(**kwargs):
    return ProjectResult(success=True, **kwargs)


def _internal():
    return ProjectResult(success=False, error_msg="err", is_internal=True)


def _not_found():
    return ProjectResult(success=False, error_msg="not found", not_found=True)


def _bad_request(msg="bad"):
    return ProjectResult(success=False, error_msg=msg)


# ------------------------------------------------------------------
# GetProjectHandler
# ------------------------------------------------------------------

class TestGetProjectHandler(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.mock_service = AsyncMock(spec=ProjectService)
        handler = GetProjectHandler(_LOGGER, self.mock_service)

        app = Quart(__name__)

        @app.route("/projects/<int:project_id>")
        async def get_project(project_id):
            return await handler.get_project(project_id)

        self.client = app.test_client()

    async def test_get_project_success_returns_200(self):
        self.mock_service.get_project.return_value = _ok(
            data={"id": 1, "name": "Alpha"})
        async with self.client as c:
            response = await c.get("/projects/1")
        self.assertEqual(response.status_code, 200)
        data = await response.get_json()
        self.assertEqual(data["name"], "Alpha")

    async def test_get_project_not_found_returns_404(self):
        self.mock_service.get_project.return_value = _not_found()
        async with self.client as c:
            response = await c.get("/projects/99")
        self.assertEqual(response.status_code, 404)

    async def test_get_project_internal_error_returns_500(self):
        self.mock_service.get_project.return_value = _internal()
        async with self.client as c:
            response = await c.get("/projects/1")
        self.assertEqual(response.status_code, 500)


# ------------------------------------------------------------------
# ListProjectsHandler
# ------------------------------------------------------------------

class TestListProjectsHandler(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.mock_service = AsyncMock(spec=ProjectService)
        handler = ListProjectsHandler(_LOGGER, self.mock_service)

        app = Quart(__name__)

        @app.route("/projects")
        async def list_projects():
            return await handler.list_projects()

        self.client = app.test_client()

    async def test_list_projects_default_fields_returns_200(self):
        self.mock_service.list_projects.return_value = _ok(data=[])
        async with self.client as c:
            response = await c.get("/projects")
        self.assertEqual(response.status_code, 200)
        data = await response.get_json()
        self.assertIn("projects", data)
        self.mock_service.list_projects.assert_called_once_with(
            ["name"], False, False)

    async def test_list_projects_valid_value_field_returns_200(self):
        self.mock_service.list_projects.return_value = _ok(
            data=[{"id": 1, "name": "Alpha"}])
        async with self.client as c:
            response = await c.get("/projects?value_fields=name")
        self.assertEqual(response.status_code, 200)
        self.mock_service.list_projects.assert_called_once_with(
            ["name"], False, False)

    async def test_list_projects_invalid_value_field_returns_400(self):
        async with self.client as c:
            response = await c.get("/projects?value_fields=secret")
        self.assertEqual(response.status_code, 400)
        self.mock_service.list_projects.assert_not_called()

    async def test_list_projects_count_milestones_returns_200(self):
        self.mock_service.list_projects.return_value = _ok(data=[])
        async with self.client as c:
            response = await c.get(
                "/projects?count_fields=no_of_milestones")
        self.assertEqual(response.status_code, 200)
        self.mock_service.list_projects.assert_called_once_with(
            ["name"], True, False)

    async def test_list_projects_count_test_runs_returns_200(self):
        self.mock_service.list_projects.return_value = _ok(data=[])
        async with self.client as c:
            response = await c.get(
                "/projects?count_fields=no_of_test_runs")
        self.assertEqual(response.status_code, 200)
        self.mock_service.list_projects.assert_called_once_with(
            ["name"], False, True)

    async def test_list_projects_invalid_count_field_returns_400(self):
        async with self.client as c:
            response = await c.get("/projects?count_fields=no_of_secrets")
        self.assertEqual(response.status_code, 400)
        self.mock_service.list_projects.assert_not_called()

    async def test_list_projects_service_error_returns_500(self):
        self.mock_service.list_projects.return_value = _internal()
        async with self.client as c:
            response = await c.get("/projects")
        self.assertEqual(response.status_code, 500)


# ------------------------------------------------------------------
# CreateProjectHandler
# ------------------------------------------------------------------

class TestCreateProjectHandler(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.mock_service = AsyncMock(spec=ProjectService)
        handler = CreateProjectHandler(_LOGGER, self.mock_service)

        app = Quart(__name__)

        @app.route("/projects", methods=["POST"])
        async def create_project():
            return await handler.create_project()

        self.client = app.test_client()

    async def _post(self, body):
        async with self.client as c:
            return await c.post("/projects", json=body)

    async def test_create_project_success_returns_200(self):
        self.mock_service.create_project.return_value = _ok(data=5)
        response = await self._post(
            {"name": "Alpha", "announcement": "", "announcement_on_overview": False})
        self.assertEqual(response.status_code, 200)
        data = await response.get_json()
        self.assertEqual(data["project_id"], 5)

    async def test_create_project_name_conflict_returns_400(self):
        self.mock_service.create_project.return_value = _bad_request(
            "Project name already exists")
        response = await self._post(
            {"name": "Alpha", "announcement": "", "announcement_on_overview": False})
        self.assertEqual(response.status_code, 400)

    async def test_create_project_missing_field_returns_400(self):
        response = await self._post({"name": "Alpha"})
        self.assertEqual(response.status_code, 400)
        self.mock_service.create_project.assert_not_called()

    async def test_create_project_internal_error_returns_500(self):
        self.mock_service.create_project.return_value = _internal()
        response = await self._post(
            {"name": "Alpha", "announcement": "", "announcement_on_overview": False})
        self.assertEqual(response.status_code, 500)


# ------------------------------------------------------------------
# ModifyProjectHandler
# ------------------------------------------------------------------

class TestModifyProjectHandler(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.mock_service = AsyncMock(spec=ProjectService)
        handler = ModifyProjectHandler(_LOGGER, self.mock_service)

        app = Quart(__name__)

        @app.route("/projects/<int:project_id>", methods=["PATCH"])
        async def modify_project(project_id):
            return await handler.modify_project(project_id)

        self.client = app.test_client()

    async def _patch(self, project_id, body):
        async with self.client as c:
            return await c.patch(f"/projects/{project_id}", json=body)

    _VALID_BODY = {
        "name": "Beta",
        "announcement": "Hello",
        "announcement_on_overview": True,
    }

    async def test_modify_project_success_returns_200(self):
        self.mock_service.modify_project.return_value = _ok()
        response = await self._patch(1, self._VALID_BODY)
        self.assertEqual(response.status_code, 200)
        data = await response.get_json()
        self.assertEqual(data["status"], 1)

    async def test_modify_project_bad_request_returns_400(self):
        self.mock_service.modify_project.return_value = _bad_request(
            "New project name already exists")
        response = await self._patch(1, self._VALID_BODY)
        self.assertEqual(response.status_code, 400)

    async def test_modify_project_not_found_returns_404(self):
        self.mock_service.modify_project.return_value = _not_found()
        response = await self._patch(99, self._VALID_BODY)
        self.assertEqual(response.status_code, 404)

    async def test_modify_project_internal_error_returns_500(self):
        self.mock_service.modify_project.return_value = _internal()
        response = await self._patch(1, self._VALID_BODY)
        self.assertEqual(response.status_code, 500)

    async def test_modify_project_missing_field_returns_400(self):
        response = await self._patch(1, {"name": "Beta"})
        self.assertEqual(response.status_code, 400)
        self.mock_service.modify_project.assert_not_called()


# ------------------------------------------------------------------
# DeleteProjectHandler
# ------------------------------------------------------------------

class TestDeleteProjectHandler(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.mock_service = AsyncMock(spec=ProjectService)
        handler = DeleteProjectHandler(_LOGGER, self.mock_service)

        app = Quart(__name__)

        @app.route("/projects/<int:project_id>", methods=["DELETE"])
        async def delete_project(project_id):
            return await handler.delete_project(project_id)

        self.client = app.test_client()

    async def test_delete_project_no_param_soft_deletes(self):
        self.mock_service.delete_project.return_value = _ok()
        async with self.client as c:
            response = await c.delete("/projects/1")
        self.assertEqual(response.status_code, 200)
        self.mock_service.delete_project.assert_called_once_with(1, False)

    async def test_delete_project_hard_delete_true(self):
        self.mock_service.delete_project.return_value = _ok()
        async with self.client as c:
            response = await c.delete("/projects/1?hard_delete=true")
        self.assertEqual(response.status_code, 200)
        self.mock_service.delete_project.assert_called_once_with(1, True)

    async def test_delete_project_hard_delete_numeric_1(self):
        self.mock_service.delete_project.return_value = _ok()
        async with self.client as c:
            response = await c.delete("/projects/1?hard_delete=1")
        self.assertEqual(response.status_code, 200)
        self.mock_service.delete_project.assert_called_once_with(1, True)

    async def test_delete_project_hard_delete_false(self):
        self.mock_service.delete_project.return_value = _ok()
        async with self.client as c:
            response = await c.delete("/projects/1?hard_delete=false")
        self.assertEqual(response.status_code, 200)
        self.mock_service.delete_project.assert_called_once_with(1, False)

    async def test_delete_project_invalid_param_returns_400(self):
        async with self.client as c:
            response = await c.delete("/projects/1?hard_delete=maybe")
        self.assertEqual(response.status_code, 400)
        self.mock_service.delete_project.assert_not_called()

    async def test_delete_project_not_found_returns_404(self):
        self.mock_service.delete_project.return_value = _not_found()
        async with self.client as c:
            response = await c.delete("/projects/1")
        self.assertEqual(response.status_code, 404)

    async def test_delete_project_internal_error_returns_500(self):
        self.mock_service.delete_project.return_value = _internal()
        async with self.client as c:
            response = await c.delete("/projects/1")
        self.assertEqual(response.status_code, 500)


if __name__ == "__main__":
    unittest.main()
