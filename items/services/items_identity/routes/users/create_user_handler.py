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
    SCHEMA_CREATE_USER_REQUEST)
from items.services.items_identity.services.user_management_service import (
    UserManagementService)
from items.shared.service_state import ServiceState


class CreateUserHandler(BaseApiRoute):
    """Handles POST /users — create a new user account."""

    def __init__(self,
                 logger: logging.Logger,
                 service_state: ServiceState,
                 configuration: IdentityConfiguration) -> None:
        self._logger = logger.getChild(__name__)
        self._service_state: ServiceState = service_state

        repo = UserRepository(self._logger, configuration)
        self._service = UserManagementService(
            self._logger, self._service_state, repo)

    @validate_json(SCHEMA_CREATE_USER_REQUEST)
    async def create_user(self, request_msg: ApiResponse) -> Response:
        """Create a new user account.

        Args:
            request_msg: Validated request containing ``email_address``,
                ``full_name``, ``display_name``, ``password``, and
                optionally ``is_administrator`` (defaults to ``false``).

        Returns:
            201 with ``{"id": <new_user_id>}`` on success.
            409 if the email address is already registered.
            503 if the service is unavailable.
        """
        body = request_msg.body
        result = await self._service.create_user(
            email=body["email_address"],
            full_name=body["full_name"],
            display_name=body["display_name"],
            password=body.get("password"),
            is_administrator=body.get("is_administrator", False))

        if not result.available:
            return Response(
                json.dumps({"error": "Service unavailable"}),
                status=HTTPStatus.SERVICE_UNAVAILABLE,
                content_type="application/json")

        if result.conflict:
            return Response(
                json.dumps({"error": "Email address already registered"}),
                status=HTTPStatus.CONFLICT,
                content_type="application/json")

        response_body: dict = {"id": result.user_id}
        if result.generated_password is not None:
            response_body["generated_password"] = result.generated_password
        return Response(
            json.dumps(response_body),
            status=HTTPStatus.CREATED,
            content_type="application/json")
