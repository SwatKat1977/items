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
from apis.testcases_api_view import TestCasesApiView
from sqlite_interface import SqliteInterface


def create_blueprint(logger: logging.Logger, db: SqliteInterface) -> Blueprint:
    """
    Creates and returns a Quart Blueprint for the test cases API.

    This function initializes a `TestcasesApiView` instance and registers
    asynchronous routes under `/testcases/` for handling requests.

    Args:
        logger (logging.Logger): The logger instance used for logging API
                                 registration.
        db (SqliteInterface): Database interface instance.

    Returns:
        Blueprint: A Quart Blueprint instance with the registered health status
                   route.
    """
    view = TestCasesApiView(logger, db)

    blueprint = Blueprint('testcases_api', __name__)

    logger.info("Registering Test Cases API:")

    logger.info("=> /testcases/testcase_details [POST]")

    @blueprint.route('/testcases/details', methods=['POST'])
    async def testcase_details():
        return await view.testcase_details()

    logger.info("=> /testcases/case/<case_id> [POST]")

    @blueprint.route('/testcases/get_case/<case_id>', methods=['POST'])
    async def testcase_get_case(case_id: int):
        return await view.testcase_get_case(case_id)

    return blueprint
