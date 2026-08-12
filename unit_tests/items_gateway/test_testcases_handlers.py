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
from items.services.items_gateway.routes.web.testcases.get_testcase_handler \
    import GetTestcaseHandler
from items.services.items_gateway.routes.web.testcases.get_testcases_handler \
    import GetTestcasesHandler

_LOGGER = MagicMock()


def _config():
    config = MagicMock()
    config.apis_cms_svc = "http://cms/"
    return config


# ------------------------------------------------------------------
# GetTestcaseHandler
# ------------------------------------------------------------------

class TestGetTestcaseHandler(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.mock_rest_client = AsyncMock()
        handler = GetTestcaseHandler(_LOGGER, _config(), self.mock_rest_client)

        app = Quart(__name__)

        @app.route("/testcases/<int:case_id>", methods=["GET"])
        async def get_testcase(case_id):
            return await handler.get_testcase(case_id)

        self.client = app.test_client()

    async def _get(self, query=""):
        async with self.client as c:
            return await c.get(f"/testcases/1{query}")

    async def test_not_found_returns_404(self):
        self.mock_rest_client.get.return_value = ApiResponse(
            status_code=404, body={"error": "Test case not found"})
        response = await self._get("?project_id=5")
        self.assertEqual(response.status_code, 404)
        data = await response.get_json()
        self.assertEqual(data["error"], "Test case not found")

    async def test_other_error_returns_500(self):
        self.mock_rest_client.get.return_value = ApiResponse(status_code=503)
        response = await self._get("?project_id=5")
        self.assertEqual(response.status_code, 500)

    async def test_success_returns_200(self):
        self.mock_rest_client.get.return_value = ApiResponse(
            status_code=200, body={"id": 1, "name": "Login test"})
        response = await self._get("?project_id=5")
        self.assertEqual(response.status_code, 200)
        data = await response.get_json()
        self.assertEqual(data["name"], "Login test")

    async def test_forwards_project_id_to_cms(self):
        self.mock_rest_client.get.return_value = ApiResponse(
            status_code=200, body={"id": 1})
        await self._get("?project_id=5")
        called_url = self.mock_rest_client.get.await_args.args[0]
        self.assertIn("project_id=5", called_url)

    async def test_missing_project_id_returns_400_without_calling_cms(self):
        response = await self._get()
        self.assertEqual(response.status_code, 400)
        self.mock_rest_client.get.assert_not_called()

    async def test_non_integer_project_id_returns_400_without_calling_cms(self):
        response = await self._get("?project_id=abc")
        self.assertEqual(response.status_code, 400)
        self.mock_rest_client.get.assert_not_called()


# ------------------------------------------------------------------
# GetTestcasesHandler
# ------------------------------------------------------------------

class TestGetTestcasesHandler(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.mock_rest_client = AsyncMock()
        handler = GetTestcasesHandler(_LOGGER, _config(), self.mock_rest_client)

        app = Quart(__name__)

        @app.route("/<int:project_id>/testcases", methods=["GET"])
        async def get_testcases(project_id):
            return await handler.get_testcases(project_id)

        self.client = app.test_client()

    async def _get(self, project_id=1):
        async with self.client as c:
            return await c.get(f"/{project_id}/testcases")

    async def test_not_found_returns_404(self):
        self.mock_rest_client.get.return_value = ApiResponse(
            status_code=404, body={"error": "Project id is invalid"})
        response = await self._get(999)
        self.assertEqual(response.status_code, 404)
        data = await response.get_json()
        self.assertEqual(data["error"], "Project id is invalid")

    async def test_other_error_returns_500(self):
        self.mock_rest_client.get.return_value = ApiResponse(status_code=503)
        response = await self._get()
        self.assertEqual(response.status_code, 500)

    async def test_success_returns_200(self):
        self.mock_rest_client.get.return_value = ApiResponse(
            status_code=200, body={"folders": [], "test_cases": []})
        response = await self._get()
        self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
    unittest.main()
