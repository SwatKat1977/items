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
from weaver_framework.microservice.base_api_route import BaseApiRoute, validate_json
from weaver_framework.microservice.api_response import ApiResponse
from items.services.items_cms.services.project_service import ProjectService
from items.shared.interfaces.cms.project import SCHEMA_ADD_PROJECT_REQUEST


class CreateProjectHandler(BaseApiRoute):
    """Handles POST /projects requests."""

    def __init__(self,
                 logger: logging.Logger,
                 service: ProjectService) -> None:
        self._logger = logger.getChild(__name__)
        self._service = service

    @validate_json(SCHEMA_ADD_PROJECT_REQUEST)
    async def create_project(self, request_msg: ApiResponse) -> Response:
        body = request_msg.body
        result = self._service.create_project(
            name=body["name"],
            announcement=body["announcement"],
            announcement_on_overview=body["announcement_on_overview"])

        if not result.success:
            status = (HTTPStatus.INTERNAL_SERVER_ERROR
                      if result.is_internal else HTTPStatus.BAD_REQUEST)
            return Response(
                json.dumps({"status": 0, "error_msg": result.error_msg}),
                status=status,
                content_type="application/json")

        return Response(
            json.dumps({"project_id": result.data}),
            status=HTTPStatus.OK,
            content_type="application/json")
