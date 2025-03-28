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
from apis.project_api_view import ProjectApiView
from sqlite_interface import SqliteInterface


def create_blueprint(logger: logging.Logger, db: SqliteInterface) -> Blueprint:
    """
    Creates and returns a Quart Blueprint for the project API.

    This function initializes a `ProjectApiView` instance and registers
    asynchronous routes for handling requests.

    Args:
        logger (logging.Logger): The logger instance used for logging API
                                 registration.
        db (SqliteInterface): Database interface instance.

    Returns:
        Blueprint: A Quart Blueprint instance with the registered routes.
    """
    view = ProjectApiView(logger, db)

    blueprint = Blueprint('project_api', __name__)

    logger.info("Registering Project API:")

    logger.info("=> /project/overviews [GET]")

    @blueprint.route('/project/overviews', methods=['GET'])
    async def project_overview():
        return await view.project_overviews()

    logger.info("=> /project/add [POST]")

    @blueprint.route('/project/add', methods=['POST'])
    async def add_project():
        return await view.add_project()

    logger.info("=> /project/delete [DELETE]")

    @blueprint.route('/project/delete/<int:project_id>', methods=['DELETE'])
    async def delete_project(project_id: int):
        return await view.delete_project(project_id)

    return blueprint
