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


def _permissions(read=True, add_modify=True, delete=True) -> ApiResponse:
    """The gateway's "my permissions" answer for Test Cases."""
    return ApiResponse(status_code=HTTPStatus.OK, body={
        "project_id": 1,
        "areas": {"test_cases": {
            "read": read, "add_modify": add_modify, "delete": delete}}})


# The Portal asks last, once the page's own data has loaded.
_PERMISSIONS_ALL = _permissions()
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
            _PERMISSIONS_ALL,
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
            _PERMISSIONS_ALL,
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
            _PERMISSIONS_ALL,
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
            _PERMISSIONS_ALL,
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

    async def test_every_section_has_a_delete_button(self):
        self._page_with(
            [{"id": 1, "parent_id": None, "name": "AlphaFolder"},
             {"id": 2, "parent_id": 1, "name": "BetaChild"}], [])
        text = await self._page_text()
        self.assertEqual(text.count("delete-section-btn"), 2)
        self.assertRegex(
            text, r'delete-section-btn"\s+title="Delete section"\s+'
                  r'data-bs-toggle="modal"\s+'
                  r'data-bs-target="#confirmDeleteSectionModal"\s+'
                  r'data-id="1"\s+data-name="AlphaFolder"')
        self.assertIn('data-id="2"', text)

    # ----- the count shown up front ------------------------------------

    def _counts(self, text):
        import re
        return {int(i): int(c) for i, c in re.findall(
            r'data-id="(\d+)"\s+data-name="[^"]*"\s+'
            r'data-testcase-count="(\d+)"', text)}

    async def test_each_section_carries_how_many_test_cases_it_would_remove(
            self):
        self._page_with(
            [{"id": 1, "parent_id": None, "name": "Top"},
             {"id": 2, "parent_id": 1, "name": "Child"},
             {"id": 3, "parent_id": 2, "name": "Grandchild"},
             {"id": 4, "parent_id": None, "name": "Other"},
             {"id": 5, "parent_id": None, "name": "Empty"}],
            [{"id": 10, "folder_id": 1, "case_type_id": 15, "name": "T1"},
             {"id": 11, "folder_id": 2, "case_type_id": 15, "name": "T2"},
             {"id": 12, "folder_id": 2, "case_type_id": 15, "name": "T3"},
             {"id": 13, "folder_id": 3, "case_type_id": 15, "name": "T4"},
             {"id": 14, "folder_id": 4, "case_type_id": 15, "name": "T5"},
             {"id": 15, "folder_id": None, "case_type_id": 15,
              "name": "AtRoot"}])
        counts = self._counts(await self._page_text())
        # Top: its own 1 + Child's 2 + Grandchild's 1. Child: 2 + 1.
        self.assertEqual(counts, {1: 4, 2: 3, 3: 1, 4: 1, 5: 0})

    async def test_a_section_with_no_test_cases_anywhere_has_a_zero_count(
            self):
        self._page_with(
            [{"id": 1, "parent_id": None, "name": "Top"},
             {"id": 2, "parent_id": 1, "name": "Child"}], [])
        self.assertEqual(self._counts(await self._page_text()),
                         {1: 0, 2: 0})

    async def test_root_level_test_cases_are_not_counted_in_any_section(self):
        self._page_with(
            [{"id": 1, "parent_id": None, "name": "Top"}],
            [{"id": 10, "folder_id": None, "case_type_id": 15,
              "name": "AtRoot"}])
        self.assertEqual(self._counts(await self._page_text()), {1: 0})

    async def test_the_single_confirmation_can_show_a_warning_and_cascade(
            self):
        self._page_with(
            [{"id": 1, "parent_id": None, "name": "Top"}], [])
        text = await self._page_text()
        # Hidden until the script sees a non-zero count on the button.
        self.assertRegex(
            text, r'id="sec-delete-warning"\s+style="display: none;"')
        self.assertIn('id="sec-delete-count"', text)
        self.assertIn('id="secConfirmLabel"', text)
        # Posts a plain delete unless the script sets it.
        self.assertRegex(
            text, r'<input type="hidden" name="cascade" id="sec-cascade" '
                  r'value="">')

    async def test_list_has_the_first_step_modal_and_no_second_step(self):
        self._page_with(
            [{"id": 1, "parent_id": None, "name": "AlphaFolder"}], [])
        text = await self._page_text()
        self.assertIn('id="confirmDeleteSectionModal"', text)
        self.assertIn('id="secDeleteForm"', text)
        self.assertIn('data-action-template="/1/folders/__ID__/delete"',
                      text)
        self.assertIn('id="secConfirmDeleteButton"', text)
        # The second prompt only exists after the server refused step one.
        self.assertNotIn("confirmCascadeSectionModal", text)

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
            _PERMISSIONS_ALL,
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
            _PERMISSIONS_ALL,
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


