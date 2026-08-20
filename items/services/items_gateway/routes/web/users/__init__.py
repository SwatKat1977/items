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
from items.services.items_gateway.auth_decorators import require_administrator
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
from items.services.items_gateway.routes.web.users.list_user_projects_handler import (
    ListUserProjectsHandler)
from items.services.items_gateway.routes.web.users.add_user_project_handler import (
    AddUserProjectHandler)
from items.services.items_gateway.routes.web.users.modify_user_project_handler import (
    ModifyUserProjectHandler)
from items.services.items_gateway.routes.web.users.remove_user_project_handler import (
    RemoveUserProjectHandler)


def create_users_routes(injections: RouteInjections) -> Blueprint:
    """Create the Blueprint containing user management web routes.

    All routes are admin-only, enforced here via ``@require_administrator``
    rather than trusted to the caller.

    Registered routes:
        GET  /users              List all user accounts.
        POST /users              Create a user account.
        GET  /users/<user_id>    Get a single user account.
        PATCH /users/<user_id>   Update a user's profile fields (patch-style).
        POST /users/<user_id>/password   Reset a user's password (admin).
        GET  /users/<user_id>/projects   List the user's project memberships.
        POST /users/<user_id>/projects   Add the user to a project.
        PATCH /users/<user_id>/projects/<project_id>   Change the user's
            role on a project.
        DELETE /users/<user_id>/projects/<project_id>   Remove the user's
            membership of a project.

    Note:
        ``POST /users/me/password`` (change own password) is not registered
        here yet. ``SessionEntry.user_id`` now exists (added for
        ``gateway_membership_enforcement``) so the gateway can resolve the
        caller's user ID from their session - the architecture blocker is
        gone, this route just hasn't been built.

    Args:
        injections: Shared application dependencies.

    Returns:
        A configured Quart Blueprint.
    """
    # pylint: disable=too-many-locals
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
        injections.logger, injections.configuration, injections.rest_client,
        injections.email_service)
    handler_list_projects = ListUserProjectsHandler(
        injections.logger, injections.configuration, injections.rest_client)
    handler_add_project = AddUserProjectHandler(
        injections.logger, injections.configuration, injections.rest_client,
        injections.sessions)
    handler_modify_project = ModifyUserProjectHandler(
        injections.logger, injections.configuration, injections.rest_client)
    handler_remove_project = RemoveUserProjectHandler(
        injections.logger, injections.configuration, injections.rest_client,
        injections.sessions)

    injections.logger.debug(" Users WEB routes:")

    injections.logger.debug("=> %s GET  /web/users",
                            "List users".ljust(40))

    @routes.route('/users', methods=['GET'])
    @require_administrator(injections.sessions)
    async def list_users_request():
        return await handler_list.list_users()

    injections.logger.debug("=> %s POST /web/users",
                            "Create user".ljust(40))

    @routes.route('/users', methods=['POST'])
    @require_administrator(injections.sessions)
    async def create_user_request():
        return await handler_create.create_user()

    injections.logger.debug("=> %s GET  /web/users/<string:user_id>",
                            "Get user".ljust(40))

    @routes.route('/users/<string:user_id>', methods=['GET'])
    @require_administrator(injections.sessions)
    async def get_user_request(user_id: str):
        return await handler_get.get_user(user_id)

    injections.logger.debug("=> %s PATCH /web/users/<string:user_id>",
                            "Modify user".ljust(40))

    @routes.route('/users/<string:user_id>', methods=['PATCH'])
    @require_administrator(injections.sessions)
    async def modify_user_request(user_id: str):
        return await handler_modify.modify_user(user_id)

    injections.logger.debug("=> %s POST /web/users/<string:user_id>/password",
                            "Reset user password".ljust(40))

    @routes.route('/users/<string:user_id>/password', methods=['POST'])
    @require_administrator(injections.sessions)
    async def reset_password_request(user_id: str):
        return await handler_reset_password.reset_password(user_id)

    injections.logger.debug("=> %s GET  /web/users/<string:user_id>/projects",
                            "List project memberships".ljust(40))

    @routes.route('/users/<string:user_id>/projects', methods=['GET'])
    @require_administrator(injections.sessions)
    async def list_user_projects_request(user_id: str):
        return await handler_list_projects.list_user_projects(user_id)

    injections.logger.debug("=> %s POST /web/users/<string:user_id>/projects",
                            "Add project membership".ljust(40))

    @routes.route('/users/<string:user_id>/projects', methods=['POST'])
    @require_administrator(injections.sessions)
    async def add_user_project_request(user_id: str):
        return await handler_add_project.add_user_project(user_id)

    injections.logger.debug(
        "=> %s PATCH /web/users/<string:user_id>/projects/<int:project_id>",
        "Change membership role".ljust(40))

    @routes.route('/users/<string:user_id>/projects/<int:project_id>',
                  methods=['PATCH'])
    @require_administrator(injections.sessions)
    async def modify_user_project_request(user_id: str, project_id: int):
        return await handler_modify_project.modify_user_project(
            user_id, project_id)

    injections.logger.debug(
        "=> %s DELETE /web/users/<string:user_id>/projects/<int:project_id>",
        "Remove project membership".ljust(40))

    @routes.route('/users/<string:user_id>/projects/<int:project_id>',
                  methods=['DELETE'])
    @require_administrator(injections.sessions)
    async def remove_user_project_request(user_id: str, project_id: int):
        return await handler_remove_project.remove_user_project(
            user_id, project_id)

    return routes
