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
from items.services.items_cms.services.case_types_service import (
    CaseTypesService,
)


class GetCaseTypesHandler(BaseApiRoute):
    """Handles GET /case_types requests."""

    def __init__(self,
                 logger: logging.Logger,
                 service: CaseTypesService) -> None:
        """Initialise the handler.

        Args:
            logger:  Parent logger instance.
            service: Case types service used to retrieve type definitions.
        """
        self._logger = logger.getChild(__name__)
        self._service = service

    async def get_case_types(self) -> Response:
        """Retrieve every case type.

        Returns:
            200 with a list of case type rows on success.
            500 on an internal database error.
        """
        result = await self._service.get_all_case_types()

        if not result.success:
            return Response(
                json.dumps({"error": result.error_msg}),
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
                content_type="application/json")

        return Response(
            json.dumps(result.data),
            status=HTTPStatus.OK,
            content_type="application/json")
