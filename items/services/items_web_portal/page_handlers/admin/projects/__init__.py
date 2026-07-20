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
from items.services.items_web_portal.page_handlers.admin.projects.\
    admin_add_project_page_handlers import AdminAddProjectPageHandlers
from items.services.items_web_portal.page_handlers.admin.projects.\
    admin_modify_project_page_handlers import AdminModifyProjectPageHandlers
from items.services.items_web_portal.page_handlers.admin.projects.\
    admin_projects_page_handlers import AdminProjectsPageHandlers


def create_admin_projects_page_handlers(injections: PageHandlerInjections) -> Blueprint:

    routes = Blueprint('admin_projects_pages_routes', __name__)

    injections.logger.debug(" Admin Pages | Projects Handlers:")

    handlers_projects: AdminProjectsPageHandlers = AdminProjectsPageHandlers(
        injections.logger,
        injections.config,
        injections.rest_client,
        injections.metadata)
    handlers_add_project: AdminAddProjectPageHandlers = \
        AdminAddProjectPageHandlers(
            injections.logger,
            injections.config,
            injections.rest_client,
            injections.metadata)
    handlers_modify_project: AdminModifyProjectPageHandlers = AdminModifyProjectPageHandlers(
            injections.logger,
            injections.config,
            injections.rest_client,
            injections.metadata)

    # Admin page | Projects (read): '/admin/projects'
    injections.logger.debug("=> %s GET /admin/projects",
                            "Admin Projects page (read)".ljust(40))

    @routes.route('/projects', methods=['GET'])
    async def admin_page_projects_read_request():
        return await handlers_projects.projects_read()

    # Admin page | Projects (update): '/admin/projects'
    injections.logger.debug("=> %s POST /admin/projects",
                            "Admin Projects page (post)".ljust(40))

    @routes.route('/projects', methods=['POST'])
    async def admin_page_projects_post_request():
        return await handlers_projects.projects_post()

    # Admin page | Add Project (read): '/admin/add_project'
    injections.logger.debug("=> %s GET /admin/add_project",
                            "Admin add project page (read)".ljust(40))

    @routes.route('/add_project', methods=['GET'])
    async def admin_add_project_read_request():
        return await handlers_add_project.add_project_get()

    # Admin page | Add Project (post): '/admin/add_project'
    injections.logger.debug("=> %s POST /admin/add_project",
                            "Admin add project page (post)".ljust(40))

    @routes.route('/add_project', methods=['POST'])
    async def admin_add_project_request():
        return await handlers_add_project.add_project_post()

    # Admin page | Modify Project (read): '/admin/modify_project'
    injections.logger.debug("=> %s GET /admin/modify_project",
                            "Admin Modify project page (read)".ljust(40))

    @routes.route('/<project_id>/modify_project', methods=['GET'])
    async def admin_modify_project_get_request(project_id: int):
        return await handlers_modify_project.modify_project_get(project_id)

    # Admin page | Modify Project (post): '/admin/modify_project'
    injections.logger.debug("=> %s POST /admin/modify_project",
                            "Admin Modify project page (post)".ljust(40))

    @routes.route('/<project_id>/modify_project', methods=['POST'])
    async def admin_modify_project_post_request(project_id: int):
        return await handlers_modify_project.modify_project_post(project_id)

    return routes
