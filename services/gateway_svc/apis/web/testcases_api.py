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
from .testcases_api_view import TestCasesApiView
from sessions import Sessions


def create_blueprint(logger: logging.Logger, sessions: Sessions) -> Blueprint:
    view = TestCasesApiView(logger, sessions)

    blueprint = Blueprint('testcase_api', __name__)

    logger.debug("-------------- Registering Web Testcases routes -----------")

    logger.debug(f"=> {'Get all testcase for projects'.ljust(30)}"
                 "POST /web/<project_id>/testcase/testcase_details")

    @blueprint.route('/<int:project_id>/testcase/testcases_details',
                     methods=['POST'])
    async def testcases_details_request(project_id: int):
        return await view.testcases_details(project_id)

    logger.debug(f"=> {'Get testcase details'.ljust(30)}"
                 "POST /web/<int:project_id>/testcase/get_case/<int:case_id>")

    @blueprint.route('/<int:project_id>/testcase/get_case/<int:case_id>',
                     methods=['POST'])
    async def get_case_request(project_id: int, case_id: int):
        # pylint: disable=unused-variable
        return await view.get_testcase(project_id, case_id)

    return blueprint
