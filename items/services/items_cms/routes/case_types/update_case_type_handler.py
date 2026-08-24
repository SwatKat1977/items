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
from items.services.items_cms.services.case_types_service import (
    CaseTypesService,
)

SCHEMA_UPDATE_CASE_TYPE_REQUEST: dict = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "Update Case Type",
    "type": "object",
    "properties": {
        "name": {
            "type": "string",
            "minLength": 1,
            "description": "The display name of the case type."
        },
        "description": {
            "type": "string",
            "description": "A human-readable description of the case type."
        }
    },
    "required": ["name", "description"],
    "additionalProperties": False
}


class UpdateCaseTypeHandler(BaseApiRoute):
    """Handles PATCH /case_types/<type_id> requests.

    Name and description only - ``is_default`` is deliberately not
    accepted here (not present in the request schema at all). Changing
    which type is default is a separate, dedicated action (see
    SetDefaultCaseTypeHandler) since it's a swap affecting two rows, not
    a plain field edit on one.
    """

    def __init__(self,
                 logger: logging.Logger,
                 service: CaseTypesService) -> None:
        """Initialise the handler.

        Args:
            logger:  Parent logger instance.
            service: Case types service used to update type definitions.
        """
        self._logger = logger.getChild(__name__)
        self._service = service

    @validate_json(SCHEMA_UPDATE_CASE_TYPE_REQUEST)
    async def update_case_type(self,
                               request_msg: ApiResponse,
                               type_id: int) -> Response:
        """Update a case type's name and description.

        Path parameters:
            type_id (int): ID of the case type to update.

        Request body (JSON):
            name (str):        New display name. Must be unique.
            description (str): New description (may be empty).

        Returns:
            200 with ``{}`` on success.
            400 on invalid or missing request fields.
            404 if no case type exists with the given ID.
            409 if name is already used by another case type.
            500 on an internal database error.
        """
        body = request_msg.body

        result = await self._service.update_case_type(
            type_id=type_id, name=body["name"],
            description=body["description"])

        if not result.success:
            if result.is_internal:
                status = HTTPStatus.INTERNAL_SERVER_ERROR
            elif result.not_found:
                status = HTTPStatus.NOT_FOUND
            elif result.is_conflict:
                status = HTTPStatus.CONFLICT
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
