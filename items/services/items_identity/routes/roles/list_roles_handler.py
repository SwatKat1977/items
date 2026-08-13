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


class ListRolesHandler(BaseApiRoute):
    """Handles GET /roles — return all roles (name only, not their grids)."""

    def __init__(self,
                 logger: logging.Logger,
                 service_state: ServiceState,
                 configuration: IdentityConfiguration) -> None:
        self._logger = logger.getChild(__name__)
        self._service_state: ServiceState = service_state

        repo = RoleRepository(self._logger, configuration)
        self._service = RoleManagementService(
            self._logger, self._service_state, repo)

    async def list_roles(self) -> Response:
        """Return all roles as a JSON array.

        Returns:
            200 with ``{"roles": [...]}`` on success. Each entry is
            ``{"id": ..., "name": ...}`` - use ``GET /roles/<id>`` for a
            role's full permission grid.
            503 if the service is unavailable.
        """
        result = await self._service.get_all_roles()

        if not result.available:
            return Response(
                json.dumps({"error": "Service unavailable"}),
                status=HTTPStatus.SERVICE_UNAVAILABLE,
                content_type="application/json")

        return Response(
            json.dumps({"roles": result.roles}),
            status=HTTPStatus.OK,
            content_type="application/json")
