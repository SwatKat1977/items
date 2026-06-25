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
from items.services.items_cms.services.testcase_custom_fields_service import (
    TestcaseCustomFieldsService,
)


class GetCustomFieldsHandler(BaseApiRoute):
    """Handles GET /testcase_custom_fields requests."""

    def __init__(self,
                 logger: logging.Logger,
                 service: TestcaseCustomFieldsService) -> None:
        """Initialise the handler.

        Args:
            logger:  Parent logger instance.
            service: Custom fields service used to retrieve field definitions.
        """
        self._logger = logger.getChild(__name__)
        self._service = service

    async def get_custom_fields(self) -> Response:
        """Retrieve testcase custom field definitions.

        Query parameters:
            project_id (int, optional): If provided, return only the fields
                                        applicable to that project. If omitted,
                                        all fields are returned.

        Returns:
            200 with a list of custom field rows on success.
            400 if ``project_id`` is present but not a valid integer.
            500 on an internal database error.
        """
        project_id: int | None = None
        project_id_param = quart.request.args.get("project_id")

        if project_id_param is not None:
            try:
                project_id = int(project_id_param)
            except ValueError:
                return Response(
                    json.dumps({"error": "project_id must be an integer"}),
                    status=HTTPStatus.BAD_REQUEST,
                    content_type="application/json")

        result = await self._service.get_custom_fields(project_id)

        if not result.success:
            return Response(
                json.dumps({"error": result.error_msg}),
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
                content_type="application/json")

        return Response(
            json.dumps(result.data),
            status=HTTPStatus.OK,
            content_type="application/json")
