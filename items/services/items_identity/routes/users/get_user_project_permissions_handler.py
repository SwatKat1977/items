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


class GetUserProjectPermissionsHandler(BaseApiRoute):
    """Handles GET /users/<user_id>/projects/<project_id>/permissions.

    Returns what a user may do in one project, resolved per
    ``user_roles_design.md`` section 8. The Gateway calls this on every
    permission-gated request (section 9.5), so it only reads and never
    changes anything.
    """

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

    async def get_user_project_permissions(self, user_id: str,
                                           project_id: int) -> Response:
        """Return a user's effective permissions in a project.

        Args:
            user_id: The user's UUID (from the URL).
            project_id: The project's id (from the URL).

        Returns:
            200 with ``{"project_id", "areas"}`` on success. ``areas`` has
            an entry for every area, each ``{"read", "add_modify",
            "delete"}``. A non-member, a member with no role and a disabled
            account all get 200 with every flag false: having no access is
            an answer, not an error.
            404 if no user exists with that UUID.
            503 if the service is unavailable.
        """
        result = await self._service.get_effective_permissions(user_id,
                                                               project_id)

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
            json.dumps({"project_id": project_id, "areas": result.areas}),
            status=HTTPStatus.OK,
            content_type="application/json")
