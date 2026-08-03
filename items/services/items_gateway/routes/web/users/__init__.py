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
from quart import Blueprint
from items.services.items_gateway.route_injections import RouteInjections
from items.services.items_gateway.routes.web.users.list_users_handler import (
    ListUsersHandler)
from items.services.items_gateway.routes.web.users.get_user_handler import (
    GetUserHandler)
from items.services.items_gateway.routes.web.users.create_user_handler import (
    CreateUserHandler)
from items.services.items_gateway.routes.web.users.modify_user_handler import (
    ModifyUserHandler)
from items.services.items_gateway.routes.web.users.reset_password_handler import (
    ResetPasswordHandler)


def create_users_routes(injections: RouteInjections) -> Blueprint:
    """Create the Blueprint containing user management web routes.

    All routes are admin-only and must be enforced at this layer or by the
    caller (the web portal, which checks ``is_administrator`` before calling).

    Registered routes:
        GET  /users              List all user accounts.
        POST /users              Create a user account.
        GET  /users/<user_id>    Get a single user account.
        PATCH /users/<user_id>   Update a user's profile fields (patch-style).
        POST /users/<user_id>/password   Reset a user's password (admin).

    Note:
        ``POST /users/me/password`` (change own password) is not registered
        here. It requires the gateway to resolve the caller's user ID from
        the session, which needs additional session architecture
        (``user_id`` stored in ``SessionEntry`` at login).

    Args:
        injections: Shared application dependencies.

    Returns:
        A configured Quart Blueprint.
    """
    routes = Blueprint('users_routes', __name__)

    handler_list = ListUsersHandler(
        injections.logger, injections.configuration, injections.rest_client)
    handler_get = GetUserHandler(
        injections.logger, injections.configuration, injections.rest_client)
    handler_create = CreateUserHandler(
        injections.logger, injections.configuration, injections.rest_client)
    handler_modify = ModifyUserHandler(
        injections.logger, injections.configuration, injections.rest_client)
    handler_reset_password = ResetPasswordHandler(
        injections.logger, injections.configuration, injections.rest_client)

    injections.logger.debug(" Users WEB routes:")

    injections.logger.debug("=> %s GET  /web/users",
                            "List users".ljust(40))

    @routes.route('/users', methods=['GET'])
    async def list_users_request():
        return await handler_list.list_users()

    injections.logger.debug("=> %s POST /web/users",
                            "Create user".ljust(40))

    @routes.route('/users', methods=['POST'])
    async def create_user_request():
        return await handler_create.create_user()

    injections.logger.debug("=> %s GET  /web/users/<int:user_id>",
                            "Get user".ljust(40))

    @routes.route('/users/<int:user_id>', methods=['GET'])
    async def get_user_request(user_id: int):
        return await handler_get.get_user(user_id)

    injections.logger.debug("=> %s PATCH /web/users/<int:user_id>",
                            "Modify user".ljust(40))

    @routes.route('/users/<int:user_id>', methods=['PATCH'])
    async def modify_user_request(user_id: int):
        return await handler_modify.modify_user(user_id)

    injections.logger.debug("=> %s POST /web/users/<int:user_id>/password",
                            "Reset user password".ljust(40))

    @routes.route('/users/<int:user_id>/password', methods=['POST'])
    async def reset_password_request(user_id: int):
        return await handler_reset_password.reset_password(user_id)

    return routes
