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
from items.services.items_cms.routes.project_id_parameter import (
    read_required_project_id)
from items.services.items_cms.services.testcase_service import TestcaseService

SCHEMA_MOVE_TESTCASE_REQUEST: dict = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "folder_id": {"type": ["integer", "null"]}
    },
    "required": ["folder_id"]
}


class MoveTestcaseHandler(BaseApiRoute):
    """Handles POST /testcases/<case_id>/move requests."""

    def __init__(self,
                 logger: logging.Logger,
                 service: TestcaseService) -> None:
        """Initialise the handler.

        Args:
            logger:  Parent logger instance.
            service: Testcase service used to move test cases.
        """
        self._logger = logger.getChild(__name__)
        self._service = service

    @validate_json(SCHEMA_MOVE_TESTCASE_REQUEST)
    async def move_testcase(self,
                            request_msg: ApiResponse,
                            case_id: int) -> Response:
        """Move a test case into another folder, or to the top level.

        Args:
            case_id: ID of the test case to move, taken from the URL path.

        Query parameters:
            project_id (int): Required. The project the test case belongs
                              to; checked against the test case itself.

        Request body (JSON):
            folder_id (int | null): The destination folder, or null to move
                                    the test case to the top level. Must be
                                    in the same project. Always required, so
                                    that an omitted value is never mistaken
                                    for "the top level".

        Returns:
            200 with ``{"status": 1}`` on success (including when the test
            case is already in the destination).
            400 if the request body is invalid, ``project_id`` is missing or
            not an integer, or the destination folder belongs to a
            different project.
            404 if no test case exists with the given ID, it belongs to a
            different project than ``project_id``, or the destination
            folder does not exist.
            409 if the destination already holds a test case with the same
            name.
            500 on an internal database error.
        """
        # pylint: disable=duplicate-code

        project_id, error_response = read_required_project_id()
        if error_response is not None:
            return error_response

        result = await self._service.move_testcase(
            case_id=case_id,
            project_id=project_id,
            folder_id=request_msg.body["folder_id"])

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
            json.dumps({"status": 1}),
            status=HTTPStatus.OK,
            content_type="application/json")
