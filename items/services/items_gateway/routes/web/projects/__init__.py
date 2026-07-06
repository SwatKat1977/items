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
from weaver_framework.microservice.rest_client import RestClient
from items.services.items_gateway.gateway_configuration import (
    GatewayConfiguration)
from items.services.items_gateway.routes.web.projects.add_project_handler \
    import AddProjectHandler
from items.services.items_gateway.routes.web.projects.delete_project_handler \
    import DeleteProjectHandler
from items.services.items_gateway.routes.web.projects.get_all_projects_handler \
    import GetAllProjectsHandler
from items.services.items_gateway.routes.web.projects.get_project_handler \
    import GetProjectHandler
from items.services.items_gateway.routes.web.projects.update_project_handler \
    import UpdateProjectHandler


def create_projects_routes(logger: logging.Logger,
                           config: GatewayConfiguration,
                           rest_client: RestClient) -> Blueprint:
    """Create the project management API routes.

    Creates and configures the Blueprint containing all project-related
    gateway endpoints. Each route delegates request handling to a dedicated
    handler class responsible for communicating with the CMS service.

    The following endpoints are registered:

    - ``GET /projects`` - List all accessible projects.
    - ``GET /projects/<project_id>`` - Retrieve a specific project.
    - ``POST /projects`` - Create a new project.
    - ``PATCH /projects/<project_id>`` - Update an existing project.
    - ``DELETE /projects/<project_id>`` - Delete a project.

    Args:
        logger: Parent logger used for route registration logging and for
            creating child loggers within route handlers.
        config: Gateway configuration containing backend service endpoint
            information.
        rest_client: REST client used by the route handlers to communicate
            with backend services.

    Returns:
        A configured Quart ``Blueprint`` containing all project-related API
        routes.
    """
    handler_add_project: AddProjectHandler = AddProjectHandler(logger,
                                                               config,
                                                               rest_client)
    handler_delete_project: DeleteProjectHandler = DeleteProjectHandler(logger,
                                                               config,
                                                               rest_client)
    handler_get_all_projects: GetAllProjectsHandler = GetAllProjectsHandler(
        logger,
        config,
        rest_client)
    handler_get_project: GetProjectHandler = GetProjectHandler(logger,
                                                               config,
                                                               rest_client)
    handler_update_project: UpdateProjectHandler = UpdateProjectHandler(
        logger, config, rest_client)

    projects_routes = Blueprint("projects_routes", __name__)

    logger.debug(" Projects WEB routes:")

    # Get details of a specific project.
    logger.debug("=> %s GET /projects/<int:project_id>",
                 "Get project details".ljust(40))

    @projects_routes.route('/projects/<int:project_id>', methods=['GET'])
    async def get_project(project_id: int):
        return await handler_get_project.get_project(project_id)

    # List all of the available projects.
    logger.debug("=> %s GET /projects",
                 "List accessible projects".ljust(40))

    @projects_routes.route('/projects', methods=['GET'])
    async def list_projects():
        return await handler_get_all_projects.list_all_projects()

    # Create project
    logger.debug("=> %s POST /projects",
                 "Add new project".ljust(40))

    @projects_routes.route('/projects', methods=['POST'])
    async def add_project():
        # pylint: disable=no-value-for-parameter
        return await handler_add_project.add_project()

    # Update project details.
    logger.debug("=> %s PATCH /projects/<int:project_id>",
                 "Update project".ljust(40))

    @projects_routes.route('/projects/<int:project_id>', methods=['PATCH'])
    async def update_project(project_id: int):
        # pylint: disable=no-value-for-parameter
        return await handler_update_project.update_project(project_id)

    # Delete a project.
    logger.debug("=> %s DELETE /projects/<int:project_id>",
                 "Delete a project".ljust(40))

    @projects_routes.route('/projects/<int:project_id>', methods=['DELETE'])
    async def delete_project(project_id: int):
        return await handler_delete_project.delete_project(project_id)

    return projects_routes
