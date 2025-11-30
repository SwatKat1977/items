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
import logging
from quart import Blueprint
from apis.dashboard_api_view import DashboardApiView
from metadata_settings import MetadataSettings


def create_blueprint(logger: logging.Logger,
                     metadata: MetadataSettings) -> Blueprint:
    """
    Creates and registers a Quart Blueprint for handling dashboard API routes.

    Args:
        logger (logging.Logger): A logger instance for logging messages.
        metadata (MetadataSettings): A metadata settings instance.

    Returns:
        Blueprint: A Quart `Blueprint` object containing the registered route.
    """
    view = DashboardApiView(logger, metadata)

    ### logger.debug("=> / [GET]              : Home page (web page)")

    blueprint = Blueprint('dashboard_api', __name__)

    logger.debug("----------- Registering Admin Dashboard routes ------------")

    logger.debug("=> /admin/overview [GET]                          : Admin "
                 "overview (web page)")

    @blueprint.route('/admin/overview', methods=['GET'])
    async def admin_overview_request():
        return await view.admin_overview()

    logger.debug("=> /admin/projects [GET, POST]                    : Manage "
                 "projects (web page)")

    @blueprint.route('/admin/projects', methods=['GET', 'POST'])
    async def admin_projects_request():
        return await view.admin_projects()

    logger.debug("=> /admin/users_roles [GET]                       : Manage "
                 "user roles (web page)")

    @blueprint.route('/admin/users_roles', methods=['GET'])
    async def admin_admin_users_and_roles_request():
        return await view.admin_users_and_roles()

    logger.debug("=> /admin/manage_data [GET]                       : Manage "
                 "data (web page)")

    @blueprint.route('/admin/manage_data', methods=['GET'])
    async def admin_admin_manage_data_request():
        return await view.admin_manage_data()

    logger.debug("=> /admin/site_settings [GET]                     : Site "
                 "Settings (web page)")

    @blueprint.route('/admin/site_settings', methods=['GET'])
    async def admin_site_settings_request():
        return await view.admin_site_settings()

    logger.debug("=> /admin/add_project [GET, POST]                 : Add "
                 "project (web page)")

    @blueprint.route('/admin/add_project', methods=['GET', 'POST'])
    async def admin_add_project_request():
        return await view.admin_add_project()

    logger.debug("=> /admin/<project_id>/modify_project [GET, POST] : Modify "
                 "project (web page)")

    @blueprint.route('/admin/<project_id>/modify_project',
                     methods=['GET', 'POST'])
    async def admin_modify_project_request(project_id: int):
        return await view.admin_modify_project(project_id)

    return blueprint
