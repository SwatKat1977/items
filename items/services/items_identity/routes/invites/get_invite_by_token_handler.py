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


class GetInviteByTokenHandler(BaseApiRoute):
    """Handles GET /invites/token/<token> — resolve an invitation link.

    Called when an invited person opens their invitation link, so that the
    address the account is created for comes from the invite record rather
    than from anything the recipient supplies.

    Unknown, cancelled and expired tokens all return 404. They are not
    distinguished, so this endpoint cannot be used to discover whether a
    particular token exists.
    """

    def __init__(self,
                 logger: logging.Logger,
                 configuration: IdentityConfiguration) -> None:
        self._logger = logger.getChild(__name__)
        invite_repo = InviteRepository(self._logger, configuration)
        user_repo = UserRepository(self._logger, configuration)
        self._service = InviteManagementService(
            self._logger, invite_repo, user_repo)

    async def get_invite_by_token(self, token: str) -> Response:
        """Resolve an invite token to the address it was issued to.

        Args:
            token: The token from the invitation link.

        Returns:
            200 with ``{"email_address": <address>}`` when the token matches a
            pending, unexpired invite.
            404 otherwise - whether the token is unknown, already used,
            cancelled or expired.
        """
        result = await self._service.get_invite_by_token(token)

        if not result.valid:
            return Response(
                json.dumps({"error": "Invite not found or no longer valid"}),
                status=HTTPStatus.NOT_FOUND,
                content_type="application/json")

        return Response(
            json.dumps({"email_address": result.email_address}),
            status=HTTPStatus.OK,
            content_type="application/json")
