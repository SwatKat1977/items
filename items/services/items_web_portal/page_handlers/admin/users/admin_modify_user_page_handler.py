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


class AdminModifyUserPageHandler(PortalPageHandler):
    """Handles requests for editing an existing user.

    Fetches the current user data from the gateway on GET and submits a
    patch-style update on POST.
    """

    def __init__(self,
                 logger: logging.Logger,
                 config: Configuration,
                 rest_client: RestClient,
                 metadata: MetadataSettings):
        """Initialise the modify user page handler.

        Args:
            logger: Logger used to record diagnostic and operational messages.
            config: Application configuration settings.
            rest_client: REST client used to communicate with backend services.
            metadata: Instance metadata used to populate page content.
        """
        super().__init__(logger, config, rest_client)
        self._metadata_settings = metadata

    @require_administrator
    async def modify_user_get(self, user_id: str):
        """Render the edit user page pre-populated with current user data.

        Args:
            user_id: The ID of the user to edit.

        Returns:
            The rendered edit user page, or an error page if the user is
            not found or the gateway is unavailable.
        """
        url = f"{self._config.apis_gateway_svc}web/users/{user_id}"
        response: ApiResponse = await self._rest_client.get(url)

        if response.status_code == http.HTTPStatus.NOT_FOUND:
            return await self._render(
                user_id=user_id,
                form_data={},
                error_msg_str="User not found.")

        if response.status_code != http.HTTPStatus.OK:
            self._logger.error(
                "Gateway GET /web/users/%s failed: status=%s",
                user_id, response.status_code)
            return await self._render(
                user_id=user_id,
                form_data={},
                error_msg_str="Could not load user — please try again.")

        user = response.body
        form_data = {
            "full_name": user.get("full_name", ""),
            "display_name": user.get("display_name", ""),
            "email_address": user.get("email_address", ""),
            "account_status": user.get("account_status", 1),
        }
        return await self._render(user_id=user_id, form_data=form_data)

    @require_administrator
    async def modify_user_post(self, user_id: str):
        """Process an edit user submission.

        Sends a PATCH request to the gateway with the supplied fields.
        Redirects to the user list on success; re-renders the form with an
        error message on failure.

        Args:
            user_id: The ID of the user to update.

        Returns:
            A redirect to /admin/users_roles on success, or the rendered
            edit page with an error message on failure.
        """
        form = await request.form
        form_data = form.to_dict()

        full_name: str = form.get("full_name", "").strip()
        display_name: str = form.get("display_name", "").strip()
        account_status: int = 1 if form.get("account_status") == "1" else 0

        # Re-inject account_status as int for template re-population
        form_data["account_status"] = account_status

        if not all([full_name, display_name]):
            return await self._render(
                user_id=user_id,
                form_data=form_data,
                error_msg_str="Full name and display name are required.")

        gateway_body: dict = {
            "full_name": full_name,
            "display_name": display_name,
            "account_status": account_status,
        }

        url = f"{self._config.apis_gateway_svc}web/users/{user_id}"
        response: ApiResponse = await self._rest_client.patch(
            url, json_data=gateway_body)

        if response.status_code == http.HTTPStatus.FORBIDDEN:
            return await self._render(
                user_id=user_id,
                form_data=form_data,
                error_msg_str="Cannot deactivate the last active administrator.")

        if response.status_code == http.HTTPStatus.NOT_FOUND:
            return await self._render(
                user_id=user_id,
                form_data=form_data,
                error_msg_str="User not found.")

        if response.status_code != http.HTTPStatus.OK:
            self._logger.error(
                "Gateway PATCH /web/users/%s failed: status=%s body=%s",
                user_id, response.status_code, response.body)
            return await self._render(
                user_id=user_id,
                form_data=form_data,
                error_msg_str="An unexpected error occurred. Please try again.")

        return await make_response(
            self._generate_redirect('/admin/users_roles'))

    async def _render(self,
                      user_id: str,
                      form_data: dict,
                      error_msg_str: str | None = None):
        """Render the edit user page.

        Args:
            user_id: ID of the user being edited (used in the form action).
            form_data: Values used to pre-populate the form fields.
            error_msg_str: Optional error message to display.

        Returns:
            The rendered edit user page response.
        """
        return await self._render_page(
            pages.PAGE_INSTANCE_ADMIN_MODIFY_USER,
            instance_name=self._metadata_settings.instance_name,
            active_page="administration",
            active_admin_page="admin_page_users_roles",
            user_id=user_id,
            form_data=form_data,
            error_msg_str=error_msg_str)
