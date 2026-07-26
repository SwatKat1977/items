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
from items.services.items_cms.services.testcase_field_values_service import (
    TestcaseFieldValuesService,
)

SCHEMA_SET_FIELD_VALUES_REQUEST: dict = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "values": {
            "type": "object",
            "additionalProperties": {"type": "string"}
        }
    },
    "required": ["values"]
}


class SetTestcaseFieldValuesHandler(BaseApiRoute):
    """Handles PUT /testcases/<case_id>/custom_fields requests."""

    def __init__(self,
                 logger: logging.Logger,
                 service: TestcaseFieldValuesService) -> None:
        """Initialise the handler.

        Args:
            logger:  Parent logger instance.
            service: Testcase field values service used to set values.
        """
        self._logger = logger.getChild(__name__)
        self._service = service

    @validate_json(SCHEMA_SET_FIELD_VALUES_REQUEST)
    async def set_field_values(self,
                               request_msg: ApiResponse,
                               case_id: int) -> Response:
        """Set one or more custom field values for a test case.

        Only the fields present in the request body are affected — omitted
        fields keep whatever value (or default) they already had.

        Args:
            case_id: ID of the test case to update, taken from the URL
                     path.

        Request body (JSON):
            values (dict): Mapping of field_id (as a string key) to the
                           new value string.

        Returns:
            200 with ``{"status": 1}`` on success.
            400 if the request body is invalid, a field_id key is not
            numeric, a field does not apply to the test case's project,
            or a value fails validation.
            404 if no test case exists with the given ID.
            500 on an internal database error.
        """
        # pylint: disable=duplicate-code

        raw_values: dict = request_msg.body["values"]

        try:
            values = {int(field_id): value
                      for field_id, value in raw_values.items()}
        except ValueError:
            return Response(
                json.dumps({"error": "values keys must be numeric field ids"}),
                status=HTTPStatus.BAD_REQUEST,
                content_type="application/json")

        result = await self._service.set_field_values(case_id, values)

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
            json.dumps({"status": 1}),
            status=HTTPStatus.OK,
            content_type="application/json")
