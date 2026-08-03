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
import logging
from weaver_framework.microservice.rest_client import RestClient
from items.services.items_web_portal.configuration import Configuration
from items.services.items_web_portal.decorators import require_administrator
from items.services.items_web_portal.metadata_settings import MetadataSettings
import items.services.items_web_portal.page_locations as pages
from items.services.items_web_portal.portal_page_handler import (
    PortalPageHandler)


class AdminUsersAndRolesPageHandler(PortalPageHandler):
    """Handles requests for the administration users and roles page.

    This handler fetches the current list of users from the gateway and
    renders the administration page used to manage user accounts and role
    assignments.
    """

    def __init__(self,
                 logger: logging.Logger,
                 config: Configuration,
                 rest_client: RestClient,
                 metadata: MetadataSettings):
        """Initialize the administration users and roles page handler.

        Args:
            logger: Logger used to record diagnostic and operational messages.
            config: Application configuration settings.
            rest_client: REST client used to communicate with backend services.
            metadata: Instance metadata used to populate page content.
        """
        super().__init__(logger, config, rest_client)
        self._metadata_settings = metadata

    @require_administrator
    async def users_and_roles(self):
        """Render the administration users and roles page.

        Fetches all users from the gateway and passes them to the template.
        On gateway failure the page is rendered with an empty user list and
        an error message.

        Returns:
            The rendered administration users and roles page response.
        """
        url = f"{self._config.apis_gateway_svc}web/users"
        response = await self._rest_client.get(url)

        if response.status_code == 200:
            users = response.body.get("users", [])
            error_msg_str = None
        else:
            self._logger.error(
                "Failed to fetch users from gateway: status=%s",
                response.status_code)
            users = []
            error_msg_str = "Could not load users — please try again."

        return await self._render_page(
            pages.PAGE_INSTANCE_ADMIN_USERS_AND_ROLES,
            instance_name=self._metadata_settings.instance_name,
            active_page="administration",
            active_admin_page="admin_page_users_roles",
            users=users,
            error_msg_str=error_msg_str)
