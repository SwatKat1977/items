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
        # The old placeholders pointed at modals that never existed.
        self.assertNotIn("addSectionModal", text)
        self.assertNotIn("addTestCaseModal", text)
        # "Add Section" is the working button in the title bar, once - not
        # a second copy inside the empty message.
        self.assertEqual(text.count("Add Section"), 2)  # button + modal title
        self.assertEqual(text.count('id="add-section-btn"'), 1)

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
        self.assertIn(">A</a>", text)
        self.assertIn("<td>Unknown</td>", text)

    async def test_add_test_case_button_links_to_the_add_page(self):
        self._page_with([], [])
        text = await self._page_text()
        self.assertIn('href="/1/testcases/add"', text)
        self.assertIn("Add Test Case", text)

    async def test_name_opens_the_view_and_pencil_opens_the_editor(self):
        """The name opens the read-only view (which has its own Edit
        button); the pencil is the one-step shortcut to editing."""
        self._page_with(
            [{"id": 1, "parent_id": None, "name": "AlphaFolder"}],
            [{"id": 3, "folder_id": None, "case_type_id": 15,
              "name": "RootCase"},
             {"id": 4, "folder_id": 1, "case_type_id": 9,
              "name": "FolderCase"}])
        text = await self._page_text()
        self.assertEqual(text.count('href="/1/testcases/3/edit"'), 1)
        self.assertEqual(text.count('href="/1/testcases/4/edit"'), 1)
        self.assertRegex(
            text, r'testcase-name-link"\s+href="/1/testcases/3">'
                  r'RootCase</a>')
        self.assertRegex(
            text, r'testcase-name-link"\s+href="/1/testcases/4">'
                  r'FolderCase</a>')
        self.assertRegex(
            text, r'edit-testcase-btn"\s+title="Edit"\s+'
                  r'href="/1/testcases/3/edit"')

    async def test_title_bar_has_an_add_section_button(self):
        self._page_with([], [])
        text = await self._page_text()
        self.assertRegex(
            text, r'id="add-section-btn"\s+data-bs-toggle="modal"\s+'
                  r'data-bs-target="#sectionModal"\s+'
                  r'data-section-mode="add"')

    async def test_every_section_can_add_a_subsection_and_be_renamed(self):
        self._page_with(
            [{"id": 1, "parent_id": None, "name": "AlphaFolder"},
             {"id": 2, "parent_id": 1, "name": "BetaChild"}], [])
        text = await self._page_text()
        self.assertEqual(text.count("add-subsection-btn"), 2)
        self.assertEqual(text.count("rename-section-btn"), 2)
        self.assertRegex(
            text, r'data-section-mode="add-sub"\s+data-parent-id="1"\s+'
                  r'data-parent-name="AlphaFolder"')
        self.assertRegex(
            text, r'data-section-mode="rename"\s+data-id="2"\s+'
                  r'data-name="BetaChild"')

    async def test_list_has_the_section_modal_and_its_form(self):
        self._page_with([], [])
        text = await self._page_text()
        self.assertIn('id="sectionModal"', text)
        self.assertIn('id="sectionForm"', text)
        self.assertIn('data-add-action="/1/folders/add"', text)
        self.assertIn(
            'data-rename-action-template="/1/folders/__ID__/rename"', text)
        self.assertIn('name="parent_id"', text)
        self.assertRegex(text, r'name="name"\s+required')

    async def test_section_names_are_escaped_in_the_buttons(self):
        self._page_with(
            [{"id": 1, "parent_id": None, "name": '"><b>x</b>'}], [])
        text = await self._page_text()
        self.assertNotIn('"><b>x</b>', text)

    async def test_every_test_case_has_a_delete_button(self):
        self._page_with(
            [{"id": 1, "parent_id": None, "name": "AlphaFolder"}],
            [{"id": 3, "folder_id": None, "case_type_id": 15,
              "name": "RootCase"},
             {"id": 4, "folder_id": 1, "case_type_id": 9,
              "name": "FolderCase"}])
        text = await self._page_text()
        self.assertEqual(text.count("delete-testcase-btn"), 2)
        self.assertRegex(
            text, r'delete-testcase-btn"\s+title="Delete"\s+'
                  r'data-bs-toggle="modal"\s+'
                  r'data-bs-target="#confirmDeleteTestcaseModal"\s+'
                  r'data-id="3"\s+data-name="RootCase"')
        self.assertIn('data-id="4"', text)

    async def test_list_has_the_confirm_modal_form_and_script(self):
        self._page_with([], [
            {"id": 3, "folder_id": None, "case_type_id": 15, "name": "A"}])
        text = await self._page_text()
        self.assertIn('id="confirmDeleteTestcaseModal"', text)
        self.assertIn('id="tcDeleteForm"', text)
        self.assertIn('data-action-template="/1/testcases/__ID__/delete"',
                      text)
        self.assertIn("scripts/project_testcases.js", text)

    async def test_no_error_banner_on_a_normal_page(self):
        self._page_with([], [
            {"id": 3, "folder_id": None, "case_type_id": 15, "name": "A"}])
        text = await self._page_text()
        self.assertNotIn('id="testcases-error"', text)

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


