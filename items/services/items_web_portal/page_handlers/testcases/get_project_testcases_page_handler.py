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
from quart import Response
from weaver_framework.microservice.rest_client import RestClient
from items.services.items_web_portal.configuration import Configuration
from items.services.items_web_portal.metadata_settings import MetadataSettings
import items.services.items_web_portal.page_locations as pages
from items.services.items_web_portal.portal_page_handler import (
    PortalPageHandler)


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

    async def test_cases(self, project_id: int):
        """Renders the test cases page for a project.

        Retrieves the project's folder and test case information from the
        gateway service, transforms the flat API response into a hierarchical
        structure suitable for display, and renders the test cases page.

        If the gateway service request fails, an HTTP 500 response containing
        an error payload is returned.

        Args:
            project_id (int):
                Unique identifier of the project.

        Returns:
            Response:
                A rendered HTML page on success, or a JSON error response with
                HTTP 500 status if the gateway request fails.
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

        details = self._transform_tests_details_data(response.body)

        return await self._render_page(
            pages.TEMPLATE_TEST_DEFINITIONS_PAGE,
            data=details,
            active_page="test-cases",
            has_testcases=len(details) > 0,
            project_id=project_id,
            project_name=project_name,
            instance_name=self._metadata_settings.instance_name)

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
