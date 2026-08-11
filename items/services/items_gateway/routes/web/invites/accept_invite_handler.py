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
from quart import request, Response
from weaver_framework.microservice.api_response import ApiResponse
from weaver_framework.microservice.base_api_route import BaseApiRoute
from weaver_framework.microservice.rest_client import RestClient
from items.services.items_gateway.gateway_configuration import GatewayConfiguration
from items.services.items_gateway.services.email_service import EmailService
from items.services.items_gateway.services.invite_email import (
    send_welcome_email)

_REQUIRED_FIELDS = ("token", "full_name", "display_name", "password")


class AcceptInviteHandler(BaseApiRoute):
    """Handles POST /accept_invite — redeem an invitation.

    This is the one route an unauthenticated caller is *meant* to be able to
    reach: the person accepting an invite does not yet have an account. The
    invite token is what authorises the request, so it is validated here
    rather than being trusted from the page that submitted the form.

    The email address is taken from the invite record, never from the request
    body. Otherwise an invitation issued to one address could be redeemed to
    create an account for another.

    The invite is consumed *before* the account is created. If consuming
    succeeded and creation then failed, the invite is spent and an
    administrator must reissue it - which is a nuisance. The other ordering
    would leave a live invite that could be redeemed repeatedly, which is a
    security hole. The nuisance is the better failure.
    """

    def __init__(self,
                 logger: logging.Logger,
                 configuration: GatewayConfiguration,
                 rest_client: RestClient,
                 email_service: EmailService | None = None) -> None:
        self._logger = logger.getChild(type(self).__name__)
        self._configuration = configuration
        self._rest_client = rest_client
        self._email_service = email_service

    async def accept_invite(self) -> Response:
        """Redeem an invitation and create the invited user's account.

        Returns:
            201 with the created user on success.
            400 if the body is missing fields or is not valid JSON.
            404 if the token is unknown, already used, cancelled or expired.
            500 if the identity service is unreachable, or if the account
            could not be created after the invite was consumed.
        """
        body = await request.get_json(force=True, silent=True)
        if body is None:
            return self._error("Invalid JSON body", HTTPStatus.BAD_REQUEST)

        missing = [f for f in _REQUIRED_FIELDS if not body.get(f)]
        if missing:
            return self._error(
                f"Missing required field(s): {', '.join(missing)}",
                HTTPStatus.BAD_REQUEST)

        # 1. Resolve the token. The address comes from here, not the caller.
        email_address = await self._resolve_token(body["token"])
        if email_address is None:
            return self._error("Invite not found or no longer valid",
                               HTTPStatus.NOT_FOUND)

        # 2. Consume the invite before creating anything (see class docstring).
        consumed = await self._consume_invite(email_address)
        if not consumed:
            return self._error("Could not redeem this invite",
                               HTTPStatus.INTERNAL_SERVER_ERROR)

        # 3. Create the account.
        create_response = await self._create_user(body, email_address)

        if create_response.status_code != HTTPStatus.CREATED:
            self._logger.error(
                "Invite for %s was consumed but account creation failed "
                "(status %s). The invite must be reissued.",
                email_address, create_response.status_code)
            return self._error(
                "Your invitation could not be completed. Please ask an "
                "administrator to send a new invitation.",
                HTTPStatus.INTERNAL_SERVER_ERROR)

        # 4. Confirm to the new user. Never fails the request.
        await send_welcome_email(
            logger=self._logger,
            email_service=self._email_service,
            portal_url=self._configuration.apis_web_portal_svc,
            email_address=email_address,
            display_name=body["display_name"])

        self._logger.info("Invite accepted; account created for %s",
                          email_address)

        return Response(json.dumps(create_response.body),
                        status=HTTPStatus.CREATED,
                        content_type="application/json")

    # ------------------------------------------------------------------
    # Steps
    # ------------------------------------------------------------------

    async def _resolve_token(self, token: str) -> str | None:
        """Return the address an invite was issued to, or None if unusable."""
        url = (f"{self._configuration.apis_identity_svc}"
               f"invites/token/{token}")
        response: ApiResponse = await self._rest_client.get(url)

        if response.exception_msg is not None:
            self._logger.error("Connection to identity service failed: %s",
                               response.exception_msg)
            return None

        if response.status_code != HTTPStatus.OK:
            return None

        return (response.body or {}).get("email_address")

    async def _consume_invite(self, email_address: str) -> bool:
        """Mark the invite as used so the link cannot be redeemed again."""
        url = f"{self._configuration.apis_identity_svc}invites/uninvite"
        response: ApiResponse = await self._rest_client.post(
            url, json_data={"email_address": email_address})

        if response.exception_msg is not None or \
                response.status_code != HTTPStatus.OK:
            self._logger.error(
                "Could not consume invite for %s (status %s); refusing to "
                "create the account, as the invite would remain redeemable",
                email_address, response.status_code)
            return False

        return True

    async def _create_user(self, body: dict,
                           email_address: str) -> ApiResponse:
        """Create the account, using the address from the invite."""
        url = f"{self._configuration.apis_identity_svc}users"
        return await self._rest_client.post(url, json_data={
            # Deliberately from the invite, not from the submitted form.
            "email_address": email_address,
            "full_name": body["full_name"],
            "display_name": body["display_name"],
            "password": body["password"],
        })

    @staticmethod
    def _error(message: str, status: HTTPStatus) -> Response:
        """Build a JSON error response."""
        return Response(json.dumps({"error": message}),
                        status=status,
                        content_type="application/json")
