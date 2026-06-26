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
from apis.projects_api_view import ProjectsApiView
from metadata_settings import MetadataSettings


def create_blueprint(logger: logging.Logger,
                     metadata: MetadataSettings) -> Blueprint:
    """
    Creates and registers a Quart Blueprint for handling HTML pages related to
    projects.

    This function initializes a `View` object with Metadata settings and an
    instance of logger, and then defines  API endpoints for projects pages.

    Args:
        logger (logging.Logger): A logger instance for logging messages.
        metadata (MetadataSettings): A metadata settings instance.

    Returns:
        Blueprint: A Quart `Blueprint` object containing the registered route.
    """
    view = ProjectsApiView(logger, metadata)

    blueprint = Blueprint('test_cases_api', __name__)

    logger.debug("-------------- Registering Projects routes ----------------")

    logger.debug("=> /<project_id>/project_overview [GET] : Project overview "
                 "(web page)")

    @blueprint.route('/<project_id>/project_overview',
                     methods=['GET'])
    async def project_overview_request(project_id: int):
        return await view.project_overview(project_id)

    logger.debug("=> /<project_id>/test_cases [GET]       : Project test cases "
                 "(web page)")

    @blueprint.route('/<project_id>/test_cases', methods=['GET'])
    async def test_definitions_page_request(project_id: int):
        return await view.test_cases(project_id)

    return blueprint
