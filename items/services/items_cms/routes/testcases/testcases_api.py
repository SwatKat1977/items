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
from items_common.service_state import ServiceState
from .testcases_api_view import TestCasesApiView


def create_testcases_routes(logger: logging.Logger,
                            _service_state: ServiceState) -> Blueprint:

    # view = TestCasesApiView(logger, service_state)
    testcases_routes = Blueprint("testcases_routes", __name__)

    logger.debug("Registering Testcases API routes:")

    logger.debug("=> %s GET /testcases?project_id=<id>",
                 "Get testcases for a project".ljust(40))

    @testcases_routes.route('/testcases', methods=['GET'])
    async def testcase_details():
        # pylint: disable=no-value-for-parameter
        return None
        # COMMENT OUT UNTIL UPDATED: return await view.testcase_details()

    logger.debug("=> %s GET /testcases/<int:case_id>",
                 "Get testcase details".ljust(40))

    @testcases_routes.route('/testcases/<int:case_id>', methods=['GET'])
    async def testcase_get_case(case_id: int):
        # pylint: disable=no-value-for-parameter
        return None
        # COMMENT OUT UNTIL UPDATED: return await view.testcase_get_case(case_id)

    return testcases_routes
