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
from .list_users_handler import ListUsersHandler
from .get_user_handler import GetUserHandler
from .create_user_handler import CreateUserHandler
from .modify_user_handler import ModifyUserHandler
from .reset_password_handler import ResetPasswordHandler
from .change_password_handler import ChangePasswordHandler


def create_users_routes(logger: logging.Logger,
                        service_state: ServiceState,
                        config: IdentityConfiguration) -> quart.Blueprint:
    """
    Create and configure user-related routes.

    Registered routes:

    * ``POST /users/profile``          - Retrieve a user's profile by email
      (internal; used by the gateway at login).
    * ``GET  /users``                  - List all user profiles.
    * ``POST /users``                  - Create a new user account.
    * ``GET  /users/<user_id>``        - Retrieve a single user's profile (UUID).
    * ``PATCH /users/<user_id>``       - Update a user's profile fields (UUID).
    * ``POST /users/<user_id>/password`` - Admin password reset (UUID).
    * ``POST /users/me/password``      - Self-service password change.

    Args:
        logger:
            Logger used for route registration and request handling.

        service_state:
            Shared service state used by handlers to determine service
            availability and operational status.

        config:
            Identity service configuration used to initialize components.

    Returns:
        A configured Quart blueprint containing all registered user routes.
    """
    # pylint: disable=too-many-locals
    users_routes = quart.Blueprint("users_routes", __name__)

    handler_profile = GetUserProfileHandler(logger, service_state, config)
    handler_list = ListUsersHandler(logger, service_state, config)
    handler_get = GetUserHandler(logger, service_state, config)
    handler_create = CreateUserHandler(logger, service_state, config)
    handler_modify = ModifyUserHandler(logger, service_state, config)
    handler_reset_password = ResetPasswordHandler(logger, service_state, config)
    handler_change_password = ChangePasswordHandler(logger, service_state, config)

    logger.debug("Registering Users API routes:")

    logger.debug("=> %s POST /users/profile",
                 'Get user profile'.ljust(40))
    logger.debug("=> %s GET  /users",
                 'List users'.ljust(40))
    logger.debug("=> %s POST /users",
                 'Create user'.ljust(40))
    logger.debug("=> %s GET  /users/<user_id>",
                 'Get user'.ljust(40))
    logger.debug("=> %s PATCH /users/<user_id>",
                 'Modify user'.ljust(40))
    logger.debug("=> %s POST /users/<user_id>/password",
                 'Reset password'.ljust(40))
    logger.debug("=> %s POST /users/me/password",
                 'Change own password'.ljust(40))

    # pylint: disable=no-value-for-parameter

    @users_routes.route('/users/profile', methods=['POST'])
    async def get_user_profile_request():
        return await handler_profile.get_user_profile()

    @users_routes.route('/users', methods=['GET'])
    async def list_users_request():
        return await handler_list.list_users()

    @users_routes.route('/users', methods=['POST'])
    async def create_user_request():
        return await handler_create.create_user()

    @users_routes.route('/users/<string:user_id>', methods=['GET'])
    async def get_user_request(user_id: str):
        return await handler_get.get_user(user_id)

    @users_routes.route('/users/<string:user_id>', methods=['PATCH'])
    async def modify_user_request(user_id: str):
        return await handler_modify.modify_user(user_id=user_id)

    @users_routes.route('/users/<string:user_id>/password', methods=['POST'])
    async def reset_password_request(user_id: str):
        return await handler_reset_password.reset_password(user_id=user_id)

    @users_routes.route('/users/me/password', methods=['POST'])
    async def change_password_request():
        return await handler_change_password.change_password()

    return users_routes
