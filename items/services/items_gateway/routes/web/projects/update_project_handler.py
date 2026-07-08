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
from weaver_framework.microservice.microservice_decorators import validate_json
from items.services.items_gateway.gateway_configuration import GatewayConfiguration

SCHEMA_UPDATE_PROJECT_REQUEST: dict = {
    "$schema": "http://json-schema.org/draft-07/schema#",

    "type": "object",
    "additionalProperties": False,

    "properties":
        {
            "name":
                {
                    "type": "string"
                },
            "announcement":
                {
                    "type": "string"
                },
            "announcement_on_overview":
                {
                    "type": "boolean"
                }
        },
    "required": ["name", "announcement", "announcement_on_overview"]
}


class UpdateProjectHandler(BaseApiRoute):
    """API route handler for updating projects.

    This handler processes project update requests received by the gateway.
    Incoming request data is validated against the update project schema
    before being forwarded to the CMS service. The handler translates backend
    responses into appropriate HTTP responses for the client.
    """

    def __init__(self,
                 logger: logging.Logger,
                 config: GatewayConfiguration,
                 rest_client: RestClient) -> None:
        """Initialise the project update handler.

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

    @validate_json(SCHEMA_UPDATE_PROJECT_REQUEST)
    async def update_project(self,
                             request_msg: ApiResponse,
                             project_id: int):
        """Update an existing project.

        The request body is validated using
        ``SCHEMA_UPDATE_PROJECT_REQUEST`` before this method is invoked.
        Validated project details are forwarded to the CMS service using a
        PATCH request.

        Args:
            request_msg: Validated request payload containing the project
                details to update.
            project_id: Unique identifier of the project to update.

        Returns:
            A Quart ``Response`` indicating whether the project was updated
            successfully or describing any validation or backend errors that
            occurred.
        """
        cms_svc: str = self._config.apis_cms_svc
        url: str = f"{cms_svc}projects/{project_id}"

        request: dict = {
            "name": request_msg.body["name"],
            "announcement": request_msg.body["announcement"],
            "announcement_on_overview":
                request_msg.body["announcement_on_overview"],
        }
        response: ApiResponse = await self._rest_client.patch(
            url, json_data=request)

        if response.status_code == HTTPStatus.NOT_FOUND:
            self._logger.critical("Project update request invalid, "
                                  "project ID is invalid")
            response_json = {
                "status": 0,
                'error': "project ID is invalid"
            }
            return Response(json.dumps(response_json),
                            status=HTTPStatus.NOT_FOUND)

        if response.status_code == HTTPStatus.BAD_REQUEST:
            self._logger.critical("Project update request invalid, "
                                  "reason: %s", response.body.get("error"))
            response_json = {
                "status": 0,
                'error': response.body.get("error")
            }
            return Response(json.dumps(response_json),
                            status=HTTPStatus.BAD_REQUEST)

        if response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR:
            self._logger.critical("Project update request internal error, "
                                  "reason: %s", response.exception_msg)
            response_json = {
                "status": 0,
                'error': response.exception_msg
            }
            return Response(json.dumps(response_json),
                            status=HTTPStatus.BAD_REQUEST)

        response_json: dict = {"status": 1}
        return Response(json.dumps(response_json),
                        status=HTTPStatus.OK,
                        content_type="application/json")
