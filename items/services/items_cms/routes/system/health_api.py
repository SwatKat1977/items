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
from .health_api_view import HealthApiView


def create_blueprint(logger: logging.Logger,
                     service_state: ServiceState) -> Blueprint:
    """
    Creates and returns a Quart Blueprint for the Health Status API.

    This function initializes a `HealthApiView` instance and registers an
    asynchronous route `/health/status` for handling health check requests. The
    route is logged upon registration.

    Args:
        logger (logging.Logger): The logger instance used for logging API
                                 registration.
        service_state (ServiceState): The application state object passed to the
                                    view.

    Returns:
        Blueprint: A Quart Blueprint instance with the registered health status
                   route.
    """
    view = HealthApiView(logger, service_state)

    blueprint = Blueprint('health_api', __name__)

    logger.debug("---------------- Registering health routes ----------------")

    logger.debug("=> /health/status [GET]    : Get health status")
    @blueprint.route('/status', methods=['GET'])
    async def authenticate_request():
        return await view.health()

    return blueprint
