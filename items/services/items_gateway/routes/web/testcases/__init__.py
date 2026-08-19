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
from items.services.items_gateway.auth_decorators import require_project_member
from items.services.items_gateway.route_injections import RouteInjections
from items.services.items_gateway.routes.web.testcases.get_testcase_handler \
    import GetTestcaseHandler
from items.services.items_gateway.routes.web.testcases.get_testcases_handler \
    import GetTestcasesHandler


def create_testcases_routes(injections: RouteInjections) -> Blueprint:
    """Create the Blueprint containing testcase web routes.

    This function creates and configures the routes used to retrieve testcase
    information through the web interface. It instantiates the required request
    handlers, registers the available endpoints, and logs the registered routes
    during application startup.

    Both routes require a valid session and membership of the project the
    testcase(s) belong to (``@require_project_member``) - any authenticated
    member of that project can browse its testcases, not just admins, who
    bypass the membership check entirely and see every project's testcases.

    ``GET /web/testcases/<id>`` checks membership against its
    ``project_id`` query parameter before ever calling CMS. That's safe
    despite being client-supplied: CMS independently verifies the testcase
    actually belongs to the stated project and 404s otherwise (see
    ``GetTestcaseHandler``), so a caller can't use a project they belong to
    as a lie to reach a testcase in one they don't.

    Registered routes:
        - GET /<project_id>/testcases:
            Retrieve all testcases belonging to the specified project.
        - GET /testcases/<case_id>:
            Retrieve the details of a specific testcase.

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

    routes = Blueprint('testcases_routes', __name__)

    injections.logger.debug(" Testcases WEB routes:")

    injections.logger.debug("=> %s GET /web/<project_id>/testcases",
                            "Get testcases for a project".ljust(40))

    @routes.route('/<int:project_id>/testcases',
                  methods=['GET'])
    @require_project_member(injections.sessions)
    async def testcases_details_request(project_id: int):
        return await handler_get_testcases.get_testcases(project_id)

    injections.logger.debug(
        "=> %s GET /web/testcases/<int:case_id>",
        "Get details of a testcase".ljust(40))

    @routes.route('/testcases/<int:case_id>',
                  methods=['GET'])
    @require_project_member(injections.sessions)
    async def get_case_request(case_id: int):
        # pylint: disable=unused-variable
        return await handler_get_testcase.get_testcase(case_id)

    return routes
