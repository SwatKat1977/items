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
import quart
from quart import Response
from weaver_framework.microservice.base_api_route import BaseApiRoute
from items.services.items_cms.services.folder_service import FolderService


class ListFoldersHandler(BaseApiRoute):
    """Handles GET /folders requests."""

    def __init__(self,
                 logger: logging.Logger,
                 service: FolderService) -> None:
        """Initialise the handler.

        Args:
            logger:  Parent logger instance.
            service: Folder service used to retrieve folder data.
        """
        self._logger = logger.getChild(__name__)
        self._service = service

    async def list_folders(self) -> Response:
        """Retrieve every folder for a project.

        Query parameters:
            project_id (int): ID of the project to list folders for.
                              Required.

        Returns:
            200 with ``{"folders": [...]}`` on success.
            400 if ``project_id`` is missing or not an integer.
            404 if ``project_id`` does not refer to an existing project.
            500 on an internal database error.
        """
        # pylint: disable=duplicate-code

        project_id_param = quart.request.args.get("project_id")

        if project_id_param is None:
            return Response(
                json.dumps({"error": "project_id is required"}),
                status=HTTPStatus.BAD_REQUEST,
                content_type="application/json")

        try:
            project_id = int(project_id_param)
        except ValueError:
            return Response(
                json.dumps({"error": "project_id must be an integer"}),
                status=HTTPStatus.BAD_REQUEST,
                content_type="application/json")

        result = await self._service.list_folders(project_id)

        if not result.success:
            status = (HTTPStatus.INTERNAL_SERVER_ERROR
                      if result.is_internal else HTTPStatus.NOT_FOUND)
            return Response(
                json.dumps({"error": result.error_msg}),
                status=status,
                content_type="application/json")

        return Response(
            json.dumps({"folders": result.data}),
            status=HTTPStatus.OK,
            content_type="application/json")
