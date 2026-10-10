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
import json
import unittest
from unittest.mock import AsyncMock, MagicMock
from http import HTTPStatus
from weaver_framework.microservice.api_response import ApiResponse
from _test_utils import make_app
from items.services.items_web_portal.page_handlers.admin.\
    admin_customisations_page_handler import AdminCustomisationsPageHandler

_LOGGER = MagicMock()
_AUTH_HEADERS = {"Cookie": "items_token=abc; items_user=bob"}
_SESSION_VALID = ApiResponse(
    status_code=HTTPStatus.OK,
    body={"status": "VALID", "is_administrator": True})


def _config():
    config = MagicMock()
    config.apis_gateway_svc = "http://gateway/"
    return config


def _metadata():
    metadata = MagicMock()
    metadata.instance_name = "INSTANCE"
    return metadata


def _row(field_id=1, field_name="Priority", description="desc",
        system_name="priority", field_type="Dropdown", entry_type="user",
        enabled=1, position=1, is_required=0, default_value="Medium",
        applies_to_all=1, linked_projects=None):
    """Build a positional case-field row matching the API column order."""
    return [field_id, field_name, description, system_name, field_type,
           entry_type, enabled, position, is_required, default_value,
           applies_to_all, linked_projects]


_FIELDS_LIST_OK = ApiResponse(status_code=HTTPStatus.OK, body=[_row()])
_PROJECTS_OK = ApiResponse(
    status_code=HTTPStatus.OK,
    body={"projects": [{"id": 1, "name": "Alpha"}, {"id": 2, "name": "Beta"}]})
_CASE_TYPES = [
    {"id": 1, "name": "Smoke", "description": "Quick sanity checks",
     "is_default": False},
    {"id": 2, "name": "Other", "description": "Anything else",
     "is_default": True},
]
_CASE_TYPES_OK = ApiResponse(status_code=HTTPStatus.OK, body=_CASE_TYPES)


class TestCustomisationsRead(unittest.IsolatedAsyncioTestCase):
    """Tests for AdminCustomisationsPageHandler.customisations (GET)."""

    async def asyncSetUp(self):
        self.mock_rest_client = AsyncMock()
        self.mock_rest_client.post.return_value = _SESSION_VALID
        handler = AdminCustomisationsPageHandler(
            _LOGGER, _config(), self.mock_rest_client, _metadata())

        app = make_app()

        @app.route("/admin/customisations", methods=["GET"])
        async def get_route():
            return await handler.customisations()

        self.client = app.test_client()

    async def _get(self, headers=_AUTH_HEADERS):
        async with self.client as c:
            return await c.get("/admin/customisations", headers=headers)

    async def test_not_authenticated_redirects(self):
        response = await self._get(headers={})
        self.assertEqual(response.status_code, 200)
        text = await response.get_data(as_text=True)
        self.assertIn("Refresh", text)

    async def test_success_renders_page_with_fields(self):
        self.mock_rest_client.get.side_effect = [_FIELDS_LIST_OK, _PROJECTS_OK, _CASE_TYPES_OK]
        response = await self._get()
        self.assertEqual(response.status_code, 200)
        text = await response.get_data(as_text=True)
        self.assertIn("Priority", text)
        self.assertIn("Alpha", text)

    async def test_fields_list_failure_renders_internal_error(self):
        self.mock_rest_client.get.side_effect = [
            ApiResponse(status_code=HTTPStatus.INTERNAL_SERVER_ERROR)]
        response = await self._get()
        self.assertEqual(response.status_code, 200)
        text = await response.get_data(as_text=True)
        self.assertNotIn("Priority", text)
        # Only the fields-list call happened - never reached the projects call.
        self.assertEqual(self.mock_rest_client.get.call_count, 1)

    async def test_projects_fetch_non_200_still_renders_page(self):
        self.mock_rest_client.get.side_effect = [
            _FIELDS_LIST_OK,
            ApiResponse(status_code=HTTPStatus.INTERNAL_SERVER_ERROR),
            _CASE_TYPES_OK]
        response = await self._get()
        self.assertEqual(response.status_code, 200)
        text = await response.get_data(as_text=True)
        self.assertIn("Priority", text)

    async def test_projects_fetch_exception_still_renders_page(self):
        self.mock_rest_client.get.side_effect = [
            _FIELDS_LIST_OK, RuntimeError("boom"), _CASE_TYPES_OK]
        response = await self._get()
        self.assertEqual(response.status_code, 200)
        text = await response.get_data(as_text=True)
        self.assertIn("Priority", text)


