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
from items.services.items_web_portal.page_handlers.auth.index_page_handler \
    import IndexPageHandler
from items.services.items_web_portal.page_handlers.auth.login_get_page_handler \
    import LoginGetPageHandler
from items.services.items_web_portal.page_handlers.auth.login_post_page_handler \
    import LoginPostPageHandler
from items.services.items_web_portal.page_handlers.auth.logout_page_handler \
    import LogoutPageHandler


def create_auth_page_handlers(injections: PageHandlerInjections) -> Blueprint:
    """Creates the authentication-related page handlers and routes.

    This function instantiates the page handler objects responsible for
    authentication and portal navigation, registers their associated HTTP
    routes on a Quart blueprint, and returns the configured blueprint for
    registration with the application.

    The following routes are registered:

    - ``GET /`` – Displays the portal dashboard.
    - ``GET /login`` – Displays the login page.
    - ``POST /login`` – Authenticates a user.
    - ``GET /logout`` – Logs the current user out.

    Args:
        injections: Collection of shared application dependencies required by
            the page handlers, including the logger, configuration, REST
            client, and metadata settings.

    Returns:
        A configured Quart ``Blueprint`` containing the authentication-related
        routes.
    """
    handler_index: IndexPageHandler = IndexPageHandler(
        injections.logger,
        injections.config,
        injections.rest_client,
        injections.metadata)
    handler_login_get: LoginGetPageHandler = LoginGetPageHandler(
        injections.logger,
        injections.config,
        injections.rest_client)
    handler_login_post: LoginPostPageHandler = LoginPostPageHandler(
        injections.logger,
        injections.config,
        injections.rest_client)
    handler_logout: LogoutPageHandler = LogoutPageHandler(
        injections.logger,
        injections.config,
        injections.rest_client)

    routes = Blueprint('auth_routes', __name__)

    injections.logger.debug(" Auth Page Handlers:")

    # Index page: '/'
    injections.logger.debug("=> %s GET /",
                            "Home / index page".ljust(40))

    @routes.route('/', methods=['GET'])
    async def index_page_request():
        return await handler_index.index()

    # Login page (authentication): '/login'
    injections.logger.debug("=> %s POST /login",
                            "Login (authentication)".ljust(40))

    @routes.route('/login', methods=['POST'])
    async def login_page_request_post():
        return await handler_login_post.login_post()

    # Login page (read): '/login'
    injections.logger.debug("=> %s GET /login",
                            "Login (read page)".ljust(40))

    @routes.route('/login', methods=['GET'])
    async def login_page_request_get():
        return await handler_login_get.login_get()

    # Logout page: '/logout'
    injections.logger.debug("=> %s GET /logout",
                            "Authentication logout".ljust(40))

    @routes.route('/logout', methods=['GET'])
    async def logout_page_request():
        return await handler_logout.logout()

    return routes
