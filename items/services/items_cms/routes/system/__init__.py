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
from quart import Blueprint, Response
from items.shared.service_state import ServiceState
from items.services.items_cms.routes.system.health_handler import HealthHandler


def create_system_routes(logger: logging.Logger,
                         state_object: ServiceState) -> Blueprint:
    """Create and register system-related blueprints.

    This function creates the parent system blueprint and registers
    all system-level route blueprints, such as health check routes.

    Args:
        logger: Logger instance used by system route handlers.
        state_object (ServiceState): A StateObject instance.

    Returns:
        The configured system blueprint containing all registered
        system routes.
    """
    system_routes = Blueprint("system_routes", __name__)

    # Health route handler
    health_route_handler: HealthHandler = HealthHandler(logger, state_object)

    logger.debug("--- Registering System API routes ---")

    logger.debug("=> %s GET /system/health",
                 'Get system health'.ljust(40))

    @system_routes.route('/system/health', methods=['GET'])
    async def health_request():
        """Handle incoming system health requests.

        Returns:
            A response containing the current system health status.
        """
        return await health_route_handler.health()

    return system_routes