class TestCaseFieldAdd(unittest.IsolatedAsyncioTestCase):
    """Tests for AdminCustomisationsPageHandler.case_field_add (POST)."""

    async def asyncSetUp(self):
        self.mock_rest_client = AsyncMock()
        handler = AdminCustomisationsPageHandler(
            _LOGGER, _config(), self.mock_rest_client, _metadata())

        app = make_app()

        @app.route("/admin/customisations/case_fields", methods=["POST"])
        async def post_route():
            return await handler.case_field_add()

        self.client = app.test_client()

    async def _post(self, form):
        async with self.client as c:
            return await c.post("/admin/customisations/case_fields",
                               form=form, headers=_AUTH_HEADERS)

    async def test_applies_to_all_true_omits_projects_key(self):
        self.mock_rest_client.post.side_effect = [
            _SESSION_VALID, ApiResponse(status_code=HTTPStatus.OK)]
        self.mock_rest_client.get.side_effect = [_FIELDS_LIST_OK, _PROJECTS_OK, _CASE_TYPES_OK]

        await self._post({
            "field_name": "New Field", "system_name": "new_field",
            "field_type": "String", "applies_to_all_projects": "on",
            "enabled": "on",
        })

        payload = self.mock_rest_client.post.call_args_list[1].kwargs["json_data"]
        self.assertNotIn("projects", payload)
        self.assertTrue(payload["applies_to_all_projects"])
        self.assertTrue(payload["enabled"])
        self.assertFalse(payload["is_required"])

    async def test_applies_to_all_false_includes_selected_projects(self):
        self.mock_rest_client.post.side_effect = [
            _SESSION_VALID, ApiResponse(status_code=HTTPStatus.OK)]
        self.mock_rest_client.get.side_effect = [_FIELDS_LIST_OK, _PROJECTS_OK, _CASE_TYPES_OK]

        async with self.client as c:
            response = await c.post(
                "/admin/customisations/case_fields",
                form=[
                    ("field_name", "New Field"),
                    ("system_name", "new_field"),
                    ("field_type", "String"),
                    ("projects", "Alpha"),
                    ("projects", "Beta"),
                ],
                headers=_AUTH_HEADERS)
        self.assertEqual(response.status_code, 200)

        payload = self.mock_rest_client.post.call_args_list[1].kwargs["json_data"]
        self.assertFalse(payload["applies_to_all_projects"])
        self.assertEqual(payload["projects"], ["Alpha", "Beta"])

    async def test_success_rerenders_page(self):
        self.mock_rest_client.post.side_effect = [
            _SESSION_VALID, ApiResponse(status_code=HTTPStatus.OK)]
        self.mock_rest_client.get.side_effect = [_FIELDS_LIST_OK, _PROJECTS_OK, _CASE_TYPES_OK]

        response = await self._post({
            "field_name": "New Field", "system_name": "new_field",
            "field_type": "String"})
        self.assertEqual(response.status_code, 200)
        text = await response.get_data(as_text=True)
        self.assertIn("Priority", text)

    async def test_failure_shows_error_banner_from_body(self):
        self.mock_rest_client.post.side_effect = [
            _SESSION_VALID,
            ApiResponse(status_code=HTTPStatus.CONFLICT,
                       body={"error": "already exists"})]
        self.mock_rest_client.get.side_effect = [_FIELDS_LIST_OK, _PROJECTS_OK, _CASE_TYPES_OK]

        response = await self._post({
            "field_name": "New Field", "system_name": "new_field",
            "field_type": "String"})
        self.assertEqual(response.status_code, 200)
        text = await response.get_data(as_text=True)
        self.assertIn("already exists", text)

    async def test_failure_shows_fallback_message_without_error_key(self):
        self.mock_rest_client.post.side_effect = [
            _SESSION_VALID,
            ApiResponse(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, body={})]
        self.mock_rest_client.get.side_effect = [_FIELDS_LIST_OK, _PROJECTS_OK, _CASE_TYPES_OK]

        response = await self._post({
            "field_name": "New Field", "system_name": "new_field",
            "field_type": "String"})
        self.assertEqual(response.status_code, 200)
        text = await response.get_data(as_text=True)
        self.assertIn("The request could not be completed", text)


