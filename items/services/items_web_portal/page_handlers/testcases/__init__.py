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
from items.services.items_web_portal.page_handlers.testcases.\
    get_project_testcases_page_handler import GetProjectTestcasesPageHandler
from items.services.items_web_portal.page_handlers.testcases.\
    testcase_form_page_handler import TestcaseFormPageHandler


def create_testcases_page_handlers(injections: PageHandlerInjections) \
        -> Blueprint:
    """Creates the blueprint containing project test case page routes.

    Registers all HTTP routes responsible for displaying and interacting
    with the test cases page for a project. The handlers are constructed
    using the supplied dependency injection container.

    Args:
        injections (PageHandlerInjections):
            Container providing the shared dependencies required by the
            page handlers, including the logger, configuration, REST
            client, and metadata settings.

    Returns:
        Blueprint:
            The configured Quart blueprint containing the test case page
            routes.
    """
    routes = Blueprint('testcases_routes', __name__)

    injections.logger.debug(" Testcases Page Handlers:")

    handler_get_testcase = GetProjectTestcasesPageHandler(
        injections.logger,
        injections.config,
        injections.rest_client,
        injections.metadata)

    handler_form = TestcaseFormPageHandler(
        injections.logger,
        injections.config,
        injections.rest_client,
        injections.metadata)

    injections.logger.debug("=> %s GET /<project_id>/testcases",
                            "Get testcases for a project".ljust(40))

    @routes.route('/<project_id>/testcases', methods=['GET'])
    async def test_definitions_page_request(project_id: int):
        return await handler_get_testcase.test_cases(project_id)

    injections.logger.debug("=> %s POST /<project_id>/folders/add",
                            "Add section".ljust(40))

    @routes.route('/<int:project_id>/folders/add', methods=['POST'])
    async def add_section_request(project_id: int):
        return await handler_get_testcase.add_section(project_id)

    injections.logger.debug("=> %s POST /<project_id>/folders/<id>/rename",
                            "Rename section".ljust(40))

    @routes.route('/<int:project_id>/folders/<int:folder_id>/rename',
                  methods=['POST'])
    async def rename_section_request(project_id: int, folder_id: int):
        return await handler_get_testcase.rename_section(
            project_id, folder_id)

    injections.logger.debug("=> %s POST /<project_id>/folders/<id>/delete",
                            "Delete section".ljust(40))

    @routes.route('/<int:project_id>/folders/<int:folder_id>/delete',
                  methods=['POST'])
    async def delete_section_request(project_id: int, folder_id: int):
        return await handler_get_testcase.delete_section(
            project_id, folder_id)

    injections.logger.debug("=> %s POST /<project_id>/testcases/<id>/delete",
                            "Delete test case".ljust(40))

    @routes.route('/<int:project_id>/testcases/<int:case_id>/delete',
                  methods=['POST'])
    async def delete_testcase_request(project_id: int, case_id: int):
        return await handler_get_testcase.delete_test_case(
            project_id, case_id)

    injections.logger.debug("=> %s GET /<project_id>/testcases/<id>",
                            "View test case page".ljust(40))

    @routes.route('/<int:project_id>/testcases/<int:case_id>',
                  methods=['GET'])
    async def view_testcase_page_request(project_id: int, case_id: int):
        return await handler_form.view_page(project_id, case_id)

    injections.logger.debug("=> %s GET /<project_id>/testcases/add",
                            "Add test case page (read)".ljust(40))

    @routes.route('/<int:project_id>/testcases/add', methods=['GET'])
    async def add_testcase_page_request(project_id: int):
        return await handler_form.add_form(project_id)

    injections.logger.debug("=> %s POST /<project_id>/testcases/add",
                            "Add test case (submit)".ljust(40))

    @routes.route('/<int:project_id>/testcases/add', methods=['POST'])
    async def add_testcase_submit_request(project_id: int):
        return await handler_form.add_submit(project_id)

    injections.logger.debug(
        "=> %s GET /<project_id>/testcases/<id>/edit",
        "Edit test case page (read)".ljust(40))

    @routes.route('/<int:project_id>/testcases/<int:case_id>/edit',
                  methods=['GET'])
    async def edit_testcase_page_request(project_id: int, case_id: int):
        return await handler_form.edit_form(project_id, case_id)

    injections.logger.debug(
        "=> %s POST /<project_id>/testcases/<id>/edit",
        "Edit test case (submit)".ljust(40))

    @routes.route('/<int:project_id>/testcases/<int:case_id>/edit',
                  methods=['POST'])
    async def edit_testcase_submit_request(project_id: int, case_id: int):
        return await handler_form.edit_submit(project_id, case_id)

    return routes
