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
from quart import Blueprint
from items.shared.service_state import ServiceState
from items.services.items_cms.cms_configuration import CMSConfiguration
from items.services.items_cms.repositories.testcase_custom_fields_repository import (
    TestcaseCustomFieldsRepository,
)
from items.services.items_cms.services.testcase_custom_fields_service import (
    TestcaseCustomFieldsService,
)
from .add_custom_field_handler import AddCustomFieldHandler
from .get_custom_fields_handler import GetCustomFieldsHandler
from .move_custom_field_handler import MoveCustomFieldHandler
from .update_custom_field_handler import UpdateCustomFieldHandler
from .delete_custom_field_handler import DeleteCustomFieldHandler


def create_testcase_custom_fields_routes(logger: logging.Logger,
                                         service_state: ServiceState,
                                         config: CMSConfiguration) -> Blueprint:
    """Create and return the testcase custom fields API Blueprint.

    Instantiates the repository and service once, wires them into
    individual route handlers, and registers all custom field endpoints
    with a Quart Blueprint.

    Args:
        logger:        Parent logger instance.
        service_state: Shared service operational state.
        config:        CMS service configuration, used to locate the
                       database file.

    Returns:
        A configured Blueprint with all testcase custom field routes registered.
    """
    custom_fields_routes = Blueprint("testcase_custom_fields_routes", __name__)

    repository = TestcaseCustomFieldsRepository(logger, config)
    service = TestcaseCustomFieldsService(logger, service_state, repository)

    add_handler = AddCustomFieldHandler(logger, service)
    get_handler = GetCustomFieldsHandler(logger, service)
    move_handler = MoveCustomFieldHandler(logger, service)
    update_handler = UpdateCustomFieldHandler(logger, service)
    delete_handler = DeleteCustomFieldHandler(logger, service)

    logger.debug("--- Registering Testcase Custom Fields API routes ---")

    logger.debug("=> %s POST /testcase_custom_fields",
                 "Add testcase custom field".ljust(40))

    @custom_fields_routes.route('/testcase_custom_fields', methods=['POST'])
    async def add_testcase_custom_field():
        # pylint: disable=no-value-for-parameter
        return await add_handler.add_custom_field()

    logger.debug("=> %s GET /testcase_custom_fields",
                 "Get testcase custom fields".ljust(40))

    @custom_fields_routes.route('/testcase_custom_fields', methods=['GET'])
    async def get_testcase_custom_fields():
        return await get_handler.get_custom_fields()

    logger.debug("=> %s PATCH /testcase_custom_fields/<field_id>",
                 "Move testcase custom field".ljust(40))

    @custom_fields_routes.route(
        '/testcase_custom_fields/<int:field_id>', methods=['PATCH'])
    async def move_testcase_custom_field(field_id: int):
        # pylint: disable=no-value-for-parameter
        return await move_handler.move_custom_field(field_id)

    logger.debug("=> %s PUT /testcase_custom_fields/<field_id>",
                 "Update testcase custom field".ljust(40))

    @custom_fields_routes.route(
        '/testcase_custom_fields/<int:field_id>', methods=['PUT'])
    async def update_testcase_custom_field(field_id: int):
        return await update_handler.update_custom_field(field_id)

    logger.debug("=> %s DELETE /testcase_custom_fields/<field_id>",
                 "Delete testcase custom field".ljust(40))

    @custom_fields_routes.route(
        '/testcase_custom_fields/<int:field_id>', methods=['DELETE'])
    async def delete_testcase_custom_field(field_id: int):
        return await delete_handler.delete_custom_field(field_id)

    return custom_fields_routes
