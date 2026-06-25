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
from items.services.items_cms.services.project_service import ProjectService

SCHEMA_MODIFY_PROJECT_REQUEST: dict = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "name": {"type": "string"},
        "announcement": {"type": "string"},
        "announcement_on_overview": {"type": "boolean"}
    },
    "required": ["name", "announcement", "announcement_on_overview"]
}


class ModifyProjectHandler(BaseApiRoute):
    """Handles PATCH /projects/<project_id> requests."""

    def __init__(self,
                 logger: logging.Logger,
                 service: ProjectService) -> None:
        """Initialise the handler.

        Args:
            logger:  Parent logger instance.
            service: Project service used to update projects.
        """
        self._logger = logger.getChild(__name__)
        self._service = service

    @validate_json(SCHEMA_MODIFY_PROJECT_REQUEST)
    async def modify_project(self,
                             request_msg: ApiResponse,
                             project_id: int) -> Response:
        """Update the details of an existing project.

        Args:
            project_id: ID of the project to update, taken from the
                        URL path.

        Request body (JSON):
            name (str):                     New project name. Must be unique
                                            if changed.
            announcement (str):             Updated announcement text.
            announcement_on_overview (bool): Whether to display the
                                             announcement on the overview page.

        Returns:
            200 with ``{"status": 1}`` on success.
            400 if the request body is invalid or the new name is already
                taken by another project.
            404 if no project exists with the given ID.
            500 on an internal database error.
        """
        # pylint: disable=duplicate-code

        body = request_msg.body
        result = await self._service.modify_project(
            project_id=project_id,
            name=body["name"],
            announcement=body["announcement"],
            announcement_on_overview=body["announcement_on_overview"])

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
