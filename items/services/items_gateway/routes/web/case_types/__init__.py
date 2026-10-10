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
from items.services.items_gateway.auth_decorators import (
    require_administrator, require_session)
from items.services.items_gateway.route_injections import RouteInjections
from items.services.items_gateway.routes.web.case_types.\
    create_case_type_handler import CreateCaseTypeHandler
from items.services.items_gateway.routes.web.case_types.\
    delete_case_type_handler import DeleteCaseTypeHandler
from items.services.items_gateway.routes.web.case_types.\
    get_case_type_handler import GetCaseTypeHandler
from items.services.items_gateway.routes.web.case_types.\
    list_case_types_handler import ListCaseTypesHandler
from items.services.items_gateway.routes.web.case_types.\
    modify_case_type_handler import ModifyCaseTypeHandler
from items.services.items_gateway.routes.web.case_types.\
    set_default_case_type_handler import SetDefaultCaseTypeHandler


def create_case_types_routes(injections: RouteInjections) -> Blueprint:
    """Create the Blueprint containing test case type web routes.

    The two read routes need any valid session (``@require_session``): every
    user who creates or edits a test case needs the list of types, and the
    default to pre-select, not just administrators. Case types are global
    rather than project-scoped and carry nothing sensitive, so no project
    membership is required. The write routes are admin-only
    (``@require_administrator``) - types are managed from the
    administrator-only Customisations page. Both are enforced here rather
    than trusted to the caller.

    Registered routes:
        GET    /case_types                         List all case types.
        POST   /case_types                         Create a case type.
        GET    /case_types/<type_id>               Get a single case type.
        PATCH  /case_types/<type_id>               Change name/description.
        DELETE /case_types/<type_id>               Delete a case type.
        POST   /case_types/<type_id>/set_default   Make this the default.

    Args:
        injections: Shared application dependencies.

    Returns:
        A configured Quart Blueprint.
    """
    routes = Blueprint('case_types_routes', __name__)

    handler_list = ListCaseTypesHandler(
        injections.logger, injections.configuration, injections.rest_client)
    handler_get = GetCaseTypeHandler(
        injections.logger, injections.configuration, injections.rest_client)
    handler_create = CreateCaseTypeHandler(
        injections.logger, injections.configuration, injections.rest_client)
    handler_modify = ModifyCaseTypeHandler(
        injections.logger, injections.configuration, injections.rest_client)
    handler_set_default = SetDefaultCaseTypeHandler(
        injections.logger, injections.configuration, injections.rest_client)
    handler_delete = DeleteCaseTypeHandler(
        injections.logger, injections.configuration, injections.rest_client)

    injections.logger.debug(" Case Types WEB routes:")

    injections.logger.debug("=> %s GET  /web/case_types",
                            "List case types".ljust(40))

    @routes.route('/case_types', methods=['GET'])
    @require_session(injections.sessions)
    async def list_case_types_request():
        return await handler_list.list_case_types()

    injections.logger.debug("=> %s POST /web/case_types",
                            "Create case type".ljust(40))

    @routes.route('/case_types', methods=['POST'])
    @require_administrator(injections.sessions)
    async def create_case_type_request():
        return await handler_create.create_case_type()

    injections.logger.debug("=> %s GET  /web/case_types/<int:type_id>",
                            "Get case type".ljust(40))

    @routes.route('/case_types/<int:type_id>', methods=['GET'])
    @require_session(injections.sessions)
    async def get_case_type_request(type_id: int):
        return await handler_get.get_case_type(type_id)

    injections.logger.debug("=> %s PATCH /web/case_types/<int:type_id>",
                            "Modify case type".ljust(40))

    @routes.route('/case_types/<int:type_id>', methods=['PATCH'])
    @require_administrator(injections.sessions)
    async def modify_case_type_request(type_id: int):
        return await handler_modify.modify_case_type(type_id)

    injections.logger.debug(
        "=> %s POST /web/case_types/<int:type_id>/set_default",
        "Set default case type".ljust(40))

    @routes.route('/case_types/<int:type_id>/set_default', methods=['POST'])
    @require_administrator(injections.sessions)
    async def set_default_case_type_request(type_id: int):
        return await handler_set_default.set_default_case_type(type_id)

    injections.logger.debug("=> %s DELETE /web/case_types/<int:type_id>",
                            "Delete case type".ljust(40))

    @routes.route('/case_types/<int:type_id>', methods=['DELETE'])
    @require_administrator(injections.sessions)
    async def delete_case_type_request(type_id: int):
        return await handler_delete.delete_case_type(type_id)

    return routes
