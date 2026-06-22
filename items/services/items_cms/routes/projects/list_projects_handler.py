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


class ListProjectsHandler(BaseApiRoute):
    """Handles GET /projects requests."""

    VALID_OVERVIEW_FIELDS = {"name"}
    VALID_COUNT_FIELDS = {"no_of_milestones", "no_of_test_runs"}
    DEFAULT_OVERVIEW_FIELDS = ["name"]

    def __init__(self,
                 logger: logging.Logger,
                 service: ProjectService) -> None:
        self._logger = logger.getChild(__name__)
        self._service = service

    async def list_projects(self) -> Response:
        value_fields_param = quart.request.args.get("value_fields")
        count_fields_param = quart.request.args.get("count_fields")

        if value_fields_param:
            requested_fields = value_fields_param.split(",")
            invalid = [f for f in requested_fields
                       if f not in self.VALID_OVERVIEW_FIELDS]
            if invalid:
                return Response(
                    json.dumps({"error": "Invalid value field"}),
                    status=HTTPStatus.BAD_REQUEST,
                    content_type="application/json")
        else:
            requested_fields = list(self.DEFAULT_OVERVIEW_FIELDS)

        count_milestones = False
        count_test_runs = False

        if count_fields_param:
            requested_count_fields = count_fields_param.split(",")
            invalid = [f for f in requested_count_fields
                       if f not in self.VALID_COUNT_FIELDS]
            if invalid:
                return Response(
                    json.dumps({"error": "Invalid count field"}),
                    status=HTTPStatus.BAD_REQUEST,
                    content_type="application/json")

            count_milestones = "no_of_milestones" in requested_count_fields
            count_test_runs = "no_of_test_runs" in requested_count_fields

        result = self._service.list_projects(
            requested_fields, count_milestones, count_test_runs)

        if not result.success:
            status = (HTTPStatus.INTERNAL_SERVER_ERROR
                      if result.is_internal else HTTPStatus.BAD_REQUEST)
            return Response(
                json.dumps({"error": result.error_msg}),
                status=status,
                content_type="application/json")

        return Response(
            json.dumps({"projects": result.data}),
            status=HTTPStatus.OK,
            content_type="application/json")
