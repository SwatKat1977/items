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
        url: str = (f"{self._configuration.apis_cms_svc}testcase_custom_fields"
                    f"/{field_id}")

        response: ApiResponse = await self._rest_client.patch(url)
        print("Response:")
        print(f"=> Status Code : {response.status_code}")
        print(f"=> Exception   : {response.exception_msg}")
        print(f"=> Body        : {response.body}")

        '''
Move testcase custom field               PATCH /testcase_custom_fields/<field_id>
        '''

        '''
        cms_svc: str = self._configuration.apis_cms_svc
        url: str = f"{cms_svc}admin/testcase_custom_fields/" \
                   f"testcase_custom_fields/{field_id}/{move_position}"
        '''

        if hasattr(request_msg.body, "position"):
            return await self._move_custom_field(request_msg, field_id)

        return Response(json.dumps(api_response.body),
                              status=HTTPStatus.BAD_REQUEST,
                              content_type="application/json")

