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
from quart import make_response, Response
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
            instance_name=self._metadata_settings.instance_name)

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
