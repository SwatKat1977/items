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
from apis.test_cases_api_view import TestCasesApiView
from metadata_settings import MetadataSettings


def create_blueprint(logger: logging.Logger,
                     metadata: MetadataSettings) -> Blueprint:
    """
    Creates and registers a Flask Blueprint for handling authentication
    handshake API routes.

    This function initializes a `View` object with the provided SQL interface
    and logger, and then defines an API endpoint for authentication handshake.

    Args:
        logger (logging.Logger): A logger instance for logging messages.
        metadata (MetadataSettings): A metadata settings instance.

    Returns:
        Blueprint: A Flask `Blueprint` object containing the registered route.
    """
    view = TestCasesApiView(logger, metadata)

    blueprint = Blueprint('test_cases_api', __name__)

    logger.info("Registering Test Cases endpoint:")

    logger.info("=> /<project_id>/test_cases [GET]")

    @blueprint.route('/<project_id>/test_cases', methods=['GET'])
    async def test_definitions_page_request(project_id: int):
        return await view.test_cases(project_id)

    return blueprint
