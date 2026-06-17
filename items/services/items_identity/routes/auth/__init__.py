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
from items.services.items_identity.identity_configuration import IdentityConfiguration
from items.shared.service_state import ServiceState
from .authenticate_password_handler import AuthenticatePasswordHandler


def create_auth_routes(logger: logging.Logger,
                       service_state: ServiceState,
                       config: IdentityConfiguration) -> quart.Blueprint:
    """
    Create and configure authentication-related routes.

    This function creates the authentication blueprint, initializes
    the required route handlers, and registers all authentication
    endpoints with the blueprint.

    Currently registered routes include:

    * ``POST /auth/login`` - Authenticate a user using email and password
      credentials.

    Args:
        logger:
            Logger used for route registration and request handling.

        service_state:
            Shared service state used by authentication handlers to
            determine service availability and operational status.

        config:
            Identity service configuration used to initialize
            authentication components.

    Returns:
        A configured Quart blueprint containing all registered
        authentication routes.
    """
    auth_routes = quart.Blueprint("auth_routes", __name__)

    auth_password_handler: AuthenticatePasswordHandler = \
        AuthenticatePasswordHandler(logger, service_state, config)

    logger.debug("Registering Auth API routes:")

    logger.debug("=> %s POST /auth/login",
                 'Authenticate with password'.ljust(40))

    # pylint: disable=no-value-for-parameter
    @auth_routes.route('/auth/login', methods=['POST'])
    async def authenticate_password_request():
        return await auth_password_handler.authenticate_password()

    return auth_routes
