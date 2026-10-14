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
from http import HTTPStatus
import logging
from typing import Optional
from quart import make_response, request
from weaver_framework.microservice.api_response import ApiResponse
from weaver_framework.microservice.rest_client import RestClient
from items.services.items_web_portal.configuration import Configuration
from items.services.items_web_portal.decorators import require_session
from items.services.items_web_portal.metadata_settings import MetadataSettings
import items.services.items_web_portal.page_locations as pages
from items.services.items_web_portal.page_handlers.testcases.\
    get_project_testcases_page_handler import UNKNOWN_CASE_TYPE_NAME
from items.services.items_web_portal.portal_page_handler import (
    PortalPageHandler)

# Shown instead of a gateway message when it did not supply one.
_FALLBACK_ERROR: str = "The request could not be completed. Please try again."


class TestcaseFormPageHandler(PortalPageHandler):
    """Handles the View, Add and Edit Test Case pages.

    Each is a full page rather than a pop-up: a test case is expected to grow
    (custom field values and more), so it needs room. Viewing is read-only,
    with an Edit button; saving a form posts it, and on success returns to
    the project's test case list; on failure the form is shown again, with
    what was typed and an error banner.

    Test cases are created at the root of the project (no folder) for now;
    sections (folders) are a later piece of work.
    """

    def __init__(self,
                 logger: logging.Logger,
                 config: Configuration,
                 rest_client: RestClient,
                 metadata: MetadataSettings):
        """Initialise the test case form page handler.

        Args:
            logger: Logger used for diagnostic and error messages.
            config: Application configuration containing service endpoints.
            rest_client: REST client used to communicate with the gateway.
            metadata: Instance metadata used when rendering portal pages.
        """
        super().__init__(logger, config, rest_client)
        self._metadata_settings = metadata

    # ------------------------------------------------------------------
    # View
    # ------------------------------------------------------------------

    @require_session
    async def view_page(self, project_id: int, case_id: int):
        """Render a test case read-only, with an Edit button.

        Args:
            project_id: ID of the project the test case belongs to.
            case_id: ID of the test case to show.

        Returns:
            The rendered page; a redirect to the test case list if the test
            case no longer exists, or to the dashboard if the user may not
            use this project; or the internal error page for any other
            gateway failure.
        """
        testcase, early_response = await self._fetch_testcase(
            project_id, case_id)
        if early_response is not None:
            return early_response

        type_name = UNKNOWN_CASE_TYPE_NAME
        for case_type in await self._fetch_case_types() or []:
            if case_type.get("id") == testcase.get("case_type_id"):
                type_name = case_type.get("name", UNKNOWN_CASE_TYPE_NAME)

        return await self._render_page(
            pages.TEMPLATE_TESTCASE_VIEW_PAGE,
            active_page="test-cases",
            project_id=project_id,
            project_name=await self._fetch_project_name(project_id),
            instance_name=self._metadata_settings.instance_name,
            testcase=testcase,
            case_type_name=type_name)

    # ------------------------------------------------------------------
    # Add
    # ------------------------------------------------------------------

    @require_session
    async def add_form(self, project_id: int):
        """Render the empty Add Test Case form.

        The case type dropdown starts on the instance's default type, and
        the section dropdown on "(No section)", the project root.

        Args:
            project_id: ID of the project the test case will be created in.

        Returns:
            The rendered form page.
        """
        case_types = await self._fetch_case_types()

        default_id = ""
        for case_type in case_types or []:
            if case_type.get("is_default"):
                default_id = str(case_type["id"])

        return await self._render_form(
            project_id=project_id, case_id=None, case_types=case_types,
            sections=await self._fetch_sections(project_id),
            form_data={"name": "", "description": "",
                       "case_type_id": default_id, "folder_id": ""})

    @require_session
    async def add_submit(self, project_id: int):
        """Create a test case from the submitted form.

        Args:
            project_id: ID of the project to create the test case in.

        Returns:
            A redirect to the project's test case list on success (or to the
            dashboard if the user may not use this project), otherwise the
            form again with an error banner.
        """
        form = await request.form

        raw_folder = (form.get("folder_id") or "").strip()
        if raw_folder and not raw_folder.isdigit():
            return await self._render_form(
                project_id=project_id, case_id=None,
                case_types=await self._fetch_case_types(),
                sections=await self._fetch_sections(project_id),
                form_data=self._form_values(form),
                error_message="Invalid section.")

        payload: dict = self._build_payload(form)
        payload["folder_id"] = int(raw_folder) if raw_folder else None

        base_url: str = self._config.apis_gateway_svc
        response: ApiResponse = await self._rest_client.post(
            f"{base_url}web/{project_id}/testcases", json_data=payload)

        return await self._finish_submit(
            response, project_id=project_id, case_id=None, form=form,
            action="add")

    # ------------------------------------------------------------------
    # Edit
    # ------------------------------------------------------------------

    @require_session
    async def edit_form(self, project_id: int, case_id: int):
        """Render the Edit Test Case form, filled with the current values.

        Args:
            project_id: ID of the project the test case belongs to.
            case_id: ID of the test case to edit.

        Returns:
            The rendered form page; a redirect to the test case list if the
            test case no longer exists, or to the dashboard if the user may
            not use this project; or the internal error page for any other
            gateway failure.
        """
        testcase, early_response = await self._fetch_testcase(
            project_id, case_id)
        if early_response is not None:
            return early_response

        case_types = await self._fetch_case_types()

        return await self._render_form(
            project_id=project_id, case_id=case_id, case_types=case_types,
            form_data={
                "name": testcase.get("name", ""),
                "description": testcase.get("description") or "",
                "case_type_id": str(testcase.get("case_type_id", ""))})

    @require_session
    async def edit_submit(self, project_id: int, case_id: int):
        """Save changes to a test case from the submitted form.

        Args:
            project_id: ID of the project the test case belongs to.
            case_id: ID of the test case being edited.

        Returns:
            A redirect to the project's test case list on success (or to the
            dashboard if the user may not use this project), otherwise the
            form again with an error banner.
        """
        form = await request.form
        payload: dict = self._build_payload(form)

        base_url: str = self._config.apis_gateway_svc
        response: ApiResponse = await self._rest_client.patch(
            f"{base_url}web/testcases/{case_id}?project_id={project_id}",
            json_data=payload)

        return await self._finish_submit(
            response, project_id=project_id, case_id=case_id, form=form,
            action="edit")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    async def _fetch_testcase(self, project_id: int, case_id: int):
        """Fetch one test case from the gateway for the view and edit pages.

        Args:
            project_id: ID of the project the test case belongs to.
            case_id: ID of the test case.

        Returns:
            ``(test_case_dict, None)`` on success. Otherwise ``(None,
            response)`` where ``response`` is what the page should return
            instead: a redirect to the dashboard if the user may not use the
            project (403), a redirect to the test case list if the test case
            does not exist (404), or the internal error page for anything
            else.
        """
        base_url: str = self._config.apis_gateway_svc
        response: ApiResponse = await self._rest_client.get(
            f"{base_url}web/testcases/{case_id}?project_id={project_id}")

        if response.status_code == HTTPStatus.FORBIDDEN:
            return None, await make_response(self._generate_redirect('/'))

        if response.status_code == HTTPStatus.NOT_FOUND:
            return None, await make_response(
                self._generate_redirect(f"{project_id}/testcases"))

        if response.status_code != HTTPStatus.OK or \
                not isinstance(response.body, dict):
            self._logger.critical(
                "Gateway svc request for test case %s failed (status %s)",
                case_id, response.status_code)
            return None, await self._render_page(
                pages.TEMPLATE_INTERNAL_ERROR_PAGE)

        return response.body, None

    @staticmethod
    def _build_payload(form) -> dict:
        """Build a gateway request body from the submitted form.

        Trimming and the required-name rule are the CMS's job; values are
        forwarded as entered. ``case_type_id`` is left out when the form did
        not carry a usable one (for example the case types could not be
        loaded), which means "default type" on create and "unchanged" on
        edit.

        Args:
            form: The submitted form.

        Returns:
            A dict with ``name``, ``description`` and, if given,
            ``case_type_id``.
        """
        payload: dict = {
            "name": form.get("name") or "",
            "description": form.get("description") or "",
        }

        raw_type_id = form.get("case_type_id") or ""
        if raw_type_id.isdigit():
            payload["case_type_id"] = int(raw_type_id)

        return payload

    async def _finish_submit(self, response: ApiResponse, project_id: int,
                             case_id: Optional[int], form, action: str):
        """Complete an add or edit: redirect on success, else show the form.

        Args:
            response: The gateway's response to the add or edit call.
            project_id: ID of the project.
            case_id: ID of the test case being edited, or None when adding.
            form: The submitted form, so its values can be shown again.
            action: Short action name for log messages ("add", "edit").

        Returns:
            A redirect, or the form page with an error banner.
        """
        if response.status_code == HTTPStatus.OK:
            return await make_response(
                self._generate_redirect(f"{project_id}/testcases"))

        if response.status_code == HTTPStatus.FORBIDDEN:
            return await make_response(self._generate_redirect('/'))

        error_message = self._extract_error(response)
        self._logger.warning("Test case %s failed (status %s): %s",
                             action, response.status_code, error_message)

        return await self._render_form(
            project_id=project_id, case_id=case_id,
            case_types=await self._fetch_case_types(),
            sections=(await self._fetch_sections(project_id)
                      if case_id is None else None),
            form_data=self._form_values(form),
            error_message=error_message)

    @staticmethod
    def _form_values(form) -> dict:
        """Collect the submitted values so the form can show them again.

        Args:
            form: The submitted form.

        Returns:
            A dict with the name, description, case type and section as
            typed or chosen.
        """
        return {
            "name": form.get("name") or "",
            "description": form.get("description") or "",
            "case_type_id": form.get("case_type_id") or "",
            "folder_id": form.get("folder_id") or ""}

    async def _fetch_sections(self,
                              project_id: int) -> Optional[list[dict]]:
        """Fetch the project's sections for the Section dropdown.

        The gateway has no read route for sections of its own: the test case
        list returns the whole folder tree, so its ``folders`` are used. They
        are flattened depth-first so each sub-section follows its parent, with
        a label indented by depth.

        A failure is non-fatal: the form still works and the test case is
        created with no section.

        Args:
            project_id: ID of the project.

        Returns:
            A list of ``{"id", "name", "depth", "label"}`` dicts in tree
            order, or None if the sections could not be loaded.
        """
        base_url: str = self._config.apis_gateway_svc
        try:
            response: ApiResponse = await self._rest_client.get(
                f"{base_url}web/{project_id}/testcases")
        except Exception:  # pylint: disable=broad-except
            self._logger.warning("Unable to fetch sections")
            return None

        if response.status_code != HTTPStatus.OK or \
                not isinstance(response.body, dict) or \
                not isinstance(response.body.get("folders"), list):
            self._logger.warning(
                "Unable to fetch sections (status %s)",
                response.status_code)
            return None

        children: dict = {}
        for folder in response.body["folders"]:
            children.setdefault(folder.get("parent_id"), []).append(folder)

        sections: list[dict] = []

        def walk(parent_id, depth: int) -> None:
            for folder in children.get(parent_id, []):
                sections.append({
                    "id": folder["id"],
                    "name": folder["name"],
                    "depth": depth,
                    "label": "    " * depth
                             + folder["name"]})
                walk(folder["id"], depth + 1)

        walk(None, 0)
        return sections

    async def _render_form(self, project_id: int, case_id: Optional[int],
                           case_types: Optional[list[dict]], form_data: dict,
                           error_message: Optional[str] = None,
                           sections: Optional[list[dict]] = None):
        """Render the add/edit form page.

        Args:
            project_id: ID of the project.
            case_id: ID of the test case being edited, or None when adding.
            case_types: The case types for the dropdown, or None if they
                could not be loaded.
            form_data: The values to show in the form.
            error_message: Optional error banner text.
            sections: The project's sections for the Section dropdown (shown
                only when adding), or None if they could not be loaded.

        Returns:
            The rendered page.
        """
        # pylint: disable=too-many-arguments, too-many-positional-arguments
        return await self._render_page(
            pages.TEMPLATE_TESTCASE_FORM_PAGE,
            active_page="test-cases",
            project_id=project_id,
            project_name=await self._fetch_project_name(project_id),
            instance_name=self._metadata_settings.instance_name,
            case_id=case_id,
            case_types=case_types,
            sections=sections,
            form_data=form_data,
            error_message=error_message)

    async def _fetch_project_name(self, project_id: int) -> str:
        """Fetch the project's name for the page's sidebar.

        Returns:
            The project's name, or "Unknown Project" if it cannot be read.
        """
        base_url: str = self._config.apis_gateway_svc
        response: ApiResponse = await self._rest_client.get(
            f"{base_url}web/projects/{project_id}")

        if response.status_code == HTTPStatus.OK and \
                isinstance(response.body, dict):
            return response.body.get("name", "Unknown Project")

        return "Unknown Project"

    async def _fetch_case_types(self) -> Optional[list[dict]]:
        """Fetch the case types for the dropdown.

        A failure is non-fatal: the form still works and leaves the type to
        the server (the default on create, unchanged on edit).

        Returns:
            The list of case type dicts, or None if they could not be loaded.
        """
        base_url: str = self._config.apis_gateway_svc
        try:
            response: ApiResponse = await self._rest_client.get(
                f"{base_url}web/case_types")
        except Exception:  # pylint: disable=broad-except
            self._logger.warning("Unable to fetch case types")
            return None

        if response.status_code != HTTPStatus.OK or \
                not isinstance(response.body, list):
            self._logger.warning(
                "Unable to fetch case types (status %s)",
                response.status_code)
            return None

        return response.body

    @staticmethod
    def _extract_error(response: ApiResponse) -> str:
        """Extract a human-readable error message from a gateway response."""
        if isinstance(response.body, dict) and response.body.get("error"):
            return str(response.body["error"])
        return _FALLBACK_ERROR