class TestCaseFieldModify(unittest.IsolatedAsyncioTestCase):
    """Tests for AdminCustomisationsPageHandler.case_field_modify (POST)."""

    async def asyncSetUp(self):
        self.mock_rest_client = AsyncMock()
        self.mock_rest_client.post.return_value = _SESSION_VALID
        handler = AdminCustomisationsPageHandler(
            _LOGGER, _config(), self.mock_rest_client, _metadata())

        app = make_app()

        @app.route("/admin/customisations/case_fields/<int:field_id>/modify",
                  methods=["POST"])
        async def post_route(field_id):
            return await handler.case_field_modify(field_id)

        self.client = app.test_client()

    async def _post(self, field_id, form):
        async with self.client as c:
            return await c.post(
                f"/admin/customisations/case_fields/{field_id}/modify",
                form=form, headers=_AUTH_HEADERS)

    async def test_non_system_field_uses_submitted_form_values(self):
        current_row = _row(field_id=1, field_name="Old Name", entry_type="user")
        self.mock_rest_client.get.side_effect = [
            ApiResponse(status_code=HTTPStatus.OK, body=current_row),
            _FIELDS_LIST_OK, _PROJECTS_OK, _CASE_TYPES_OK]
        self.mock_rest_client.put.return_value = ApiResponse(
            status_code=HTTPStatus.OK)

        await self._post(1, {
            "field_name": "New Name", "system_name": "new_name",
            "field_type": "String", "default_value": "abc"})

        payload = self.mock_rest_client.put.call_args.kwargs["json_data"]
        self.assertEqual(payload["field_name"], "New Name")
        self.assertEqual(payload["system_name"], "new_name")
        self.assertEqual(payload["default_value"], "abc")

    async def test_system_field_locks_immutable_attributes(self):
        current_row = _row(field_id=2, field_name="Milestone",
                           system_name="milestone", field_type="String",
                           description="System field", default_value="",
                           is_required=1, entry_type="system")
        self.mock_rest_client.get.side_effect = [
            ApiResponse(status_code=HTTPStatus.OK, body=current_row),
            _FIELDS_LIST_OK, _PROJECTS_OK, _CASE_TYPES_OK]
        self.mock_rest_client.put.return_value = ApiResponse(
            status_code=HTTPStatus.BAD_REQUEST,
            body={"error": "System custom fields cannot be modified"})

        # Attempt to smuggle different values through the form for fields
        # that should be locked - they must not reach the payload.
        await self._post(2, {
            "field_name": "Hacked Name", "system_name": "hacked_name",
            "field_type": "Integer", "default_value": "999",
            "enabled": "on"})

        payload = self.mock_rest_client.put.call_args.kwargs["json_data"]
        self.assertEqual(payload["field_name"], "Milestone")
        self.assertEqual(payload["system_name"], "milestone")
        self.assertEqual(payload["field_type"], "String")
        self.assertEqual(payload["default_value"], "")
        self.assertTrue(payload["is_required"])
        self.assertTrue(payload["enabled"])

    async def test_current_fetch_failure_falls_back_to_form_payload(self):
        self.mock_rest_client.get.side_effect = [
            ApiResponse(status_code=HTTPStatus.NOT_FOUND),
            _FIELDS_LIST_OK, _PROJECTS_OK, _CASE_TYPES_OK]
        self.mock_rest_client.put.return_value = ApiResponse(
            status_code=HTTPStatus.NOT_FOUND, body={"error": "not found"})

        response = await self._post(999, {
            "field_name": "New Name", "system_name": "new_name",
            "field_type": "String"})
        self.assertEqual(response.status_code, 200)

        payload = self.mock_rest_client.put.call_args.kwargs["json_data"]
        self.assertEqual(payload["field_name"], "New Name")

    async def test_success_rerenders_page(self):
        current_row = _row(field_id=1, entry_type="user")
        self.mock_rest_client.get.side_effect = [
            ApiResponse(status_code=HTTPStatus.OK, body=current_row),
            _FIELDS_LIST_OK, _PROJECTS_OK, _CASE_TYPES_OK]
        self.mock_rest_client.put.return_value = ApiResponse(
            status_code=HTTPStatus.OK)

        response = await self._post(1, {
            "field_name": "New Name", "system_name": "new_name",
            "field_type": "String"})
        self.assertEqual(response.status_code, 200)
        text = await response.get_data(as_text=True)
        self.assertIn("Priority", text)

    async def test_failure_shows_error_banner(self):
        current_row = _row(field_id=1, entry_type="user")
        self.mock_rest_client.get.side_effect = [
            ApiResponse(status_code=HTTPStatus.OK, body=current_row),
            _FIELDS_LIST_OK, _PROJECTS_OK, _CASE_TYPES_OK]
        self.mock_rest_client.put.return_value = ApiResponse(
            status_code=HTTPStatus.CONFLICT, body={"error": "name taken"})

        response = await self._post(1, {
            "field_name": "New Name", "system_name": "new_name",
            "field_type": "String"})
        self.assertEqual(response.status_code, 200)
        text = await response.get_data(as_text=True)
        self.assertIn("name taken", text)


