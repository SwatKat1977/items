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
from weaver_framework.microservice.base_api_route import BaseApiRoute
from items.services.items_identity.data_access.role_repository import (
    RoleRepository)
from items.services.items_identity.identity_configuration import (
    IdentityConfiguration)
from items.services.items_identity.services.role_management_service import (
    RoleManagementService)
from items.shared.service_state import ServiceState


class DeleteRoleHandler(BaseApiRoute):
    """Handles DELETE /roles/<role_id> — delete a role."""

    def __init__(self,
                 logger: logging.Logger,
                 service_state: ServiceState,
                 configuration: IdentityConfiguration) -> None:
        self._logger = logger.getChild(__name__)
        self._service_state: ServiceState = service_state

        repo = RoleRepository(self._logger, configuration)
        self._service = RoleManagementService(
            self._logger, self._service_state, repo)

    async def delete_role(self, role_id: int) -> Response:
        """Delete a role.

        Any project membership holding this role has its role assignment
        cleared, not deleted - the membership itself remains (§4.3 of
        user_roles_design.md).

        Args:
            role_id: The role's id (from the URL).

        Returns:
            200 on success.
            404 if no role exists with that id.
            503 if the service is unavailable.
        """
        result = await self._service.delete_role(role_id)

        if not result.available:
            return Response(
                json.dumps({"error": "Service unavailable"}),
                status=HTTPStatus.SERVICE_UNAVAILABLE,
                content_type="application/json")

        if not result.found:
            return Response(
                json.dumps({"error": "Role not found"}),
                status=HTTPStatus.NOT_FOUND,
                content_type="application/json")

        return Response(
            json.dumps({"status": "ok"}),
            status=HTTPStatus.OK,
            content_type="application/json")
