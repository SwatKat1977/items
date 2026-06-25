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
from items.services.items_cms.services.testcase_custom_fields_service import (
    TestcaseCustomFieldsService,
)


class UpdateCustomFieldHandler(BaseApiRoute):
    """Handles PUT /testcase_custom_fields/<field_id> requests."""

    def __init__(self,
                 logger: logging.Logger,
                 service: TestcaseCustomFieldsService) -> None:
        """Initialise the handler.

        Args:
            logger:  Parent logger instance.
            service: Custom fields service (not yet used by this stub).
        """
        self._logger = logger.getChild(__name__)
        self._service = service

    async def update_custom_field(self, field_id: int) -> Response:
        """Update a testcase custom field definition.

        Not yet implemented.

        Path parameters:
            field_id (int): ID of the field to update.

        Returns:
            501 Not Implemented.
        """
        return Response(
            json.dumps({"error": "Update custom field is not yet implemented"}),
            status=HTTPStatus.NOT_IMPLEMENTED,
            content_type="application/json")
