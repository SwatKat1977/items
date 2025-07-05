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
            url = f"{base_url}web/projects/{project_id}"
            response: ApiResponse = await self._call_api_delete(url)

            if response.status_code != http.HTTPStatus.OK:
                self._logger.critical("Gateway svc request invalid - Reason: %s",
                                      response.exception_msg)
                return await self._render_page(pages.TEMPLATE_INTERNAL_ERROR_PAGE)

        base_url: str = ThreadSafeConfiguration().apis_gateway_svc
        url = f"{base_url}/web/projects?value_fields=name"
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
            form = await quart.request.form
            project_name: str = form.get('project_name')
            announcement: str = form.get('announcement')
            show_announcement: bool = form.get('show_announcement') == 'on'

            if all([project_name, (announcement is not None)]):
                gateway_request_body: dict = {
                    "name": project_name,
                    "announcement": announcement.rstrip(),
                    "announcement_on_overview": show_announcement
                }
                base_url: str = ThreadSafeConfiguration().apis_gateway_svc
                url = f"{base_url}/project/add"
                response: ApiResponse = await self._call_api_post(
                    url, gateway_request_body)

                if response.status_code == http.HTTPStatus.INTERNAL_SERVER_ERROR:
                    self._logger.critical(
                        "Gateway svc request '/project/add' is invalid: %s",
                        response.body)
                    form = await quart.request.form
                    form_data = form.to_dict()
                    return await self._render_page(
                        pages.PAGE_INSTANCE_ADMIN_ADD_PROJECT,
                        instance_name=self._metadata_settings.instance_name,
                        active_page="administration",
                        active_admin_page="admin_page_site_settings",
                        error_msg_str="Internal server error!",
                        form_data=form_data)

                if response.status_code == http.HTTPStatus.BAD_REQUEST:
                    status_code = response.body.get("status")
                    error_msg = response.body.get("error") \
                        if status_code is not None \
                        else "Internal ITEMS error"

                    form = await quart.request.form
                    form_data = form.to_dict()

                    return await self._render_page(
                        pages.PAGE_INSTANCE_ADMIN_ADD_PROJECT,
                        instance_name=self._metadata_settings.instance_name,
                        active_page="administration",
                        active_admin_page="admin_page_site_settings",
                        error_msg_str=error_msg,
                        form_data=form_data)

                redirect = self._generate_redirect('/admin/projects')
                return await quart.make_response(redirect)

        return await self._render_page(
            pages.PAGE_INSTANCE_ADMIN_ADD_PROJECT,
            instance_name=self._metadata_settings.instance_name,
            active_page="administration",
            active_admin_page="admin_page_site_settings",
            form_data={})

    async def admin_modify_project(self, project_id):

        base_url: str = ThreadSafeConfiguration().apis_gateway_svc

        if quart.request.method == 'POST':
            url = f"{base_url}/web/projects/{project_id}"
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
