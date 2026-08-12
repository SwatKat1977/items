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
from items.services.items_gateway.auth_decorators import require_administrator
from items.services.items_gateway.route_injections import RouteInjections
from items.services.items_gateway.routes.web.testcase_custom_fields.\
    add_custom_field_handler import AddCustomFieldHandler
from items.services.items_gateway.routes.web.testcase_custom_fields.\
    delete_custom_field_handler import DeleteCustomFieldHandler
from items.services.items_gateway.routes.web.testcase_custom_fields.\
    get_all_custom_fields_handler import GetAllCustomFieldsHandler
from items.services.items_gateway.routes.web.testcase_custom_fields.\
    get_custom_field_handler import GetCustomFieldHandler
from items.services.items_gateway.routes.web.testcase_custom_fields.\
    modify_custom_field_handler import ModifyCustomFieldHandler
from items.services.items_gateway.routes.web.testcase_custom_fields.\
    move_custom_field_handler import MoveCustomFieldHandler


def create_testcase_custom_fields_routes(injections: RouteInjections) \
        -> Blueprint:
    """Create the Blueprint containing testcase custom field web routes.

    This function creates and configures the routes used to retrieve testcase
    custom field definitions through the web interface. It instantiates the
    required request handlers, registers the available endpoints, and logs the
    registered routes during application startup.

    All routes are admin-only (the Customisations page they back is entirely
    ``@require_administrator`` in the web portal, including its read view),
    enforced here via ``@require_administrator`` rather than trusted to the
    caller.

    Registered routes:
        - GET /testcase_custom_fields/:
            Retrieve all available testcase custom field definitions.
        - GET /testcase_custom_fields/<field_id>:
            Retrieve a single testcase custom field definition.

    Args:
        injections: Collection of shared application dependencies, including
            the logger, configuration, and REST client used by the route
            handlers.

    Returns:
        Blueprint: A configured Quart Blueprint containing the testcase custom
        field routes.
    """
    routes = Blueprint('testcase_custom_fields_routes', __name__)


    handler_add_custom_field: AddCustomFieldHandler = AddCustomFieldHandler(
                                  injections.logger,
                                  injections.configuration,
                                  injections.rest_client)
    handler_delete_custom_field: DeleteCustomFieldHandler = DeleteCustomFieldHandler(
                                  injections.logger,
                                  injections.configuration,
                                  injections.rest_client)
    handler_get_all_fields: GetAllCustomFieldsHandler = \
        GetAllCustomFieldsHandler(injections.logger,
                                  injections.configuration,
                                  injections.rest_client)
    handler_get_custom_field: GetCustomFieldHandler = GetCustomFieldHandler(
                                  injections.logger,
                                  injections.configuration,
                                  injections.rest_client)
    handler_modify_custom_field: ModifyCustomFieldHandler = \
        ModifyCustomFieldHandler(injections.logger,
                                 injections.configuration,
                                 injections.rest_client)
    handler_move_custom_field: MoveCustomFieldHandler = MoveCustomFieldHandler(
        injections.logger,
        injections.configuration,
        injections.rest_client)

    injections.logger.debug(" Testcase Custom Fields WEB routes:")

    injections.logger.debug("=> %s GET /web/testcase_custom_fields",
                            "Get all TC custom fields".ljust(40))

    @routes.route('/testcase_custom_fields/', methods=['GET'])
    @require_administrator(injections.sessions)
    async def get_all_custom_fields_request():
        return await handler_get_all_fields.get_all_custom_fields()

    injections.logger.debug(
        "=> %s GET /web/testcase_custom_fields/<int:field_id>",
        "Get single TC custom field".ljust(40))

    @routes.route('/testcase_custom_fields/<int:field_id>', methods=['GET'])
    @require_administrator(injections.sessions)
    async def get_custom_field_request(field_id: int):
        return await handler_get_custom_field.get_custom_field(field_id)

    injections.logger.debug("=> %s PUT /web/testcase_custom_fields",
                            "Modify Testcase Custom Fields".ljust(40))

    @routes.route('/testcase_custom_fields/<int:field_id>', methods=['PUT'])
    @require_administrator(injections.sessions)
    async def modify_custom_field_request(field_id: int):
        # pylint: disable=no-value-for-parameter
        return await handler_modify_custom_field.modify_custom_field(field_id)

    injections.logger.debug(
        "=> %s PATCH /web/testcase_custom_fields/<int:field_id>",
        "Move Testcase Custom Fields Position".ljust(40))

    @routes.route('/testcase_custom_fields/<int:field_id>', methods=['PATCH'])
    @require_administrator(injections.sessions)
    async def move_custom_field_request(field_id: int):
        # pylint: disable=no-value-for-parameter
        return await handler_move_custom_field.move_custom_field(field_id)

    injections.logger.debug("=> %s POST /web/testcase_custom_fields",
                            "Add Testcase Custom Field".ljust(40))

    @routes.route('/testcase_custom_fields/', methods=['POST'])
    @require_administrator(injections.sessions)
    async def add_custom_field_request():
        # pylint: disable=no-value-for-parameter
        return await handler_add_custom_field.add_custom_field()

    @routes.route('/testcase_custom_fields/<int:field_id>', methods=['DELETE'])
    @require_administrator(injections.sessions)
    async def delete_custom_field_request(field_id: int):
        # pylint: disable=no-value-for-parameter
        return await handler_delete_custom_field.delete_custom_field(field_id)

    return routes
