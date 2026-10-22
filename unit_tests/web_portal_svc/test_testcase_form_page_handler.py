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
from items.services.items_web_portal.page_handlers.testcases.\
    testcase_form_page_handler import TestcaseFormPageHandler

_LOGGER = MagicMock()
_AUTH_HEADERS = {"Cookie": "items_token=abc; items_user=bob"}
_SESSION_VALID = ApiResponse(
    status_code=HTTPStatus.OK,
    body={"status": "VALID", "is_administrator": False})

_GW = "http://gateway/"
_PROJECT_URL = f"{_GW}web/projects/1"
_CASE_TYPES_URL = f"{_GW}web/case_types"
_TESTCASE_URL = f"{_GW}web/testcases/7?project_id=1"
_PERMISSIONS_URL = f"{_GW}web/projects/1/permissions"

_PROJECT_OK = ApiResponse(status_code=HTTPStatus.OK,
                          body={"name": "Zephyr Project"})
_CASE_TYPES_OK = ApiResponse(status_code=HTTPStatus.OK, body=[
    {"id": 9, "name": "Smoke", "description": "", "is_default": False},
    {"id": 15, "name": "Other", "description": "", "is_default": True},
])


def _permissions(read=True, add_modify=True, delete=True) -> ApiResponse:
    """The gateway's "my permissions" answer for Test Cases."""
    return ApiResponse(status_code=HTTPStatus.OK, body={
        "project_id": 1,
        "areas": {"test_cases": {
            "read": read, "add_modify": add_modify, "delete": delete}}})


_PERMISSIONS_ALL = _permissions()
_TESTCASE_OK = ApiResponse(status_code=HTTPStatus.OK, body={
    "id": 7, "project_id": 1, "folder_id": None, "case_type_id": 9,
    "name": "Login works", "description": "Check the login."})

# The gateway has no section read route: the test case list carries the
# whole folder tree, and the form's Section dropdown is built from it.
_SECTIONS_URL = f"{_GW}web/1/testcases"
_SECTIONS_OK = ApiResponse(status_code=HTTPStatus.OK, body={
    # In the order the API returns them (by parent, then id). The dropdown
    # must put each sub-section straight after its parent: 1, 2, 4, 3.
    "folders": [
        {"id": 1, "parent_id": None, "name": "Regression"},
        {"id": 3, "parent_id": None, "name": "Performance"},
        {"id": 2, "parent_id": 1, "name": "Smoke"},
        {"id": 4, "parent_id": 2, "name": "Login"},
    ],
    "test_cases": []})

def _testcase_in(folder_id) -> ApiResponse:
    """The test case (as _TESTCASE_OK) sitting in the given section."""
    return ApiResponse(status_code=HTTPStatus.OK, body={
        **_TESTCASE_OK.body, "folder_id": folder_id})


_MOVE_URL = f"{_GW}web/testcases/7/move?project_id=1"

_REDIRECT_TO_LIST = "url='http://localhost/1/testcases'"
_REDIRECT_TO_DASHBOARD = "url='http://localhost//'"


def _config():
    config = MagicMock()
    config.apis_gateway_svc = _GW
    return config


def _metadata():
    metadata = MagicMock()
    metadata.instance_name = "INSTANCE"
    return metadata


class _FormPageTestCase(unittest.IsolatedAsyncioTestCase):
    """Shared setup: a Quart app exposing the four form routes."""

    async def asyncSetUp(self):
        self.mock_rest_client = AsyncMock()
        self.mock_rest_client.post.return_value = _SESSION_VALID
        handler = TestcaseFormPageHandler(
            _LOGGER, _config(), self.mock_rest_client, _metadata())

        app = make_app()

        @app.route("/<int:project_id>/testcases/<int:case_id>",
                   methods=["GET"])
        async def view_get(project_id, case_id):
            return await handler.view_page(project_id, case_id)

        @app.route("/<int:project_id>/testcases/add", methods=["GET"])
        async def add_get(project_id):
            return await handler.add_form(project_id)

        @app.route("/<int:project_id>/testcases/add", methods=["POST"])
        async def add_post(project_id):
            return await handler.add_submit(project_id)

        @app.route("/<int:project_id>/testcases/<int:case_id>/edit",
                   methods=["GET"])
        async def edit_get(project_id, case_id):
            return await handler.edit_form(project_id, case_id)

        @app.route("/<int:project_id>/testcases/<int:case_id>/edit",
                   methods=["POST"])
        async def edit_post(project_id, case_id):
            return await handler.edit_submit(project_id, case_id)

        @app.route("/<int:project_id>/testcases/<int:case_id>/move",
                   methods=["POST"])
        async def move_post(project_id, case_id):
            return await handler.move_submit(project_id, case_id)

        self.client = app.test_client()

    def _gateway_gets(self, responses: dict):
        """Answer gateway GETs by URL, so tests don't depend on call order.

        An entry that is an exception is raised; a URL not listed fails the
        test loudly. The "my permissions" answer defaults to "allowed
        everything" (a test about a refusal lists its own), because the Add
        and Edit forms now ask it before showing themselves. The sections
        default to a small tree: every page that shows a section asks for
        them, and the page swallows a failed lookup, so a missing answer
        would quietly test the "unavailable" path instead of failing.
        """
        responses = {_PERMISSIONS_URL: _PERMISSIONS_ALL,
                     _SECTIONS_URL: _SECTIONS_OK, **responses}

        async def fake_get(url, *_args, **_kwargs):
            if url not in responses:
                raise AssertionError(f"unexpected gateway GET {url}")
            response = responses[url]
            if isinstance(response, Exception):
                raise response
            return response

        self.mock_rest_client.get.side_effect = fake_get

    def _session_then(self, *gateway_posts):
        """Session validation is the first POST; gateway POSTs follow."""
        self.mock_rest_client.post.side_effect = [
            _SESSION_VALID, *gateway_posts]

    async def _text(self, response):
        return await response.get_data(as_text=True)


# ---------------------------------------------------------------------------
# View: read-only
# ---------------------------------------------------------------------------

