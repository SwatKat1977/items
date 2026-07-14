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


SCHEMA_UPDATE_CUSTOM_FIELD_REQUEST: dict = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "Update Custom Field",
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


class ModifyCustomFieldHandler(BaseApiRoute):

    def __init__(self,
                 logger: logging.Logger,
                 configuration: GatewayConfiguration,
                 rest_client: RestClient) -> None:
        self._logger = logger.getChild(type(self).__name__)
        self._configuration = configuration
        self._rest_client = rest_client

    @validate_json(SCHEMA_UPDATE_CUSTOM_FIELD_REQUEST)
    async def modify_custom_field(self, request_msg: ApiResponse,
                                  field_id: int):
        url = (f"{self._configuration.apis_cms_svc}testcase_custom_fields"
               f"/{field_id}")

        response: ApiResponse = await self._rest_client.put(url, request_msg.body)
        if response.status_code != HTTPStatus.OK:
            body: dict = {
                "status": 0,
                "error": response.body.get("error", "Unknown error")
            }
            return Response(json.dumps(body),
                            status=response.status_code,
                            content_type="application/json")

        body: dict = {"status": 1}
        return Response(json.dumps(body),
                        status=HTTPStatus.OK,
                        content_type="application/json")
