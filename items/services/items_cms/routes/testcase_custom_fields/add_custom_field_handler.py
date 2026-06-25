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

SCHEMA_ADD_TEST_CASE_CUSTOM_FIELD_REQUEST: dict = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "Custom Field Definition",
    "type": "object",
    "properties": {
        "field_name": {
            "type": "string",
            "minLength": 1,
            "description": "The display name of the custom field."
        },
        "description": {
            "type": "string",
            "description": "A human-readable description of the field."
        },
        "system_name": {
            "type": "string",
            "pattern": "^[a-z][a-z0-9_]*$",
            "description": "Internal system identifier (lowercase letters, digits, and underscores; must start with a letter)."
        },
        "field_type": {
            "type": "string",
            "description": "The data type of the field.",
            "enum": [
                "Checkbox",
                "Date",
                "Dropdown",
                "Integer",
                "String",
                "Text",
                "Url (Link)",
                "User"
            ]
        },
        "enabled": {
            "type": "boolean",
            "description": "Whether the field is active."
        },
        "is_required": {
            "type": "boolean",
            "description": "Whether the field must be filled in for test cases."
        },
        "default_value": {
            "type": "string",
            "description": "Optional default value for the field."
        },
        "applies_to_all_projects": {
            "type": "boolean",
            "description": "If true, the field applies to all projects."
        },
        "projects": {
            "type": "array",
            "description": "List of project names (required when applies_to_all_projects is false).",
            "items": {"type": "string"}
        }
    },
    "required": [
        "field_name",
        "description",
        "system_name",
        "field_type",
        "enabled",
        "is_required",
        "default_value",
        "applies_to_all_projects"
    ],
    "additionalProperties": False,
    "allOf": [
        {
            "if": {
                "properties": {"applies_to_all_projects": {"const": True}}
            },
            "then": {"not": {"required": ["projects"]}},
            "else": {"required": ["projects"]}
        }
    ]
}


class AddCustomFieldHandler(BaseApiRoute):
    """Handles POST /testcase_custom_fields requests."""

    def __init__(self,
                 logger: logging.Logger,
                 service: TestcaseCustomFieldsService) -> None:
        """Initialise the handler.

        Args:
            logger:  Parent logger instance.
            service: Custom fields service used to create new fields.
        """
        self._logger = logger.getChild(__name__)
        self._service = service

    @validate_json(SCHEMA_ADD_TEST_CASE_CUSTOM_FIELD_REQUEST)
    async def add_custom_field(self, request_msg: ApiResponse) -> Response:
        """Create a new testcase custom field definition.

        Request body (JSON):
            field_name (str):               Display name. Must be unique.
            description (str):              Human-readable description.
            system_name (str):              Internal identifier.
            field_type (str):               One of the supported type values.
            enabled (bool):                 Whether the field is active.
            is_required (bool):             Whether the field must be filled in.
            default_value (str):            Default value (may be empty string).
            applies_to_all_projects (bool): If true, no project list needed.
            projects (list[str]):           Required when applies_to_all_projects
                                            is false.

        Returns:
            200 with ``{"field_id": <int>}`` on success.
            400 on invalid or missing request fields.
            409 if field_name or system_name is already in use.
            500 on an internal database error.
        """
        body = request_msg.body

        result = await self._service.add_custom_field(
            field_name=body["field_name"],
            description=body["description"],
            system_name=body["system_name"],
            field_type=body["field_type"],
            enabled=body["enabled"],
            is_required=body["is_required"],
            default_value=body["default_value"],
            applies_to_all_projects=body["applies_to_all_projects"],
            projects=body.get("projects"))

        if not result.success:
            if result.is_internal:
                status = HTTPStatus.INTERNAL_SERVER_ERROR
            elif result.is_conflict:
                status = HTTPStatus.CONFLICT
            else:
                status = HTTPStatus.BAD_REQUEST
            return Response(
                json.dumps({"error": result.error_msg}),
                status=status,
                content_type="application/json")

        return Response(
            json.dumps({"field_id": result.data}),
            status=HTTPStatus.OK,
            content_type="application/json")