class TestViewTestcasePage(_FormPageTestCase):

    async def _get(self):
        async with self.client as c:
            return await c.get("/1/testcases/7", headers=_AUTH_HEADERS)

    def _ready(self, testcase=_TESTCASE_OK, case_types=_CASE_TYPES_OK,
               permissions=_PERMISSIONS_ALL):
        self._gateway_gets({_TESTCASE_URL: testcase,
                            _PROJECT_URL: _PROJECT_OK,
                            _CASE_TYPES_URL: case_types,
                            _PERMISSIONS_URL: permissions})

    async def test_shows_the_test_case_read_only(self):
        self._ready()
        response = await self._get()
        self.assertEqual(response.status_code, 200)
        text = await self._text(response)
        self.assertIn("Login works", text)
        self.assertIn("Check the login.", text)
        self.assertIn("Zephyr Project", text)
        # Read-only: no form to type into.
        self.assertNotIn('id="testcaseForm"', text)
        self.assertNotIn("<textarea", text)

    async def test_shows_the_type_name_not_its_id(self):
        self._ready()
        text = await self._text(await self._get())
        self.assertRegex(text, r'id="testcase-view-type">Smoke<')

    async def test_shows_which_section_the_test_case_is_in_as_a_path(self):
        self._ready(testcase=_testcase_in(4))
        text = await self._text(await self._get())
        self.assertRegex(
            text, r'id="testcase-view-section">Regression / Smoke / Login<')

    async def test_a_test_case_with_no_section_says_so(self):
        self._ready()
        text = await self._text(await self._get())
        self.assertRegex(text, r'id="testcase-view-section">\(No section\)<')

    async def test_section_is_unavailable_when_the_sections_cannot_be_read(
            self):
        """The page still works: only the Section row loses its answer."""
        for bad in (ApiResponse(status_code=503),
                    ApiResponse(status_code=200, body={"folders": "x"}),
                    RuntimeError("gateway down")):
            with self.subTest(sections=bad):
                self._gateway_gets({_TESTCASE_URL: _testcase_in(4),
                                    _PROJECT_URL: _PROJECT_OK,
                                    _CASE_TYPES_URL: _CASE_TYPES_OK,
                                    _SECTIONS_URL: bad})
                response = await self._get()
                self.assertEqual(response.status_code, 200)
                text = await self._text(response)
                self.assertRegex(
                    text, r'id="testcase-view-section"><span class="text-muted">'
                          r'Unavailable</span>')
                self.assertIn("Login works", text)

    async def test_a_section_that_is_not_in_the_list_is_unavailable(self):
        self._ready(testcase=_testcase_in(99))
        text = await self._text(await self._get())
        self.assertRegex(
            text, r'id="testcase-view-section"><span class="text-muted">'
                  r'Unavailable</span>')

    async def test_section_row_sits_between_description_and_type(self):
        """The same order as the Add and Edit pages."""
        self._ready()
        text = await self._text(await self._get())
        self.assertLess(text.index("testcase-view-description"),
                        text.index("testcase-view-section"))
        self.assertLess(text.index("testcase-view-section"),
                        text.index("testcase-view-type"))

    async def test_edit_button_goes_to_the_edit_page(self):
        self._ready()
        text = await self._text(await self._get())
        self.assertRegex(
            text, r'href="/1/testcases/7/edit"\s+class="btn btn-header"'
                  r'\s+id="edit-testcase-btn"')

    async def test_delete_button_opens_the_confirm_modal_for_this_case(self):
        self._ready()
        text = await self._text(await self._get())
        self.assertRegex(
            text, r'id="delete-testcase-btn"\s+data-bs-toggle="modal"\s+'
                  r'data-bs-target="#confirmDeleteTestcaseModal"\s+'
                  r'data-id="7"\s+data-name="Login works"')
        self.assertIn('id="confirmDeleteTestcaseModal"', text)
        self.assertIn('data-action-template="/1/testcases/__ID__/delete"',
                      text)
        self.assertIn("scripts/project_testcases.js", text)

    async def test_delete_modal_is_not_on_the_edit_page(self):
        self._gateway_gets({_TESTCASE_URL: _TESTCASE_OK,
                            _PROJECT_URL: _PROJECT_OK,
                            _CASE_TYPES_URL: _CASE_TYPES_OK})
        async with self.client as c:
            edit = await self._text(await c.get(
                "/1/testcases/7/edit", headers=_AUTH_HEADERS))
        self.assertNotIn("confirmDeleteTestcaseModal", edit)

    async def test_title_names_the_test_case_by_id(self):
        self._ready()
        text = await self._text(await self._get())
        self.assertRegex(text, r'id="testcase-view-title">Test Case #7<')

    async def test_shows_name_description_and_type_in_that_order(self):
        """The same field order as the add and edit forms."""
        self._ready()
        text = await self._text(await self._get())
        self.assertLess(text.index('id="testcase-view-name"'),
                        text.index('id="testcase-view-description"'))
        self.assertLess(text.index('id="testcase-view-description"'),
                        text.index('id="testcase-view-type"'))

    async def test_back_link_returns_to_the_list(self):
        self._ready()
        text = await self._text(await self._get())
        self.assertIn('href="/1/testcases"', text)
        self.assertIn("Back to Test Cases", text)

    async def test_buttons_are_inside_the_card_in_the_site_colours(self):
        """Edit is the navy primary button and Back the outline one, in the
        card's button row - the same place and style as Save and Cancel on
        the form."""
        self._ready()
        text = await self._text(await self._get())
        self.assertRegex(
            text, r'(?s)testcase-form-card">.*?testcase-form-actions">'
                  r'\s*<a href="/1/testcases/7/edit"\s+class="btn btn-header"'
                  r'\s+id="edit-testcase-btn">.*?Edit</a>\s*'
                  r'<a href="/1/testcases" class="btn btn-header-outline">'
                  r'Back to Test Cases</a>\s*<button.*?</button>\s*</div>'
                  r'\s*</div>')
        self.assertNotIn("btn-outline-secondary", text)
        self.assertNotIn("btn-primary", text)

    async def test_view_and_edit_pages_share_one_layout(self):
        """Switching between viewing and editing must not feel like two
        different pages: same card, same labels in the same order, same
        button row."""
        self._ready()
        view = await self._text(await self._get())
        self._gateway_gets({_TESTCASE_URL: _TESTCASE_OK,
                            _PROJECT_URL: _PROJECT_OK,
                            _CASE_TYPES_URL: _CASE_TYPES_OK})
        async with self.client as c:
            edit = await self._text(await c.get(
                "/1/testcases/7/edit", headers=_AUTH_HEADERS))

        for marker in ('id="testcases-title-bar"', 'testcase-form-card',
                       'testcase-form-actions', 'btn-header-outline'):
            with self.subTest(marker=marker):
                self.assertIn(marker, view)
                self.assertIn(marker, edit)

        view_order = [view.index('>Name<'), view.index('>Description<'),
                      view.index('>Type<')]
        edit_order = [edit.index('>Name '), edit.index('>Description<'),
                      edit.index('>Type<')]
        self.assertEqual(view_order, sorted(view_order))
        self.assertEqual(edit_order, sorted(edit_order))

        self.assertIn("Test Case #7", view)
        self.assertIn("Edit Test Case #7", edit)

    async def test_missing_description_says_so(self):
        self._ready(ApiResponse(status_code=HTTPStatus.OK, body={
            "id": 7, "name": "Login works", "case_type_id": 9,
            "description": None}))
        text = await self._text(await self._get())
        self.assertIn("No description", text)
        self.assertNotIn("None", text)

    async def test_unknown_type_shows_the_placeholder(self):
        self._ready(ApiResponse(status_code=HTTPStatus.OK, body={
            "id": 7, "name": "Login works", "case_type_id": 777,
            "description": "d"}))
        text = await self._text(await self._get())
        self.assertRegex(text, r'id="testcase-view-type">Unknown<')

    async def test_case_types_unavailable_still_renders(self):
        self._ready(case_types=ApiResponse(status_code=503))
        response = await self._get()
        self.assertEqual(response.status_code, 200)
        self.assertRegex(await self._text(response),
                         r'id="testcase-view-type">Unknown<')

    async def test_the_gateway_is_asked_for_that_test_case_in_that_project(
            self):
        self._ready()
        await self._get()
        self.mock_rest_client.get.assert_any_call(_TESTCASE_URL)

    async def test_missing_test_case_returns_to_the_list(self):
        self._ready(ApiResponse(status_code=HTTPStatus.NOT_FOUND, body={}))
        text = await self._text(await self._get())
        self.assertIn(_REDIRECT_TO_LIST, text)

    async def test_a_member_whose_role_cannot_read_is_told_so(self):
        """On the project (its own page loads) but refused the test case:
        a plain message and a way back, not a silent trip to the dashboard."""
        self._ready(ApiResponse(status_code=HTTPStatus.FORBIDDEN, body={}))
        text = await self._text(await self._get())
        self.assertIn('id="no-permission-message"', text)
        self.assertIn("have permission to view the test cases", text)
        self.assertIn('href="/1/overview"', text)
        self.assertIn("Zephyr Project", text)
        self.assertNotIn(_REDIRECT_TO_DASHBOARD, text)
        self.assertNotIn("testcase-view-title", text)

    async def test_not_a_member_goes_to_the_dashboard(self):
        """Not on the project at all: nothing naming it is shown."""
        self._gateway_gets({
            _TESTCASE_URL: ApiResponse(status_code=HTTPStatus.FORBIDDEN),
            _PROJECT_URL: ApiResponse(status_code=HTTPStatus.FORBIDDEN),
            _CASE_TYPES_URL: _CASE_TYPES_OK})
        text = await self._text(await self._get())
        self.assertIn(_REDIRECT_TO_DASHBOARD, text)
        self.assertNotIn('id="no-permission-message"', text)

    async def test_gateway_failure_shows_the_error_page(self):
        self._ready(ApiResponse(status_code=HTTPStatus.INTERNAL_SERVER_ERROR))
        text = await self._text(await self._get())
        self.assertNotIn("testcase-view-title", text)

    async def test_unexpected_body_shows_the_error_page(self):
        self._ready(ApiResponse(status_code=HTTPStatus.OK, body=[1, 2]))
        text = await self._text(await self._get())
        self.assertNotIn("testcase-view-title", text)

    async def test_html_in_the_description_is_escaped(self):
        self._ready(ApiResponse(status_code=HTTPStatus.OK, body={
            "id": 7, "name": "N", "case_type_id": 9,
            "description": "<script>alert(1)</script>"}))
        text = await self._text(await self._get())
        self.assertNotIn("<script>alert(1)</script>", text)
        self.assertIn("&lt;script&gt;", text)