class TestCaseFieldDelete(unittest.IsolatedAsyncioTestCase):
    """Tests for AdminCustomisationsPageHandler.case_field_delete (POST)."""

    async def asyncSetUp(self):
        self.mock_rest_client = AsyncMock()
        self.mock_rest_client.post.return_value = _SESSION_VALID
        handler = AdminCustomisationsPageHandler(
            _LOGGER, _config(), self.mock_rest_client, _metadata())

        app = make_app()

        @app.route("/admin/customisations/case_fields/<int:field_id>/delete",
                  methods=["POST"])
        async def post_route(field_id):
            return await handler.case_field_delete(field_id)

        self.client = app.test_client()

    async def _post(self, field_id):
        async with self.client as c:
            return await c.post(
                f"/admin/customisations/case_fields/{field_id}/delete",
                headers=_AUTH_HEADERS)

    async def test_success_rerenders_page(self):
        self.mock_rest_client.delete.return_value = ApiResponse(
            status_code=HTTPStatus.OK)
        self.mock_rest_client.get.side_effect = [_FIELDS_LIST_OK, _PROJECTS_OK, _CASE_TYPES_OK]

        response = await self._post(1)
        self.assertEqual(response.status_code, 200)
        text = await response.get_data(as_text=True)
        self.assertIn("Priority", text)

    async def test_failure_shows_error_banner(self):
        self.mock_rest_client.delete.return_value = ApiResponse(
            status_code=HTTPStatus.BAD_REQUEST,
            body={"error": "System custom fields cannot be deleted"})
        self.mock_rest_client.get.side_effect = [_FIELDS_LIST_OK, _PROJECTS_OK, _CASE_TYPES_OK]

        response = await self._post(1)
        self.assertEqual(response.status_code, 200)
        text = await response.get_data(as_text=True)
        self.assertIn("System custom fields cannot be deleted", text)


