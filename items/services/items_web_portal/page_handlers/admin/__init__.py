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
from quart import Blueprint
from items.services.items_web_portal.page_handler_injections import (
    PageHandlerInjections)
from items.services.items_web_portal.page_handlers.admin.dashboard import \
    create_admin_dashboard_page_handler
from items.services.items_web_portal.page_handlers.admin.projects import \
    create_admin_projects_page_handlers


def create_admin_page_handlers(injections: PageHandlerInjections,
                               prefix: str) -> Blueprint:
    """Create the admin page route handlers.

    This function creates and configures the blueprint containing the
    administrative page routes for the web application. It registers the
    admin dashboard routes, project management routes, and page handlers
    for user and role management, data management, and site settings.

    The returned blueprint can be registered with the main application to
    expose the administrative interface.

    Args:
        injections: Dependency injection container providing the page
            handlers, logger, and supporting services required by the
            administrative pages.
        prefix: URL prefix applied when creating nested admin blueprints.

    Returns:
        Blueprint: A configured Quart blueprint containing all
        administrative page routes.
    """
    routes = Blueprint('admin_pages_routes', __name__)

    injections.logger.debug(" Admin Pages Handlers:")

    # Register admin dashboard pages
    routes.register_blueprint(create_admin_dashboard_page_handler(injections,
                                                                  prefix))

    # Admin page | Users Roles (read): '/admin/users_roles'
    injections.logger.debug("=> %s GET /admin/users_roles",
                            "Admin Users Roles page (read)".ljust(40))

    @routes.route('/admin/users_roles', methods=['GET'])
    async def admin_admin_users_and_roles_request():
        return await injections.admin_users_and_roles()

    # Admin page | Manage Data (read): '/admin/users_roles'
    injections.logger.debug("=> %s GET /admin/manage_data",
                            "Admin manage data  page (read)".ljust(40))

    @routes.route('/admin/manage_data', methods=['GET'])
    async def admin_admin_manage_data_request():
        return await injections.admin_manage_data()

    # Admin page | Site Settings (read): '/admin/site_settings'
    injections.logger.debug("=> %s GET /admin/site_settings",
                            "Admin site settings page (read)".ljust(40))

    @routes.route('/admin/site_settings', methods=['GET'])
    async def admin_site_settings_request():
        return await injections.admin_site_settings()

    # Register testcases pages
    routes.register_blueprint(create_admin_projects_page_handlers(injections))

    return routes
