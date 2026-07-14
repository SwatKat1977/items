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
from items.services.items_gateway.routes.web.testcases.get_testcase_handler \
    import GetTestcaseHandler
from items.services.items_gateway.routes.web.testcases.get_testcases_handler \
    import GetTestcasesHandler


def create_testcases_routes(injections: RouteInjections) -> Blueprint:
    handler_get_testcase: GetTestcaseHandler = GetTestcaseHandler(
        injections.logger,
        injections.configuration,
        injections.rest_client)
    handler_get_testcases: GetTestcasesHandler = GetTestcasesHandler(
        injections.logger,
        injections.configuration,
        injections.rest_client)

    routes = Blueprint('testcases_routes', __name__)

    injections.logger.debug(" Testcases WEB routes:")

    injections.logger.debug("=> %s GET /web/<project_id>/testcases",
                            "Get testcases for a project".ljust(40))

    @routes.route('/<int:project_id>/testcases',
                  methods=['GET'])
    async def testcases_details_request(project_id: int):
        return await handler_get_testcases.get_testcases(project_id)

    injections.logger.debug(
        "=> %s GET /web/testcases/<int:case_id>",
        "Get details of a testcase".ljust(40))

    @routes.route('/testcases/<int:case_id>',
                  methods=['GET'])
    async def get_case_request(case_id: int):
        # pylint: disable=unused-variable
        return await handler_get_testcase.get_testcase(case_id)

    return routes
