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
import json
import logging
from http import HTTPStatus
from quart import Response
from weaver_framework.microservice.base_api_route import BaseApiRoute
from weaver_framework.microservice.microservice_decorators import validate_json
from weaver_framework.microservice.api_response import ApiResponse
from items.services.items_cms.services.testcase_custom_fields_service import (
    TestcaseCustomFieldsService,
)

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
    """Handles PATCH /testcase_custom_fields/<field_id> requests."""

    def __init__(self,
                 logger: logging.Logger,
                 service: TestcaseCustomFieldsService) -> None:
        """Initialise the handler.

        Args:
            logger:  Parent logger instance.
            service: Custom fields service used to reorder fields.
        """
        self._logger = logger.getChild(__name__)
        self._service = service

    @validate_json(SCHEMA_MOVE_CUSTOM_FIELD_REQUEST)
    async def move_custom_field(self,
                                request_msg: ApiResponse,
                                field_id: int) -> Response:
        """Move a custom field up or down in the ordered list.

        Path parameters:
            field_id (int): ID of the field to move.

        Request body (JSON):
            direction (str): ``"up"`` or ``"down"``.

        Returns:
            200 with ``{}`` on success.
            400 if the request body is invalid.
            404 if the field is not found or is already at the boundary.
            500 on an internal database error.
        """
        direction = request_msg.body["direction"]
        result = await self._service.move_custom_field(field_id, direction)

        if not result.success:
            if result.is_internal:
                status = HTTPStatus.INTERNAL_SERVER_ERROR
            elif result.not_found:
                status = HTTPStatus.NOT_FOUND
            else:
                status = HTTPStatus.BAD_REQUEST
            return Response(
                json.dumps({"error": result.error_msg}),
                status=status,
                content_type="application/json")

        return Response(
            json.dumps({}),
            status=HTTPStatus.OK,
            content_type="application/json")
