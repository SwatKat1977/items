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
from items.services.items_gateway.routes.web.roles.list_roles_handler import (
    ListRolesHandler)
from items.services.items_gateway.routes.web.roles.get_role_handler import (
    GetRoleHandler)
from items.services.items_gateway.routes.web.roles.create_role_handler import (
    CreateRoleHandler)
from items.services.items_gateway.routes.web.roles.modify_role_handler import (
    ModifyRoleHandler)
from items.services.items_gateway.routes.web.roles.delete_role_handler import (
    DeleteRoleHandler)


def create_roles_routes(injections: RouteInjections) -> Blueprint:
    """Create the Blueprint containing role management web routes.

    All routes are admin-only, enforced here via ``@require_administrator``
    rather than trusted to the caller - role definitions gate what every
    project member can do, so managing them is administrator-only, same as
    users, invites, and testcase custom fields.

    Registered routes:
        GET    /roles              List all roles (name only).
        POST   /roles              Create a new role.
        GET    /roles/<role_id>    Get a single role's full grid.
        PATCH  /roles/<role_id>    Update a role's name and/or grid.
        DELETE /roles/<role_id>    Delete a role.

    Args:
        injections: Shared application dependencies.

    Returns:
        A configured Quart Blueprint.
    """
    routes = Blueprint('roles_routes', __name__)

    handler_list = ListRolesHandler(
        injections.logger, injections.configuration, injections.rest_client)
    handler_get = GetRoleHandler(
        injections.logger, injections.configuration, injections.rest_client)
    handler_create = CreateRoleHandler(
        injections.logger, injections.configuration, injections.rest_client)
    handler_modify = ModifyRoleHandler(
        injections.logger, injections.configuration, injections.rest_client)
    handler_delete = DeleteRoleHandler(
        injections.logger, injections.configuration, injections.rest_client)

    injections.logger.debug(" Roles WEB routes:")

    injections.logger.debug("=> %s GET  /web/roles",
                            "List roles".ljust(40))

    @routes.route('/roles', methods=['GET'])
    @require_administrator(injections.sessions)
    async def list_roles_request():
        return await handler_list.list_roles()

    injections.logger.debug("=> %s POST /web/roles",
                            "Create role".ljust(40))

    @routes.route('/roles', methods=['POST'])
    @require_administrator(injections.sessions)
    async def create_role_request():
        return await handler_create.create_role()

    injections.logger.debug("=> %s GET  /web/roles/<int:role_id>",
                            "Get role".ljust(40))

    @routes.route('/roles/<int:role_id>', methods=['GET'])
    @require_administrator(injections.sessions)
    async def get_role_request(role_id: int):
        return await handler_get.get_role(role_id)

    injections.logger.debug("=> %s PATCH /web/roles/<int:role_id>",
                            "Modify role".ljust(40))

    @routes.route('/roles/<int:role_id>', methods=['PATCH'])
    @require_administrator(injections.sessions)
    async def modify_role_request(role_id: int):
        return await handler_modify.modify_role(role_id)

    injections.logger.debug("=> %s DELETE /web/roles/<int:role_id>",
                            "Delete role".ljust(40))

    @routes.route('/roles/<int:role_id>', methods=['DELETE'])
    @require_administrator(injections.sessions)
    async def delete_role_request(role_id: int):
        return await handler_delete.delete_role(role_id)

    return routes
