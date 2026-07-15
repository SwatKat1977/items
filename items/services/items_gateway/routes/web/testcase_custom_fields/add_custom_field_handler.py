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

"""JSON Schema for validating add-testcase-custom-field requests.

This schema defines the structure of the JSON payload accepted when creating
a new testcase custom field. It validates the field metadata, supported data
types, required properties, and conditional requirements for project-specific
custom fields.

The schema enforces that:

* ``field_name`` is a non-empty display name.
* ``system_name`` is a valid internal identifier consisting of lowercase
  letters, digits, and underscores, beginning with a letter.
* ``field_type`` is one of the supported testcase custom field types.
* Required metadata such as the description, enabled state, default value,
  and required flag are present.
* When ``applies_to_all_projects`` is ``False``, the ``projects`` property
  must also be supplied.
* Additional properties outside the schema are rejected.
"""
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
            "description": (
                "Internal system identifier (lowercase letters, digits, "
                "and underscores; must start with a letter)."
            )
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
            "description": (
                "List of project names "
                "(required when applies_to_all_projects is false)."
            ),
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
    "if": {
        "properties": {"applies_to_all_projects": {"const": False}},
        "required": ["applies_to_all_projects"]
    },
    "then": {"required": ["projects"]}
}


class AddCustomFieldHandler(BaseApiRoute):
    """Handle requests for creating testcase custom fields.

    This handler validates incoming custom field definitions and forwards valid
    requests to the CMS service. It translates CMS responses into appropriate
    HTTP responses for the client.
    """

    def __init__(self,
                 logger: logging.Logger,
                 configuration: GatewayConfiguration,
                 rest_client: RestClient) -> None:
        """Initialise the handler.

        Args:
            logger: Application logger used for diagnostic and error logging.
            configuration: Gateway configuration containing service endpoint
                information.
            rest_client: REST client used to communicate with the CMS service.
        """
        self._logger = logger.getChild(type(self).__name__)
        self._configuration = configuration
        self._rest_client = rest_client

    @validate_json(SCHEMA_ADD_TEST_CASE_CUSTOM_FIELD_REQUEST)
    async def add_custom_field(self, request_msg: ApiResponse):
        """Create a new testcase custom field.

        Validates the request payload, forwards the create request to the CMS
        service, and returns the result to the caller.

        Args:
            request_msg: The validated API request containing the new custom
                field definition.

        Returns:
            Response: A Quart JSON response indicating whether the operation
            succeeded. A CMS connection failure yields 500; any non-OK CMS
            status is propagated back to the caller.
        """
        url: str = f"{self._configuration.apis_cms_svc}testcase_custom_fields"

        response: ApiResponse = await self._rest_client.post(
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
