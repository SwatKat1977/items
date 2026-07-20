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
from items.services.items_web_portal.page_handlers.admin.dashboard.admin_overview_page_handler import \
    AdminOverviewPageHandler


def create_admin_dashboard_page_handler(injections: PageHandlerInjections,
                                        prefix: str) -> Blueprint:
    routes = Blueprint('admin_dashboard_pages_routes', __name__)

    injections.logger.debug(" Admin Pages | Dashboard Page Handler:")

    handler_overview: AdminOverviewPageHandler = AdminOverviewPageHandler(
        injections.logger,
        injections.config,
        injections.rest_client,
        injections.metadata)

    # Admin page | Overview: '/overview'
    injections.logger.debug("=> %s GET %s/overview",
                            "Admin overview page".ljust(40),
                            prefix)

    @routes.route('/', methods=['GET'])
    async def admin_page_top_level_request():
        return await handler_overview.overview()

    return routes