class TestDeleteSection(_SectionWriteCase):
    """POST /<project_id>/folders/<id>/delete - the two-step delete."""

    _URL = "http://gateway/web/folders/4?project_id=1"

    async def asyncSetUp(self):
        await super().asyncSetUp()
        handler = GetProjectTestcasesPageHandler(
            _LOGGER, _config(), self.mock_rest_client, _metadata())
        app = make_app("section_delete")

        @app.route("/<int:project_id>/folders/<int:folder_id>/delete",
                   methods=["POST"])
        async def delete_route(project_id, folder_id):
            return await handler.delete_section(project_id, folder_id)

        self.client = app.test_client()

    async def _post(self, form=None):
        async with self.client as c:
            return await c.post("/1/folders/4/delete", form=form or {},
                                headers=_AUTH_HEADERS)

    def _folders_response(self, folders=None):
        folders = [{"id": 4, "parent_id": None,
                    "name": "Regression 2"}] if folders is None else folders
        self.mock_rest_client.get.side_effect = [
            _PROJECT_OK,
            ApiResponse(status_code=HTTPStatus.OK, body={
                "folders": folders, "test_cases": []}),
            _CASE_TYPES_OK,
            _PERMISSIONS_ALL,
        ]

    @staticmethod
    def _refusal(count):
        return ApiResponse(
            status_code=HTTPStatus.CONFLICT,
            body={"error": f"Folder contains {count} test case(s)",
                  "testcase_count": count})

    # ----- step one ----------------------------------------------------

    async def test_step_one_sends_a_plain_delete(self):
        self.mock_rest_client.delete.return_value = ApiResponse(
            status_code=HTTPStatus.OK, body={})
        await self._post()
        self.mock_rest_client.delete.assert_awaited_once_with(self._URL)

    async def test_success_returns_to_the_list(self):
        self.mock_rest_client.delete.return_value = ApiResponse(
            status_code=HTTPStatus.OK, body={})
        text = await self._text(await self._post())
        self.assertIn("url='http://localhost/1/testcases'", text)

    async def test_already_deleted_also_returns_to_the_list(self):
        self.mock_rest_client.delete.return_value = ApiResponse(
            status_code=HTTPStatus.NOT_FOUND,
            body={"error": "Folder not found"})
        text = await self._text(await self._post())
        self.assertIn("url='http://localhost/1/testcases'", text)

    async def test_not_a_member_goes_to_the_dashboard(self):
        self.mock_rest_client.delete.return_value = ApiResponse(
            status_code=HTTPStatus.FORBIDDEN, body={})
        text = await self._text(await self._post())
        self.assertIn("url='http://localhost//'", text)

    # ----- the second prompt -------------------------------------------

    async def test_refusal_shows_the_second_prompt_with_the_count(self):
        self.mock_rest_client.delete.return_value = self._refusal(12)
        self._folders_response()
        response = await self._post()
        self.assertEqual(response.status_code, 200)
        text = await self._text(response)
        self.assertIn('id="confirmCascadeSectionModal"', text)
        self.assertIn('data-auto-open="true"', text)
        self.assertRegex(text, r'id="cascade-testcase-count">12<')
        self.assertIn("<strong>Regression 2</strong>", text)
        self.assertIn("Delete the section and 12 test cases", text)
        # It explains why it is appearing, so it does not look like a fault.
        self.assertIn('id="cascade-changed-note"', text)
        self.assertIn("This section has changed since this page was loaded, "
                      "so nothing has been deleted.", " ".join(text.split()))

    async def test_second_prompt_posts_cascade_to_that_section(self):
        self.mock_rest_client.delete.return_value = self._refusal(3)
        self._folders_response()
        text = await self._text(await self._post())
        self.assertIn('action="/1/folders/4/delete"', text)
        self.assertRegex(
            text, r'<input type="hidden" name="cascade" value="true">')

    async def test_second_prompt_is_not_dismissed_by_a_stray_click(self):
        self.mock_rest_client.delete.return_value = self._refusal(3)
        self._folders_response()
        text = await self._text(await self._post())
        self.assertIn('data-bs-backdrop="static"', text)

    async def test_a_single_test_case_is_not_pluralised(self):
        self.mock_rest_client.delete.return_value = self._refusal(1)
        self._folders_response()
        text = " ".join((await self._text(await self._post())).split())
        self.assertIn("Delete the section and 1 test case <", text)
        self.assertNotIn("1 test cases", text)
        self.assertIn("permanently delete that test case too", text)

    async def test_refusal_leaves_nothing_deleted_and_shows_no_banner(self):
        self.mock_rest_client.delete.return_value = self._refusal(2)
        self._folders_response()
        text = await self._text(await self._post())
        self.assertNotIn('id="testcases-error"', text)
        # The section is still in the list.
        self.assertIn('data-name="Regression 2"', text)
        self.mock_rest_client.delete.assert_awaited_once()

    async def test_no_prompt_if_the_section_vanished_from_the_list(self):
        self.mock_rest_client.delete.return_value = self._refusal(2)
        self._folders_response(folders=[])
        response = await self._post()
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("confirmCascadeSectionModal",
                         await self._text(response))

    async def test_a_refusal_without_a_count_is_just_an_error(self):
        for body in ({"error": "Folder name already exists"},
                     {"error": "x", "testcase_count": 0}, None):
            with self.subTest(body=body):
                self.mock_rest_client.delete.return_value = ApiResponse(
                    status_code=HTTPStatus.CONFLICT, body=body)
                self._folders_response()
                text = await self._text(await self._post())
                self.assertNotIn("confirmCascadeSectionModal", text)
                self.assertIn('id="testcases-error"', text)

    # ----- step two (cascade) ------------------------------------------

    async def test_cascade_true_is_forwarded_to_the_gateway(self):
        self.mock_rest_client.delete.return_value = ApiResponse(
            status_code=HTTPStatus.OK, body={})
        text = await self._text(await self._post({"cascade": "true"}))
        self.mock_rest_client.delete.assert_awaited_once_with(
            self._URL + "&cascade=true")
        self.assertIn("url='http://localhost/1/testcases'", text)

    async def test_anything_but_true_is_not_a_cascade(self):
        """Only the prompt's exact value deletes test cases."""
        self.mock_rest_client.delete.return_value = ApiResponse(
            status_code=HTTPStatus.OK, body={})
        for value in ("yes", "1", "TRUE", "True", "false", ""):
            with self.subTest(value=value):
                self.mock_rest_client.delete.reset_mock()
                await self._post({"cascade": value})
                self.mock_rest_client.delete.assert_awaited_once_with(
                    self._URL)

    async def test_a_refusal_after_cascade_is_an_error_not_a_loop(self):
        self.mock_rest_client.delete.return_value = self._refusal(5)
        self._folders_response()
        text = await self._text(await self._post({"cascade": "true"}))
        self.assertNotIn("confirmCascadeSectionModal", text)
        self.assertIn('id="testcases-error"', text)

    # ----- other failures ----------------------------------------------

    async def test_other_failure_shows_the_list_with_the_message(self):
        self.mock_rest_client.delete.return_value = ApiResponse(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            body={"error": "CMS service unavailable"})
        self._folders_response()
        text = await self._text(await self._post())
        self.assertIn('id="testcases-error"', text)
        self.assertIn("CMS service unavailable", text)
        self.assertIn('data-name="Regression 2"', text)

    async def test_failure_without_a_message_shows_the_fallback(self):
        self.mock_rest_client.delete.return_value = ApiResponse(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR, body={})
        self._folders_response()
        text = await self._text(await self._post())
        self.assertIn("The request could not be completed", text)


