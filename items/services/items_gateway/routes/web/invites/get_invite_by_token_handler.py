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
from weaver_framework.microservice.rest_client import RestClient
from items.services.items_gateway.gateway_configuration import GatewayConfiguration


class GetInviteByTokenHandler(BaseApiRoute):
    """Handles GET /invites/token/<token> — resolve an invitation link.

    **Deliberately unauthenticated**, like ``POST /accept_invite``: someone
    opening an invitation link has no account yet. It exists so the setup page
    can show the invited address read-only, rather than asking the recipient
    to type it - which would let an invitation be redeemed for a different
    address.

    Only the email address is returned. Unknown, expired and cancelled tokens
    are all reported as 404 and cannot be told apart, so this cannot be used
    to probe for valid tokens.
    """

    def __init__(self,
                 logger: logging.Logger,
                 configuration: GatewayConfiguration,
                 rest_client: RestClient) -> None:
        self._logger = logger.getChild(type(self).__name__)
        self._configuration = configuration
        self._rest_client = rest_client

    async def get_invite_by_token(self, token: str) -> Response:
        """Resolve an invite token to the address it was issued to.

        Args:
            token: The token from the invitation link.

        Returns:
            200 with ``{"email_address": <address>}`` for a usable invite.
            404 if the token is unknown, used, cancelled or expired.
            500 if the identity service is unreachable.
        """
        url: str = (f"{self._configuration.apis_identity_svc}"
                    f"invites/token/{token}")
        response: ApiResponse = await self._rest_client.get(url)

        if response.exception_msg is not None:
            self._logger.error("Connection to identity service failed: %s",
                               response.exception_msg)
            return Response(
                json.dumps({"error": "Identity service unavailable"}),
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
                content_type="application/json")

        if response.status_code != HTTPStatus.OK:
            return Response(
                json.dumps({"error": "Invite not found or no longer valid"}),
                status=HTTPStatus.NOT_FOUND,
                content_type="application/json")

        return Response(
            json.dumps({"email_address":
                        (response.body or {}).get("email_address")}),
            status=HTTPStatus.OK,
            content_type="application/json")
