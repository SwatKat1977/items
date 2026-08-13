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
from http import HTTPStatus
import json
import logging
from quart import Response
from weaver_framework.microservice.api_response import ApiResponse
from weaver_framework.microservice.base_api_route import BaseApiRoute
from weaver_framework.microservice.microservice_decorators import validate_json
from items.services.items_identity.data_access.role_repository import (
    RoleRepository)
from items.services.items_identity.identity_configuration import (
    IdentityConfiguration)
from items.services.items_identity.routes.roles.schemas import (
    SCHEMA_MODIFY_ROLE_REQUEST)
from items.services.items_identity.services.role_management_service import (
    RoleManagementService)
from items.shared.service_state import ServiceState


class ModifyRoleHandler(BaseApiRoute):
    """Handles PATCH /roles/<role_id> — update a role's name and/or grid."""

    def __init__(self,
                 logger: logging.Logger,
                 service_state: ServiceState,
                 configuration: IdentityConfiguration) -> None:
        self._logger = logger.getChild(__name__)
        self._service_state: ServiceState = service_state

        repo = RoleRepository(self._logger, configuration)
        self._service = RoleManagementService(
            self._logger, self._service_state, repo)

    @validate_json(SCHEMA_MODIFY_ROLE_REQUEST)
    async def modify_role(self, request_msg: ApiResponse,
                          role_id: int) -> Response:
        """Update a role's name and/or replace its permission grid.

        Args:
            request_msg: Validated request. All fields are optional:
                ``name``, ``permissions``. Omitted fields retain their
                current values. ``permissions``, when present, *replaces*
                the entire grid - see ``RoleRepository`` for why there is
                no partial update.
            role_id: The role's id (from the URL).

        Returns:
            200 on success.
            400 if the supplied grid violates Add/Modify-implies-Read, or
            repeats the same area more than once.
            404 if no role exists with that id.
            409 if renaming to a name already in use by another role.
            503 if the service is unavailable.
        """
        body = request_msg.body
        result = await self._service.update_role(
            role_id=role_id,
            name=body.get("name"),
            permissions=body.get("permissions"))

        if not result.available:
            return Response(
                json.dumps({"error": "Service unavailable"}),
                status=HTTPStatus.SERVICE_UNAVAILABLE,
                content_type="application/json")

        if result.invalid:
            return Response(
                json.dumps({"error": "Invalid permission grid - "
                           "Add/Modify requires Read, and each area may "
                           "appear at most once"}),
                status=HTTPStatus.BAD_REQUEST,
                content_type="application/json")

        if not result.found:
            return Response(
                json.dumps({"error": "Role not found"}),
                status=HTTPStatus.NOT_FOUND,
                content_type="application/json")

        if result.conflict:
            return Response(
                json.dumps({"error": "Role name already in use"}),
                status=HTTPStatus.CONFLICT,
                content_type="application/json")

        return Response(
            json.dumps({"status": "ok"}),
            status=HTTPStatus.OK,
            content_type="application/json")
