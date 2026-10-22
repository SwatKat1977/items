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
from items.services.items_web_portal.page_handlers.testcases.\
    permission_messages import NO_ACCESS_TO_TEST_CASES, REFUSED
from items.services.items_web_portal.portal_page_handler import (
    PortalPageHandler)

# Shown instead of a gateway message when it did not supply one.
_FALLBACK_ERROR: str = "The request could not be completed. Please try again."

# What a test case with no section (the project's top level) is called.
NO_SECTION_LABEL: str = "(No section)"

# Shown when a move is refused because the chosen section has gone. (A test
# case that has gone is a redirect to the list instead.)
_SECTION_GONE: str = "That section no longer exists. Please choose another."


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
            case no longer exists; a "no permission" page if the person is on
            the project but their role cannot read test cases, or a redirect
            to the dashboard if they are not on it at all; or the internal
            error page for any other gateway failure.
        """
        testcase, early_response = await self._fetch_testcase(
            project_id, case_id)
        if early_response is not None:
            return early_response

        type_name = UNKNOWN_CASE_TYPE_NAME
        for case_type in await self._fetch_case_types() or []:
            if case_type.get("id") == testcase.get("case_type_id"):
                type_name = case_type.get("name", UNKNOWN_CASE_TYPE_NAME)

        section_name = self._describe_section(
            await self._fetch_sections(project_id), testcase.get("folder_id"))

        return await self._render_page(
            pages.TEMPLATE_TESTCASE_VIEW_PAGE,
            active_page="test-cases",
            project_id=project_id,
            project_name=await self._fetch_project_name(project_id),
            instance_name=self._metadata_settings.instance_name,
            testcase=testcase,
            case_type_name=type_name,
            section_name=section_name,
            permissions=await self._fetch_testcase_permissions(project_id))

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
            The rendered form page; or, for a person whose role does not
            allow adding test cases, a page saying so (or the dashboard if
            they are not on the project at all), instead of a form they could
            fill in but not save.
        """
        if not (await self._fetch_testcase_permissions(
                project_id))["add_modify"]:
            return await self._no_permission_or_dashboard(
                project_id, self._metadata_settings.instance_name,
                REFUSED["add_test_case"],
                f"/{project_id}/testcases", "Back to Test Cases")

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
            A redirect to the project's test case list on success, otherwise
            the form again with an error banner (which says plainly when the
            person's role does not allow adding test cases).
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
            test case no longer exists; a "no permission" page if the person
            is on the project but their role cannot read, or cannot edit,
            test cases (or the dashboard if they are not on it at all); or the
            internal error page for any other gateway failure.
        """
        testcase, early_response = await self._fetch_testcase(
            project_id, case_id)
        if early_response is not None:
            return early_response

        if not (await self._fetch_testcase_permissions(
                project_id))["add_modify"]:
            return await self._no_permission_or_dashboard(
                project_id, self._metadata_settings.instance_name,
                REFUSED["edit_test_case"],
                f"/{project_id}/testcases/{case_id}", "Back to the test case")

        return await self._render_form(
            project_id=project_id, case_id=case_id,
            case_types=await self._fetch_case_types(),
            form_data=self._saved_values(testcase), testcase=testcase)

    @require_session
    async def edit_submit(self, project_id: int, case_id: int):
        """Save changes to a test case from the submitted form.

        Args:
            project_id: ID of the project the test case belongs to.
            case_id: ID of the test case being edited.

        Returns:
            A redirect to the project's test case list on success, otherwise
            the form again with an error banner (which says plainly when the
            person's role does not allow editing test cases).
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
    # Move
    # ------------------------------------------------------------------

    @require_session
    async def move_submit(self, project_id: int, case_id: int):
        """Move a test case to the section chosen on the Edit page.

        Moving is its own action, with its own box and button on the Edit
        page, so it posts on its own: the rest of the edit form is neither
        sent nor saved.

        Args:
            project_id: ID of the project the test case belongs to.
            case_id: ID of the test case to move.

        Returns:
            A redirect to the project's test case list on success. Otherwise
            the Edit page again with an error banner and the chosen section
            still selected; or a redirect to the list if the test case has
            gone. A 403 (the person's role does not allow it) says so
            plainly, rather than quietly sending them to the dashboard.
        """
        form = await request.form
        raw_folder = (form.get("folder_id") or "").strip()

        if raw_folder and not raw_folder.isdigit():
            return await self._move_failed(
                project_id, case_id, raw_folder, "Invalid section.")

        base_url: str = self._config.apis_gateway_svc
        response: ApiResponse = await self._rest_client.post(
            f"{base_url}web/testcases/{case_id}/move?project_id={project_id}",
            json_data={"folder_id": int(raw_folder) if raw_folder else None})

        if response.status_code == HTTPStatus.OK:
            return await make_response(
                self._generate_redirect(f"{project_id}/testcases"))

        if response.status_code == HTTPStatus.FORBIDDEN:
            error_message = REFUSED["move_test_case"]
        elif response.status_code == HTTPStatus.NOT_FOUND:
            error_message = _SECTION_GONE
        else:
            error_message = self._extract_error(response)
        self._logger.warning("Test case move failed (status %s): %s",
                             response.status_code, error_message)

        return await self._move_failed(
            project_id, case_id, raw_folder, error_message)

    async def _move_failed(self, project_id: int, case_id: int,
                           chosen: str, error_message: str):
        """Show the Edit page again after a move that did not happen.

        The test case is read afresh so the page shows what is really saved
        (the move form carries nothing else), and so a test case that has
        gone is noticed and sent back to the list.

        Args:
            project_id: ID of the project.
            case_id: ID of the test case.
            chosen: The section the person picked, as submitted ("" for none),
                kept selected so they need not find it again.
            error_message: The banner text.

        Returns:
            The Edit page with the banner, or whatever ``_fetch_testcase``
            says the page should return instead (the list if the test case
            has gone, a "no permission" page if they can no longer read it).
        """
        testcase, early_response = await self._fetch_testcase(
            project_id, case_id)
        if early_response is not None:
            return early_response

        return await self._render_form(
            project_id=project_id, case_id=case_id,
            case_types=await self._fetch_case_types(),
            form_data=self._saved_values(testcase), testcase=testcase,
            move_choice=chosen, error_message=error_message)

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
            instead: for a 403, a "no permission" page if the person is on
            the project (their role cannot read test cases) or a redirect to
            the dashboard if they are not; a redirect to the test case list
            if the test case does not exist (404); or the internal error page
            for anything else.
        """
        base_url: str = self._config.apis_gateway_svc
        response: ApiResponse = await self._rest_client.get(
            f"{base_url}web/testcases/{case_id}?project_id={project_id}")

        if response.status_code == HTTPStatus.FORBIDDEN:
            return None, await self._no_permission_or_dashboard(
                project_id, self._metadata_settings.instance_name,
                NO_ACCESS_TO_TEST_CASES,
                f"/{project_id}/overview", "Back to Project Overview")

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
            A redirect on success, otherwise the form page with an error
            banner and what was typed. A 403 (the person's role does not
            allow it) says so plainly, rather than quietly sending them to the
            dashboard and losing their input.
        """
        if response.status_code == HTTPStatus.OK:
            return await make_response(
                self._generate_redirect(f"{project_id}/testcases"))

        if response.status_code == HTTPStatus.FORBIDDEN:
            error_message = REFUSED[f"{action}_test_case"]
        else:
            error_message = self._extract_error(response)
        self._logger.warning("Test case %s failed (status %s): %s",
                             action, response.status_code, error_message)

        return await self._render_form(
            project_id=project_id, case_id=case_id,
            case_types=await self._fetch_case_types(),
            sections=(await self._fetch_sections(project_id)
                      if case_id is None else None),
            form_data=self._form_values(form),
            error_message=error_message,
            testcase=(await self._fetch_testcase_quietly(project_id, case_id)
                      if case_id is not None else None))

    @staticmethod
    def _saved_values(testcase: dict) -> dict:
        """The form values for a test case as it is saved.

        Args:
            testcase: The test case as the gateway returned it.

        Returns:
            A dict with the name, description and case type to show.
        """
        return {
            "name": testcase.get("name", ""),
            "description": testcase.get("description") or "",
            "case_type_id": str(testcase.get("case_type_id", ""))}

    @staticmethod
    def _describe_section(sections: Optional[list[dict]],
                          folder_id: Optional[int]) -> Optional[str]:
        """Say which section a test case is in, as a path.

        Args:
            sections: The project's sections as ``_fetch_sections`` returns
                them, or None if they could not be loaded.
            folder_id: The test case's section, or None for the top level.

        Returns:
            ``(No section)`` for the top level, the section's path (for
            example ``Regression / Smoke``), or None if it cannot be worked
            out (the sections could not be loaded, or it is not among them).
        """
        if folder_id is None:
            return NO_SECTION_LABEL

        for section in sections or []:
            if section["id"] == folder_id:
                return section["path"]

        return None

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
            A list of ``{"id", "name", "depth", "label", "path"}`` dicts in
            tree order (``path`` is the names from the top, joined with
            `` / ``), or None if the sections could not be loaded.
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

        def walk(parent_id, depth: int, trail: str) -> None:
            for folder in children.get(parent_id, []):
                path = f"{trail} / {folder['name']}" if trail \
                    else folder["name"]
                sections.append({
                    "id": folder["id"],
                    "name": folder["name"],
                    "path": path,
                    "depth": depth,
                    "label": "    " * depth
                             + folder["name"]})
                walk(folder["id"], depth + 1, path)

        walk(None, 0, "")
        return sections

    async def _render_form(self, project_id: int, case_id: Optional[int],
                           case_types: Optional[list[dict]], form_data: dict,
                           error_message: Optional[str] = None,
                           sections: Optional[list[dict]] = None,
                           testcase: Optional[dict] = None,
                           move_choice: Optional[str] = None):
        """Render the add/edit form page.

        Args:
            project_id: ID of the project.
            case_id: ID of the test case being edited, or None when adding.
            case_types: The case types for the dropdown, or None if they
                could not be loaded.
            form_data: The values to show in the form.
            error_message: Optional error banner text.
            sections: When adding, the project's sections for the Section
                dropdown, or None if they could not be loaded. (When editing
                the sections are loaded here, for the Move box.)
            testcase: When editing, the test case as saved, which says what
                section it is in now; None if it could not be read again.
            move_choice: When editing, the section the Move box should have
                selected (``""`` for none); defaults to where the test case
                is now.

        Returns:
            The rendered page.
        """
        # pylint: disable=too-many-arguments, too-many-positional-arguments
        current_section = None
        move_selected = ""
        if case_id is not None:
            sections = await self._fetch_sections(project_id)
            folder_id = testcase.get("folder_id") if testcase else None
            if testcase is not None:
                current_section = self._describe_section(sections, folder_id)
            move_selected = move_choice if move_choice is not None \
                else ("" if folder_id is None else str(folder_id))

        return await self._render_page(
            pages.TEMPLATE_TESTCASE_FORM_PAGE,
            active_page="test-cases",
            project_id=project_id,
            project_name=await self._fetch_project_name(project_id),
            instance_name=self._metadata_settings.instance_name,
            case_id=case_id,
            case_types=case_types,
            sections=sections,
            current_section=current_section,
            move_selected=move_selected,
            form_data=form_data,
            error_message=error_message)

    async def _fetch_testcase_quietly(self, project_id: int,
                                      case_id: int) -> Optional[dict]:
        """Read a test case only to show where it is, without failing.

        Used when the Edit page is shown again after a failed save, where the
        typed input must not be lost to a second failure.

        Args:
            project_id: ID of the project.
            case_id: ID of the test case.

        Returns:
            The test case as the gateway returned it, or None if it could
            not be read.
        """
        base_url: str = self._config.apis_gateway_svc
        try:
            response: ApiResponse = await self._rest_client.get(
                f"{base_url}web/testcases/{case_id}?project_id={project_id}")
        except Exception:  # pylint: disable=broad-except
            self._logger.warning("Unable to re-read test case %s", case_id)
            return None

        if response.status_code != HTTPStatus.OK or \
                not isinstance(response.body, dict):
            return None

        return response.body

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
