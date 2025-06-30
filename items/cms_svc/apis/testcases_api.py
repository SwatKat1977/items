"""
Copyright 2025 Integrated Test Management Suite Development Team

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
from state_object import StateObject
from .testcases_api_view import TestCasesApiView


def create_blueprint(logger: logging.Logger,
                     state_object: StateObject) -> Blueprint:
    """
    Creates and returns a Quart Blueprint for the test cases API.

    This function initializes a `TestcasesApiView` instance and registers
    asynchronous routes under `/testcases/` for handling requests.

    Args:
        logger (logging.Logger): The logger instance used for logging API
                                 registration.
        state_object (StateObject): StateObject instance for database.

    Returns:
        Blueprint: A Quart Blueprint instance with the registered health status
                   route.
    """
    view = TestCasesApiView(logger, state_object)

    blueprint = Blueprint('testcases_api', __name__)

    logger.debug("Registering test cases routes:")

    logger.debug("=> /testcases/testcase_details [POST]")

    @blueprint.route('/details', methods=['POST'])
    async def testcase_details():
        # pylint: disable=no-value-for-parameter
        return await view.testcase_details()

    logger.debug("=> /case/<case_id> [POST]")

    @blueprint.route('/get_case/<case_id>', methods=['POST'])
    async def testcase_get_case(case_id: int):
        # pylint: disable=no-value-for-parameter
        return await view.testcase_get_case(case_id)

    return blueprint
