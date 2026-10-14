"""
Copyright 2025-2026 Integrated Test Management Suite Development Team
Copyright 2017-2025 INTMAC Development Team [Defunct]

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
import json
import logging
from typing import Optional
from quart import make_response, request, Response
from weaver_framework.microservice.api_response import ApiResponse
from weaver_framework.microservice.rest_client import RestClient
from items.services.items_web_portal.configuration import Configuration
from items.services.items_web_portal.decorators import require_session
from items.services.items_web_portal.metadata_settings import MetadataSettings
import items.services.items_web_portal.page_locations as pages
from items.services.items_web_portal.portal_page_handler import (
    PortalPageHandler)


# Shown in the Type column when a test case's type cannot be resolved (the
# case types could not be loaded, or the id is not in the list).
UNKNOWN_CASE_TYPE_NAME: str = "Unknown"

# Shown instead of a gateway message when it did not supply one.
_FALLBACK_ERROR: str = "The request could not be completed. Please try again."


class GetProjectTestcasesPageHandler(PortalPageHandler):
    """Handles requests for the project test cases page.

    This handler retrieves the project's test case hierarchy from the gateway
    service, transforms the returned folder and test case data into a nested
    tree structure, and renders the test cases page.

    Attributes:
        _metadata_settings (MetadataSettings):
            Metadata configuration used when rendering the page.
    """

    def __init__(self,
                 logger: logging.Logger,
                 config: Configuration,
                 rest_client: RestClient,
                 metadata: MetadataSettings):
        """Initializes the project test cases page handler.

        Args:
            logger (logging.Logger):
                Logger used for diagnostic and error messages.
            config (Configuration):
                Application configuration containing service endpoints.
            rest_client (RestClient):
                REST client used to communicate with backend services.
            metadata (MetadataSettings):
                Metadata settings used when rendering portal pages.
        """
        super().__init__(logger, config, rest_client)
        self._metadata_settings = metadata

    @require_session
    async def test_cases(self, project_id: int):
        """Renders the test cases page for a project.

        Retrieves the project's folder and test case information from the
        gateway service, transforms the flat API response into a hierarchical
        structure suitable for display, and renders the test cases page.

        A 403 (not a member of this project) or 404 (project doesn't exist)
        redirects to the dashboard rather than showing an error - both are
        normal, expected states (e.g. an admin removed the user's access
        while they still had the page bookmarked), not failures worth
        surfacing as one. Any other non-200 is treated as a genuine
        unexpected failure and returns a JSON error response with HTTP 500.

        Args:
            project_id (int):
                Unique identifier of the project.

        Returns:
            Response:
                A rendered HTML page on success, a redirect to the
                dashboard on 403/404, or a JSON error response with HTTP
                500 for any other gateway failure.
        """
        return await self._render_list(project_id)

    @require_session
    async def delete_test_case(self, project_id: int, case_id: int):
        """Delete a test case, then show the project's test case list.

        Args:
            project_id (int):
                Unique identifier of the project the test case belongs to.
            case_id (int):
                Unique identifier of the test case to delete.

        Returns:
            Response:
                A redirect to the list on success, or if the test case is
                already gone (404); a redirect to the dashboard if the user
                may not use this project (403); otherwise the list page again
                with an error banner.
        """
        gateway_svc: str = self._config.apis_gateway_svc
        response: ApiResponse = await self._rest_client.delete(
            f"{gateway_svc}web/testcases/{case_id}?project_id={project_id}")

        if response.status_code in (HTTPStatus.OK, HTTPStatus.NOT_FOUND):
            return await make_response(
                self._generate_redirect(f"{project_id}/testcases"))

        if response.status_code == HTTPStatus.FORBIDDEN:
            return await make_response(self._generate_redirect('/'))

        error_message = self._extract_error(response)
        self._logger.warning("Test case delete failed (status %s): %s",
                             response.status_code, error_message)
        return await self._render_list(project_id,
                                       error_message=error_message)

    @require_session
    async def add_section(self, project_id: int):
        """Create a section (folder) from the submitted form.

        The form carries ``name`` and, for a sub-section, ``parent_id``;
        without a parent the section is created at the top level.

        Args:
            project_id (int):
                Unique identifier of the project to add the section to.

        Returns:
            Response:
                A redirect to the list on success; a redirect to the
                dashboard if the user may not use this project (403);
                otherwise the list page again with an error banner.
        """
        form = await request.form
        raw_parent = (form.get("parent_id") or "").strip()

        if raw_parent and not raw_parent.isdigit():
            return await self._render_list(
                project_id, error_message="Invalid parent section.")

        gateway_svc: str = self._config.apis_gateway_svc
        response: ApiResponse = await self._rest_client.post(
            f"{gateway_svc}web/{project_id}/folders",
            json_data={
                "parent_id": int(raw_parent) if raw_parent else None,
                "name": form.get("name") or ""})

        return await self._finish_section_write(response, project_id, "add")

    @require_session
    async def rename_section(self, project_id: int, folder_id: int):
        """Rename a section (folder) from the submitted form.

        Args:
            project_id (int):
                Unique identifier of the project the section belongs to.
            folder_id (int):
                Unique identifier of the section to rename.

        Returns:
            Response:
                A redirect to the list on success; a redirect to the
                dashboard if the user may not use this project (403);
                otherwise the list page again with an error banner.
        """
        form = await request.form

        gateway_svc: str = self._config.apis_gateway_svc
        response: ApiResponse = await self._rest_client.patch(
            f"{gateway_svc}web/folders/{folder_id}?project_id={project_id}",
            json_data={"name": form.get("name") or ""})

        return await self._finish_section_write(
            response, project_id, "rename")

    async def _finish_section_write(self, response: ApiResponse,
                                    project_id: int, action: str):
        """Complete a section add or rename: redirect, or show the list.

        Args:
            response (ApiResponse):
                The gateway's response to the add or rename call.
            project_id (int):
                Unique identifier of the project.
            action (str):
                Short action name for log messages ("add", "rename").

        Returns:
            Response:
                A redirect to the list on success, a redirect to the
                dashboard on 403, otherwise the list page with a banner.
        """
        if response.status_code == HTTPStatus.OK:
            return await make_response(
                self._generate_redirect(f"{project_id}/testcases"))

        if response.status_code == HTTPStatus.FORBIDDEN:
            return await make_response(self._generate_redirect('/'))

        error_message = self._extract_error(response)
        self._logger.warning("Section %s failed (status %s): %s",
                             action, response.status_code, error_message)
        return await self._render_list(project_id,
                                       error_message=error_message)

    async def _render_list(self, project_id: int,
                           error_message: Optional[str] = None):
        """Fetch the project's test cases and render the list page.

        Args:
            project_id (int):
                Unique identifier of the project.
            error_message (Optional[str]):
                Optional error banner text to show above the list.

        Returns:
            Response:
                The rendered page, a redirect to the dashboard on 403/404,
                or a JSON error response with HTTP 500 for any other gateway
                failure.
        """
        gateway_svc: str = self._config.apis_gateway_svc

        # Fetch project details to get the project name for the sidebar.
        project_url: str = f"{gateway_svc}web/projects/{project_id}"
        project_response = await self._rest_client.get(project_url)

        project_name: str = "Unknown Project"
        if project_response.status_code == HTTPStatus.OK:
            project_name = project_response.body.get("name", project_name)

        url: str = f"{gateway_svc}web/{project_id}/testcases"
        response = await self._rest_client.get(url)

        if response.status_code in (HTTPStatus.FORBIDDEN, HTTPStatus.NOT_FOUND):
            return await make_response(self._generate_redirect('/'))

        if response.status_code != HTTPStatus.OK:
            self._logger.critical("Gateway svc request invalid - Reason: %s",
                                  response.exception_msg)
            response_json = {
                "status": 0,
                'error': 'Internal error!'
            }
            return Response(json.dumps(response_json),
                            status=HTTPStatus.INTERNAL_SERVER_ERROR,
                            content_type="application/json")

        case_type_names = await self._fetch_case_type_names()
        for test_case in response.body['test_cases']:
            test_case['case_type_name'] = case_type_names.get(
                test_case.get('case_type_id'), UNKNOWN_CASE_TYPE_NAME)

        details = self._transform_tests_details_data(response.body)
        root_test_cases = [test_case for test_case
                           in response.body['test_cases']
                           if test_case['folder_id'] is None]

        return await self._render_page(
            pages.TEMPLATE_TEST_DEFINITIONS_PAGE,
            data=details,
            root_test_cases=root_test_cases,
            active_page="test-cases",
            has_testcases=len(details) > 0 or len(root_test_cases) > 0,
            project_id=project_id,
            project_name=project_name,
            instance_name=self._metadata_settings.instance_name,
            error_message=error_message)

    @staticmethod
    def _extract_error(response: ApiResponse) -> str:
        """Extract a human-readable error message from a gateway response."""
        if isinstance(response.body, dict) and response.body.get("error"):
            return str(response.body["error"])
        return _FALLBACK_ERROR

    async def _fetch_case_type_names(self) -> dict[int, str]:
        """Fetch the case types as an ``{id: name}`` lookup.

        The test case list carries only each test case's ``case_type_id``, so
        names come from the case types list. A failure here is non-fatal: the
        page still renders and shows the placeholder name for every type.

        Returns:
            A dict mapping case type id to name, empty if they could not be
            loaded.
        """
        gateway_svc: str = self._config.apis_gateway_svc
        try:
            response = await self._rest_client.get(
                f"{gateway_svc}web/case_types")
        except Exception:  # pylint: disable=broad-except
            self._logger.warning("Unable to fetch case types")
            return {}

        if response.status_code != HTTPStatus.OK or \
                not isinstance(response.body, list):
            self._logger.warning(
                "Unable to fetch case types (status %s)",
                response.status_code)
            return {}

        return {case_type['id']: case_type['name']
                for case_type in response.body}

    def _transform_tests_details_data(self, data):
        """Converts flat folder and test case data into a hierarchical tree.

        The incoming data is expected to contain two collections:

        - ``folders``: A flat list of folder objects containing ``id`` and
          ``parent_id`` fields.
        - ``test_cases``: A flat list of test case objects containing a
          ``folder_id`` reference.

        This method builds a nested folder hierarchy by linking each folder
        to its parent, then assigns each test case to its corresponding
        folder.

        Args:
            data (dict):
                API response containing ``folders`` and ``test_cases``
                collections.

        Returns:
            list[dict]:
                A list of root-level folders. Each folder contains:

                - ``subfolders``: Child folder objects.
                - ``test_cases``: Test cases belonging directly to the folder.
        """
        folder_map = {folder['id']: {**folder, 'subfolders': [],
                                     'test_cases': []}
                      for folder in data['folders']}
        root_folders = []

        # Organize folders into a tree structure
        for folder in folder_map.values():
            if folder['parent_id'] is None:
                root_folders.append(folder)
            else:
                parent = folder_map.get(folder['parent_id'])
                if parent:
                    parent['subfolders'].append(folder)

        # Assign test cases to the corresponding folder
        for test_case in data['test_cases']:
            folder = folder_map.get(test_case['folder_id'])
            if folder:
                folder['test_cases'].append(test_case)

        return root_folders
