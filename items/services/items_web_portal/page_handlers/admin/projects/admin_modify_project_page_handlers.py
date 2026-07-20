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
import quart
from base_view import ApiResponse
from base_web_view import PortalPageHandler
from metadata_settings import MetadataSettings
import page_locations as pages
from threadsafe_configuration import ThreadSafeConfiguration


class DashboardApiView(PortalPageHandler):
    """
    Dashboard view handler for administrative pages.

    This class provides asynchronous route handlers for the
    administration dashboard, managing projects, users, roles,
    data management, and site settings. It relies on the gateway
    service for backend operations and uses PortalPageHandler helpers
    for template rendering and API calls.
    """

    def __init__(self,
                 logger: logging.Logger,
                 metadata: MetadataSettings):
        """
        Initialize the DashboardApiView.

        Args:
            logger (logging.Logger): Logger instance for diagnostic output.
            metadata (MetadataSettings): Metadata object containing instance
                                         configuration.
        """
        super().__init__(logger)
        self._metadata_settings = metadata

    async def admin_modify_project(self, project_id):
        """
        Modify an existing project.

        Retrieves project details with GET on initial load,
        or applies changes via PATCH if called with POST.

        Args:
            project_id (str): ID of the project to modify.

        Returns:
            Rendered modify-project page or redirect response.
        """
        base_url: str = ThreadSafeConfiguration().apis_gateway_svc

        if quart.request.method == 'POST':
            url = f"{base_url}web/admin/projects/{project_id}"
            form = await quart.request.form
            request_data: dict = {
                "name": form.get('project_name'),
                "announcement": form.get('announcement'),
                "announcement_on_overview": form.get('show_announcement') == 'on'
            }
            response: ApiResponse = await self._call_api_patch(url,
                                                               request_data)
            if response.status_code != http.HTTPStatus.OK:
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
            return await quart.make_response(redirect)

        url = f"{base_url}/web/projects/{project_id}"

        api_response = await self._call_api_get(url)

        if api_response.status_code != http.HTTPStatus.OK:
            self._logger.critical(
                "(admin_modify_project) Cannot get details for project %s"
                " - Reason: %s",project_id, api_response.exception_msg)
            redirect = self._generate_redirect('admin/projects')
            return await quart.make_response(redirect)

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
