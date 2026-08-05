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
from items.services.items_identity.data_access.invite_repository import (
    InviteRepository)
from items.services.items_identity.data_access.user_repository import (
    UserRepository)
from items.services.items_identity.identity_configuration import (
    IdentityConfiguration)
from items.services.items_identity.routes.invites.schemas import (
    SCHEMA_CREATE_INVITE_REQUEST)
from items.services.items_identity.services.invite_management_service import (
    InviteManagementService, InviteCreateStatus)


class CreateInviteHandler(BaseApiRoute):
    """Handles POST /invites — create a new user invite."""

    def __init__(self,
                 logger: logging.Logger,
                 configuration: IdentityConfiguration) -> None:
        self._logger = logger.getChild(__name__)
        invite_repo = InviteRepository(self._logger, configuration)
        user_repo = UserRepository(self._logger, configuration)
        self._service = InviteManagementService(
            self._logger, invite_repo, user_repo)

    @validate_json(SCHEMA_CREATE_INVITE_REQUEST)
    async def create_invite(self, request_msg: ApiResponse) -> Response:
        """Create a new pending invite for an email address.

        Args:
            request_msg: Validated request containing ``email_address``.

        Returns:
            201 with ``{"token": <uuid>}`` on success.
            409 if the email is already registered or already has a pending invite.
        """
        email_address: str = request_msg.body["email_address"]
        result = await self._service.create_invite(email_address)

        if result.status == InviteCreateStatus.ALREADY_REGISTERED:
            return Response(
                json.dumps({"error": "Email address is already registered"}),
                status=HTTPStatus.CONFLICT,
                content_type="application/json")

        if result.status == InviteCreateStatus.ALREADY_INVITED:
            return Response(
                json.dumps({"error": "A pending invite already exists for this email"}),
                status=HTTPStatus.CONFLICT,
                content_type="application/json")

        return Response(
            json.dumps({"token": result.token}),
            status=HTTPStatus.CREATED,
            content_type="application/json")
