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
import quart
from items.shared.service_state import ServiceState
from .auth import create_auth_routes
from .system import create_system_routes
from items.services.items_identity.identity_configuration import (
    IdentityConfiguration)


def create_routes(logger: logging.Logger,
                  state: ServiceState,
                  configuration: IdentityConfiguration) -> quart.Blueprint:
    """
    Create and configure the API route blueprint for the application.

    This function initializes a Quart blueprint for the API routes and registers
    sub-blueprints, such as the authentication API, under appropriate URL prefixes.

    Args:
        logger (logging.Logger): Logger instance for logging within the route views.
        state (ServiceState): Shared application state object passed to route views.

    Returns:
        quart.Blueprint: The configured API blueprint with registered sub-routes.
    """
    routes_bp = quart.Blueprint("api_routes", __name__)

    routes_bp.register_blueprint(create_auth_routes(logger, state, configuration))
    routes_bp.register_blueprint(create_system_routes(logger, state))

    return routes_bp