# ------------------------------------------------------------------
# Controls follow the person's permissions (design doc section 9.5)
# ------------------------------------------------------------------

_PERMISSIONS_URL = "http://gateway/web/projects/1/permissions"

# Markers that appear in the page only when the control does. The controls
# are left out of the HTML entirely (not styled away), so absent really
# means absent: there is nothing to unhide in the browser.
_ADD_CONTROLS = ('id="add-section-btn"', 'id="add-testcase-btn"',
                 "edit-testcase-btn", "add-subsection-btn",
                 "rename-section-btn", 'id="sectionModal"')
_DELETE_CONTROLS = ("delete-testcase-btn", "delete-section-btn",
                    'id="confirmDeleteTestcaseModal"',
                    'id="confirmDeleteSectionModal"')

_FOLDERS = [{"id": 1, "parent_id": None, "name": "Regression"}]
_TEST_CASES = [
    {"id": 3, "folder_id": 1, "case_type_id": 9, "name": "In a section"},
    {"id": 4, "folder_id": None, "case_type_id": 9, "name": "At the root"},
]


class TestListControlsFollowPermissions(unittest.IsolatedAsyncioTestCase):
    """What the test case list offers each kind of person.

    Hiding is for tidiness only: the gateway refuses the action whatever the
    page shows. These tests are about the page.
    """

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

    async def _page(self, permissions):
        """Render the list; ``permissions`` is the gateway's answer, or an
        exception to raise."""
        async def fake_get(url, *_args, **_kwargs):
            if url == "http://gateway/web/projects/1":
                return _PROJECT_OK
            if url == "http://gateway/web/1/testcases":
                return ApiResponse(status_code=HTTPStatus.OK, body={
                    "folders": _FOLDERS, "test_cases": _TEST_CASES})
            if url == "http://gateway/web/case_types":
                return _CASE_TYPES_OK
            if url == _PERMISSIONS_URL:
                if isinstance(permissions, Exception):
                    raise permissions
                return permissions
            raise AssertionError(f"unexpected gateway GET {url}")

        self.mock_rest_client.get.side_effect = fake_get
        async with self.client as c:
            response = await c.get("/1/testcases", headers=_AUTH_HEADERS)
        self.assertEqual(response.status_code, 200)
        return await response.get_data(as_text=True)

    def _assert_present(self, text, markers):
        for marker in markers:
            self.assertIn(marker, text, marker)

    def _assert_absent(self, text, markers):
        for marker in markers:
            self.assertNotIn(marker, text, marker)

    async def test_a_reader_is_offered_no_controls_at_all(self):
        text = await self._page(_permissions(add_modify=False, delete=False))
        self._assert_absent(text, _ADD_CONTROLS + _DELETE_CONTROLS)
        # No empty "Actions" column left behind either.
        self.assertNotIn(">Actions<", text)

    async def test_a_reader_still_sees_everything_they_may_read(self):
        text = await self._page(_permissions(add_modify=False, delete=False))
        self.assertIn("Regression", text)
        self.assertIn("In a section", text)
        self.assertIn("At the root", text)
        self.assertIn('href="/1/testcases/3"', text)  # the name still links

    async def test_a_tester_can_add_and_edit_but_not_delete(self):
        text = await self._page(_permissions(delete=False))
        self._assert_present(text, _ADD_CONTROLS)
        self._assert_absent(text, _DELETE_CONTROLS)
        self.assertIn(">Actions<", text)

    async def test_a_lead_is_offered_everything(self):
        text = await self._page(_permissions())
        self._assert_present(text, _ADD_CONTROLS + _DELETE_CONTROLS)

    async def test_each_control_follows_its_own_permission(self):
        """Delete without Add/Modify cannot be saved as a role, but the page
        must not depend on that: each control checks its own permission."""
        text = await self._page(_permissions(add_modify=False))
        self._assert_present(text, _DELETE_CONTROLS)
        self._assert_absent(text, _ADD_CONTROLS)

    async def test_controls_appear_for_every_test_case_and_section(self):
        text = await self._page(_permissions())
        self.assertEqual(text.count("edit-testcase-btn"), 2)
        self.assertEqual(text.count("delete-testcase-btn"), 2)
        self.assertEqual(text.count("rename-section-btn"), 1)

    async def test_nothing_granted_means_nothing_offered(self):
        text = await self._page(_permissions(False, False, False))
        self._assert_absent(text, _ADD_CONTROLS + _DELETE_CONTROLS)

    async def test_it_asks_the_gateway_about_this_project_last(self):
        await self._page(_permissions())
        urls = [call.args[0]
                for call in self.mock_rest_client.get.await_args_list]
        self.assertEqual(urls[-1], _PERMISSIONS_URL)
        self.assertEqual(urls.count(_PERMISSIONS_URL), 1)

    # --- fail closed ---------------------------------------------------

    async def test_if_it_cannot_find_out_it_offers_nothing(self):
        """The page still loads; it just shows no controls, rather than
        guessing that they would be allowed."""
        cannot_find_out = {
            "gateway error": ApiResponse(status_code=503),
            "forbidden": ApiResponse(status_code=403),
            "not found": ApiResponse(status_code=404),
            "unreachable": ApiResponse(exception_msg="connection refused"),
            "raises": RuntimeError("boom"),
            "no body": ApiResponse(status_code=HTTPStatus.OK, body=None),
            "list body": ApiResponse(status_code=HTTPStatus.OK, body=[]),
            "no areas": ApiResponse(status_code=HTTPStatus.OK, body={}),
            "areas not a dict": ApiResponse(
                status_code=HTTPStatus.OK, body={"areas": []}),
            "no test cases area": ApiResponse(
                status_code=HTTPStatus.OK, body={"areas": {}}),
            "area not a dict": ApiResponse(
                status_code=HTTPStatus.OK,
                body={"areas": {"test_cases": True}}),
        }
        for label, permissions in cannot_find_out.items():
            with self.subTest(label):
                text = await self._page(permissions)
                self._assert_absent(text, _ADD_CONTROLS + _DELETE_CONTROLS)
                self.assertIn("In a section", text)

    async def test_only_a_real_true_counts(self):
        """"true", 1 and null are not grants."""
        for value in ("true", 1, None, "yes", [True]):
            with self.subTest(value=value):
                text = await self._page(ApiResponse(
                    status_code=HTTPStatus.OK,
                    body={"areas": {"test_cases": {
                        "read": value, "add_modify": value,
                        "delete": value}}}))
                self._assert_absent(text, _ADD_CONTROLS + _DELETE_CONTROLS)

    async def test_a_missing_action_is_not_granted(self):
        text = await self._page(ApiResponse(
            status_code=HTTPStatus.OK,
            body={"areas": {"test_cases": {"add_modify": True}}}))
        self._assert_present(text, _ADD_CONTROLS)
        self._assert_absent(text, _DELETE_CONTROLS)


if __name__ == "__main__":
    unittest.main()
