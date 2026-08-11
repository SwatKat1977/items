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


class AdminAddUserPageHandler(PortalPageHandler):
    """Handles requests for creating new users.

    This handler renders the user creation form and processes submitted user
    details by forwarding them to the gateway user management API.
    """

    def __init__(self,
                 logger: logging.Logger,
                 config: Configuration,
                 rest_client: RestClient,
                 metadata: MetadataSettings):
        """Initialize the user creation page handler.

        Args:
            logger: Logger used to record diagnostic and operational messages.
            config: Application configuration settings.
            rest_client: REST client used to communicate with backend services.
            metadata: Instance metadata used to populate page content.
        """
        super().__init__(logger, config, rest_client)
        self._metadata_settings = metadata

    @require_administrator
    async def add_user_get(self):
        """Render the user creation page.

        Returns:
            The rendered user creation page response.
        """
        return await self._render(form_data={})

    @require_administrator
    async def add_user_post(self):
        """Process a user creation request.

        Reads the submitted form, builds a gateway request, and handles
        success, conflict, and error responses. On success the generated
        password (if any) is displayed before returning the blank form.

        Returns:
            The rendered user creation page, either with a success message
            (including any generated password) or an error message.
        """
        form = await request.form
        form_data = form.to_dict()

        full_name: str = form.get("full_name", "").strip()
        display_name: str = form.get("display_name", "").strip()
        email_address: str = form.get("email_address", "").strip()
        password: str = form.get("password", "").strip()
        is_administrator: bool = form.get("is_administrator") == "1"

        # Re-inject for template re-population - an unchecked checkbox is
        # simply absent from form_data, unlike the text fields above.
        form_data["is_administrator"] = is_administrator

        if not all([full_name, display_name, email_address]):
            return await self._render(
                form_data=form_data,
                error_msg_str="Full name, display name and email address are required.")

        if not password or len(password) < 8:
            return await self._render(
                form_data=form_data,
                error_msg_str="Password must be at least 8 characters.")

        gateway_body: dict = {
            "full_name": full_name,
            "display_name": display_name,
            "email_address": email_address,
            "password": password,
            "is_administrator": is_administrator,
        }

        url = f"{self._config.apis_gateway_svc}web/users"
        response: ApiResponse = await self._rest_client.post(
            url, json_data=gateway_body)

        if response.status_code == http.HTTPStatus.CONFLICT:
            return await self._render(
                form_data=form_data,
                error_msg_str="That email address is already registered.")

        if response.status_code != http.HTTPStatus.CREATED:
            self._logger.error(
                "Gateway POST /web/users failed: status=%s body=%s",
                response.status_code, response.body)
            return await self._render(
                form_data=form_data,
                error_msg_str="An unexpected error occurred. Please try again.")

        return await make_response(
            self._generate_redirect('/admin/users_roles'))

    async def _render(self,
                      form_data: dict,
                      error_msg_str: str | None = None):
        """Render the user creation page.

        Args:
            form_data: Values used to pre-populate the form fields.
            error_msg_str: Optional error message to display.

        Returns:
            The rendered user creation page response.
        """
        return await self._render_page(
            pages.PAGE_INSTANCE_ADMIN_ADD_USER,
            instance_name=self._metadata_settings.instance_name,
            active_page="administration",
            active_admin_page="admin_page_users_roles",
            form_data=form_data,
            error_msg_str=error_msg_str)
