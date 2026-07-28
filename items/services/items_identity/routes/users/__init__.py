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
from items.services.items_identity.identity_configuration import (
    IdentityConfiguration)
from items.shared.service_state import ServiceState
from .get_user_profile_handler import GetUserProfileHandler


def create_users_routes(logger: logging.Logger,
                        service_state: ServiceState,
                        config: IdentityConfiguration) -> quart.Blueprint:
    """
    Create and configure user-related routes.

    Currently registered routes include:

    * ``POST /users/profile`` - Retrieve a user's profile details, including
      whether they are an administrator.

    Args:
        logger:
            Logger used for route registration and request handling.

        service_state:
            Shared service state used by handlers to determine service
            availability and operational status.

        config:
            Identity service configuration used to initialize user
            components.

    Returns:
        A configured Quart blueprint containing all registered user routes.
    """
    users_routes = quart.Blueprint("users_routes", __name__)

    profile_handler: GetUserProfileHandler = GetUserProfileHandler(
        logger, service_state, config)

    logger.debug("Registering Users API routes:")

    logger.debug("=> %s POST /users/profile",
                 'Get user profile'.ljust(40))

    # pylint: disable=no-value-for-parameter
    @users_routes.route('/users/profile', methods=['POST'])
    async def get_user_profile_request():
        return await profile_handler.get_user_profile()

    return users_routes
