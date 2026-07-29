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
from items.services.items_identity.identity_configuration import (
    IdentityConfiguration)
from .auth import create_auth_routes
from .system import create_system_routes
from .users import create_users_routes


def create_routes(logger: logging.Logger,
                  state: ServiceState,
                  configuration: IdentityConfiguration) -> quart.Blueprint:
    """
    Create and configure the application's API route blueprint.

    This function creates the root API blueprint and registers all
    route groups used by the identity service. Each route group is
    implemented as a separate Quart blueprint and is registered under
    the root API blueprint.

    Currently registered route groups include:

    * Authentication routes
    * System and health monitoring routes
    * User routes

    Args:
        logger:
            Logger used by route handlers and route registration code.

        state:
            Shared service state used by route handlers to determine
            service availability and operational status.

        configuration:
            Identity service configuration used to initialize
            route handlers and supporting services.

    Returns:
        A configured Quart blueprint containing all registered API
        routes for the application.
    """
    routes_bp = quart.Blueprint("api_routes", __name__)

    routes_bp.register_blueprint(create_auth_routes(logger, state, configuration))
    routes_bp.register_blueprint(create_system_routes(logger, state))
    routes_bp.register_blueprint(create_users_routes(logger, state,
                                                    configuration))

    return routes_bp
