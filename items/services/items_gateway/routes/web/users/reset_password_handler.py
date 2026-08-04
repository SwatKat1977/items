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
from items.services.items_gateway.services.email_service import (
    EmailService, EmailServiceError)

_PASSWORD_RESET_SUBJECT = "Your ITEMS password has been reset"


def _build_reset_body(portal_url: str) -> str:
    login_url = portal_url.rstrip("/") + "/login"
    return (
        "Hello,\n\n"
        "An administrator has reset your ITEMS password.\n\n"
        "Please log in and change your password at your earliest convenience:\n"
        f"{login_url}\n\n"
        "If you did not expect this change, please contact your administrator.\n"
    )


class ResetPasswordHandler(BaseApiRoute):
    """Handles POST /users/<user_id>/password — admin password reset.

    Does not verify the existing password. Intended for administrator use;
    enforcement is the gateway's responsibility (admin-only route).

    After a successful reset the handler attempts to notify the user by email.
    A failure to send the notification is logged but does not cause the
    response to the caller to fail — the password has already been changed.
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

    async def reset_password(self, user_id: str) -> Response:
        """Reset a user's password without verifying the current one.

        On success, attempts to send a notification email to the user.
        Email delivery failures are logged but do not affect the response.

        Args:
            user_id: The user's UUID (from the URL).

        Returns:
            200 on success.
            400 if the request body is missing or not valid JSON.
            404 if no user exists with that ID.
            500 if the identity service is unreachable.
        """
        body = await request.get_json(force=True, silent=True)
        if body is None:
            return Response(
                json.dumps({"error": "Invalid JSON body"}),
                status=HTTPStatus.BAD_REQUEST,
                content_type="application/json")

        url: str = (f"{self._configuration.apis_identity_svc}"
                    f"users/{user_id}/password")
        response: ApiResponse = await self._rest_client.post(url,
                                                              json_data=body)

        if response.exception_msg is not None:
            self._logger.error("Connection to identity service failed: %s",
                               response.exception_msg)
            return Response(
                json.dumps({"error": "Identity service unavailable"}),
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
                content_type="application/json")

        if response.status_code == HTTPStatus.OK and self._email_service:
            await self._send_reset_notification(user_id)

        return Response(json.dumps(response.body),
                        status=response.status_code,
                        content_type="application/json")

    async def _send_reset_notification(self, user_id: str) -> None:
        """Fetch the user's email address and send a reset notification.

        Failures are logged but not propagated — the password has already
        been changed successfully.
        """
        user_url = f"{self._configuration.apis_identity_svc}users/{user_id}"
        user_response: ApiResponse = await self._rest_client.get(user_url)

        if user_response.exception_msg is not None or \
                user_response.status_code != HTTPStatus.OK:
            self._logger.warning(
                "Could not fetch user %s to send password reset email: "
                "status=%s", user_id, user_response.status_code)
            return

        email_address = user_response.body.get("email_address")
        if not email_address:
            self._logger.warning(
                "User %s has no email address; skipping reset notification",
                user_id)
            return

        try:
            await self._email_service.send(
                to=email_address,
                subject=_PASSWORD_RESET_SUBJECT,
                body=_build_reset_body(self._configuration.apis_web_portal_svc))
        except EmailServiceError as exc:
            self._logger.error(
                "Failed to send password reset notification to %s: %s",
                email_address, exc)
