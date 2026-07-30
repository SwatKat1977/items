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
from http import HTTPStatus
import logging
from quart import request
from weaver_framework.microservice.api_response import ApiResponse
from weaver_framework.microservice.rest_client import RestClient
from items.services.items_web_portal.configuration import Configuration
from items.services.items_web_portal.metadata_settings import MetadataSettings
import items.services.items_web_portal.page_locations as pages
from items.services.items_web_portal.portal_page_handler import (
    PortalPageHandler)
from items.services.items_web_portal.decorators import require_administrator


class AdminProjectsPageHandlers(PortalPageHandler):
    """Handles requests for the administration projects page.

    This handler provides operations for displaying the list of projects
    and deleting existing projects through the backend projects API.
    """

    def __init__(self,
                 logger: logging.Logger,
                 config: Configuration,
                 rest_client: RestClient,
                 metadata: MetadataSettings):
        """Initialize the administration projects page handlers.

        Args:
            logger: Logger used to record diagnostic and operational messages.
            config: Application configuration settings.
            rest_client: REST client used to communicate with backend services.
            metadata: Instance metadata used to populate page content.
        """
        super().__init__(logger, config, rest_client)
        self._metadata_settings = metadata

    @require_administrator
    async def projects_post(self):
        """Delete a project.

        Retrieves the selected project identifier from the submitted form
        and requests its deletion through the backend API. After a
        successful deletion, the updated projects page is rendered.

        Returns:
            The rendered projects page response after deletion, or the
            internal error page if the deletion request fails.
        """
        form = await request.form
        project_id = form.get('projectId')

        base_url: str = self._config.apis_gateway_svc
        url = f"{base_url}web/projects/{project_id}"

        response: ApiResponse = await self._rest_client.delete(url)

        if response.status_code != HTTPStatus.OK:
            self._logger.critical("Gateway svc request invalid - Reason: %s",
                                  response.exception_msg)
            return await self._render_page(pages.TEMPLATE_INTERNAL_ERROR_PAGE)

        return await self.projects_read()

    @require_administrator
    async def projects_read(self):
        """Render the administration projects page.

        Retrieves the list of projects from the backend API and renders the
        administration projects page.

        Returns:
            The rendered administration projects page response, or the
            internal error page if the projects cannot be retrieved.
        """
        base_url: str = self._config.apis_gateway_svc
        url = f"{base_url}web/projects?value_fields=name"
        response: ApiResponse = await self._rest_client.get(url)

        if response.status_code != HTTPStatus.OK:
            self._logger.critical(
                "Gateway svc request invalid - Reason: %s",
                response.exception_msg)
            return await self._render_page(pages.TEMPLATE_INTERNAL_ERROR_PAGE)

        projects = response.body["projects"]

        return await self._render_page(
            pages.PAGE_INSTANCE_ADMIN_PROJECTS,
            instance_name=self._metadata_settings.instance_name,
            active_page="administration",
            active_admin_page="admin_page_projects",
            projects=projects)
