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
from weaver_framework.microservice.api_response import ApiResponse
from weaver_framework.microservice.base_api_route import BaseApiRoute
from weaver_framework.microservice.rest_client import RestClient
from items.services.items_gateway.gateway_configuration import GatewayConfiguration


class GetProjectHandler(BaseApiRoute):
    """API route handler for retrieving project details.

    This handler processes requests to retrieve information about a specific
    project. It forwards the request to the CMS service and converts the
    backend response into an appropriate HTTP response for the client.
    """

    def __init__(self,
                 logger: logging.Logger,
                 config: GatewayConfiguration,
                 rest_client: RestClient) -> None:
        """Initialise the project retrieval handler.

        Args:
            logger: Parent logger instance used to create a child logger for
                this handler.
            config: Gateway configuration containing service endpoint
                information.
            rest_client: REST client used to communicate with backend
                services.
        """
        self._logger = logger.getChild(type(self).__name__)
        self._config: GatewayConfiguration = config
        self._rest_client: RestClient = rest_client

    async def get_project(self, project_id: int):
        """Retrieve the details of a project.

        Sends a request to the CMS service to obtain information for the
        specified project and returns the result to the client. Appropriate
        error responses are returned if the project cannot be found or if the
        backend service reports an error.

        Args:
            project_id: Unique identifier of the project to retrieve.

        Returns:
            A Quart ``Response`` containing the project details if the request
            succeeds, or an error response describing why the request failed.
        """
        cms_svc: str = self._config.apis_cms_svc
        url: str = f"{cms_svc}projects/{project_id}"

        response: ApiResponse = await self._rest_client.get(url)

        if response.status_code == HTTPStatus.NOT_FOUND:
            self._logger.warning("[WEB Get Project] Failed to get project")
            return Response(status=HTTPStatus.NOT_FOUND)

        if response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR:
            error_msg: str = response.body.get("error", "")
            self._logger.warning(
                "[WEB Get Project] Failed to get project, reason: %s",
                error_msg)
            response_json: dict = {"status": 0, "error": error_msg}
            return Response(json.dumps(response_json),
                            status=HTTPStatus.BAD_REQUEST,
                            content_type="application/json")

        if response.status_code != HTTPStatus.OK:
            self._logger.critical(
                "[WEB Get Projects] Get projects returned HTTP status %s",
                response.status_code)
            return Response(
                json.dumps({"status": 0, "error": "Internal error!"}),
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
                content_type="application/json")

        return Response(json.dumps(response.body),
                        status=HTTPStatus.OK,
                        content_type="application/json")
