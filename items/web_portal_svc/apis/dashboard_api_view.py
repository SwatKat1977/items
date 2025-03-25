"""
Copyright 2025 Integrated Test Management Suite Development Team

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
from base_web_view import BaseWebView
from metadata_settings import MetadataSettings
import page_locations as pages
from threadsafe_configuration import ThreadSafeConfiguration


class DashboardApiView(BaseWebView):

    def __init__(self,
                 logger: logging.Logger,
                 metadata: MetadataSettings):
        super().__init__(logger)
        self._metadata_settings = metadata

    async def admin_overview(self):

        return await self._render_page(
            pages.PAGE_INSTANCE_ADMIN_OVERVIEW,
            instance_name=self._metadata_settings.instance_name,
            active_page="administration",
            active_admin_page="admin_page_overview")

    async def admin_projects(self):

        # POST method
        if quart.request.method == 'POST':

            form = await quart.request.form
            project_id = form.get('projectId')

            base_url: str = ThreadSafeConfiguration().apis_gateway_svc
            url = f"{base_url}{project_id}/delete_project"
            response: ApiResponse = await self._call_api_delete(url)

            if response.status_code != http.HTTPStatus.OK:
                self._logger.critical("Gateway svc request invalid - Reason: %s",
                                      response.exception_msg)
                return await self._render_page(pages.TEMPLATE_INTERNAL_ERROR_PAGE)

        base_url: str = ThreadSafeConfiguration().apis_gateway_svc
        url = f"{base_url}/project/overviews?value_fields=name"
        response: ApiResponse = await self._call_api_get(url)

        if response.status_code != http.HTTPStatus.OK:
            self._logger.critical(
                "Gateway svc request invalid - Reason: %s",
                response.exception_msg)
            return await self._render_page(pages.TEMPLATE_INTERNAL_ERROR_PAGE)

        page: str = "dashboard"
        projects = response.body["projects"]

        return await self._render_page(
            pages.PAGE_INSTANCE_ADMIN_PROJECTS,
            instance_name=self._metadata_settings.instance_name,
            active_page="administration",
            active_admin_page="admin_page_projects",
            projects=projects)

    async def admin_users_and_roles(self):

        return await self._render_page(
            pages.PAGE_INSTANCE_ADMIN_USERS_AND_ROLES,
            instance_name=self._metadata_settings.instance_name,
            active_page="administration",
            active_admin_page="admin_page_users_roles")

    async def admin_manage_data(self):

        return await self._render_page(
            pages.PAGE_INSTANCE_ADMIN_MANAGE_DATA,
            instance_name=self._metadata_settings.instance_name,
            active_page="administration",
            active_admin_page="admin_page_manage_data")

    async def admin_site_settings(self):

        return await self._render_page(
            pages.PAGE_INSTANCE_ADMIN_SITE_SETTINGS,
            instance_name=self._metadata_settings.instance_name,
            active_page="administration",
            active_admin_page="admin_page_site_settings")

    async def admin_add_project(self):

        # POST method - send new project to gateway
        if quart.request.method == 'POST':
            print("I am a post")

            form = await quart.request.form
            project_name: str = form.get('project_name')
            announcement: str = form.get('announcement')
            show_announcement: bool = form.get('show_announcement') == 'on'
            print(f"project_name      : {project_name}")
            print(f"announcement      : {announcement}")
            print(f"show_announcement : {show_announcement}")

        return await self._render_page(
            pages.PAGE_INSTANCE_ADMIN_ADD_PROJECT,
            instance_name=self._metadata_settings.instance_name,
            active_page="administration",
            active_admin_page="admin_page_site_settings")
