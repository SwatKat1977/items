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
from items_common.service_state import ServiceState
from .projects_api_view import ProjectsApiView


def create_blueprint(logger: logging.Logger,
                     service_state: ServiceState) -> Blueprint:
    """
    Creates and returns a Quart Blueprint for the project API.

    This function initializes a `ProjectApiView` instance and registers
    asynchronous routes for handling requests.

    Args:
        logger (logging.Logger): The logger instance used for logging API
                                 registration.
        state_object (StateObject): Instance of state object.

    Returns:
        Blueprint: A Quart Blueprint instance with the registered routes.
    """
    view = ProjectsApiView(logger, service_state)

    blueprint = Blueprint('project_api', __name__)

    logger.debug("--------------- Registering projects routes ---------------")

    logger.debug("=> /<int:project_id> [GET] : Get project details")
    @blueprint.route('/<project_id>', methods=['GET'])
    async def project_details(project_id: int):
        return await view.project_details(project_id)

    logger.debug("=> / [GET]                 : List accessible projects")
    @blueprint.route('/', methods=['GET'])
    async def list_projects():
        return await view.list_projects()

    # Create project
    logger.debug("=> /projects [POST]        : Create project")
    @blueprint.route('/', methods=['POST'])
    async def create_project():
        # pylint: disable=no-value-for-parameter
        return await view.create_project()

    logger.debug("=> /projects [PATCH]       : Modify project ")
    @blueprint.route('/<int:project_id>', methods=['PATCH'])
    async def modify_project(project_id: int):
        # pylint: disable=no-value-for-parameter
        return await view.modify_project(project_id)

    logger.debug("=> /projects [DELETE]      : Modify project ")
    @blueprint.route('/<int:project_id>', methods=['DELETE'])
    async def delete_project(project_id: int):
        return await view.delete_project(project_id)

    return blueprint
