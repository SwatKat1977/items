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
from items.services.items_web_portal.page_handler_injections import (
    PageHandlerInjections)
from items.services.items_web_portal.page_handlers.testcases.get_project_testcases_page_handler import \
    GetProjectTestcasesPageHandler


def create_testcases_page_handlers(injections: PageHandlerInjections) \
        -> Blueprint:
    routes = Blueprint('testcases_routes', __name__)

    injections.logger.debug(" Testcases Page Handlers:")

    handler_get_testcase: GetProjectTestcasesPageHandler = \
        GetProjectTestcasesPageHandler(injections.logger,
                                       injections.config,
                                       injections.rest_client,
                                       injections.metadata)

    injections.logger.debug("=> %s GET /<project_id>/testcases",
                            "Get testcases for a project".ljust(40))

    @routes.route('/<project_id>/testcases', methods=['GET'])
    async def test_definitions_page_request(project_id: int):
        return await handler_get_testcase.test_cases(project_id)

    return routes
