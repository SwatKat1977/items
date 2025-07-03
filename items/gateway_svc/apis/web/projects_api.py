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


def create_blueprint(logger: logging.Logger) -> Blueprint:
    view = ProjectsApiView(logger)

    blueprint = Blueprint('project_api', __name__)

    logger.info("Registering Project endpoint:")

    logger.info("=> /project/overviews [GET]")

    @blueprint.route('/project/overviews', methods=['GET'])
    async def project_overviews_request():
        return await view.project_overviews()

    @blueprint.route('/project/details/<project_id>', methods=['GET'])
    async def project_details_request(project_id: int):
        return await view.project_details(project_id)

    logger.info("=> /project/add [POST]")

    @blueprint.route('/project/add', methods=['POST'])
    async def add_project_request():
        return await view.add_project()

    logger.info("=> /project/modify/<int:project_id> [POST]")

    @blueprint.route('/project/modify/<int:project_id>', methods=['POST'])
    async def modify_project_request(project_id: int):
        return await view.modify_project(project_id)

    logger.info("=> /<project_id>/delete_project [DELETE]")

    @blueprint.route('/<project_id>/delete_project', methods=['DELETE'])
    async def delete_project_request(project_id: int):
        return await view.delete_project(project_id)

    return blueprint