class TestDeleteTestcaseFromList(unittest.IsolatedAsyncioTestCase):
    """POST /<project_id>/testcases/<id>/delete."""

    _DELETE_URL = "http://gateway/web/testcases/7?project_id=1"

    async def asyncSetUp(self):
        self.mock_rest_client = AsyncMock()
        self.mock_rest_client.post.return_value = ApiResponse(
            status_code=HTTPStatus.OK, body={"status": "VALID"})
        handler = GetProjectTestcasesPageHandler(
            _LOGGER, _config(), self.mock_rest_client, _metadata())

        app = make_app()

        @app.route("/<int:project_id>/testcases/<int:case_id>/delete",
                   methods=["POST"])
        async def route(project_id, case_id):
            return await handler.delete_test_case(project_id, case_id)

        self.client = app.test_client()

    async def _post(self):
        async with self.client as c:
            return await c.post("/1/testcases/7/delete",
                                headers=_AUTH_HEADERS)

    def _list_page_responses(self):
        """What re-showing the list needs: project, test cases, types."""
        self.mock_rest_client.get.side_effect = [
            _PROJECT_OK,
            ApiResponse(status_code=HTTPStatus.OK, body={
                "folders": [], "test_cases": [
                    {"id": 7, "folder_id": None, "case_type_id": 15,
                     "name": "StillHere"}]}),
            _CASE_TYPES_OK,
        ]

    async def test_deletes_via_the_gateway_with_the_project(self):
        self.mock_rest_client.delete.return_value = ApiResponse(
            status_code=HTTPStatus.OK, body={})
        await self._post()
        self.mock_rest_client.delete.assert_awaited_once_with(
            self._DELETE_URL)

    async def test_success_returns_to_the_list(self):
        self.mock_rest_client.delete.return_value = ApiResponse(
            status_code=HTTPStatus.OK, body={})
        response = await self._post()
        text = await response.get_data(as_text=True)
        self.assertIn("url='http://localhost/1/testcases'", text)

    async def test_already_deleted_also_returns_to_the_list(self):
        self.mock_rest_client.delete.return_value = ApiResponse(
            status_code=HTTPStatus.NOT_FOUND,
            body={"error": "Test case not found"})
        text = await (await self._post()).get_data(as_text=True)
        self.assertIn("url='http://localhost/1/testcases'", text)

    async def test_not_a_member_goes_to_the_dashboard(self):
        self.mock_rest_client.delete.return_value = ApiResponse(
            status_code=HTTPStatus.FORBIDDEN, body={"error": "Forbidden"})
        text = await (await self._post()).get_data(as_text=True)
        self.assertIn("url='http://localhost//'", text)

    async def test_failure_shows_the_list_with_the_gateway_message(self):
        self.mock_rest_client.delete.return_value = ApiResponse(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            body={"error": "CMS service unavailable"})
        self._list_page_responses()
        response = await self._post()
        self.assertEqual(response.status_code, 200)
        text = await response.get_data(as_text=True)
        self.assertIn('id="testcases-error"', text)
        self.assertIn("CMS service unavailable", text)
        # The list is shown again, with the test case still there.
        self.assertIn("StillHere", text)

    async def test_failure_without_a_message_shows_the_fallback(self):
        self.mock_rest_client.delete.return_value = ApiResponse(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR, body={})
        self._list_page_responses()
        text = await (await self._post()).get_data(as_text=True)
        self.assertIn("The request could not be completed", text)