# ---------------------------------------------------------------------------
# Add: the empty form
# ---------------------------------------------------------------------------

class TestAddTestcaseForm(_FormPageTestCase):

    async def _get(self):
        async with self.client as c:
            return await c.get("/1/testcases/add", headers=_AUTH_HEADERS)

    async def test_renders_the_add_form(self):
        self._gateway_gets({_PROJECT_URL: _PROJECT_OK,
                            _CASE_TYPES_URL: _CASE_TYPES_OK})
        response = await self._get()
        self.assertEqual(response.status_code, 200)
        text = await self._text(response)
        self.assertIn("Add Test Case", text)
        self.assertIn('action="/1/testcases/add"', text)
        self.assertIn("Zephyr Project", text)
        self.assertIn('name="name"', text)
        self.assertIn('name="description"', text)

    async def test_a_reader_is_told_they_cannot_add_instead_of_the_form(self):
        self._gateway_gets({
            _PROJECT_URL: _PROJECT_OK, _CASE_TYPES_URL: _CASE_TYPES_OK,
            _PERMISSIONS_URL: _permissions(add_modify=False, delete=False)})
        text = await self._text(await self._get())
        self.assertIn('id="no-permission-message"', text)
        self.assertIn("have permission to add test cases", text)
        self.assertIn('href="/1/testcases"', text)
        self.assertIn("Zephyr Project", text)
        self.assertNotIn('id="testcaseForm"', text)

    async def test_a_role_that_can_add_gets_the_form(self):
        self._gateway_gets({_PROJECT_URL: _PROJECT_OK,
                            _CASE_TYPES_URL: _CASE_TYPES_OK,
                            _PERMISSIONS_URL: _permissions(delete=False)})
        text = await self._text(await self._get())
        self.assertIn('id="testcaseForm"', text)
        self.assertNotIn('id="no-permission-message"', text)

    async def test_not_a_member_goes_to_the_dashboard(self):
        """Not on the project at all: the dashboard, with nothing naming it."""
        self._gateway_gets({
            _PROJECT_URL: ApiResponse(status_code=HTTPStatus.FORBIDDEN),
            _CASE_TYPES_URL: _CASE_TYPES_OK,
            _PERMISSIONS_URL: _permissions(False, False, False)})
        text = await self._text(await self._get())
        self.assertIn(_REDIRECT_TO_DASHBOARD, text)
        self.assertNotIn('id="no-permission-message"', text)

    async def test_if_the_permissions_cannot_be_had_the_form_is_withheld(self):
        """Fails closed: not knowing is not a reason to show the form."""
        self._gateway_gets({_PROJECT_URL: _PROJECT_OK,
                            _CASE_TYPES_URL: _CASE_TYPES_OK,
                            _PERMISSIONS_URL: RuntimeError("boom")})
        text = await self._text(await self._get())
        self.assertIn('id="no-permission-message"', text)
        self.assertNotIn('id="testcaseForm"', text)

    async def test_type_dropdown_lists_every_type_and_marks_the_default(self):
        self._gateway_gets({_PROJECT_URL: _PROJECT_OK,
                            _CASE_TYPES_URL: _CASE_TYPES_OK})
        text = await self._text(await self._get())
        self.assertIn("Smoke", text)
        self.assertIn("Other (Default)", text)

    async def test_default_type_is_preselected(self):
        self._gateway_gets({_PROJECT_URL: _PROJECT_OK,
                            _CASE_TYPES_URL: _CASE_TYPES_OK})
        text = await self._text(await self._get())
        self.assertRegex(text, r'<option value="15"\s+selected>')
        self.assertNotRegex(text, r'<option value="9"\s+selected>')

    def _ready_with_sections(self, sections=_SECTIONS_OK):
        self._gateway_gets({_PROJECT_URL: _PROJECT_OK,
                            _CASE_TYPES_URL: _CASE_TYPES_OK,
                            _SECTIONS_URL: sections})

    async def test_section_dropdown_starts_on_no_section(self):
        self._ready_with_sections()
        text = await self._text(await self._get())
        self.assertIn('for="tc-section"', text)
        self.assertRegex(text, r'<option value=""\s+selected>\(No section\)')
        self.assertNotRegex(text, r'<option value="[0-9]+"\s+selected>\s*'
                                  r'(Regression|Smoke|Performance|Login)')

    async def test_sections_are_listed_in_tree_order_with_indentation(self):
        self._ready_with_sections()
        text = await self._text(await self._get())
        order = [text.index(f'<option value="{i}"') for i in (1, 2, 4, 3)]
        self.assertEqual(order, sorted(order))
        self.assertRegex(text, r'value="1"[^>]*>\s*Regression\s*</option>')
        self.assertRegex(
            text, '<option value="2"[^>]*>\\s*\u00a0{4}Smoke\\s*</option>')
        self.assertRegex(
            text, '<option value="4"[^>]*>\\s*\u00a0{8}Login\\s*</option>')

    async def test_sections_unavailable_says_no_section_will_be_used(self):
        for bad in (ApiResponse(status_code=503),
                    ApiResponse(status_code=HTTPStatus.OK,
                                body={"unexpected": 1}),
                    ApiResponse(status_code=HTTPStatus.OK,
                                body={"folders": "nope"}),
                    ApiResponse(status_code=HTTPStatus.OK, body=[1, 2]),
                    RuntimeError("boom")):
            with self.subTest(bad=bad):
                self._ready_with_sections(bad)
                response = await self._get()
                self.assertEqual(response.status_code, 200)
                text = await self._text(response)
                self.assertIn("The sections could not be loaded", text)
                self.assertNotIn('id="tc-section"', text)

    async def test_no_sections_in_the_project_offers_only_no_section(self):
        self._ready_with_sections(ApiResponse(
            status_code=HTTPStatus.OK,
            body={"folders": [], "test_cases": []}))
        text = await self._text(await self._get())
        self.assertEqual(text.count('name="folder_id"'), 1)
        # Look only inside the Section dropdown (the Type one has options
        # of its own).
        match = re.search(r'name="folder_id">(.*?)</select>', text, re.S)
        self.assertIsNotNone(match)
        self.assertEqual(match.group(1).count("<option"), 1)
        self.assertIn("(No section)", match.group(1))

    async def test_the_sections_are_asked_for_in_this_project(self):
        self._ready_with_sections()
        await self._get()
        self.mock_rest_client.get.assert_any_call(_SECTIONS_URL)

    async def test_cancel_goes_back_to_the_list(self):
        self._gateway_gets({_PROJECT_URL: _PROJECT_OK,
                            _CASE_TYPES_URL: _CASE_TYPES_OK})
        text = await self._text(await self._get())
        self.assertIn('href="/1/testcases"', text)

    async def test_buttons_are_inside_the_card_and_use_the_site_colours(self):
        """Save is the navy primary button, Cancel the matching outline
        button, and both sit in the card under the fields (not floating
        below it)."""
        self._gateway_gets({_PROJECT_URL: _PROJECT_OK,
                            _CASE_TYPES_URL: _CASE_TYPES_OK})
        text = await self._text(await self._get())
        self.assertRegex(
            text, r'(?s)testcase-form-card">.*?testcase-form-actions">'
                  r'\s*<button type="submit" class="btn btn-header">'
                  r'Add Test Case</button>\s*'
                  r'<a href="/1/testcases" class="btn btn-header-outline">'
                  r'Cancel</a>\s*</div>\s*</div>\s*</form>')
        self.assertNotIn("btn-primary", text)
        self.assertNotIn("btn-outline-secondary", text)

    async def test_case_types_unavailable_says_the_default_will_be_used(self):
        self._gateway_gets({
            _PROJECT_URL: _PROJECT_OK,
            _CASE_TYPES_URL: ApiResponse(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR)})
        text = await self._text(await self._get())
        self.assertIn("The case types could not be loaded", text)
        self.assertIn("The default type will be used", text)
        self.assertNotIn('id="tc-case-type"', text)

    async def test_case_types_non_list_body_is_treated_as_unavailable(self):
        self._gateway_gets({
            _PROJECT_URL: _PROJECT_OK,
            _CASE_TYPES_URL: ApiResponse(status_code=HTTPStatus.OK,
                                         body={"unexpected": 1})})
        text = await self._text(await self._get())
        self.assertIn("The case types could not be loaded", text)

    async def test_case_types_exception_is_treated_as_unavailable(self):
        self._gateway_gets({_PROJECT_URL: _PROJECT_OK,
                            _CASE_TYPES_URL: RuntimeError("boom")})
        response = await self._get()
        self.assertEqual(response.status_code, 200)
        self.assertIn("The case types could not be loaded",
                      await self._text(response))

    async def test_project_name_lookup_failure_falls_back(self):
        self._gateway_gets({
            _PROJECT_URL: ApiResponse(status_code=503),
            _CASE_TYPES_URL: _CASE_TYPES_OK})
        text = await self._text(await self._get())
        self.assertIn("Unknown Project", text)

    async def test_no_session_does_not_render_the_form(self):
        self.mock_rest_client.post.return_value = ApiResponse(
            status_code=HTTPStatus.OK, body={"status": "INVALID"})
        async with self.client as c:
            response = await c.get("/1/testcases/add")
        self.assertNotIn('id="testcaseForm"', await self._text(response))


