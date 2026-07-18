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


def create_admin_page_handlers(injections: PageHandlerInjections) -> Blueprint:

    routes = Blueprint('admin_pages_routes', __name__)

    injections.logger.debug(" Admin Pages Handlers:")

    # Admin page | Overview: '/overview'
    injections.logger.debug("=> %s GET /admin/overview",
                            "Admin overview page".ljust(40))

    @routes.route('/overview', methods=['GET'])
    async def admin_page_overview_request():
        return None
        return await handler_logout.logout()

    # Admin page | Projects (read): '/admin/projects'
    injections.logger.debug("=> %s GET /admin/projects",
                            "Admin Projects page (read)".ljust(40))

    @routes.route('/admin/projects', methods=['GET'])
    async def admin_page_projects_read_request():
        return None
        return await view.admin_projects()

    # Admin page | Projects (update): '/admin/projects'
    injections.logger.debug("=> %s POST /admin/projects",
                            "Admin Projects page (post)".ljust(40))

    @routes.route('/admin/projects', methods=['POST'])
    async def admin_page_projects_post_request():
        return None
        return await view.admin_projects()

    return routes
