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
from items.services.items_cms.services.testcase_service import TestcaseService

SCHEMA_ADD_TESTCASE_REQUEST: dict = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "project_id": {"type": "integer"},
        "folder_id": {"type": ["integer", "null"]},
        "name": {"type": "string", "minLength": 1},
        "description": {"type": "string"}
    },
    "required": ["project_id", "folder_id", "name", "description"]
}


class AddTestcaseHandler(BaseApiRoute):
    """Handles POST /testcases requests."""

    def __init__(self,
                 logger: logging.Logger,
                 service: TestcaseService) -> None:
        """Initialise the handler.

        Args:
            logger:  Parent logger instance.
            service: Testcase service used to create test cases.
        """
        self._logger = logger.getChild(__name__)
        self._service = service

    @validate_json(SCHEMA_ADD_TESTCASE_REQUEST)
    async def add_testcase(self, request_msg: ApiResponse) -> Response:
        """Create a new test case.

        Request body (JSON):
            project_id (int):        Project the test case belongs to.
            folder_id (int | null):  Folder ID, or null for a root-level
                                     test case.
            name (str):              Test case name. Must be unique among
                                     its siblings.
            description (str):       Test case description.

        Returns:
            200 with ``{"testcase_id": <int>}`` on success.
            400 if the request body is invalid.
            404 if the project or folder does not exist.
            409 if the name is already taken by a sibling test case.
            500 on an internal database error.
        """
        body = request_msg.body
        result = await self._service.create_testcase(
            project_id=body["project_id"],
            folder_id=body["folder_id"],
            name=body["name"],
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
            json.dumps({"testcase_id": result.data}),
            status=HTTPStatus.OK,
            content_type="application/json")
