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
from quart import Response
import logging
from items.services.items_web_portal.metadata_settings import MetadataSettings
import items.services.items_web_portal.page_locations as pages
from items.services.items_web_portal.portal_page_handler import (
    PortalPageHandler)


class GetProjectOverviewPageHandler(PortalPageHandler):

    def __init__(self,
                 logger: logging.Logger,
                 metadata: MetadataSettings):
        """
        Initialize the ProjectsApiView.

        Args:
            logger (logging.Logger):
                Logger instance used for recording application events.
            metadata (MetadataSettings):
                Application metadata configuration used in UI rendering.
        """
        super().__init__(logger)
        self._metadata_settings = metadata

    async def test_cases(self, project_id: int):
        """
        Fetch and display structured test case information for a project.

        This method:
        - Constructs the API URL for the gateway service.
        - Sends an HTTP POST request.
        - Validates the response.
        - Transforms the returned folder/test case data into a tree structure.
        - Renders the test case definitions page.

        Args:
            project_id (int):
                ID of the project whose test case information is requested.

        Returns:
            quart.Response:
                - Rendered HTML page with structured test case data if successful.
                - JSON error response if the gateway request fails.
        """
        gateway_svc: str = self._config.apis_gateway_svc

        url: str = f"{gateway_svc}web/{project_id}/testcase/testcases_details"

        response = await self._rest_client.post(url)

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

        page = "test-cases"  # Default to 'Overview'
        return await self._render_page(
            pages.TEMPLATE_TEST_DEFINITIONS_PAGE,
            data=details, active_page=page,
            has_testcases=True,
            instance_name=self._metadata_settings.instance_name)

    async def project_overview(self, _project_id: int):
        """ PLACEHOLDER """
        return None

    def _transform_tests_details_data(self, data):
        """
        Convert raw folder and test case data into a hierarchical tree structure.

        The incoming data is expected to contain:
        - `folders`: a flat list of folder objects with `id` and `parent_id`
        - `test_cases`: a flat list of test case objects referencing `folder_id`

        This method:
        - Builds a folder map keyed by folder ID.
        - Constructs a nested folder tree based on parent relationships.
        - Assigns test cases to their respective folders.

        Args:
            data (dict):
                Raw data from the API containing folder and test case lists.

        Returns:
            list[dict]:
                A list of root-level folder objects, each with nested
                `subfolders` and associated `test_cases`.
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