# ---------------------------------------------------------------------------
# Add: submitting
# ---------------------------------------------------------------------------

class TestAddTestcaseSubmit(_FormPageTestCase):

    async def _post(self, form):
        async with self.client as c:
            return await c.post("/1/testcases/add", form=form,
                                headers=_AUTH_HEADERS)

    def _ready(self, gateway_post, sections=_SECTIONS_OK):
        self._session_then(gateway_post)
        self._gateway_gets({_PROJECT_URL: _PROJECT_OK,
                            _CASE_TYPES_URL: _CASE_TYPES_OK,
                            _SECTIONS_URL: sections})

    async def test_section_choice_is_posted_as_the_folder(self):
        self._ready(ApiResponse(status_code=HTTPStatus.OK,
                                body={"testcase_id": 3}))
        await self._post({"name": "Login", "case_type_id": "9",
                          "folder_id": "2"})
        sent = self.mock_rest_client.post.call_args_list[1].kwargs[
            "json_data"]
        self.assertEqual(sent["folder_id"], 2)

    async def test_no_section_chosen_posts_a_null_folder(self):
        for form in ({"name": "A", "folder_id": ""}, {"name": "A"}):
            with self.subTest(form=form):
                self.mock_rest_client.post.reset_mock()
                self._ready(ApiResponse(status_code=HTTPStatus.OK, body={}))
                await self._post(form)
                sent = self.mock_rest_client.post.call_args_list[1].kwargs[
                    "json_data"]
                self.assertIsNone(sent["folder_id"])

    async def test_a_bad_section_is_refused_without_calling_the_gateway(
            self):
        for bad in ("abc", "-1", "1.5", "2; DROP"):
            with self.subTest(section=bad):
                self.mock_rest_client.post.reset_mock()
                self._ready(ApiResponse(status_code=HTTPStatus.OK, body={}))
                response = await self._post({
                    "name": "Kept name", "description": "Kept text",
                    "case_type_id": "9", "folder_id": bad})
                text = await self._text(response)
                self.assertIn("Invalid section.", text)
                self.assertIn('value="Kept name"', text)
                self.assertIn("Kept text", text)
                # Only the session check - never a gateway create.
                self.assertEqual(self.mock_rest_client.post.call_count, 1)

    async def test_failure_keeps_the_chosen_section_selected(self):
        self._ready(ApiResponse(
            status_code=HTTPStatus.CONFLICT,
            body={"error": "Test case name already exists"}))
        text = await self._text(await self._post({
            "name": "Login", "case_type_id": "9", "folder_id": "2"}))
        self.assertIn("Test case name already exists", text)
        self.assertRegex(text, r'<option value="2"\s+selected>')
        self.assertIn('id="tc-section"', text)

    async def test_posts_to_the_gateway_with_no_folder(self):
        self._ready(ApiResponse(status_code=HTTPStatus.OK,
                                body={"testcase_id": 3}))
        await self._post({"name": "Login", "description": "d",
                          "case_type_id": "9"})
        call = self.mock_rest_client.post.call_args_list[1]
        self.assertEqual(call.args[0], "http://gateway/web/1/testcases")
        self.assertEqual(call.kwargs["json_data"], {
            "name": "Login", "description": "d", "case_type_id": 9,
            "folder_id": None})

    async def test_no_project_id_is_sent_in_the_body(self):
        """The gateway takes the project from the URL and rejects it in the
        body."""
        self._ready(ApiResponse(status_code=HTTPStatus.OK, body={}))
        await self._post({"name": "Login", "case_type_id": "9"})
        sent = self.mock_rest_client.post.call_args_list[1].kwargs["json_data"]
        self.assertNotIn("project_id", sent)

    async def test_blank_or_missing_type_is_left_out_of_the_body(self):
        for form in ({"name": "A", "case_type_id": ""},
                     {"name": "A", "case_type_id": "abc"},
                     {"name": "A"}):
            with self.subTest(form=form):
                self.mock_rest_client.post.reset_mock()
                self._ready(ApiResponse(status_code=HTTPStatus.OK, body={}))
                await self._post(form)
                sent = self.mock_rest_client.post.call_args_list[
                    1].kwargs["json_data"]
                self.assertNotIn("case_type_id", sent)

    async def test_success_returns_to_the_list(self):
        self._ready(ApiResponse(status_code=HTTPStatus.OK,
                                body={"testcase_id": 3}))
        response = await self._post({"name": "Login", "case_type_id": "9"})
        self.assertEqual(response.status_code, 200)
        text = await self._text(response)
        self.assertIn(_REDIRECT_TO_LIST, text)
        self.assertNotIn('id="testcaseForm"', text)

    async def test_refused_by_the_role_says_so_and_keeps_the_input(self):
        """A 403 means the role does not allow adding. What was typed is not
        thrown away, and the person is not silently sent to the dashboard."""
        self._ready(ApiResponse(status_code=HTTPStatus.FORBIDDEN,
                                body={"error": "Forbidden"}))
        response = await self._post({
            "name": "Login", "description": "My description",
            "case_type_id": "9"})
        self.assertEqual(response.status_code, 200)
        text = await self._text(response)
        self.assertIn("have permission to add test cases", text)
        self.assertIn('id="testcaseForm"', text)
        self.assertIn('value="Login"', text)
        self.assertIn("My description", text)
        self.assertNotIn(_REDIRECT_TO_DASHBOARD, text)

    async def test_duplicate_name_shows_the_banner_and_keeps_the_input(self):
        self._ready(ApiResponse(
            status_code=HTTPStatus.CONFLICT,
            body={"error": "Test case name already exists"}))
        response = await self._post({
            "name": "Login", "description": "My description",
            "case_type_id": "9"})
        self.assertEqual(response.status_code, 200)
        text = await self._text(response)
        self.assertIn("Test case name already exists", text)
        self.assertIn('value="Login"', text)
        self.assertIn("My description", text)
        self.assertRegex(text, r'<option value="9"\s+selected>')

    async def test_validation_error_message_is_shown(self):
        self._ready(ApiResponse(status_code=HTTPStatus.BAD_REQUEST,
                                body={"error": "Invalid JSON body"}))
        text = await self._text(await self._post({"name": "   "}))
        self.assertIn("Invalid JSON body", text)

    async def test_failure_without_a_message_shows_the_fallback(self):
        self._ready(ApiResponse(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR, body={}))
        text = await self._text(await self._post({"name": "Login"}))
        self.assertIn("The request could not be completed", text)


