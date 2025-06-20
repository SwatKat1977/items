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
from .projects_api_view import ProjectsApiView
from state_object import StateObject


def create_blueprint(logger: logging.Logger,
                     state_object: StateObject) -> Blueprint:
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
    view = ProjectsApiView(logger, state_object)

    blueprint = Blueprint('project_api', __name__)

    logger.debug("Registering WEB projects routes:")

    logger.debug("=> /details/<int:project_id> [GET]")

    @blueprint.route('/details/<project_id>', methods=['GET'])
    async def project_details(project_id: int):
        return await view.project_details(project_id)

    logger.debug("=> /overviews [GET]")

    @blueprint.route('/overviews', methods=['GET'])
    async def project_overviews():
        return await view.project_overviews()

    logger.debug("=> /add [POST]")

    @blueprint.route('/add', methods=['POST'])
    async def add_project():
        return await view.add_project()

    logger.debug("=> /modify [POST]")

    @blueprint.route('/modify/<int:project_id>', methods=['POST'])
    async def modify_project(project_id: int):
        return await view.modify_project(project_id)

    logger.debug("=> /project/delete [DELETE]")

    @blueprint.route('/delete/<int:project_id>', methods=['DELETE'])
    async def delete_project(project_id: int):
        return await view.delete_project(project_id)

    return blueprint
