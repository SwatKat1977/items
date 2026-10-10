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


class DeleteCaseTypeHandler(BaseApiRoute):
    """Handles DELETE /case_types/<type_id> requests.

    Test cases using the deleted type are moved to the current default
    type, in the same transaction as the delete. The default type itself
    can never be deleted.
    """

    def __init__(self,
                 logger: logging.Logger,
                 service: CaseTypesService) -> None:
        """Initialise the handler.

        Args:
            logger:  Parent logger instance.
            service: Case types service used to delete case types.
        """
        self._logger = logger.getChild(__name__)
        self._service = service

    async def delete_case_type(self, type_id: int) -> Response:
        """Delete a case type, moving its test cases to the default type.

        Path parameters:
            type_id (int): ID of the case type to delete.

        Returns:
            200 with ``{}`` on success.
            404 if no case type exists with the given ID.
            409 if the case type is the default, which is never deleted.
            500 on an internal database error.
        """
        result = await self._service.delete_case_type(type_id)

        if not result.success:
            status = (HTTPStatus.INTERNAL_SERVER_ERROR if result.is_internal
                      else HTTPStatus.NOT_FOUND if result.not_found
                      else HTTPStatus.CONFLICT if result.is_conflict
                      else HTTPStatus.BAD_REQUEST)
            return Response(
                json.dumps({"error": result.error_msg}),
                status=status,
                content_type="application/json")

        return Response(
            json.dumps({}),
            status=HTTPStatus.OK,
            content_type="application/json")