class TestCaseFieldMove(unittest.IsolatedAsyncioTestCase):
    """Tests for AdminCustomisationsPageHandler.case_field_move (POST)."""

    async def asyncSetUp(self):
        self.mock_rest_client = AsyncMock()
        self.mock_rest_client.post.return_value = _SESSION_VALID
        handler = AdminCustomisationsPageHandler(
            _LOGGER, _config(), self.mock_rest_client, _metadata())

        app = make_app()

        @app.route("/admin/customisations/case_fields/<int:field_id>/move",
                  methods=["POST"])
        async def post_route(field_id):
            return await handler.case_field_move(field_id)

        self.client = app.test_client()

    async def _post(self, field_id, direction):
        async with self.client as c:
            return await c.post(
                f"/admin/customisations/case_fields/{field_id}/move",
                form={"direction": direction}, headers=_AUTH_HEADERS)

    async def test_direction_passed_through_to_gateway(self):
        self.mock_rest_client.patch.return_value = ApiResponse(
            status_code=HTTPStatus.OK)
        self.mock_rest_client.get.side_effect = [_FIELDS_LIST_OK, _PROJECTS_OK, _CASE_TYPES_OK]

        response = await self._post(1, "up")
        self.assertEqual(response.status_code, 200)

        payload = self.mock_rest_client.patch.call_args.kwargs["json_data"]
        self.assertEqual(payload, {"direction": "up"})

    async def test_failure_shows_error_banner(self):
        self.mock_rest_client.patch.return_value = ApiResponse(
            status_code=HTTPStatus.BAD_REQUEST,
            body={"error": "already at the boundary"})
        self.mock_rest_client.get.side_effect = [_FIELDS_LIST_OK, _PROJECTS_OK, _CASE_TYPES_OK]

        response = await self._post(1, "up")
        self.assertEqual(response.status_code, 200)
        text = await response.get_data(as_text=True)
        self.assertIn("already at the boundary", text)


class TestRowToField(unittest.TestCase):
    """Direct unit tests for the _row_to_field mapping helper."""

    def test_maps_scalar_columns(self):
        field = AdminCustomisationsPageHandler._row_to_field(
            _row(field_id=7, field_name="Severity", field_type="Integer",
                is_required=1, applies_to_all=0))
        self.assertEqual(field["id"], 7)
        self.assertEqual(field["field_name"], "Severity")
        self.assertEqual(field["field_type"], "Integer")
        self.assertTrue(field["is_required"])
        self.assertFalse(field["applies_to_all_projects"])

    def test_is_system_true_for_system_entry_type(self):
        field = AdminCustomisationsPageHandler._row_to_field(
            _row(entry_type="system"))
        self.assertTrue(field["is_system"])

    def test_is_system_false_for_user_entry_type(self):
        field = AdminCustomisationsPageHandler._row_to_field(
            _row(entry_type="user"))
        self.assertFalse(field["is_system"])

    def test_no_linked_projects_when_none(self):
        field = AdminCustomisationsPageHandler._row_to_field(
            _row(linked_projects=None))
        self.assertEqual(field["linked_projects"], [])
        self.assertEqual(field["linked_projects_json"], "[]")

    def test_parses_multiple_linked_projects(self):
        field = AdminCustomisationsPageHandler._row_to_field(
            _row(linked_projects="1:Alpha,2:Beta"))
        self.assertEqual(field["linked_projects"], ["Alpha", "Beta"])
        self.assertEqual(json.loads(field["linked_projects_json"]),
                         ["Alpha", "Beta"])

    def test_linked_projects_json_survives_a_comma_in_a_single_name(self):
        # A single linked project whose name contains a comma still parses
        # correctly once split out of the raw CMS string (only ambiguous
        # once there are multiple linked projects - see the code comment).
        field = AdminCustomisationsPageHandler._row_to_field(
            _row(linked_projects="1:Acme Inc"))
        self.assertEqual(json.loads(field["linked_projects_json"]),
                         ["Acme Inc"])


