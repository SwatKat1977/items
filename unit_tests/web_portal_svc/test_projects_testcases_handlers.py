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
from items.services.items_web_portal.page_handlers.projects.\
    get_project_overview_page_handler import GetProjectOverviewPageHandler
from items.services.items_web_portal.page_handlers.testcases.\
    get_project_testcases_page_handler import GetProjectTestcasesPageHandler

_LOGGER = MagicMock()
_AUTH_HEADERS = {"Cookie": "items_token=abc; items_user=bob"}
_PROJECT_OK = ApiResponse(status_code=HTTPStatus.OK, body={"name": "Proj"})
_CASE_TYPES_OK = ApiResponse(status_code=HTTPStatus.OK, body=[
    {"id": 9, "name": "Smoke", "description": "", "is_default": False},
    {"id": 15, "name": "Other", "description": "", "is_default": True},
])


def _config():
    config = MagicMock()
    config.apis_gateway_svc = "http://gateway/"
    return config


def _metadata():
    metadata = MagicMock()
    metadata.instance_name = "INSTANCE"
    return metadata


# ------------------------------------------------------------------
# GetProjectOverviewPageHandler
# ------------------------------------------------------------------

class TestGetProjectOverviewPageHandler(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.mock_rest_client = AsyncMock()
        self.mock_rest_client.post.return_value = ApiResponse(
            status_code=HTTPStatus.OK, body={"status": "VALID"})
        handler = GetProjectOverviewPageHandler(
            _LOGGER, _config(), self.mock_rest_client, _metadata())

        app = make_app()

        @app.route("/<int:project_id>/overview", methods=["GET"])
        async def route(project_id):
            return await handler.project_overview(project_id)

        self.client = app.test_client()

    async def _get(self):
        async with self.client as c:
            return await c.get("/1/overview", headers=_AUTH_HEADERS)

    async def test_no_session_redirects_to_login(self):
        self.mock_rest_client.post.return_value = ApiResponse(
            status_code=HTTPStatus.OK, body={"status": "INVALID"})
        response = await self._get()
        self.assertEqual(response.status_code, 200)
        text = await response.get_data(as_text=True)
        self.assertIn("login", text)

    async def test_not_found_redirects_to_dashboard(self):
        self.mock_rest_client.get.return_value = ApiResponse(status_code=404)
        response = await self._get()
        self.assertEqual(response.status_code, 200)
        text = await response.get_data(as_text=True)
        self.assertIn("Refresh", text)

    async def test_forbidden_redirects_to_dashboard(self):
        """Not a member of this project any more - same treatment as 404,
        not an error worth showing."""
        self.mock_rest_client.get.return_value = ApiResponse(status_code=403)
        response = await self._get()
        self.assertEqual(response.status_code, 200)
        text = await response.get_data(as_text=True)
        self.assertIn("Refresh", text)

    async def test_other_error_returns_500(self):
        self.mock_rest_client.get.return_value = ApiResponse(status_code=503)
        response = await self._get()
        self.assertEqual(response.status_code, 500)

    async def test_success_renders_page(self):
        self.mock_rest_client.get.return_value = ApiResponse(
            status_code=HTTPStatus.OK,
            body={"name": "Project X", "announcement": "hi",
                 "show_announcement_on_overview": True})
        response = await self._get()
        self.assertEqual(response.status_code, 200)
        text = await response.get_data(as_text=True)
        self.assertIn("Project X", text)

    async def test_success_defaults_when_fields_missing(self):
        self.mock_rest_client.get.return_value = ApiResponse(
            status_code=HTTPStatus.OK, body={})
        response = await self._get()
        self.assertEqual(response.status_code, 200)
        text = await response.get_data(as_text=True)
        self.assertIn("Unknown Project", text)


# ------------------------------------------------------------------
# GetProjectTestcasesPageHandler
# ------------------------------------------------------------------

class TestGetProjectTestcasesPageHandler(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.mock_rest_client = AsyncMock()
        self.mock_rest_client.post.return_value = ApiResponse(
            status_code=HTTPStatus.OK, body={"status": "VALID"})
        handler = GetProjectTestcasesPageHandler(
            _LOGGER, _config(), self.mock_rest_client, _metadata())

        app = make_app()

        @app.route("/<project_id>/testcases", methods=["GET"])
        async def route(project_id):
            return await handler.test_cases(project_id)

        self.client = app.test_client()

    async def _get(self):
        async with self.client as c:
            return await c.get("/1/testcases", headers=_AUTH_HEADERS)

    async def test_testcases_fetch_failure_returns_500(self):
        self.mock_rest_client.get.side_effect = [
            ApiResponse(status_code=HTTPStatus.OK, body={"name": "Proj"}),
            ApiResponse(status_code=503),
        ]
        response = await self._get()
        self.assertEqual(response.status_code, 500)

    async def test_not_found_redirects_to_dashboard(self):
        self.mock_rest_client.get.side_effect = [
            ApiResponse(status_code=HTTPStatus.OK, body={"name": "Proj"}),
            ApiResponse(status_code=404),
        ]
        response = await self._get()
        self.assertEqual(response.status_code, 200)
        text = await response.get_data(as_text=True)
        self.assertIn("Refresh", text)

    async def test_forbidden_redirects_to_dashboard(self):
        """Not a member of this project any more - same treatment as 404,
        not an error worth showing."""
        self.mock_rest_client.get.side_effect = [
            ApiResponse(status_code=HTTPStatus.OK, body={"name": "Proj"}),
            ApiResponse(status_code=403),
        ]
        response = await self._get()
        self.assertEqual(response.status_code, 200)
        text = await response.get_data(as_text=True)
        self.assertIn("Refresh", text)

    async def test_project_name_lookup_failure_falls_back_to_unknown(self):
        self.mock_rest_client.get.side_effect = [
            ApiResponse(status_code=503),
            ApiResponse(status_code=HTTPStatus.OK,
                       body={"folders": [], "test_cases": []}),
            _CASE_TYPES_OK,
        ]
        response = await self._get()
        self.assertEqual(response.status_code, 200)
        text = await response.get_data(as_text=True)
        self.assertIn("Unknown Project", text)

    async def test_success_builds_folder_tree(self):
        self.mock_rest_client.get.side_effect = [
            ApiResponse(status_code=HTTPStatus.OK, body={"name": "Proj"}),
            ApiResponse(status_code=HTTPStatus.OK, body={
                "folders": [
                    {"id": 1, "parent_id": None, "name": "Root"},
                    {"id": 2, "parent_id": 1, "name": "Child"},
                    {"id": 3, "parent_id": 999, "name": "OrphanParentMissing"},
                ],
                "test_cases": [
                    {"id": 10, "folder_id": 1, "case_type_id": 9,
                     "name": "TC-1"},
                    {"id": 11, "folder_id": 999, "case_type_id": 9,
                     "name": "OrphanTestcase"},
                ]
            }),
            _CASE_TYPES_OK,
        ]
        response = await self._get()
        self.assertEqual(response.status_code, 200)
        text = await response.get_data(as_text=True)
        self.assertIn("Proj", text)

    async def test_no_testcases_sets_has_testcases_false(self):
        self.mock_rest_client.get.side_effect = [
            ApiResponse(status_code=HTTPStatus.OK, body={"name": "Proj"}),
            ApiResponse(status_code=HTTPStatus.OK,
                       body={"folders": [], "test_cases": []}),
            _CASE_TYPES_OK,
        ]
        response = await self._get()
        self.assertEqual(response.status_code, 200)

    # ------------------------------------------------------------------
    # Root-level test cases (no folder) and the Type column
    # ------------------------------------------------------------------

    def _page_with(self, folders, test_cases, case_types=_CASE_TYPES_OK):
        self.mock_rest_client.get.side_effect = [
            _PROJECT_OK,
            ApiResponse(status_code=HTTPStatus.OK, body={
                "folders": folders, "test_cases": test_cases}),
            case_types,
        ]

    async def _page_text(self):
        response = await self._get()
        self.assertEqual(response.status_code, 200)
        return await response.get_data(as_text=True)

    async def test_empty_project_shows_the_no_test_cases_message(self):
        self._page_with([], [])
        text = await self._page_text()
        self.assertIn("There aren't any test cases, yet.", text)
        self.assertNotIn('id="folder-structure"', text)

    async def test_empty_message_has_no_dead_buttons(self):
        self._page_with([], [])
        text = await self._page_text()
        self.assertNotIn("addSectionModal", text)
        self.assertNotIn("addTestCaseModal", text)
        self.assertNotIn("Add Section", text)

    async def test_root_level_test_case_is_shown_without_any_folder(self):
        """A test case with no folder used to be dropped, and with no
        folders the page claimed there were no test cases at all."""
        self._page_with([], [
            {"id": 3, "folder_id": None, "case_type_id": 15,
             "name": "Login with wonky nonkey"}])
        text = await self._page_text()
        self.assertIn("Login with wonky nonkey", text)
        self.assertIn('id="folder-structure"', text)
        self.assertNotIn("There aren't any test cases, yet.", text)

    async def test_root_and_folder_test_cases_are_both_shown(self):
        self._page_with(
            [{"id": 1, "parent_id": None, "name": "AlphaFolder"}],
            [{"id": 3, "folder_id": None, "case_type_id": 15,
              "name": "RootCase"},
             {"id": 4, "folder_id": 1, "case_type_id": 9,
              "name": "FolderCase"}])
        text = await self._page_text()
        self.assertIn("RootCase", text)
        self.assertIn("FolderCase", text)
        self.assertIn("AlphaFolder", text)

    async def test_root_test_cases_come_before_the_folders(self):
        self._page_with(
            [{"id": 1, "parent_id": None, "name": "AlphaFolder"}],
            [{"id": 3, "folder_id": None, "case_type_id": 15,
              "name": "RootCase"}])
        text = await self._page_text()
        self.assertLess(text.index("RootCase"), text.index("AlphaFolder"))

    async def test_folder_with_no_test_cases_is_shown_not_the_empty_message(
            self):
        self._page_with(
            [{"id": 1, "parent_id": None, "name": "AlphaFolder"}], [])
        text = await self._page_text()
        self.assertIn("AlphaFolder", text)
        self.assertNotIn("There aren't any test cases, yet.", text)

    async def test_type_column_shows_the_case_type_name(self):
        self._page_with([], [
            {"id": 3, "folder_id": None, "case_type_id": 15, "name": "A"},
            {"id": 4, "folder_id": None, "case_type_id": 9, "name": "B"}])
        text = await self._page_text()
        self.assertIn("<th>Type</th>", text)
        self.assertIn("<td>Other</td>", text)
        self.assertIn("<td>Smoke</td>", text)

    async def test_case_types_are_fetched_from_the_gateway(self):
        self._page_with([], [])
        await self._page_text()
        self.mock_rest_client.get.assert_any_call(
            "http://gateway/web/case_types")

    async def test_unknown_case_type_id_shows_the_placeholder(self):
        self._page_with([], [
            {"id": 3, "folder_id": None, "case_type_id": 777, "name": "A"}])
        text = await self._page_text()
        self.assertIn("<td>Unknown</td>", text)

    async def test_case_types_failure_still_renders_with_placeholder(self):
        self._page_with(
            [], [{"id": 3, "folder_id": None, "case_type_id": 15,
                  "name": "A"}],
            case_types=ApiResponse(status_code=HTTPStatus.INTERNAL_SERVER_ERROR))
        text = await self._page_text()
        self.assertIn("<td>A</td>", text)
        self.assertIn("<td>Unknown</td>", text)

    async def test_case_types_non_list_body_still_renders(self):
        self._page_with(
            [], [{"id": 3, "folder_id": None, "case_type_id": 15,
                  "name": "A"}],
            case_types=ApiResponse(status_code=HTTPStatus.OK,
                                   body={"unexpected": 1}))
        text = await self._page_text()
        self.assertIn("<td>Unknown</td>", text)

    async def test_case_types_exception_still_renders(self):
        self._page_with(
            [], [{"id": 3, "folder_id": None, "case_type_id": 15,
                  "name": "A"}], case_types=RuntimeError("boom"))
        text = await self._page_text()
        self.assertIn("<td>Unknown</td>", text)


if __name__ == "__main__":
    unittest.main()