# ---------------------------------------------------------------------------
# Edit: the filled form
# ---------------------------------------------------------------------------

class TestEditTestcaseForm(_FormPageTestCase):

    async def _get(self):
        async with self.client as c:
            return await c.get("/1/testcases/7/edit", headers=_AUTH_HEADERS)

    def _ready(self, testcase=_TESTCASE_OK, permissions=_PERMISSIONS_ALL):
        self._gateway_gets({_TESTCASE_URL: testcase,
                            _PROJECT_URL: _PROJECT_OK,
                            _CASE_TYPES_URL: _CASE_TYPES_OK,
                            _PERMISSIONS_URL: permissions})

    async def test_form_is_filled_with_the_current_values(self):
        self._ready()
        response = await self._get()
        self.assertEqual(response.status_code, 200)
        text = await self._text(response)
        self.assertIn("Edit Test Case", text)
        self.assertIn('action="/1/testcases/7/edit"', text)
        self.assertIn('value="Login works"', text)
        self.assertIn("Check the login.", text)

    async def test_current_type_is_selected_not_the_default(self):
        self._ready()
        text = await self._text(await self._get())
        self.assertRegex(text, r'<option value="9"\s+selected>')
        self.assertNotRegex(text, r'<option value="15"\s+selected>')

    @staticmethod
    def _main_form(text):
        """The edit form's own HTML: everything before the Move box."""
        return text.split('id="testcase-move-card"')[0]

    @staticmethod
    def _move_box(text):
        return text.split('id="testcase-move-card"')[1]

    async def test_the_edit_form_shows_the_section_but_does_not_change_it(
            self):
        """Moving is its own action: the section is text in the edit form,
        never a field it would send."""
        self._ready(testcase=_testcase_in(2))
        text = await self._text(await self._get())
        main = self._main_form(text)
        self.assertRegex(main, r'id="tc-section-current">Regression / Smoke<')
        self.assertNotIn('name="folder_id"', main)
        self.assertNotIn('<select class="form-select" id="tc-section"', main)

    async def test_a_test_case_with_no_section_says_so_on_the_edit_page(
            self):
        self._ready()
        text = await self._text(await self._get())
        self.assertRegex(text, r'id="tc-section-current">\(No section\)<')

    async def test_section_row_sits_between_description_and_type(self):
        """Mirrors the view page and the Add page."""
        self._ready()
        text = await self._text(await self._get())
        self.assertLess(text.index('id="tc-description"'),
                        text.index('id="tc-section-current"'))
        self.assertLess(text.index('id="tc-section-current"'),
                        text.index('id="tc-case-type"'))

    async def test_the_move_box_posts_to_the_move_address(self):
        self._ready()
        text = await self._text(await self._get())
        box = self._move_box(text)
        self.assertIn('id="moveTestcaseForm"', box)
        self.assertIn('action="/1/testcases/7/move"', box)
        self.assertIn('id="move-testcase-btn"', box)
        self.assertIn('name="folder_id"', box)

    async def test_the_move_box_is_a_separate_form_from_the_edit_form(self):
        self._ready()
        text = await self._text(await self._get())
        self.assertEqual(text.count("<form"), 2)
        self.assertLess(text.index('id="testcaseForm"'),
                        text.index('id="moveTestcaseForm"'))
        # The first form is closed before the second opens.
        self.assertLess(text.index("</form>"),
                        text.index('id="moveTestcaseForm"'))

    async def test_the_move_dropdown_lists_every_section_in_tree_order(self):
        self._ready()
        box = self._move_box(await self._text(await self._get()))
        values = re.findall(r'<option value="(\d*)"', box)
        self.assertEqual(values, ["", "1", "2", "4", "3"])
        self.assertIn("(No section)", box)
        self.assertIn("Regression", box)

    async def test_the_move_dropdown_starts_on_where_the_test_case_is(self):
        self._ready(testcase=_testcase_in(2))
        box = self._move_box(await self._text(await self._get()))
        self.assertRegex(box, r'<option value="2"\s+selected>')
        self.assertNotRegex(box, r'<option value=""\s+selected>')

    async def test_the_move_dropdown_starts_on_no_section_for_the_top_level(
            self):
        self._ready()
        box = self._move_box(await self._text(await self._get()))
        self.assertRegex(box, r'<option value=""\s+selected>')

    async def test_with_no_sections_the_move_box_offers_only_no_section(self):
        self._gateway_gets({
            _TESTCASE_URL: _TESTCASE_OK, _PROJECT_URL: _PROJECT_OK,
            _CASE_TYPES_URL: _CASE_TYPES_OK,
            _SECTIONS_URL: ApiResponse(status_code=200, body={
                "folders": [], "test_cases": []})})
        box = self._move_box(await self._text(await self._get()))
        self.assertEqual(re.findall(r'<option value="(\d*)"', box), [""])

    async def test_if_the_sections_cannot_be_read_the_move_box_says_so(self):
        """The rest of the page still works; only the move is withheld."""
        for bad in (ApiResponse(status_code=503),
                    RuntimeError("gateway down")):
            with self.subTest(sections=bad):
                self._gateway_gets({
                    _TESTCASE_URL: _testcase_in(2),
                    _PROJECT_URL: _PROJECT_OK,
                    _CASE_TYPES_URL: _CASE_TYPES_OK,
                    _SECTIONS_URL: bad})
                response = await self._get()
                self.assertEqual(response.status_code, 200)
                text = await self._text(response)
                self.assertIn('id="tc-move-unavailable"', text)
                self.assertNotIn('id="moveTestcaseForm"', text)
                self.assertIn('id="testcaseForm"', text)
                self.assertRegex(
                    text, r'id="tc-section-current"><span class="text-muted">'
                          r'Unavailable</span>')

    async def test_a_reader_gets_neither_the_form_nor_the_move_box(self):
        self._ready(permissions=_permissions(add_modify=False, delete=False))
        text = await self._text(await self._get())
        self.assertNotIn('id="testcase-move-card"', text)
        self.assertNotIn('id="moveTestcaseForm"', text)

    async def test_adding_has_no_move_box(self):
        self._gateway_gets({_PROJECT_URL: _PROJECT_OK,
                            _CASE_TYPES_URL: _CASE_TYPES_OK})
        async with self.client as c:
            response = await c.get("/1/testcases/add", headers=_AUTH_HEADERS)
        text = await self._text(response)
        self.assertNotIn('id="testcase-move-card"', text)
        self.assertNotIn("tc-section-current", text)
        # Adding still chooses the section in its own form.
        self.assertIn('id="tc-section"', text)

    async def test_missing_description_shows_as_empty(self):
        self._ready(ApiResponse(status_code=HTTPStatus.OK, body={
            "id": 7, "name": "Login works", "case_type_id": 9,
            "description": None}))
        text = await self._text(await self._get())
        self.assertNotIn("None", text)

    async def test_the_gateway_is_asked_for_that_test_case_in_that_project(
            self):
        self._ready()
        await self._get()
        self.mock_rest_client.get.assert_any_call(_TESTCASE_URL)

    async def test_missing_test_case_returns_to_the_list(self):
        self._ready(ApiResponse(status_code=HTTPStatus.NOT_FOUND,
                                body={"error": "Test case not found"}))
        text = await self._text(await self._get())
        self.assertIn(_REDIRECT_TO_LIST, text)

    async def test_a_member_whose_role_cannot_read_is_told_so(self):
        self._ready(ApiResponse(status_code=HTTPStatus.FORBIDDEN, body={}))
        text = await self._text(await self._get())
        self.assertIn('id="no-permission-message"', text)
        self.assertIn("have permission to view the test cases", text)
        self.assertNotIn(_REDIRECT_TO_DASHBOARD, text)
        self.assertNotIn('id="testcaseForm"', text)

    async def test_not_a_member_goes_to_the_dashboard(self):
        self._gateway_gets({
            _TESTCASE_URL: ApiResponse(status_code=HTTPStatus.FORBIDDEN),
            _PROJECT_URL: ApiResponse(status_code=HTTPStatus.FORBIDDEN),
            _CASE_TYPES_URL: _CASE_TYPES_OK})
        text = await self._text(await self._get())
        self.assertIn(_REDIRECT_TO_DASHBOARD, text)

    async def test_a_reader_is_told_they_cannot_edit_instead_of_the_form(self):
        """Typing the Edit address by hand: a form that could be filled in
        but never saved is not shown."""
        self._ready(permissions=_permissions(add_modify=False, delete=False))
        text = await self._text(await self._get())
        self.assertIn('id="no-permission-message"', text)
        self.assertIn("have permission to edit test cases", text)
        self.assertIn('href="/1/testcases/7"', text)
        self.assertIn("Back to the test case", text)
        self.assertNotIn('id="testcaseForm"', text)
        self.assertNotIn("<textarea", text)

    async def test_a_role_that_can_edit_gets_the_form(self):
        self._ready(permissions=_permissions(delete=False))
        text = await self._text(await self._get())
        self.assertIn('id="testcaseForm"', text)
        self.assertNotIn('id="no-permission-message"', text)

    async def test_not_a_member_cannot_see_even_the_edit_message(self):
        """Can read the test case somehow but is not a member: nothing
        naming the project."""
        self._gateway_gets({
            _TESTCASE_URL: _TESTCASE_OK,
            _PROJECT_URL: ApiResponse(status_code=HTTPStatus.FORBIDDEN),
            _CASE_TYPES_URL: _CASE_TYPES_OK,
            _PERMISSIONS_URL: _permissions(False, False, False)})
        text = await self._text(await self._get())
        self.assertIn(_REDIRECT_TO_DASHBOARD, text)

    async def test_if_the_permissions_cannot_be_had_the_form_is_withheld(self):
        """Fails closed: not knowing is not a reason to show the form."""
        self._ready(permissions=ApiResponse(status_code=503))
        text = await self._text(await self._get())
        self.assertIn('id="no-permission-message"', text)
        self.assertNotIn('id="testcaseForm"', text)

    async def test_gateway_failure_shows_the_error_page(self):
        self._ready(ApiResponse(status_code=HTTPStatus.INTERNAL_SERVER_ERROR))
        text = await self._text(await self._get())
        self.assertNotIn('id="testcaseForm"', text)

    async def test_unexpected_body_shows_the_error_page(self):
        self._ready(ApiResponse(status_code=HTTPStatus.OK, body=[1, 2]))
        text = await self._text(await self._get())
        self.assertNotIn('id="testcaseForm"', text)

    async def test_case_types_unavailable_says_the_type_is_unchanged(self):
        self._gateway_gets({
            _TESTCASE_URL: _TESTCASE_OK, _PROJECT_URL: _PROJECT_OK,
            _CASE_TYPES_URL: ApiResponse(status_code=503)})
        text = await self._text(await self._get())
        self.assertIn("The type will be left unchanged", text)


