"""
Copyright 2025-2026 Integrated Test Management Suite Development Team
Copyright 2017-2025 INTMAC Development Team [Defunct]

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
from items.services.items_web_portal.page_handler_injections import (
    PageHandlerInjections)
from items.services.items_web_portal.page_handlers.admin.users.\
    admin_add_user_page_handler import AdminAddUserPageHandler
from items.services.items_web_portal.page_handlers.admin.users.\
    admin_modify_user_page_handler import AdminModifyUserPageHandler
from items.services.items_web_portal.page_handlers.admin.users.\
    admin_reset_password_page_handler import AdminResetPasswordPageHandler


def create_admin_users_page_handlers(injections: PageHandlerInjections) -> Blueprint:
    """Create the admin user management route handlers.

    Registers routes for listing, creating, and editing users under the
    /users_roles prefix.

    Args:
        injections: Dependency injection container providing the logger,
            configuration, REST client, and metadata.

    Returns:
        A configured Quart blueprint containing the user management routes.
    """
    routes = Blueprint('admin_users_routes', __name__)

    handler_add_user = AdminAddUserPageHandler(
        injections.logger,
        injections.config,
        injections.rest_client,
        injections.metadata)

    handler_modify_user = AdminModifyUserPageHandler(
        injections.logger,
        injections.config,
        injections.rest_client,
        injections.metadata)

    handler_reset_password = AdminResetPasswordPageHandler(
        injections.logger,
        injections.config,
        injections.rest_client,
        injections.metadata)

    injections.logger.debug("=> %s GET /admin/users_roles/add",
                            "Admin add user page (read)".ljust(40))

    @routes.route('/add', methods=['GET'])
    async def admin_add_user_get():
        return await handler_add_user.add_user_get()

    injections.logger.debug("=> %s POST /admin/users_roles/add",
                            "Admin add user (submit)".ljust(40))

    @routes.route('/add', methods=['POST'])
    async def admin_add_user_post():
        return await handler_add_user.add_user_post()

    injections.logger.debug("=> %s GET /admin/users_roles/<id>/modify",
                            "Admin modify user page (read)".ljust(40))

    @routes.route('/<string:user_id>/modify', methods=['GET'])
    async def admin_modify_user_get(user_id: str):
        return await handler_modify_user.modify_user_get(user_id)

    injections.logger.debug("=> %s POST /admin/users_roles/<id>/modify",
                            "Admin modify user (submit)".ljust(40))

    @routes.route('/<string:user_id>/modify', methods=['POST'])
    async def admin_modify_user_post(user_id: str):
        return await handler_modify_user.modify_user_post(user_id)

    injections.logger.debug("=> %s POST /admin/users_roles/<id>/projects",
                            "Admin add user project".ljust(40))

    @routes.route('/<string:user_id>/projects', methods=['POST'])
    async def admin_add_user_project(user_id: str):
        return await handler_modify_user.add_user_project(user_id)

    injections.logger.debug(
        "=> %s POST /admin/users_roles/<id>/projects/<id>/modify",
        "Admin modify user project role".ljust(40))

    @routes.route('/<string:user_id>/projects/<int:project_id>/modify',
                  methods=['POST'])
    async def admin_modify_user_project(user_id: str, project_id: int):
        return await handler_modify_user.modify_user_project(
            user_id, project_id)

    injections.logger.debug(
        "=> %s POST /admin/users_roles/<id>/projects/<id>/delete",
        "Admin remove user project".ljust(40))

    @routes.route('/<string:user_id>/projects/<int:project_id>/delete',
                  methods=['POST'])
    async def admin_remove_user_project(user_id: str, project_id: int):
        return await handler_modify_user.remove_user_project(
            user_id, project_id)

    injections.logger.debug("=> %s GET /admin/users_roles/<id>/reset_password",
                            "Admin reset password page (read)".ljust(40))

    @routes.route('/<string:user_id>/reset_password', methods=['GET'])
    async def admin_reset_password_get(user_id: str):
        return await handler_reset_password.reset_password_get(user_id)

    injections.logger.debug("=> %s POST /admin/users_roles/<id>/reset_password",
                            "Admin reset password (submit)".ljust(40))

    @routes.route('/<string:user_id>/reset_password', methods=['POST'])
    async def admin_reset_password_post(user_id: str):
        return await handler_reset_password.reset_password_post(user_id)

    return routes
