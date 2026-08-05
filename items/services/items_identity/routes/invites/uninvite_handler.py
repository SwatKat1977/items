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
    SCHEMA_UNINVITE_REQUEST)
from items.services.items_identity.services.invite_management_service import (
    InviteManagementService, InviteUninviteStatus)


class UninviteHandler(BaseApiRoute):
    """Handles POST /invites/uninvite — soft-expire a pending invite."""

    def __init__(self,
                 logger: logging.Logger,
                 configuration: IdentityConfiguration) -> None:
        self._logger = logger.getChild(__name__)
        invite_repo = InviteRepository(self._logger, configuration)
        user_repo = UserRepository(self._logger, configuration)
        self._service = InviteManagementService(
            self._logger, invite_repo, user_repo)

    @validate_json(SCHEMA_UNINVITE_REQUEST)
    async def uninvite(self, request_msg: ApiResponse) -> Response:
        """Cancel a pending invite by soft-expiring it.

        Args:
            request_msg: Validated request containing ``email_address``.

        Returns:
            200 on success.
            404 if no pending invite exists for the email address.
        """
        email_address: str = request_msg.body["email_address"]
        result = await self._service.uninvite(email_address)

        if result.status == InviteUninviteStatus.NO_PENDING_INVITE:
            return Response(
                json.dumps({"error": "No pending invite found for this email address"}),
                status=HTTPStatus.NOT_FOUND,
                content_type="application/json")

        return Response(
            json.dumps({}),
            status=HTTPStatus.OK,
            content_type="application/json")