class _SectionWriteCase(unittest.IsolatedAsyncioTestCase):
    """Shared setup for the add and rename section handlers."""

    async def asyncSetUp(self):
        self.mock_rest_client = AsyncMock()
        self.mock_rest_client.post.return_value = ApiResponse(
            status_code=HTTPStatus.OK, body={"status": "VALID"})
        handler = GetProjectTestcasesPageHandler(
            _LOGGER, _config(), self.mock_rest_client, _metadata())

        app = make_app()

        @app.route("/<int:project_id>/folders/add", methods=["POST"])
        async def add_route(project_id):
            return await handler.add_section(project_id)

        @app.route("/<int:project_id>/folders/<int:folder_id>/rename",
                   methods=["POST"])
        async def rename_route(project_id, folder_id):
            return await handler.rename_section(project_id, folder_id)

        self.client = app.test_client()

    def _list_page_responses(self):
        """What re-showing the list needs: project, test cases, types."""
        self.mock_rest_client.get.side_effect = [
            _PROJECT_OK,
            ApiResponse(status_code=HTTPStatus.OK, body={
                "folders": [{"id": 1, "parent_id": None, "name": "StillHere"}],
                "test_cases": []}),
            _CASE_TYPES_OK,
        ]

    @staticmethod
    async def _text(response):
        return await response.get_data(as_text=True)


class TestAddSection(_SectionWriteCase):
    """POST /<project_id>/folders/add."""

    async def _post(self, form):
        async with self.client as c:
            return await c.post("/1/folders/add", form=form,
                                headers=_AUTH_HEADERS)

    def _gateway_replies(self, response):
        """Session validation is the first POST; the gateway's follows."""
        self.mock_rest_client.post.side_effect = [
            ApiResponse(status_code=HTTPStatus.OK,
                        body={"status": "VALID"}), response]

    async def test_top_level_section_is_posted_with_a_null_parent(self):
        self._gateway_replies(ApiResponse(
            status_code=HTTPStatus.OK, body={"folder_id": 4}))
        await self._post({"name": "Regression", "parent_id": ""})
        call = self.mock_rest_client.post.call_args_list[1]
        self.assertEqual(call.args[0], "http://gateway/web/1/folders")
        self.assertEqual(call.kwargs["json_data"],
                         {"parent_id": None, "name": "Regression"})

    async def test_missing_parent_field_also_means_top_level(self):
        self._gateway_replies(ApiResponse(
            status_code=HTTPStatus.OK, body={"folder_id": 4}))
        await self._post({"name": "Regression"})
        sent = self.mock_rest_client.post.call_args_list[1].kwargs[
            "json_data"]
        self.assertIsNone(sent["parent_id"])

    async def test_subsection_is_posted_with_its_parent_id(self):
        self._gateway_replies(ApiResponse(
            status_code=HTTPStatus.OK, body={"folder_id": 4}))
        await self._post({"name": "Sub", "parent_id": "3"})
        sent = self.mock_rest_client.post.call_args_list[1].kwargs[
            "json_data"]
        self.assertEqual(sent, {"parent_id": 3, "name": "Sub"})

    async def test_no_project_id_is_sent_in_the_body(self):
        """The gateway takes the project from the URL and rejects it in the
        body."""
        self._gateway_replies(ApiResponse(
            status_code=HTTPStatus.OK, body={"folder_id": 4}))
        await self._post({"name": "Regression", "project_id": "9"})
        sent = self.mock_rest_client.post.call_args_list[1].kwargs[
            "json_data"]
        self.assertNotIn("project_id", sent)

    async def test_a_bad_parent_is_refused_without_calling_the_gateway(self):
        self._list_page_responses()
        for bad in ("abc", "-1", "1.5", "3; DROP"):
            with self.subTest(parent=bad):
                self.mock_rest_client.post.reset_mock()
                self.mock_rest_client.post.side_effect = None
                self.mock_rest_client.post.return_value = ApiResponse(
                    status_code=HTTPStatus.OK, body={"status": "VALID"})
                self._list_page_responses()
                response = await self._post(
                    {"name": "Sub", "parent_id": bad})
                text = await self._text(response)
                self.assertIn("Invalid parent section.", text)
                # Only the session check, never a gateway create.
                self.assertEqual(self.mock_rest_client.post.call_count, 1)

    async def test_success_returns_to_the_list(self):
        self._gateway_replies(ApiResponse(
            status_code=HTTPStatus.OK, body={"folder_id": 4}))
        text = await self._text(await self._post({"name": "Regression"}))
        self.assertIn("url='http://localhost/1/testcases'", text)

    async def test_not_a_member_goes_to_the_dashboard(self):
        self._gateway_replies(ApiResponse(
            status_code=HTTPStatus.FORBIDDEN, body={"error": "Forbidden"}))
        text = await self._text(await self._post({"name": "Regression"}))
        self.assertIn("url='http://localhost//'", text)

    async def test_duplicate_name_shows_the_list_with_the_message(self):
        self._gateway_replies(ApiResponse(
            status_code=HTTPStatus.CONFLICT,
            body={"error": "Folder name already exists"}))
        self._list_page_responses()
        response = await self._post({"name": "Regression"})
        self.assertEqual(response.status_code, 200)
        text = await self._text(response)
        self.assertIn('id="testcases-error"', text)
        self.assertIn("Folder name already exists", text)
        self.assertIn("StillHere", text)

    async def test_missing_parent_section_shows_the_message(self):
        self._gateway_replies(ApiResponse(
            status_code=HTTPStatus.NOT_FOUND,
            body={"error": "Parent folder id is invalid"}))
        self._list_page_responses()
        text = await self._text(
            await self._post({"name": "Sub", "parent_id": "99"}))
        self.assertIn("Parent folder id is invalid", text)

    async def test_failure_without_a_message_shows_the_fallback(self):
        self._gateway_replies(ApiResponse(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR, body={}))
        self._list_page_responses()
        text = await self._text(await self._post({"name": "Regression"}))
        self.assertIn("The request could not be completed", text)