class TestCaseTypesTab(unittest.IsolatedAsyncioTestCase):
    """Tests for the Case Types tab rendered by customisations (GET)."""

    async def asyncSetUp(self):
        self.mock_rest_client = AsyncMock()
        self.mock_rest_client.post.return_value = _SESSION_VALID
        handler = AdminCustomisationsPageHandler(
            _LOGGER, _config(), self.mock_rest_client, _metadata())

        app = make_app()

        @app.route("/admin/customisations", methods=["GET"])
        async def get_route():
            return await handler.customisations()

        self.client = app.test_client()

    async def _get_text(self, case_types_response):
        self.mock_rest_client.get.side_effect = [
            _FIELDS_LIST_OK, _PROJECTS_OK, case_types_response]
        async with self.client as c:
            response = await c.get("/admin/customisations",
                                   headers=_AUTH_HEADERS)
        self.assertEqual(response.status_code, 200)
        return await response.get_data(as_text=True)

    async def test_case_types_are_listed_with_descriptions(self):
        text = await self._get_text(_CASE_TYPES_OK)
        self.assertIn("Smoke", text)
        self.assertIn("Quick sanity checks", text)
        self.assertIn("Other", text)

    async def test_gateway_url_for_case_types(self):
        await self._get_text(_CASE_TYPES_OK)
        self.mock_rest_client.get.assert_any_call(
            "http://gateway/web/case_types")

    async def test_only_the_default_is_marked_default(self):
        text = await self._get_text(_CASE_TYPES_OK)
        self.assertEqual(text.count("(Default)"), 1)

    async def test_default_type_has_no_delete_control(self):
        """Only the non-default type gets the (disabled) delete button."""
        text = await self._get_text(_CASE_TYPES_OK)
        self.assertEqual(text.count("delete-case-type-btn"), 1)

    async def test_delete_control_is_disabled_with_a_tooltip(self):
        text = await self._get_text(_CASE_TYPES_OK)
        self.assertIn("Deleting case types isn't available yet", text)
        self.assertRegex(text, r'delete-case-type-btn"\s+disabled')

    async def test_edit_button_carries_the_row_data(self):
        text = await self._get_text(_CASE_TYPES_OK)
        self.assertIn('data-id="2"', text)
        self.assertIn('data-name="Other"', text)
        self.assertIn('data-is-default="1"', text)
        self.assertIn('data-is-default="0"', text)

    async def test_name_and_pencil_both_open_the_edit_modal(self):
        """Each row has two edit entry points: the name link and the
        pencil. Both must target the modal and carry the row's data."""
        text = await self._get_text(_CASE_TYPES_OK)
        # Two rows x (name link + pencil).
        self.assertEqual(text.count("edit-case-type-btn"), 4)
        # Those four, plus the "+ Add Type" button.
        self.assertEqual(text.count('data-bs-target="#caseTypeModal"'), 5)
        self.assertEqual(text.count('data-name="Smoke"'), 2)
        self.assertEqual(text.count('data-name="Other"'), 2)
        self.assertRegex(
            text, r'case-type-name edit-case-type-btn"[^>]*>Smoke</button>')

    async def test_empty_list_shows_message(self):
        text = await self._get_text(
            ApiResponse(status_code=HTTPStatus.OK, body=[]))
        self.assertIn("No case types defined yet.", text)

    async def test_fetch_non_200_shows_could_not_load(self):
        text = await self._get_text(
            ApiResponse(status_code=HTTPStatus.INTERNAL_SERVER_ERROR))
        self.assertIn("Case types could not be loaded", text)
        # The rest of the page still renders.
        self.assertIn("Priority", text)

    async def test_fetch_non_list_body_shows_could_not_load(self):
        text = await self._get_text(
            ApiResponse(status_code=HTTPStatus.OK, body={"unexpected": 1}))
        self.assertIn("Case types could not be loaded", text)

    async def test_fetch_exception_shows_could_not_load(self):
        text = await self._get_text(RuntimeError("boom"))
        self.assertIn("Case types could not be loaded", text)
        self.assertIn("Priority", text)

    async def test_case_fields_tab_is_active_by_default(self):
        text = await self._get_text(_CASE_TYPES_OK)
        self.assertRegex(text, r'nav-link active" id="case-fields-tab"')
        self.assertNotRegex(text, r'nav-link active" id="case-types-tab"')


