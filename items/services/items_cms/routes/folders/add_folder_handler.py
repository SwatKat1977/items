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
from items.services.items_cms.services.folder_service import FolderService

SCHEMA_ADD_FOLDER_REQUEST: dict = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "project_id": {"type": "integer"},
        "parent_id": {"type": ["integer", "null"]},
        "name": {"type": "string", "minLength": 1}
    },
    "required": ["project_id", "parent_id", "name"]
}


class AddFolderHandler(BaseApiRoute):
    """Handles POST /folders requests."""

    def __init__(self,
                 logger: logging.Logger,
                 service: FolderService) -> None:
        """Initialise the handler.

        Args:
            logger:  Parent logger instance.
            service: Folder service used to create folders.
        """
        self._logger = logger.getChild(__name__)
        self._service = service

    @validate_json(SCHEMA_ADD_FOLDER_REQUEST)
    async def add_folder(self, request_msg: ApiResponse) -> Response:
        """Create a new testcase folder.

        Request body (JSON):
            project_id (int):        Project the folder belongs to.
            parent_id (int | null):  Parent folder ID, or null for a
                                     root-level folder.
            name (str):              Folder name. Must be unique among
                                     its siblings.

        Returns:
            200 with ``{"folder_id": <int>}`` on success.
            400 if the request body is invalid.
            404 if the project or parent folder does not exist.
            409 if the name is already taken by a sibling folder.
            500 on an internal database error.
        """
        body = request_msg.body
        result = await self._service.create_folder(
            project_id=body["project_id"],
            parent_id=body["parent_id"],
            name=body["name"])

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
            json.dumps({"folder_id": result.data}),
            status=HTTPStatus.OK,
            content_type="application/json")
