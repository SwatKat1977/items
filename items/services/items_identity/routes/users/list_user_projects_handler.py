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
from items.services.items_identity.data_access.project_member_repository import (
    ProjectMemberRepository)
from items.services.items_identity.data_access.role_repository import (
    RoleRepository)
from items.services.items_identity.data_access.user_repository import (
    UserRepository)
from items.services.items_identity.identity_configuration import (
    IdentityConfiguration)
from items.services.items_identity.services.project_membership_service import (
    ProjectMembershipService)
from items.shared.service_state import ServiceState


class ListUserProjectsHandler(BaseApiRoute):
    """Handles GET /users/<user_id>/projects — list a user's memberships."""

    def __init__(self,
                 logger: logging.Logger,
                 service_state: ServiceState,
                 configuration: IdentityConfiguration) -> None:
        self._logger = logger.getChild(__name__)
        self._service_state: ServiceState = service_state

        member_repo = ProjectMemberRepository(self._logger, configuration)
        user_repo = UserRepository(self._logger, configuration)
        role_repo = RoleRepository(self._logger, configuration)
        self._service = ProjectMembershipService(
            self._logger, self._service_state,
            member_repo, user_repo, role_repo)

    async def list_user_projects(self, user_id: str) -> Response:
        """Return every project membership held by a user.

        Args:
            user_id: The user's UUID (from the URL).

        Returns:
            200 with ``{"memberships": [...]}`` on success. Each entry is
            ``{"project_id", "role_id", "role_name"}`` - the latter two are
            ``null`` when the membership has no role assigned.
            404 if no user exists with that UUID.
            503 if the service is unavailable.
        """
        result = await self._service.get_memberships(user_id)

        if not result.available:
            return Response(
                json.dumps({"error": "Service unavailable"}),
                status=HTTPStatus.SERVICE_UNAVAILABLE,
                content_type="application/json")

        if not result.found:
            return Response(
                json.dumps({"error": "User not found"}),
                status=HTTPStatus.NOT_FOUND,
                content_type="application/json")

        return Response(
            json.dumps({"memberships": result.memberships}),
            status=HTTPStatus.OK,
            content_type="application/json")
