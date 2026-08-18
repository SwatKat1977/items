"""
Copyright 2025-2026 Integrated Test Management Suite Development Team
Copyright 2017-2025 INTMAC Development Team [Defunct]

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
import http
import logging
from quart import make_response, request
from weaver_framework.microservice.api_response import ApiResponse
from weaver_framework.microservice.rest_client import RestClient
from items.services.items_web_portal.configuration import Configuration
from items.services.items_web_portal.decorators import require_administrator
from items.services.items_web_portal.metadata_settings import MetadataSettings
import items.services.items_web_portal.page_locations as pages
from items.services.items_web_portal.portal_page_handler import (
    PortalPageHandler)


class AdminResetPasswordPageHandler(PortalPageHandler):
    """Handles requests for resetting a user's password.

    Fetches the user's name and email from the gateway for display, then
    submits the new password to the gateway reset endpoint on POST.
    """

    def __init__(self,
                 logger: logging.Logger,
                 config: Configuration,
                 rest_client: RestClient,
                 metadata: MetadataSettings):
        """Initialise the reset password page handler.

        Args:
            logger: Logger used to record diagnostic and operational messages.
            config: Application configuration settings.
            rest_client: REST client used to communicate with backend services.
            metadata: Instance metadata used to populate page content.
        """
        super().__init__(logger, config, rest_client)
        self._metadata_settings = metadata

    @require_administrator
    async def reset_password_get(self, user_id: str):
        """Render the reset password page.

        Fetches the user's full name and email to display as context.

        Args:
            user_id: The ID of the user whose password is being reset.

        Returns:
            The rendered reset password page.
        """
        user_full_name, user_email = await self._fetch_user_display(user_id)
        if user_full_name is None:
            return await self._render(
                user_id=user_id,
                user_full_name="Unknown",
                user_email="",
                error_msg_str="User not found.")

        return await self._render(
            user_id=user_id,
            user_full_name=user_full_name,
            user_email=user_email)

    @require_administrator
    async def reset_password_post(self, user_id: str):
        """Process a password reset submission.

        Validates the two password fields match and meet the minimum length,
        then forwards the new password to the gateway.

        Args:
            user_id: The ID of the user whose password is being reset.

        Returns:
            A redirect to /admin/users_roles on success, or the rendered
            reset password page with an error message on failure.
        """
        form = await request.form
        new_password: str = form.get("new_password", "").strip()
        confirm_password: str = form.get("confirm_password", "").strip()

        user_full_name, user_email = await self._fetch_user_display(user_id)
        user_full_name = user_full_name or "Unknown"
        user_email = user_email or ""

        if not new_password or len(new_password) < 8:
            return await self._render(
                user_id=user_id,
                user_full_name=user_full_name,
                user_email=user_email,
                error_msg_str="Password must be at least 8 characters.")

        if new_password != confirm_password:
            return await self._render(
                user_id=user_id,
                user_full_name=user_full_name,
                user_email=user_email,
                error_msg_str="Passwords do not match.")

        url = f"{self._config.apis_gateway_svc}web/users/{user_id}/password"
        # A longer timeout than RestClient's 2s default: password hashing
        # (argon2, in identity's user_management_service) is deliberately
        # expensive, and this call is chained through the gateway's own
        # call to identity - either hop's default timeout can otherwise
        # fire first and surface as a spurious 504 on a legitimate,
        # still-in-progress reset.
        response: ApiResponse = await self._rest_client.post(
            url, json_data={"new_password": new_password}, timeout=10)

        if response.status_code == http.HTTPStatus.NOT_FOUND:
            return await self._render(
                user_id=user_id,
                user_full_name=user_full_name,
                user_email=user_email,
                error_msg_str="User not found.")

        if response.status_code != http.HTTPStatus.OK:
            self._logger.error(
                "Gateway POST /web/users/%s/password failed: status=%s body=%s",
                user_id, response.status_code, response.body)
            return await self._render(
                user_id=user_id,
                user_full_name=user_full_name,
                user_email=user_email,
                error_msg_str="An unexpected error occurred. Please try again.")

        return await make_response(
            self._generate_redirect('/admin/users_roles'))

    async def _fetch_user_display(self, user_id: str) -> tuple[str | None, str | None]:
        """Fetch the user's full name and email for display purposes.

        Args:
            user_id: The ID of the user to look up.

        Returns:
            A ``(full_name, email_address)`` tuple, or ``(None, None)`` if
            the user is not found or the gateway is unavailable.
        """
        url = f"{self._config.apis_gateway_svc}web/users/{user_id}"
        response: ApiResponse = await self._rest_client.get(url)
        if response.status_code != http.HTTPStatus.OK:
            return None, None
        return (response.body.get("full_name"),
                response.body.get("email_address"))

    async def _render(self,
                      user_id: str,
                      user_full_name: str,
                      user_email: str,
                      error_msg_str: str | None = None):
        """Render the reset password page.

        Args:
            user_id: ID of the user (used in the form action).
            user_full_name: User's full name, shown as context.
            user_email: User's email address, shown as context.
            error_msg_str: Optional error message to display.

        Returns:
            The rendered reset password page response.
        """
        return await self._render_page(
            pages.PAGE_INSTANCE_ADMIN_RESET_PASSWORD,
            instance_name=self._metadata_settings.instance_name,
            active_page="administration",
            active_admin_page="admin_page_users_roles",
            user_id=user_id,
            user_full_name=user_full_name,
            user_email=user_email,
            error_msg_str=error_msg_str)
