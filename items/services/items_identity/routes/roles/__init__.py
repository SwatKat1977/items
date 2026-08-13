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
from .list_roles_handler import ListRolesHandler
from .get_role_handler import GetRoleHandler
from .create_role_handler import CreateRoleHandler
from .modify_role_handler import ModifyRoleHandler
from .delete_role_handler import DeleteRoleHandler


def create_roles_routes(logger: logging.Logger,
                        service_state: ServiceState,
                        config: IdentityConfiguration) -> quart.Blueprint:
    """
    Create and configure role-related routes.

    Registered routes:

    * ``GET    /roles``           - List all roles (name only).
    * ``POST   /roles``           - Create a new role.
    * ``GET    /roles/<role_id>`` - Retrieve a single role's full grid.
    * ``PATCH  /roles/<role_id>`` - Update a role's name and/or grid.
    * ``DELETE /roles/<role_id>`` - Delete a role.

    This is role *definitions* only - assigning a role to a project
    membership is a separate concern, not covered by these routes.

    Args:
        logger:
            Logger used for route registration and request handling.

        service_state:
            Shared service state used by handlers to determine service
            availability and operational status.

        config:
            Identity service configuration used to initialize components.

    Returns:
        A configured Quart blueprint containing all registered role routes.
    """
    roles_routes = quart.Blueprint("roles_routes", __name__)

    handler_list = ListRolesHandler(logger, service_state, config)
    handler_get = GetRoleHandler(logger, service_state, config)
    handler_create = CreateRoleHandler(logger, service_state, config)
    handler_modify = ModifyRoleHandler(logger, service_state, config)
    handler_delete = DeleteRoleHandler(logger, service_state, config)

    logger.debug("Registering Roles API routes:")

    logger.debug("=> %s GET  /roles",
                 'List roles'.ljust(40))
    logger.debug("=> %s POST /roles",
                 'Create role'.ljust(40))
    logger.debug("=> %s GET  /roles/<role_id>",
                 'Get role'.ljust(40))
    logger.debug("=> %s PATCH /roles/<role_id>",
                 'Modify role'.ljust(40))
    logger.debug("=> %s DELETE /roles/<role_id>",
                 'Delete role'.ljust(40))

    # pylint: disable=no-value-for-parameter

    @roles_routes.route('/roles', methods=['GET'])
    async def list_roles_request():
        return await handler_list.list_roles()

    @roles_routes.route('/roles', methods=['POST'])
    async def create_role_request():
        return await handler_create.create_role()

    @roles_routes.route('/roles/<int:role_id>', methods=['GET'])
    async def get_role_request(role_id: int):
        return await handler_get.get_role(role_id)

    @roles_routes.route('/roles/<int:role_id>', methods=['PATCH'])
    async def modify_role_request(role_id: int):
        return await handler_modify.modify_role(role_id=role_id)

    @roles_routes.route('/roles/<int:role_id>', methods=['DELETE'])
    async def delete_role_request(role_id: int):
        return await handler_delete.delete_role(role_id)

    return roles_routes
