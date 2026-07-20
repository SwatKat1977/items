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
from items.services.items_web_portal.metadata_settings import MetadataSettings
import items.services.items_web_portal.page_locations as pages
from items.services.items_web_portal.portal_page_handler import (
    PortalPageHandler)
from items.services.items_web_portal.decorators import require_session


class AdminAddProjectPageHandlers(PortalPageHandler):
    def __init__(self,
                 logger: logging.Logger,
                 config: Configuration,
                 rest_client: RestClient,
                 metadata: MetadataSettings):
        super().__init__(logger, config, rest_client)
        self._metadata_settings = metadata

    @require_session
    async def add_project_get(self):
        """Render a blank add-project form."""
        return await self._render(form_data={})

    @require_session
    async def add_project_post(self):
        form = await request.form
        form_data = form.to_dict()

        project_name: str = form.get("project_name")
        announcement: str = form.get("announcement")
        show_announcement: bool = form.get("show_announcement") == "on"

        if not all([project_name, announcement is not None]):
            return await self._render(
                form_data=form_data,
                error_msg_str="Project name and announcement are required.")

        gateway_request_body: dict = {
            "name": project_name,
            "announcement": announcement.rstrip(),
            "announcement_on_overview": show_announcement
        }
        base_url: str = self._config.apis_gateway_svc
        url = f"{base_url}web/projects"

        response: ApiResponse = await self._rest_client.post(url, gateway_request_body)

        if response.status_code in (http.HTTPStatus.INTERNAL_SERVER_ERROR,
                                    http.HTTPStatus.NOT_FOUND):
            self._logger.critical(
                "Gateway svc request '/web/admin/projects' is invalid: %s",
                response.body)
            return await self._render(
                form_data=form_data,
                error_msg_str="Internal server error!")

        if response.status_code == http.HTTPStatus.BAD_REQUEST:
            status_code = response.body.get("status")
            error_msg = response.body.get("error") \
                if status_code is not None else "Internal ITEMS error"
            return await self._render(
                form_data=form_data,
                error_msg_str=error_msg)

        redirect = self._generate_redirect('/admin/projects')
        return await make_response(redirect)

    async def _render(self, form_data: dict, error_msg_str: str | None = None):
        return await self._render_page(
            pages.PAGE_INSTANCE_ADMIN_ADD_PROJECT,
            instance_name=self._metadata_settings.instance_name,
            active_page="administration",
            active_admin_page="admin_page_site_settings",
            error_msg_str=error_msg_str,
            form_data=form_data)
