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
from weaver_framework.microservice.microservice_decorators import validate_json
from weaver_framework.microservice.rest_client import RestClient
from items.services.items_gateway.gateway_configuration import GatewayConfiguration

SCHEMA_ADD_PROJECT_REQUEST: dict = {
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
                },
        },
    "required": ["name", "announcement", "announcement_on_overview"]
}


class AddProjectHandler(BaseApiRoute):
    """API route handler for creating projects.

    This handler processes requests to create new projects. Incoming request
    data is validated against the add project schema before being forwarded to
    the CMS service. The handler translates backend responses into
    appropriate HTTP responses for the client.
    """

    def __init__(self,
                 logger: logging.Logger,
                 config: GatewayConfiguration,
                 rest_client: RestClient) -> None:
        """Initialise the project creation handler.

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

    @validate_json(SCHEMA_ADD_PROJECT_REQUEST)
    async def add_project(self, request_msg: ApiResponse):
        """Create a new project.

        The request body is validated using
        ``SCHEMA_ADD_PROJECT_REQUEST`` before this method is invoked.
        Validated project details are forwarded to the CMS service to create
        a new project.

        Args:
            request_msg: Validated request payload containing the details of
                the project to create.

        Returns:
            A Quart ``Response`` indicating whether the project was created
            successfully or describing any validation or backend errors that
            occurred.
        """
        cms_svc: str = self._config.apis_cms_svc
        url: str = f"{cms_svc}projects"

        request_body: dict = {
            "name": request_msg.body["name"],
            "announcement": request_msg.body["announcement"],
            "announcement_on_overview":
                request_msg.body["announcement_on_overview"],
        }

        response: ApiResponse = await self._rest_client.post(
            url, json_data=request_body)

        if response.exception_msg:
            self._logger.error("[Add Project API] Exception call to CMS: %s",
                               response.exception_msg)
            return Response(
                json.dumps({"status": 0, "error": "Internal error!"}),
                status=HTTPStatus.BAD_REQUEST,
                content_type="application/json")

        if response.status_code == HTTPStatus.BAD_REQUEST:
            error_msg: str = response.body.get("error", "")
            self._logger.warning(
                "[WEB Add Project] Failed to create new project, reason: %s",
                error_msg)
            response_json: dict = {"status": 0, "error": error_msg}
            return Response(json.dumps(response_json),
                            status=HTTPStatus.BAD_REQUEST,
                            content_type="application/json")

        if response.status_code != HTTPStatus.OK:
            self._logger.critical(
                "[WEB Add Project] Identity service return HTTP status %s",
                response.status_code)
            return Response(
                json.dumps({"status": 0, "error": "Internal error!"}),
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
                content_type="application/json")

        response_json: dict = {"status": 1}
        return Response(json.dumps(response_json),
                        status=HTTPStatus.OK,
                        content_type="application/json")