# ---------------------------------------------------------------------------
# Edit: submitting
# ---------------------------------------------------------------------------

class TestEditTestcaseSubmit(_FormPageTestCase):

    async def _post(self, form):
        async with self.client as c:
            return await c.post("/1/testcases/7/edit", form=form,
                                headers=_AUTH_HEADERS)

    def _ready(self, patch_response, testcase=_testcase_in(2)):
        self.mock_rest_client.patch.return_value = patch_response
        self._gateway_gets({_PROJECT_URL: _PROJECT_OK,
                            _CASE_TYPES_URL: _CASE_TYPES_OK,
                            _TESTCASE_URL: testcase})

    async def test_a_failed_save_still_shows_the_section_and_the_move_box(
            self):
        self._ready(ApiResponse(
            status_code=HTTPStatus.CONFLICT,
            body={"error": "Test case name already exists"}))
        text = await self._text(await self._post({
            "name": "Taken", "description": "Kept text",
            "case_type_id": "15"}))
        self.assertRegex(text, r'id="tc-section-current">Regression / Smoke<')
        self.assertIn('id="moveTestcaseForm"', text)
        self.assertRegex(text, r'<option value="2"\s+selected>')

    async def test_a_failed_save_survives_not_being_able_to_re_read_it(self):
        """The typed input must not be lost to a second failure."""
        for bad in (ApiResponse(status_code=503), RuntimeError("down")):
            with self.subTest(re_read=bad):
                self._ready(ApiResponse(
                    status_code=HTTPStatus.CONFLICT,
                    body={"error": "Test case name already exists"}),
                    testcase=bad)
                text = await self._text(await self._post({
                    "name": "Taken", "description": "Kept text",
                    "case_type_id": "15"}))
                self.assertIn("Test case name already exists", text)
                self.assertIn('value="Taken"', text)
                self.assertIn("Kept text", text)
                self.assertRegex(
                    text, r'id="tc-section-current"><span class="text-muted">'
                          r'Unavailable</span>')

    async def test_patches_the_gateway_with_the_project_in_the_url(self):
        self._ready(ApiResponse(status_code=HTTPStatus.OK, body={"status": 1}))
        await self._post({"name": "New", "description": "d",
                          "case_type_id": "15"})
        self.mock_rest_client.patch.assert_awaited_once_with(
            _TESTCASE_URL,
            json_data={"name": "New", "description": "d",
                       "case_type_id": 15})

    async def test_no_folder_is_sent_when_editing(self):
        self._ready(ApiResponse(status_code=HTTPStatus.OK, body={}))
        await self._post({"name": "New", "case_type_id": "9"})
        sent = self.mock_rest_client.patch.call_args.kwargs["json_data"]
        self.assertNotIn("folder_id", sent)

    async def test_unusable_type_is_left_out_so_it_stays_unchanged(self):
        self._ready(ApiResponse(status_code=HTTPStatus.OK, body={}))
        await self._post({"name": "New"})
        sent = self.mock_rest_client.patch.call_args.kwargs["json_data"]
        self.assertNotIn("case_type_id", sent)

    async def test_success_returns_to_the_list(self):
        self._ready(ApiResponse(status_code=HTTPStatus.OK, body={"status": 1}))
        text = await self._text(await self._post({"name": "New"}))
        self.assertIn(_REDIRECT_TO_LIST, text)

    async def test_refused_by_the_role_says_so_and_keeps_the_input(self):
        self._ready(ApiResponse(status_code=HTTPStatus.FORBIDDEN, body={}))
        response = await self._post({
            "name": "Renamed", "description": "Kept text",
            "case_type_id": "9"})
        self.assertEqual(response.status_code, 200)
        text = await self._text(response)
        self.assertIn("have permission to edit test cases", text)
        self.assertIn('id="testcaseForm"', text)
        self.assertIn('value="Renamed"', text)
        self.assertIn("Kept text", text)
        self.assertIn('action="/1/testcases/7/edit"', text)
        self.assertNotIn(_REDIRECT_TO_DASHBOARD, text)

    async def test_missing_test_case_shows_the_banner(self):
        self._ready(ApiResponse(status_code=HTTPStatus.NOT_FOUND,
                                body={"error": "Test case not found"}))
        text = await self._text(await self._post({"name": "New"}))
        self.assertIn("Test case not found", text)
        self.assertIn('id="testcaseForm"', text)

    async def test_duplicate_name_shows_the_banner_and_keeps_the_input(self):
        self._ready(ApiResponse(
            status_code=HTTPStatus.CONFLICT,
            body={"error": "Test case name already exists"}))
        text = await self._text(await self._post({
            "name": "Taken", "description": "Kept text",
            "case_type_id": "15"}))
        self.assertIn("Test case name already exists", text)
        self.assertIn('value="Taken"', text)
        self.assertIn("Kept text", text)
        self.assertRegex(text, r'<option value="15"\s+selected>')
        self.assertIn('action="/1/testcases/7/edit"', text)


