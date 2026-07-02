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
from http.client import responses

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
    """Handles POST /projects requests."""

    def __init__(self,
                 logger: logging.Logger,
                 config: GatewayConfiguration,
                 rest_client: RestClient) -> None:
        """Initialise the handler.

        Args:
            logger:  Parent logger instance.
        """
        self._logger = logger.getChild(type(self).__name__)
        self._config: GatewayConfiguration = config
        self._rest_client: RestClient = rest_client

    @validate_json(SCHEMA_ADD_PROJECT_REQUEST)
    async def add_project(self, request_msg: ApiResponse):

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
