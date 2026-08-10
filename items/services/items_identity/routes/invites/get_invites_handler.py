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
from items.services.items_identity.data_access.invite_repository import (
    InviteRepository)
from items.services.items_identity.data_access.user_repository import (
    UserRepository)
from items.services.items_identity.identity_configuration import (
    IdentityConfiguration)
from items.services.items_identity.services.invite_management_service import (
    InviteManagementService)


class GetInvitesHandler(BaseApiRoute):
    """Handles GET /invites — list all pending invites."""

    def __init__(self,
                 logger: logging.Logger,
                 configuration: IdentityConfiguration) -> None:
        self._logger = logger.getChild(__name__)
        invite_repo = InviteRepository(self._logger, configuration)
        user_repo = UserRepository(self._logger, configuration)
        self._service = InviteManagementService(
            self._logger, invite_repo, user_repo)

    async def get_invites(self) -> Response:
        """Return every pending invite.

        Returns:
            200 with ``{"invites": [{"email_address", "created_at",
            "expires_at"}, ...]}``, ordered by creation time (oldest
            first). Always 200 - an empty pending-invite list is not an
            error condition.
        """
        invites = await self._service.get_pending_invites()

        return Response(
            json.dumps({"invites": [
                {"email_address": invite.email_address,
                 "created_at": invite.created_at,
                 "expires_at": invite.expires_at}
                for invite in invites
            ]}),
            status=HTTPStatus.OK,
            content_type="application/json")