# ---------------------------------------------------------------------------
# Move: submitting
# ---------------------------------------------------------------------------

class TestMoveTestcaseSubmit(_FormPageTestCase):

    async def _post(self, form):
        async with self.client as c:
            return await c.post("/1/testcases/7/move", form=form,
                                headers=_AUTH_HEADERS)

    def _ready(self, move_response, testcase=_testcase_in(2),
               permissions=_PERMISSIONS_ALL):
        self._session_then(move_response)
        self._gateway_gets({_PROJECT_URL: _PROJECT_OK,
                            _CASE_TYPES_URL: _CASE_TYPES_OK,
                            _TESTCASE_URL: testcase,
                            _PERMISSIONS_URL: permissions})

    def _moves_sent(self):
        """The gateway move calls (the first POST is the session check)."""
        return self.mock_rest_client.post.call_args_list[1:]

    async def test_posts_the_chosen_section_to_the_gateway_move_route(self):
        self._ready(ApiResponse(status_code=HTTPStatus.OK, body={"status": 1}))
        await self._post({"folder_id": "3"})
        (call,) = self._moves_sent()
        self.assertEqual(call.args[0], _MOVE_URL)
        self.assertEqual(call.kwargs["json_data"], {"folder_id": 3})

    async def test_choosing_no_section_posts_null_for_the_top_level(self):
        for form in ({"folder_id": ""}, {}):
            with self.subTest(form=form):
                self.mock_rest_client.post.reset_mock()
                self._ready(ApiResponse(status_code=HTTPStatus.OK, body={}))
                await self._post(form)
                (call,) = self._moves_sent()
                self.assertEqual(call.kwargs["json_data"],
                                 {"folder_id": None})

    async def test_nothing_but_the_section_is_sent(self):
        """The edit form is a different form: a move never carries its
        name, description or type."""
        self._ready(ApiResponse(status_code=HTTPStatus.OK, body={}))
        await self._post({"folder_id": "3", "name": "x", "description": "y",
                          "case_type_id": "9"})
        (call,) = self._moves_sent()
        self.assertEqual(call.kwargs["json_data"], {"folder_id": 3})
        self.mock_rest_client.patch.assert_not_called()

    async def test_success_returns_to_the_list(self):
        self._ready(ApiResponse(status_code=HTTPStatus.OK, body={"status": 1}))
        text = await self._text(await self._post({"folder_id": "3"}))
        self.assertIn(_REDIRECT_TO_LIST, text)

    async def test_a_bad_section_is_refused_without_calling_the_gateway(self):
        for bad in ("abc", "-1", "1.5", "2; DROP"):
            with self.subTest(section=bad):
                self.mock_rest_client.post.reset_mock()
                self._ready(ApiResponse(status_code=HTTPStatus.OK, body={}))
                text = await self._text(await self._post({"folder_id": bad}))
                self.assertIn("Invalid section.", text)
                self.assertIn('id="moveTestcaseForm"', text)
                self.assertEqual(self._moves_sent(), [])

    async def test_a_name_clash_says_so_and_keeps_the_chosen_section(self):
        self._ready(ApiResponse(
            status_code=HTTPStatus.CONFLICT,
            body={"error": "Test case name already exists in the "
                           "destination"}))
        response = await self._post({"folder_id": "3"})
        self.assertEqual(response.status_code, 200)
        text = await self._text(response)
        self.assertIn("Test case name already exists in the destination",
                      text)
        self.assertIn('id="testcase-form-error"', text)
        # Back on the Edit page, the chosen section still selected...
        box = text.split('id="testcase-move-card"')[1]
        self.assertRegex(box, r'<option value="3"\s+selected>')
        self.assertNotRegex(box, r'<option value="2"\s+selected>')
        # ... and the test case as it is really saved, not as typed.
        self.assertIn('value="Login works"', text)
        self.assertRegex(text, r'id="tc-section-current">Regression / Smoke<')
        self.assertNotIn(_REDIRECT_TO_LIST, text)

    async def test_choosing_no_section_is_kept_after_a_failure(self):
        self._ready(ApiResponse(
            status_code=HTTPStatus.CONFLICT, body={"error": "clash"}))
        text = await self._text(await self._post({"folder_id": ""}))
        box = text.split('id="testcase-move-card"')[1]
        self.assertRegex(box, r'<option value=""\s+selected>')

    async def test_a_refusal_by_the_role_says_so(self):
        self._ready(ApiResponse(status_code=HTTPStatus.FORBIDDEN, body={}))
        response = await self._post({"folder_id": "3"})
        self.assertEqual(response.status_code, 200)
        text = await self._text(response)
        self.assertIn("have permission to move test cases", text)
        self.assertIn('id="testcaseForm"', text)
        self.assertNotIn(_REDIRECT_TO_DASHBOARD, text)

    async def test_a_section_that_has_gone_says_so(self):
        self._ready(ApiResponse(
            status_code=HTTPStatus.NOT_FOUND,
            body={"error": "Folder id is invalid"}))
        text = await self._text(await self._post({"folder_id": "3"}))
        self.assertIn("That section no longer exists", text)
        self.assertNotIn("Folder id is invalid", text)
        self.assertIn('id="moveTestcaseForm"', text)

    async def test_a_test_case_that_has_gone_returns_to_the_list(self):
        self._ready(
            ApiResponse(status_code=HTTPStatus.NOT_FOUND,
                        body={"error": "Test case not found"}),
            testcase=ApiResponse(status_code=HTTPStatus.NOT_FOUND,
                                 body={"error": "Test case not found"}))
        text = await self._text(await self._post({"folder_id": "3"}))
        self.assertIn(_REDIRECT_TO_LIST, text)
        self.assertNotIn("That section no longer exists", text)

    async def test_other_gateway_errors_are_shown(self):
        for status, body, shown in (
                (500, {"error": "CMS service unavailable"},
                 "CMS service unavailable"),
                (400, {"error": "Folder does not belong to the specified "
                                "project"},
                 "Folder does not belong to the specified project"),
                (500, None, "The request could not be completed")):
            with self.subTest(status=status, body=body):
                self._ready(ApiResponse(status_code=status, body=body))
                text = await self._text(await self._post({"folder_id": "3"}))
                self.assertIn(shown, text)
                self.assertIn('id="moveTestcaseForm"', text)

    async def test_if_it_can_no_longer_be_read_a_no_permission_page_is_shown(
            self):
        """Moving was refused and the test case can no longer be read at all
        (the role was changed meanwhile): the usual no-permission page, not
        a half-empty Edit page."""
        self._ready(
            ApiResponse(status_code=HTTPStatus.FORBIDDEN, body={}),
            testcase=ApiResponse(status_code=HTTPStatus.FORBIDDEN, body={}))
        text = await self._text(await self._post({"folder_id": "3"}))
        self.assertIn('id="no-permission-message"', text)
        self.assertNotIn('id="moveTestcaseForm"', text)

    async def test_the_failed_page_still_works_when_the_sections_fail(self):
        self._session_then(ApiResponse(
            status_code=HTTPStatus.CONFLICT, body={"error": "clash"}))
        self._gateway_gets({_PROJECT_URL: _PROJECT_OK,
                            _CASE_TYPES_URL: _CASE_TYPES_OK,
                            _TESTCASE_URL: _testcase_in(2),
                            _SECTIONS_URL: ApiResponse(status_code=503)})
        text = await self._text(await self._post({"folder_id": "3"}))
        self.assertIn("clash", text)
        self.assertIn('id="tc-move-unavailable"', text)


