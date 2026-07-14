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
from items.services.items_gateway.route_injections import RouteInjections
from items.services.items_gateway.routes.web.testcase_custom_fields.\
    get_all_custom_fields_handler import GetAllCustomFieldsHandler
from items.services.items_gateway.routes.admin.testcase_custom_fields_api_view \
    import ModifyCustomFieldHandler


def create_testcase_custom_fields_routes(injections: RouteInjections) \
        -> Blueprint:
    """Create the Blueprint containing testcase custom field web routes.

    This function creates and configures the routes used to retrieve testcase
    custom field definitions through the web interface. It instantiates the
    required request handlers, registers the available endpoints, and logs the
    registered routes during application startup.

    Registered routes:
        - GET /testcase_custom_fields/:
            Retrieve all available testcase custom field definitions.

    Args:
        injections: Collection of shared application dependencies, including
            the logger, configuration, and REST client used by the route
            handlers.

    Returns:
        Blueprint: A configured Quart Blueprint containing the testcase custom
        field routes.
    """
    routes = Blueprint('testcase_custom_fields_routes', __name__)

    handler_get_all_fields: GetAllCustomFieldsHandler = \
        GetAllCustomFieldsHandler(injections.logger,
                                  injections.configuration,
                                  injections.rest_client)
    handler_modify_custom_field: ModifyCustomFieldHandler = \
        ModifyCustomFieldHandler(injections.logger,
                                 injections.configuration,
                                 injections.rest_client)

    injections.logger.debug(" Testcase Custom Fields WEB routes:")

    injections.logger.debug("=> %s GET /web/testcase_custom_fields",
                            "Get all TC custom fields".ljust(40))

    @routes.route('/testcase_custom_fields/', methods=['GET'])
    async def get_all_custom_fields_request():
        return await handler_get_all_fields.get_all_custom_fields()

    injections.logger.debug("=> %s PUT /web/testcase_custom_fields",
                            "Modify Testcase Custom Fields".ljust(40))

    @routes.route('/testcase_custom_fields/<int:field_id>', methods=['PUT'])
    async def modify_custom_field_request(field_id: int):
        # pylint: disable=no-value-for-parameter
        return await handler_modify_custom_field.modify_custom_field(field_id)

    return routes
