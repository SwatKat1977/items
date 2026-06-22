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
from items.services.items_cms.services.project_service import ProjectService


class DeleteProjectHandler(BaseApiRoute):
    """Handles DELETE /projects/<project_id> requests."""

    VALID_TRUE_VALUES = {"true", "1", "yes"}
    VALID_FALSE_VALUES = {"false", "0", "no"}

    def __init__(self,
                 logger: logging.Logger,
                 service: ProjectService) -> None:
        self._logger = logger.getChild(__name__)
        self._service = service

    async def delete_project(self, project_id: int) -> Response:
        hard_delete_param = quart.request.args.get("hard_delete")

        if hard_delete_param is None:
            hard_delete = False
        else:
            lower = hard_delete_param.lower()
            if lower in self.VALID_TRUE_VALUES:
                hard_delete = True
            elif lower in self.VALID_FALSE_VALUES:
                hard_delete = False
            else:
                return Response(
                    json.dumps({"status": 0,
                                "error_msg": "Invalid parameter for hard_delete argument"}),
                    status=HTTPStatus.BAD_REQUEST,
                    content_type="application/json")

        result = self._service.delete_project(project_id, hard_delete)

        if not result.success:
            status = (HTTPStatus.INTERNAL_SERVER_ERROR
                      if result.is_internal else HTTPStatus.BAD_REQUEST)
            return Response(
                json.dumps({"status": 0, "error_msg": result.error_msg}),
                status=status,
                content_type="application/json")

        return Response(
            json.dumps({}),
            status=HTTPStatus.OK,
            content_type="application/json")
