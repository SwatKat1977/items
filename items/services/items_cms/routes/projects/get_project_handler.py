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
from items.services.items_cms.services.project_service import ProjectService


class GetProjectHandler(BaseApiRoute):
    """Handles GET /projects/<project_id> requests."""

    def __init__(self,
                 logger: logging.Logger,
                 service: ProjectService) -> None:
        """Initialise the handler.

        Args:
            logger:  Parent logger instance.
            service: Project service used to retrieve project data.
        """
        self._logger = logger.getChild(__name__)
        self._service = service

    async def get_project(self, project_id: int) -> Response:
        """Retrieve full details for a single project.

        Args:
            project_id: ID of the project to retrieve, taken from the
                        URL path.

        Returns:
            200 with the project details dict on success.
            404 if no project exists with the given ID.
            500 on an internal database error.
        """
        # pylint: disable=duplicate-code

        result = self._service.get_project(project_id)

        if not result.success:
            status = (HTTPStatus.INTERNAL_SERVER_ERROR
                      if result.is_internal else HTTPStatus.NOT_FOUND)
            return Response(
                json.dumps({"error": result.error_msg}),
                status=status,
                content_type="application/json")

        return Response(
            json.dumps(result.data),
            status=HTTPStatus.OK,
            content_type="application/json")
