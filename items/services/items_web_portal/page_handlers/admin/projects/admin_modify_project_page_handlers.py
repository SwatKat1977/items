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
from quart import make_response, request
#from base_view import ApiResponse
#from base_web_view import PortalPageHandler
#from metadata_settings import MetadataSettings
#import page_locations as pages
#from threadsafe_configuration import ThreadSafeConfiguration
from weaver_framework.microservice.api_response import ApiResponse
from weaver_framework.microservice.rest_client import RestClient
from items.services.items_web_portal.configuration import Configuration
from items.services.items_web_portal.metadata_settings import MetadataSettings
import items.services.items_web_portal.page_locations as pages
from items.services.items_web_portal.portal_page_handler import (
    PortalPageHandler)


class AdminModifyProjectPageHandlers(PortalPageHandler):
    """Handles requests for modifying existing projects.

    This handler retrieves project information for display in the
    modification form and processes updates submitted by administrators.
    """

    def __init__(self,
                 logger: logging.Logger,
                 config: Configuration,
                 rest_client: RestClient,
                 metadata: MetadataSettings):
        """Initialize the project modification page handler.

        Args:
            logger: Logger used to record diagnostic and operational messages.
            config: Application configuration settings.
            rest_client: REST client used to communicate with backend services.
            metadata: Instance metadata used to populate page content.
        """
        super().__init__(logger, config, rest_client)
        self._metadata_settings = metadata

    async def modify_project_get(self, project_id):
        """Render the project modification page.

        Retrieves the project's current details from the backend API and
        populates the modification form. If the project cannot be
        retrieved, the user is redirected to the projects administration
        page.

        Args:
            project_id: Identifier of the project to modify.

        Returns:
            The rendered project modification page response, or a redirect
            response if the project details cannot be retrieved.
        """
        url = f"{self._config.apis_gateway_svc}web/projects/{project_id}"
        api_response = await self._rest_client.get(url)

        if api_response.status_code != HTTPStatus.OK:
            self._logger.critical(
                "(admin_modify_project) Cannot get details for project %s"
                " - Reason: %s",project_id, api_response.exception_msg)
            redirect = self._generate_redirect('admin/projects')
            return await make_response(redirect)

        form_data: dict = {
            "id": project_id,
            "project_name": api_response.body["name"],
            "announcement": api_response.body["announcement"].rstrip(),
            "show_announcement": api_response.body["show_announcement_on_overview"]
        }
        return await self._render_page(
            pages.PAGE_INSTANCE_ADMIN_MODIFY_PROJECT,
            instance_name=self._metadata_settings.instance_name,
            active_page="administration",
            active_admin_page="admin_page_site_settings",
            form_data=form_data)

    async def modify_project_post(self, project_id):
        """Process a project modification request.

        Validates the submitted form data by forwarding it to the backend
        API. If the update succeeds, the user is redirected to the projects
        administration page. Otherwise, the modification page is rendered
        again with the submitted values and an error message.

        Args:
            project_id: Identifier of the project to modify.

        Returns:
            A redirect response when the project is successfully updated, or
            the rendered project modification page containing the submitted
            values and an error message if the update fails.
        """
        url = f"{self._config.apis_gateway_svc}web/projects/{project_id}"
        form = await request.form
        request_data: dict = {
            "name": form.get('project_name'),
            "announcement": form.get('announcement'),
            "announcement_on_overview": form.get('show_announcement') == 'on'
        }
        response: ApiResponse = await self._rest_client.patch(url, request_data)
        if response.status_code != HTTPStatus.OK:
            request_data: dict = {
                "project_name": form.get('project_name'),
                "announcement": form.get('announcement'),
                "show_announcement": form.get('show_announcement') == 'on'
            }
            reason: str = f" - reason: {response.body['error']}" \
                if 'error' in response.body else ''
            self._logger.warning("Unable to modify project %s%s",
                                 project_id, reason)

            return await self._render_page(
                pages.PAGE_INSTANCE_ADMIN_MODIFY_PROJECT,
                instance_name=self._metadata_settings.instance_name,
                active_page="administration",
                active_admin_page="admin_page_site_settings",
                form_data=request_data,
                error_msg_str="Internal error modifying project")

        redirect = self._generate_redirect('admin/projects')
        return await make_response(redirect)
