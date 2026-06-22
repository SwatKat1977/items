"""
Copyright 2025-2026 Integrated Test Management Suite Development Team

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
from items.shared.service_state import ServiceState
from items.services.items_cms.cms_configuration import CMSConfiguration


def create_project_routes(logger: logging.Logger,
                          service_state: ServiceState,
                          config: CMSConfiguration) -> Blueprint:
    projects_routes = Blueprint("projects_routes", __name__)

    logger.debug("Registering Projects API routes:")

    # Get details of a specific project.
    logger.debug("=> %s GET /projects/<int:project_id>",
                 "Get project details".ljust(40))

    @projects_routes.route('/projects/<int:project_id>', methods=['GET'])
    async def get_project(project_id: int):
        return None
        # return await view.project_details(project_id)

    # List all of the available projects.
    logger.debug("=> %s GET /projects",
                 "List accessible projects".ljust(40))

    @projects_routes.route('/projects', methods=['GET'])
    async def list_projects():
        return None
        # return await view.list_projects()

    # Create project
    logger.debug("=> %s POST /projects",
                 "Create new project".ljust(40))

    @projects_routes.route('/projects', methods=['POST'])
    async def create_project():
        # pylint: disable=no-value-for-parameter
        return None
        # return await view.create_project()

    # Update project details.
    logger.debug("=> %s PATCH /projects/<int:project_id>",
                 "Update project".ljust(40))

    @projects_routes.route('/projects/<int:project_id>', methods=['PATCH'])
    async def update_project(project_id: int):
        # pylint: disable=no-value-for-parameter
        return None
        # return await view.modify_project(project_id)

    # Delete a project.
    logger.debug("=> %s DELETE /projects/<int:project_id>",
                 "Delete a project".ljust(40))

    @projects_routes.route('/projects/<int:project_id>', methods=['DELETE'])
    async def delete_project(project_id: int):
        # return await view.delete_project(project_id)
        return None

    return projects_routes
