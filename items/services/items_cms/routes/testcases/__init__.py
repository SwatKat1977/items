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
from items.services.items_cms.repositories.testcase_repository import TestcaseRepository
from items.services.items_cms.services.testcase_service import TestcaseService
from .list_testcases_handler import ListTestcasesHandler
from .get_testcase_handler import GetTestcaseHandler


def create_testcases_routes(logger: logging.Logger,
                            service_state: ServiceState,
                            config: CMSConfiguration) -> Blueprint:
    """Create and return the testcases API Blueprint.

    Instantiates the testcase repository and service once, wires them
    into individual route handlers, and registers all testcase endpoints
    with a Quart Blueprint.

    Args:
        logger:        Parent logger instance.
        service_state: Shared service operational state.
        config:        CMS service configuration, used to locate the
                       database file.

    Returns:
        A configured Blueprint with all testcase routes registered.
    """
    testcases_routes = Blueprint("testcases_routes", __name__)

    repository = TestcaseRepository(logger, config)
    service = TestcaseService(logger, service_state, repository)

    list_handler = ListTestcasesHandler(logger, service)
    get_handler = GetTestcaseHandler(logger, service)

    logger.debug("--- Registering Testcases API routes ---")

    # List test cases and folder hierarchy for a project.
    logger.debug("=> %s GET /testcases?project_id=<id>",
                 "List testcases for project".ljust(40))

    @testcases_routes.route('/testcases', methods=['GET'])
    async def list_testcases():
        return await list_handler.list_testcases()

    # Get details of a specific test case.
    logger.debug("=> %s GET /testcases/<int:case_id>",
                 "Get testcase details".ljust(40))

    @testcases_routes.route('/testcases/<int:case_id>', methods=['GET'])
    async def get_testcase(case_id: int):
        return await get_handler.get_testcase(case_id)

    return testcases_routes
