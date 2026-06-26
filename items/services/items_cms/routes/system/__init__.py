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
from items.shared.service_state import ServiceState
from .health_api_view import HealthApiView


def create_system_routes(logger: logging.Logger,
                         service_state: ServiceState) -> Blueprint:
    """Create and return the system API Blueprint.

    Instantiates the system repository and service once, wires them
    into individual route handlers, and registers all system endpoints
    with a Quart Blueprint.

    Args:
        logger:       Parent logger instance.
        service_state: Shared service operational state.

    Returns:
        A configured Blueprint with all system routes registered.
    """
    #view = HealthApiView(logger, service_state)

    system_routes = Blueprint("system_routes", __name__)

    logger.debug("--- Registering System API routes ---")

    logger.debug("=> /health/status [GET]    : Get health status")
    @system_routes.route('/status', methods=['GET'])
    async def authenticate_request():
        return await view.health()

    return system_routes
