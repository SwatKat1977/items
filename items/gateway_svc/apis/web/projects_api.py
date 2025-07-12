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

    logger.debug("Registering WEB Project endpoint:")

    logger.debug(f"=> {'List all projects'.ljust(30)}GET /web/projects")

    @blueprint.route('/projects', methods=['GET'])
    async def project_overviews_request():
        return await view.list_all_projects()

    logger.debug(f"=> {'Retrieve a project'.ljust(30)}"
                 "GET /web/projects/<project_id>")

    @blueprint.route('/projects/<project_id>', methods=['GET'])
    async def project_details_request(project_id: int):
        return await view.retrieve_a_project(project_id)

    return blueprint