# ---------------------------------------------------------------------------
# View page: controls follow the person's permissions
# ---------------------------------------------------------------------------

class TestViewControlsFollowPermissions(_FormPageTestCase):
    """The view page's Edit and Delete. Left out of the HTML entirely when
    the person's role does not allow them; the gateway refuses either way."""

    async def _text_for(self, permissions):
        self._gateway_gets({_TESTCASE_URL: _TESTCASE_OK,
                            _PROJECT_URL: _PROJECT_OK,
                            _CASE_TYPES_URL: _CASE_TYPES_OK,
                            _PERMISSIONS_URL: permissions})
        async with self.client as c:
            response = await c.get("/1/testcases/7", headers=_AUTH_HEADERS)
        self.assertEqual(response.status_code, 200)
        return await self._text(response)

    async def test_a_reader_sees_the_test_case_but_no_edit_or_delete(self):
        text = await self._text_for(_permissions(add_modify=False,
                                                 delete=False))
        self.assertIn("Login works", text)
        self.assertIn("Back to Test Cases", text)
        self.assertNotIn('id="edit-testcase-btn"', text)
        self.assertNotIn('id="delete-testcase-btn"', text)
        self.assertNotIn('id="confirmDeleteTestcaseModal"', text)

    async def test_a_tester_can_edit_but_not_delete(self):
        text = await self._text_for(_permissions(delete=False))
        self.assertIn('id="edit-testcase-btn"', text)
        self.assertNotIn('id="delete-testcase-btn"', text)
        self.assertNotIn('id="confirmDeleteTestcaseModal"', text)

    async def test_a_lead_can_edit_and_delete(self):
        text = await self._text_for(_permissions())
        self.assertIn('id="edit-testcase-btn"', text)
        self.assertIn('id="delete-testcase-btn"', text)
        self.assertIn('id="confirmDeleteTestcaseModal"', text)

    async def test_each_control_follows_its_own_permission(self):
        text = await self._text_for(_permissions(add_modify=False))
        self.assertNotIn('id="edit-testcase-btn"', text)
        self.assertIn('id="delete-testcase-btn"', text)

    async def test_if_it_cannot_find_out_it_offers_nothing(self):
        cannot_find_out = {
            "gateway error": ApiResponse(status_code=503),
            "unreachable": ApiResponse(exception_msg="connection refused"),
            "raises": RuntimeError("boom"),
            "malformed": ApiResponse(status_code=HTTPStatus.OK, body={}),
            "string true": ApiResponse(
                status_code=HTTPStatus.OK,
                body={"areas": {"test_cases": {
                    "read": "true", "add_modify": "true",
                    "delete": "true"}}}),
        }
        for label, permissions in cannot_find_out.items():
            with self.subTest(label):
                text = await self._text_for(permissions)
                self.assertIn("Login works", text)
                self.assertNotIn('id="edit-testcase-btn"', text)
                self.assertNotIn('id="delete-testcase-btn"', text)


if __name__ == "__main__":
    unittest.main()
