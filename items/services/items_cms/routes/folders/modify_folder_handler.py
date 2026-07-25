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

SCHEMA_MODIFY_FOLDER_REQUEST: dict = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "name": {"type": "string", "minLength": 1}
    },
    "required": ["name"]
}


class ModifyFolderHandler(BaseApiRoute):
    """Handles PATCH /folders/<folder_id> requests."""

    def __init__(self,
                 logger: logging.Logger,
                 service: FolderService) -> None:
        """Initialise the handler.

        Args:
            logger:  Parent logger instance.
            service: Folder service used to rename folders.
        """
        self._logger = logger.getChild(__name__)
        self._service = service

    @validate_json(SCHEMA_MODIFY_FOLDER_REQUEST)
    async def modify_folder(self,
                            request_msg: ApiResponse,
                            folder_id: int) -> Response:
        """Rename an existing folder.

        Args:
            folder_id: ID of the folder to rename, taken from the URL path.

        Request body (JSON):
            name (str): New folder name. Must be unique among siblings.

        Returns:
            200 with ``{"status": 1}`` on success.
            400 if the request body is invalid.
            404 if no folder exists with the given ID.
            409 if the name is already taken by a sibling folder.
            500 on an internal database error.
        """
        # pylint: disable=duplicate-code

        result = await self._service.update_folder(
            folder_id=folder_id, name=request_msg.body["name"])

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
