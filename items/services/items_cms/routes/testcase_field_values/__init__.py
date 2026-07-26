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
from items.services.items_cms.repositories.testcase_field_values_repository import (
    TestcaseFieldValuesRepository,
)
from items.services.items_cms.services.testcase_field_values_service import (
    TestcaseFieldValuesService,
)
from .get_testcase_field_values_handler import GetTestcaseFieldValuesHandler
from .set_testcase_field_values_handler import SetTestcaseFieldValuesHandler


def create_testcase_field_values_routes(
        logger: logging.Logger,
        service_state: ServiceState,
        config: CMSConfiguration) -> Blueprint:
    """Create and return the testcase field values API Blueprint.

    Instantiates the field values repository and service once, wires them
    into individual route handlers, and registers all field value
    endpoints with a Quart Blueprint.

    Args:
        logger:        Parent logger instance.
        service_state: Shared service operational state.
        config:        CMS service configuration, used to locate the
                       database file.

    Returns:
        A configured Blueprint with all testcase field value routes
        registered.
    """
    field_values_routes = Blueprint("testcase_field_values_routes", __name__)

    repository = TestcaseFieldValuesRepository(logger, config)
    service = TestcaseFieldValuesService(logger, service_state, repository)

    get_handler = GetTestcaseFieldValuesHandler(logger, service)
    set_handler = SetTestcaseFieldValuesHandler(logger, service)

    logger.debug("--- Registering Testcase Field Values API routes ---")

    # Get every applicable custom field and its value for a test case.
    logger.debug("=> %s GET /testcases/<int:case_id>/custom_fields",
                 "Get testcase field values".ljust(40))

    @field_values_routes.route(
        '/testcases/<int:case_id>/custom_fields', methods=['GET'])
    async def get_field_values(case_id: int):
        return await get_handler.get_field_values(case_id)

    # Set one or more custom field values for a test case.
    logger.debug("=> %s PUT /testcases/<int:case_id>/custom_fields",
                 "Set testcase field values".ljust(40))

    @field_values_routes.route(
        '/testcases/<int:case_id>/custom_fields', methods=['PUT'])
    async def set_field_values(case_id: int):
        # pylint: disable=no-value-for-parameter
        return await set_handler.set_field_values(case_id)

    return field_values_routes
