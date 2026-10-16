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
from items.services.items_gateway.auth_decorators import (
    require_project_permission)
from items.services.items_gateway.route_injections import RouteInjections
from items.services.items_gateway.routes.web.testcases.create_testcase_handler \
    import CreateTestcaseHandler
from items.services.items_gateway.routes.web.testcases.delete_testcase_handler \
    import DeleteTestcaseHandler
from items.services.items_gateway.routes.web.testcases.get_testcase_handler \
    import GetTestcaseHandler
from items.services.items_gateway.routes.web.testcases.get_testcases_handler \
    import GetTestcasesHandler
from items.services.items_gateway.routes.web.testcases.modify_testcase_handler \
    import ModifyTestcaseHandler
from items.shared.permission_action import PermissionAction
from items.shared.permission_area import PermissionArea


def create_testcases_routes(injections: RouteInjections) -> Blueprint:
    """Create the Blueprint containing testcase web routes.

    This function creates and configures the routes used to read and write
    testcases through the web interface. It instantiates the required request
    handlers, registers the available endpoints, and logs the registered routes
    during application startup.

    Every route requires a valid session and the **Test Cases** permission
    that matches what it does, checked with the Identity service on every
    request (``@require_project_permission``, see section 9.5 of
    ``design_docs/user_roles_design.md``): Read to browse, Add/Modify to
    create or edit, Delete to delete. A member whose role does not grant it
    gets a 403, and so does a user who is not a member at all (they have an
    empty grid). Administrators are not special-cased here: Identity grants
    them everything. Because nothing is cached, a change to a role or
    membership applies on the very next request.

    The checks fail closed: if Identity cannot be reached or answers
    unexpectedly the route returns a 500, never access.

    The ``project_id`` of a route that has no project in its path
    (``GET``, ``PATCH`` and ``DELETE /web/testcases/<id>``) is a query
    parameter that the permission is checked against before ever calling CMS.
    That's safe despite being client-supplied: CMS independently verifies the
    testcase actually belongs to the stated project and 404s otherwise, so a
    caller can't use a project they hold the permission on as a lie to reach a
    testcase in one they don't. Unlike the old membership check, the
    decorator never skips: a missing or malformed ``project_id`` is a 400
    before anything else happens.

    Registered routes (permission in brackets):
        - GET /<project_id>/testcases [Read]:
            Retrieve all testcases belonging to the specified project.
        - POST /<project_id>/testcases [Add/Modify]:
            Create a testcase in the specified project.
        - GET /testcases/<case_id>?project_id= [Read]:
            Retrieve the details of a specific testcase.
        - PATCH /testcases/<case_id>?project_id= [Add/Modify]:
            Update a testcase's name, description and optionally its type.
        - DELETE /testcases/<case_id>?project_id= [Delete]:
            Delete a testcase.

    Args:
        injections: Collection of shared application dependencies, including
            the logger, configuration, and REST client used by the route
            handlers.

    Returns:
        Blueprint: A configured Quart Blueprint containing the testcase routes.
    """
    handler_get_testcase: GetTestcaseHandler = GetTestcaseHandler(
        injections.logger,
        injections.configuration,
        injections.rest_client)
    handler_get_testcases: GetTestcasesHandler = GetTestcasesHandler(
        injections.logger,
        injections.configuration,
        injections.rest_client)

    handler_create_testcase: CreateTestcaseHandler = CreateTestcaseHandler(
        injections.logger,
        injections.configuration,
        injections.rest_client)
    handler_modify_testcase: ModifyTestcaseHandler = ModifyTestcaseHandler(
        injections.logger,
        injections.configuration,
        injections.rest_client)
    handler_delete_testcase: DeleteTestcaseHandler = DeleteTestcaseHandler(
        injections.logger,
        injections.configuration,
        injections.rest_client)

    routes = Blueprint('testcases_routes', __name__)

    injections.logger.debug(" Testcases WEB routes:")

    injections.logger.debug("=> %s GET /web/<project_id>/testcases",
                            "Get testcases for a project".ljust(40))

    @routes.route('/<int:project_id>/testcases',
                  methods=['GET'])
    @require_project_permission(
        injections, PermissionArea.TEST_CASES,
        PermissionAction.READ)
    async def testcases_details_request(project_id: int):
        return await handler_get_testcases.get_testcases(project_id)

    injections.logger.debug(
        "=> %s GET /web/testcases/<int:case_id>",
        "Get details of a testcase".ljust(40))

    @routes.route('/testcases/<int:case_id>',
                  methods=['GET'])
    @require_project_permission(
        injections, PermissionArea.TEST_CASES,
        PermissionAction.READ)
    async def get_case_request(case_id: int):
        # pylint: disable=unused-variable
        return await handler_get_testcase.get_testcase(case_id)

    injections.logger.debug("=> %s POST /web/<project_id>/testcases",
                            "Create a testcase".ljust(40))

    @routes.route('/<int:project_id>/testcases',
                  methods=['POST'])
    @require_project_permission(
        injections, PermissionArea.TEST_CASES,
        PermissionAction.ADD_MODIFY)
    async def create_testcase_request(project_id: int):
        return await handler_create_testcase.create_testcase(project_id)

    injections.logger.debug(
        "=> %s PATCH /web/testcases/<int:case_id>",
        "Modify a testcase".ljust(40))

    @routes.route('/testcases/<int:case_id>',
                  methods=['PATCH'])
    @require_project_permission(
        injections, PermissionArea.TEST_CASES,
        PermissionAction.ADD_MODIFY)
    async def modify_testcase_request(case_id: int):
        return await handler_modify_testcase.modify_testcase(case_id)

    injections.logger.debug(
        "=> %s DELETE /web/testcases/<int:case_id>",
        "Delete a testcase".ljust(40))

    @routes.route('/testcases/<int:case_id>',
                  methods=['DELETE'])
    @require_project_permission(
        injections, PermissionArea.TEST_CASES,
        PermissionAction.DELETE)
    async def delete_testcase_request(case_id: int):
        return await handler_delete_testcase.delete_testcase(case_id)

    return routes
