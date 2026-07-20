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
from .get_project_overview_page_handler import GetProjectOverviewPageHandler


def create_projects_page_handlers(injections: PageHandlerInjections) -> Blueprint:
    """Create the project page handlers.

    This function creates and configures the blueprint containing the
    public project page routes. The blueprint currently provides the
    project overview page for individual projects.

    Args:
        injections: Dependency injection container providing the logger,
            configuration, REST client, and other services required by
            the page handlers.

    Returns:
        Blueprint: A configured Quart blueprint containing the project
        page routes.
    """
    routes = Blueprint('projects_routes', __name__)

    handler_project_overview: GetProjectOverviewPageHandler = \
        GetProjectOverviewPageHandler(injections.logger,
                                      injections.config,
                                      injections.rest_client)

    injections.logger.debug(" Projects Page Handlers:")

    # Index page: '/'
    injections.logger.debug("=> %s GET /<int:project_id>",
                            "Project overview page".ljust(40))

    @routes.route('/<int:project_id>',
                  methods=['GET'])
    async def project_overview_request(project_id: int):
        return await handler_project_overview.project_overview(project_id)

    return routes