class TestCaseTypeAdd(unittest.IsolatedAsyncioTestCase):
    """Tests for AdminCustomisationsPageHandler.case_type_add (POST)."""

    async def asyncSetUp(self):
        self.mock_rest_client = AsyncMock()
        handler = AdminCustomisationsPageHandler(
            _LOGGER, _config(), self.mock_rest_client, _metadata())

        app = make_app()

        @app.route("/admin/customisations/case_types", methods=["POST"])
        async def post_route():
            return await handler.case_type_add()

        self.client = app.test_client()

    async def _post(self, form):
        async with self.client as c:
            return await c.post("/admin/customisations/case_types",
                                form=form, headers=_AUTH_HEADERS)

    def _prime(self, add_response, *extra_posts):
        """Session check first, then the add call, then any later posts."""
        self.mock_rest_client.post.side_effect = [
            _SESSION_VALID, add_response, *extra_posts]
        self.mock_rest_client.get.side_effect = [
            _FIELDS_LIST_OK, _PROJECTS_OK, _CASE_TYPES_OK]

    async def test_posts_name_and_description_to_gateway(self):
        self._prime(ApiResponse(status_code=HTTPStatus.OK,
                                body={"case_type_id": 9}))
        await self._post({"name": "Exploratory",
                          "description": "Unscripted"})
        call = self.mock_rest_client.post.call_args_list[1]
        self.assertEqual(call.args[0], "http://gateway/web/case_types")
        self.assertEqual(call.kwargs["json_data"],
                         {"name": "Exploratory",
                          "description": "Unscripted"})

    async def test_is_default_is_never_sent_in_the_payload(self):
        self._prime(ApiResponse(status_code=HTTPStatus.OK,
                                body={"case_type_id": 9}),
                    ApiResponse(status_code=HTTPStatus.OK))
        await self._post({"name": "Exploratory", "is_default": "on"})
        payload = self.mock_rest_client.post.call_args_list[1].kwargs[
            "json_data"]
        self.assertNotIn("is_default", payload)

    async def test_default_unticked_makes_no_set_default_call(self):
        self._prime(ApiResponse(status_code=HTTPStatus.OK,
                                body={"case_type_id": 9}))
        await self._post({"name": "Exploratory"})
        # session check + add only
        self.assertEqual(self.mock_rest_client.post.call_count, 2)

    async def test_default_ticked_calls_set_default_with_new_id(self):
        self._prime(ApiResponse(status_code=HTTPStatus.OK,
                                body={"case_type_id": 9}),
                    ApiResponse(status_code=HTTPStatus.OK))
        await self._post({"name": "Exploratory", "is_default": "on"})
        self.assertEqual(self.mock_rest_client.post.call_count, 3)
        self.assertEqual(
            self.mock_rest_client.post.call_args_list[2].args[0],
            "http://gateway/web/case_types/9/set_default")

    async def test_default_ticked_but_no_id_returned_skips_set_default(self):
        self._prime(ApiResponse(status_code=HTTPStatus.OK, body={}))
        response = await self._post({"name": "Exploratory",
                                     "is_default": "on"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.mock_rest_client.post.call_count, 2)

    async def test_failed_add_does_not_call_set_default(self):
        self._prime(ApiResponse(status_code=HTTPStatus.CONFLICT,
                                body={"error": "already exists"}))
        response = await self._post({"name": "Smoke", "is_default": "on"})
        text = await response.get_data(as_text=True)
        self.assertIn("already exists", text)
        self.assertEqual(self.mock_rest_client.post.call_count, 2)

    async def test_set_default_failure_reports_partial_success(self):
        self._prime(ApiResponse(status_code=HTTPStatus.OK,
                                body={"case_type_id": 9}),
                    ApiResponse(status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                                body={"error": "boom"}))
        response = await self._post({"name": "Exploratory",
                                     "is_default": "on"})
        text = await response.get_data(as_text=True)
        self.assertIn("saved, but could not be made the default", text)
        self.assertIn("boom", text)

    async def test_result_page_stays_on_the_case_types_tab(self):
        self._prime(ApiResponse(status_code=HTTPStatus.OK,
                                body={"case_type_id": 9}))
        response = await self._post({"name": "Exploratory"})
        text = await response.get_data(as_text=True)
        self.assertRegex(text, r'nav-link active" id="case-types-tab"')
        self.assertNotRegex(text, r'nav-link active" id="case-fields-tab"')

    async def test_validation_failure_shows_error_banner(self):
        self._prime(ApiResponse(status_code=HTTPStatus.BAD_REQUEST,
                                body={"error": "name is required"}))
        response = await self._post({"name": "   "})
        text = await response.get_data(as_text=True)
        self.assertIn("name is required", text)


class TestCaseTypeModify(unittest.IsolatedAsyncioTestCase):
    """Tests for AdminCustomisationsPageHandler.case_type_modify (POST)."""

    async def asyncSetUp(self):
        self.mock_rest_client = AsyncMock()
        handler = AdminCustomisationsPageHandler(
            _LOGGER, _config(), self.mock_rest_client, _metadata())

        app = make_app()

        @app.route("/admin/customisations/case_types/<int:type_id>/modify",
                   methods=["POST"])
        async def post_route(type_id):
            return await handler.case_type_modify(type_id)

        self.client = app.test_client()

    async def _post(self, type_id, form):
        async with self.client as c:
            return await c.post(
                f"/admin/customisations/case_types/{type_id}/modify",
                form=form, headers=_AUTH_HEADERS)

    def _prime(self, patch_response, *extra_posts):
        # Session check is the first POST; set_default (if any) follows it.
        self.mock_rest_client.post.side_effect = [
            _SESSION_VALID, *extra_posts]
        self.mock_rest_client.patch.return_value = patch_response
        self.mock_rest_client.get.side_effect = [
            _FIELDS_LIST_OK, _PROJECTS_OK, _CASE_TYPES_OK]

    async def test_patches_name_and_description_to_gateway(self):
        self._prime(ApiResponse(status_code=HTTPStatus.OK))
        await self._post(4, {"name": "New", "description": "d"})
        self.mock_rest_client.patch.assert_awaited_once_with(
            "http://gateway/web/case_types/4",
            json_data={"name": "New", "description": "d"})

    async def test_default_unticked_makes_no_set_default_call(self):
        self._prime(ApiResponse(status_code=HTTPStatus.OK))
        await self._post(4, {"name": "New"})
        # Only the session-validation POST.
        self.assertEqual(self.mock_rest_client.post.call_count, 1)

    async def test_default_ticked_calls_set_default_after_patch(self):
        self._prime(ApiResponse(status_code=HTTPStatus.OK),
                    ApiResponse(status_code=HTTPStatus.OK))
        await self._post(4, {"name": "New", "is_default": "on"})
        self.assertEqual(self.mock_rest_client.post.call_count, 2)
        self.assertEqual(
            self.mock_rest_client.post.call_args_list[1].args[0],
            "http://gateway/web/case_types/4/set_default")

    async def test_failed_patch_does_not_call_set_default(self):
        self._prime(ApiResponse(status_code=HTTPStatus.CONFLICT,
                                body={"error": "already exists"}))
        response = await self._post(4, {"name": "Smoke",
                                        "is_default": "on"})
        text = await response.get_data(as_text=True)
        self.assertIn("already exists", text)
        self.assertEqual(self.mock_rest_client.post.call_count, 1)

    async def test_missing_type_shows_not_found_message(self):
        self._prime(ApiResponse(status_code=HTTPStatus.NOT_FOUND,
                                body={"error": "Case type not found"}))
        response = await self._post(99, {"name": "New"})
        text = await response.get_data(as_text=True)
        self.assertIn("Case type not found", text)

    async def test_set_default_failure_reports_partial_success(self):
        self._prime(ApiResponse(status_code=HTTPStatus.OK),
                    ApiResponse(status_code=HTTPStatus.NOT_FOUND,
                                body={"error": "Case type not found"}))
        response = await self._post(4, {"name": "New", "is_default": "on"})
        text = await response.get_data(as_text=True)
        self.assertIn("saved, but could not be made the default", text)

    async def test_result_page_stays_on_the_case_types_tab(self):
        self._prime(ApiResponse(status_code=HTTPStatus.OK))
        response = await self._post(4, {"name": "New"})
        text = await response.get_data(as_text=True)
        self.assertRegex(text, r'nav-link active" id="case-types-tab"')


if __name__ == "__main__":
    unittest.main()
