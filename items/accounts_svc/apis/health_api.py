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
from apis.health_api_view import HealthApiView
from state_object import StateObject


def create_blueprint(logger: logging.Logger,
                     state_object: StateObject) -> Blueprint:
    """
    Creates and registers a Flask Blueprint for service health API routes.

    This function initializes a `View` object with the provided logger, and
    then defines an API endpoint for health status. It registers the route the
    GET method of `/health/status` to handle the request.

    Args:
        logger (logging.Logger): A logger instance for logging messages.

    Returns:
        Blueprint: A Flask `Blueprint` object containing the registered route.

    Example:
        >>> from flask import Flask
        >>> from your_module import create_blueprint
        >>> app = Flask(__name__)
        >>> blueprint = create_blueprint(ogger)
        >>> app.register_blueprint(blueprint)
    """
    view = HealthApiView(logger, state_object)

    blueprint = Blueprint('health_api', __name__)

    logger.info("Registering Health Status API:")
    logger.info("=> health/status [GET]")

    @blueprint.route('/health/status', methods=['GET'])
    async def authenticate_request():
        return await view.health()

    return blueprint
