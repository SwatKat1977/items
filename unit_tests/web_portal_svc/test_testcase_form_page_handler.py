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

_PROJECT_OK = ApiResponse(status_code=HTTPStatus.OK,
                          body={"name": "Zephyr Project"})
_CASE_TYPES_OK = ApiResponse(status_code=HTTPStatus.OK, body=[
    {"id": 9, "name": "Smoke", "description": "", "is_default": False},
    {"id": 15, "name": "Other", "description": "", "is_default": True},
])
_TESTCASE_OK = ApiResponse(status_code=HTTPStatus.OK, body={
    "id": 7, "project_id": 1, "folder_id": None, "case_type_id": 9,
    "name": "Login works", "description": "Check the login."})

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

        self.client = app.test_client()

    def _gateway_gets(self, responses: dict):
        """Answer gateway GETs by URL, so tests don't depend on call order.

        An entry that is an exception is raised; a URL not listed fails the
        test loudly.
        """
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

    def _ready(self, testcase=_TESTCASE_OK, case_types=_CASE_TYPES_OK):
        self._gateway_gets({_TESTCASE_URL: testcase,
                            _PROJECT_URL: _PROJECT_OK,
                            _CASE_TYPES_URL: case_types})

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

    async def test_not_a_member_goes_to_the_dashboard(self):
        self._ready(ApiResponse(status_code=HTTPStatus.FORBIDDEN, body={}))
        text = await self._text(await self._get())
        self.assertIn(_REDIRECT_TO_DASHBOARD, text)

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
        self.assertNotIn('<select', text)

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

    def _ready(self, gateway_post):
        self._session_then(gateway_post)
        self._gateway_gets({_PROJECT_URL: _PROJECT_OK,
                            _CASE_TYPES_URL: _CASE_TYPES_OK})

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

    async def test_not_a_member_goes_to_the_dashboard(self):
        self._ready(ApiResponse(status_code=HTTPStatus.FORBIDDEN,
                                body={"error": "Forbidden"}))
        text = await self._text(await self._post({"name": "Login"}))
        self.assertIn(_REDIRECT_TO_DASHBOARD, text)

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

    def _ready(self, testcase=_TESTCASE_OK):
        self._gateway_gets({_TESTCASE_URL: testcase,
                            _PROJECT_URL: _PROJECT_OK,
                            _CASE_TYPES_URL: _CASE_TYPES_OK})

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

    async def test_not_a_member_goes_to_the_dashboard(self):
        self._ready(ApiResponse(status_code=HTTPStatus.FORBIDDEN, body={}))
        text = await self._text(await self._get())
        self.assertIn(_REDIRECT_TO_DASHBOARD, text)

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

    def _ready(self, patch_response):
        self.mock_rest_client.patch.return_value = patch_response
        self._gateway_gets({_PROJECT_URL: _PROJECT_OK,
                            _CASE_TYPES_URL: _CASE_TYPES_OK})

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

    async def test_not_a_member_goes_to_the_dashboard(self):
        self._ready(ApiResponse(status_code=HTTPStatus.FORBIDDEN, body={}))
        text = await self._text(await self._post({"name": "New"}))
        self.assertIn(_REDIRECT_TO_DASHBOARD, text)

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


if __name__ == "__main__":
    unittest.main()
