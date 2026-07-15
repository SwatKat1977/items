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


SCHEMA_MOVE_CUSTOM_FIELD_REQUEST: dict = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "Move Custom Field",
    "type": "object",
    "properties": {
        "direction": {
            "type": "string",
            "enum": ["up", "down"],
            "description": "Direction to move the custom field in the ordered list."
        }
    },
    "required": ["direction"],
    "additionalProperties": False
}


class MoveCustomFieldHandler(BaseApiRoute):
    """Handle requests for repositioning testcase custom fields.

    This handler validates requests to move a custom field within the ordered
    list of testcase custom fields, forwards the request to the CMS service,
    and translates the resulting status into an appropriate HTTP response for
    the client.
    """

    def __init__(self,
                 logger: logging.Logger,
                 configuration: GatewayConfiguration,
                 rest_client: RestClient) -> None:
        self._logger = logger.getChild(type(self).__name__)
        self._configuration = configuration
        self._rest_client = rest_client

    @validate_json(SCHEMA_MOVE_CUSTOM_FIELD_REQUEST)
    async def move_custom_field(self, request_msg: ApiResponse,
                                field_id: int):
        """Move a testcase custom field up or down in the ordered list.

        Validates the request payload, forwards the reposition request to the
        CMS service, and returns the result to the caller.

        Args:
            request_msg: The validated API request containing the move
                ``direction`` ("up" or "down").
            field_id: The unique identifier of the custom field to move.

        Returns:
            Response: A Quart JSON response indicating whether the operation
            succeeded. A CMS connection failure yields 500; any non-OK CMS
            status is propagated back to the caller.
        """
        url: str = (f"{self._configuration.apis_cms_svc}testcase_custom_fields"
                    f"/{field_id}")

        response: ApiResponse = await self._rest_client.patch(
            url, json_data=request_msg.body)

        # 1) CMS unreachable / transport-level failure.
        if response.exception_msg is not None:
            self._logger.error("Connection to CMS service failed: %s",
                               response.exception_msg)
            return Response(
                json.dumps({"status": 0, "error": "Internal error!"}),
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
                content_type="application/json")

        # 2) CMS reached but reported a non-OK status - propagate it.
        if response.status_code != HTTPStatus.OK:
            error_msg: str = "Unknown error"
            if isinstance(response.body, dict):
                error_msg = response.body.get("error", error_msg)
            self._logger.error("CMS service returned status %s: %s",
                               response.status_code, error_msg)
            return Response(
                json.dumps({"status": 0, "error": error_msg}),
                status=response.status_code,
                content_type="application/json")

        # 3) Success.
        return Response(
            json.dumps({"status": 1}),
            status=HTTPStatus.OK,
            content_type="application/json")
