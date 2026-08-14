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
from items.services.items_identity.data_access.project_member_repository import (
    ProjectMemberRepository)
from items.services.items_identity.data_access.role_repository import (
    RoleRepository)
from items.services.items_identity.data_access.user_repository import (
    UserRepository)
from items.services.items_identity.identity_configuration import (
    IdentityConfiguration)
from items.services.items_identity.routes.users.schemas import (
    SCHEMA_ADD_USER_PROJECT_REQUEST)
from items.services.items_identity.services.project_membership_service import (
    ProjectMembershipService)
from items.shared.service_state import ServiceState


class AddUserProjectHandler(BaseApiRoute):
    """Handles POST /users/<user_id>/projects — add the user to a project."""

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

    @validate_json(SCHEMA_ADD_USER_PROJECT_REQUEST)
    async def add_user_project(self, request_msg: ApiResponse,
                               user_id: str) -> Response:
        """Add a user to a project, optionally assigning a role.

        Args:
            request_msg: Validated request containing ``project_id`` and
                optionally ``role_id`` (defaults to ``null`` - "member, no
                role assigned yet", a valid state, not a placeholder).
            user_id: The user's UUID (from the URL).

        Returns:
            201 on success.
            400 if ``role_id`` is supplied but no such role exists.
            404 if no user exists with that UUID.
            409 if the user is already a member of this project.
            503 if the service is unavailable.
        """
        body = request_msg.body
        result = await self._service.add_membership(
            user_uuid=user_id,
            project_id=body["project_id"],
            role_id=body.get("role_id"))

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

        if result.role_not_found:
            return Response(
                json.dumps({"error": "No role exists with that id"}),
                status=HTTPStatus.BAD_REQUEST,
                content_type="application/json")

        if result.conflict:
            return Response(
                json.dumps(
                    {"error": "User is already a member of this project"}),
                status=HTTPStatus.CONFLICT,
                content_type="application/json")

        return Response(
            json.dumps({"status": "ok"}),
            status=HTTPStatus.CREATED,
            content_type="application/json")
