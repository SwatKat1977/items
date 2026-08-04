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
from items.services.items_identity.data_access.user_repository import (
    UserRepository)
from items.services.items_identity.identity_configuration import (
    IdentityConfiguration)
from items.services.items_identity.routes.users.schemas import (
    SCHEMA_CHANGE_PASSWORD_REQUEST)
from items.services.items_identity.services.user_management_service import (
    UserManagementService)
from items.shared.service_state import ServiceState


class ChangePasswordHandler(BaseApiRoute):
    """Handles POST /users/me/password — user self-service password change."""

    def __init__(self,
                 logger: logging.Logger,
                 service_state: ServiceState,
                 configuration: IdentityConfiguration) -> None:
        self._logger = logger.getChild(__name__)
        self._service_state: ServiceState = service_state

        repo = UserRepository(self._logger, configuration)
        self._service = UserManagementService(
            self._logger, self._service_state, repo)

    @validate_json(SCHEMA_CHANGE_PASSWORD_REQUEST)
    async def change_password(self, request_msg: ApiResponse) -> Response:
        """Change a user's own password after verifying the current one.

        The gateway resolves the session to a ``user_id`` and passes it in
        the request body alongside the old and new passwords. Identity
        verifies the current password before applying the change.

        Args:
            request_msg: Validated request containing ``user_id``,
                ``current_password``, and ``new_password``.

        Returns:
            200 on success.
            401 if the current password is wrong.
            404 if no user exists with that ID.
            503 if the service is unavailable.
        """
        body = request_msg.body
        result = await self._service.change_own_password(
            user_uuid=body["user_id"],
            current_password=body["current_password"],
            new_password=body["new_password"])

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

        if result.wrong_password:
            return Response(
                json.dumps({"error": "Current password is incorrect"}),
                status=HTTPStatus.UNAUTHORIZED,
                content_type="application/json")

        return Response(
            json.dumps({"status": "ok"}),
            status=HTTPStatus.OK,
            content_type="application/json")
