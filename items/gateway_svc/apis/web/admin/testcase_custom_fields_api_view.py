"""
Copyright 2025 Integrated Test Management Suite Development Team

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
import http
import json
import logging
import quart
from base_view import ApiResponse, BaseView, validate_json
import interfaces.gateway.project as json_schemas
from threadsafe_configuration import ThreadSafeConfiguration


class TestcaseCustomFieldsApiView(BaseView):

    def __init__(self, logger : logging.Logger) -> None:
        self._logger = logger.getChild(__name__)

    @validate_json(json_schemas.SCHEMA_MODIFY_TC_CUSTOM_FIELD_REQUEST)
    async def modify_custom_field(self, request_msg: ApiResponse,
                                  field_id: int):
        if hasattr(request_msg.body, "position"):
            return await self._move_custom_field(request_msg, field_id)

        return await self._modify_custom_field(request_msg, field_id)

    async def _move_custom_field(self, request_msg: ApiResponse,
                                 field_id: int):
        """
        Sends a PATCH request to move a custom field up or down in the list.

        This method extracts the desired move direction ("up" or "down") from
        the request message, constructs the appropriate CMS service URL, and
        forwards the request via PATCH. It returns the response from the CMS
        service as a Quart HTTP response.

        Args:
            request_msg (ApiResponse): The incoming API request containing the
                                       desired position.
            field_id (int): The ID of the custom field to move.

        Returns:
            quart.Response: A JSON response containing the result of the
                            operation, with HTTP 400 BAD REQUEST status if the
                            move fails.
        """
        move_position: str = request_msg.body.position
        cms_svc: str = ThreadSafeConfiguration().apis_cms_svc
        url: str = f"{cms_svc}admin/testcase_custom_fields/" \
                   f"testcase_custom_fields/{field_id}/{move_position}"

        api_response = await self._call_api_patch(url)

        return quart.Response(json.dumps(api_response.body),
                              status=http.HTTPStatus.BAD_REQUEST,
                              content_type="application/json")

    async def _modify_custom_field(self, request_msg: ApiResponse,
                                   field_id: int):
        response_body = {
            "status": -1,
            "error": "placeholder"
        }
        return quart.Response(json.dumps(response_body),
                              status=http.HTTPStatus.BAD_REQUEST,
                              content_type="application/json")
