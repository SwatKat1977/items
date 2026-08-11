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
    send_invite_email)


class ResendInviteHandler(BaseApiRoute):
    """Handles POST /invites/resend — refresh token and expiry on a
    pending invite.

    Proxies the request body to the identity service and propagates the
    response. Schema validation is performed by the identity service;
    invalid payloads will receive a 400 response propagated from there.

    Because the token is regenerated, the invitation is emailed again with the
    new link — otherwise "resend" would refresh the token without the
    recipient ever receiving it.
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

    async def resend_invite(self) -> Response:
        """Refresh the invite token and expiry for a pending invite.

        Returns:
            200 with ``{"token": <new_uuid>}`` on success.
            400 if the request body is missing or not valid JSON.
            404 if no pending invite exists for the email address.
            500 if the identity service is unreachable.
        """
        body = await request.get_json(force=True, silent=True)
        if body is None:
            return Response(
                json.dumps({"error": "Invalid JSON body"}),
                status=HTTPStatus.BAD_REQUEST,
                content_type="application/json")

        url: str = f"{self._configuration.apis_identity_svc}invites/resend"
        response: ApiResponse = await self._rest_client.post(url,
                                                              json_data=body)

        if response.exception_msg is not None:
            self._logger.error("Connection to identity service failed: %s",
                               response.exception_msg)
            return Response(
                json.dumps({"error": "Identity service unavailable"}),
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
                content_type="application/json")

        if response.body is not None and not isinstance(response.body, dict):
            # The identity service responded, but not with JSON - e.g. a
            # generic web-server error page, meaning the route doesn't exist
            # there (stale deployment, wrong version) rather than a real API
            # response. Forwarding it as-is would mislabel raw HTML as JSON.
            self._logger.error(
                "Identity service returned a non-JSON response (status %s, "
                "content-type %s) for %s",
                response.status_code, response.content_type, url)
            return Response(
                json.dumps({"error": "Identity service returned an "
                                     "unexpected response"}),
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
                content_type="application/json")

        await send_invite_email(
            logger=self._logger,
            email_service=self._email_service,
            portal_url=self._configuration.apis_web_portal_svc,
            response=response,
            email_address=body.get("email_address", ""),
            expected_status=HTTPStatus.OK)

        return Response(json.dumps(response.body),
                        status=response.status_code,
                        content_type="application/json")
