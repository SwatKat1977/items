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
from items.services.items_cms.services.folder_service import FolderService


class DeleteFolderHandler(BaseApiRoute):
    """Handles DELETE /folders/<folder_id> requests."""

    def __init__(self,
                 logger: logging.Logger,
                 service: FolderService) -> None:
        """Initialise the handler.

        Args:
            logger:  Parent logger instance.
            service: Folder service used to delete folders.
        """
        self._logger = logger.getChild(__name__)
        self._service = service

    async def delete_folder(self, folder_id: int) -> Response:
        """Delete a folder.

        Child folders and their test cases are removed automatically via
        the database's cascading delete constraints.

        Args:
            folder_id: ID of the folder to delete, taken from the URL path.

        Returns:
            200 with ``{}`` on success.
            404 if no folder exists with the given ID.
            500 on an internal database error.
        """
        # pylint: disable=duplicate-code

        result = await self._service.delete_folder(folder_id)

        if not result.success:
            status = (HTTPStatus.INTERNAL_SERVER_ERROR
                      if result.is_internal else HTTPStatus.NOT_FOUND)
            return Response(
                json.dumps({"error": result.error_msg}),
                status=status,
                content_type="application/json")

        return Response(
            json.dumps({}),
            status=HTTPStatus.OK,
            content_type="application/json")
