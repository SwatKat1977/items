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
import json
import logging
from quart import Response
from weaver_framework.microservice.api_response import ApiResponse
from weaver_framework.microservice.base_api_route import BaseApiRoute
from weaver_framework.microservice.rest_client import RestClient
from items.services.items_gateway.gateway_configuration import GatewayConfiguration
from items.services.items_gateway.routes.web.testcases.project_id_parameter \
    import read_required_project_id


class DeleteTestcaseHandler(BaseApiRoute):
    """Handles DELETE /testcases/<case_id> - delete a test case.

    Proxies to the CMS service and propagates the response. The
    ``project_id`` query parameter is what ``require_project_member``
    authorised; it is forwarded so the CMS can confirm the test case really
    belongs to that project (404 otherwise).
    """

    def __init__(self,
                 logger: logging.Logger,
                 configuration: GatewayConfiguration,
                 rest_client: RestClient) -> None:
        self._logger = logger.getChild(type(self).__name__)
        self._configuration = configuration
        self._rest_client = rest_client

    async def delete_testcase(self, case_id: int) -> Response:
        """Delete a test case.

        Query parameters: ``project_id`` (required).

        Args:
            case_id: The test case's id (from the URL).

        Returns:
            200 on success.
            400 if ``project_id`` is missing or not an integer.
            404 if the test case does not exist, or belongs to a different
            project than ``project_id``.
            500 if the CMS service is unreachable or reports an internal
            error.
        """
        project_id, error_response = read_required_project_id()
        if error_response is not None:
            return error_response

        url: str = (f"{self._configuration.apis_cms_svc}testcases/{case_id}"
                    f"?project_id={project_id}")
        response: ApiResponse = await self._rest_client.delete(url)

        if response.exception_msg is not None:
            self._logger.error("Connection to CMS service failed: %s",
                               response.exception_msg)
            return Response(
                json.dumps({"error": "CMS service unavailable"}),
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
                content_type="application/json")

        return Response(json.dumps(response.body),
                        status=response.status_code,
                        content_type="application/json")