class TestRenameSection(_SectionWriteCase):
    """POST /<project_id>/folders/<id>/rename."""

    async def _post(self, form, folder_id=4):
        async with self.client as c:
            return await c.post(f"/1/folders/{folder_id}/rename", form=form,
                                headers=_AUTH_HEADERS)

    async def test_patches_the_gateway_with_the_project_in_the_url(self):
        self.mock_rest_client.patch.return_value = ApiResponse(
            status_code=HTTPStatus.OK, body={"status": 1})
        await self._post({"name": "Renamed"})
        self.mock_rest_client.patch.assert_awaited_once_with(
            "http://gateway/web/folders/4?project_id=1",
            json_data={"name": "Renamed"})

    async def test_success_returns_to_the_list(self):
        self.mock_rest_client.patch.return_value = ApiResponse(
            status_code=HTTPStatus.OK, body={"status": 1})
        text = await self._text(await self._post({"name": "Renamed"}))
        self.assertIn("url='http://localhost/1/testcases'", text)

    async def test_not_a_member_goes_to_the_dashboard(self):
        self.mock_rest_client.patch.return_value = ApiResponse(
            status_code=HTTPStatus.FORBIDDEN, body={})
        text = await self._text(await self._post({"name": "Renamed"}))
        self.assertIn("url='http://localhost//'", text)

    async def test_duplicate_name_shows_the_list_with_the_message(self):
        self.mock_rest_client.patch.return_value = ApiResponse(
            status_code=HTTPStatus.CONFLICT,
            body={"error": "Folder name already exists"})
        self._list_page_responses()
        text = await self._text(await self._post({"name": "Taken"}))
        self.assertIn('id="testcases-error"', text)
        self.assertIn("Folder name already exists", text)

    async def test_vanished_section_shows_the_message(self):
        self.mock_rest_client.patch.return_value = ApiResponse(
            status_code=HTTPStatus.NOT_FOUND,
            body={"error": "Folder not found"})
        self._list_page_responses()
        text = await self._text(await self._post({"name": "Renamed"}))
        self.assertIn("Folder not found", text)

    async def test_failure_without_a_message_shows_the_fallback(self):
        self.mock_rest_client.patch.return_value = ApiResponse(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR, body={})
        self._list_page_responses()
        text = await self._text(await self._post({"name": "Renamed"}))
        self.assertIn("The request could not be completed", text)


if __name__ == "__main__":
    unittest.main()
