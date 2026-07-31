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
    SCHEMA_CREATE_USER_REQUEST,
    SCHEMA_SET_PASSWORD_REQUEST,
    SCHEMA_UPDATE_USER_REQUEST)
from items.services.items_identity.services.user_management_service import (
    UserManagementResult, UserManagementService)
from items.shared.service_state import ServiceState


class UserManagementHandler(BaseApiRoute):
    """Handles user account management requests.

    Provides listing, retrieval, creation, update and password reset. There is
    no deletion endpoint - accounts are deactivated instead, for the reasons
    set out in section 10.6 of ``design_docs/user_roles_design.md``.

    These endpoints do not authenticate their caller. Identity is reachable
    only via the gateway in production, and the gateway is responsible for
    enforcing that the requester is an administrator (section 9.1).
    """

    def __init__(self,
                 logger: logging.Logger,
                 service_state: ServiceState,
                 configuration: IdentityConfiguration) -> None:
        """Initialise the user management handler.

        Args:
            logger:        Logger used for diagnostic messages.
            service_state: Shared service state used to determine
                availability.
            configuration: Identity service configuration.
        """
        self._logger = logger.getChild(__name__)
        self._service_state: ServiceState = service_state

        user_repository: UserRepository = UserRepository(self._logger,
                                                         configuration)
        self._service: UserManagementService = UserManagementService(
            self._logger, self._service_state, user_repository)

    # ------------------------------------------------------------------
    # Reads
    # ------------------------------------------------------------------

    async def list_users(self) -> Response:
        """List all user accounts.

        Returns:
            200 with ``{"users": [...]}`` on success, or 503 if unavailable.
        """
        result = await self._service.list_users()

        if not result.available:
            return self._unavailable()

        return self._json({"users": result.users}, HTTPStatus.OK)

    async def get_user(self, user_id: int) -> Response:
        """Retrieve a single user account.

        Args:
            user_id: Identifier of the account.

        Returns:
            200 with the account, 404 if it does not exist, 503 if
            unavailable.
        """
        result = await self._service.get_user(user_id)
        return self._respond(result)

    # ------------------------------------------------------------------
    # Writes
    # ------------------------------------------------------------------

    @validate_json(SCHEMA_CREATE_USER_REQUEST)
    async def create_user(self, request_msg: ApiResponse) -> Response:
        """Create a user account.

        When ``password`` is omitted, one is generated and returned in the
        response exactly once - it cannot be retrieved again afterwards.

        Args:
            request_msg: Validated request body.

        Returns:
            201 with the created account, 409 if the email address is already
            in use, 503 if unavailable.
        """
        body: dict = request_msg.body

        result = await self._service.create_user(
            email=body["email_address"],
            full_name=body["full_name"],
            display_name=body["display_name"],
            is_administrator=body.get("is_administrator", False),
            enabled=body.get("enabled", True),
            password=body.get("password"))

        return self._respond(result, success_status=HTTPStatus.CREATED)

    @validate_json(SCHEMA_UPDATE_USER_REQUEST)
    async def update_user(self, request_msg: ApiResponse,
                          user_id: int) -> Response:
        """Update a user account.

        Only supplied fields are changed. Setting ``enabled`` to false
        deactivates the account, which is how accounts are retired.

        Args:
            request_msg: Validated request body.
            user_id:     Identifier of the account to update.

        Returns:
            200 with the updated account, 404 if it does not exist, 409 if the
            change conflicts (duplicate address, or it would leave no active
            administrator), 503 if unavailable.
        """
        body: dict = request_msg.body

        result = await self._service.update_user(
            user_id=user_id,
            email=body.get("email_address"),
            full_name=body.get("full_name"),
            display_name=body.get("display_name"),
            is_administrator=body.get("is_administrator"),
            enabled=body.get("enabled"))

        return self._respond(result)

    @validate_json(SCHEMA_SET_PASSWORD_REQUEST)
    async def set_password(self, request_msg: ApiResponse,
                           user_id: int) -> Response:
        """Set or reset a user's password.

        When ``password`` is omitted, one is generated and returned in the
        response exactly once.

        Args:
            request_msg: Validated request body.
            user_id:     Identifier of the account.

        Returns:
            200 on success, 404 if the account does not exist, 503 if
            unavailable.
        """
        result = await self._service.set_password(
            user_id=user_id,
            password=request_msg.body.get("password"))

        return self._respond(result)

    # ------------------------------------------------------------------
    # Response helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _json(body: dict, status: HTTPStatus) -> Response:
        """Build a JSON response."""
        return Response(json.dumps(body),
                        status=status,
                        content_type="application/json")

    def _unavailable(self) -> Response:
        """Build the 503 response used when the service cannot serve."""
        return self._json({"error": "Service unavailable"},
                          HTTPStatus.SERVICE_UNAVAILABLE)

    def _respond(self,
                 result: UserManagementResult,
                 success_status: HTTPStatus = HTTPStatus.OK) -> Response:
        """Map a service result onto an HTTP response.

        Failure conditions are checked most-severe first so that an outage is
        never reported as a missing account, and a missing account is never
        reported as a conflict.

        Args:
            result:         The service result to translate.
            success_status: Status to use on success.

        Returns:
            The corresponding JSON response.
        """
        if not result.available:
            return self._unavailable()

        if not result.found:
            return self._json({"error": "User not found"},
                              HTTPStatus.NOT_FOUND)

        if result.conflict is not None:
            return self._json({"error": result.conflict},
                              HTTPStatus.CONFLICT)

        body: dict = dict(result.user) if result.user else {}

        # Present only when the caller did not supply a password. This is the
        # only time it is ever available - it is not stored in plaintext.
        if result.generated_password is not None:
            body["generated_password"] = result.generated_password

        return self._json(body, success_status)
