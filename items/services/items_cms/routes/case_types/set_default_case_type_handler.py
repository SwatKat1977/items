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


class SetDefaultCaseTypeHandler(BaseApiRoute):
    """Handles POST /case_types/<type_id>/set_default requests.

    A dedicated action rather than a field on the general update
    endpoint, since making a type the default is a swap affecting two
    rows (un-defaulting whichever held it, defaulting this one) rather
    than a plain edit on one.
    """

    def __init__(self,
                 logger: logging.Logger,
                 service: CaseTypesService) -> None:
        """Initialise the handler.

        Args:
            logger:  Parent logger instance.
            service: Case types service used to change the default type.
        """
        self._logger = logger.getChild(__name__)
        self._service = service

    async def set_default_case_type(self, type_id: int) -> Response:
        """Make a case type the default, un-defaulting whichever held it.

        Idempotent - calling this on the type that's already the default
        succeeds without error.

        Path parameters:
            type_id (int): ID of the case type to make the default.

        Returns:
            200 with ``{}`` on success.
            404 if no case type exists with the given ID.
            500 on an internal database error.
        """
        result = await self._service.set_default_case_type(type_id)

        if not result.success:
            status = (HTTPStatus.INTERNAL_SERVER_ERROR if result.is_internal
                      else HTTPStatus.NOT_FOUND if result.not_found
                      else HTTPStatus.BAD_REQUEST)
            return Response(
                json.dumps({"error": result.error_msg}),
                status=status,
                content_type="application/json")

        return Response(
            json.dumps({}),
            status=HTTPStatus.OK,
            content_type="application/json")
