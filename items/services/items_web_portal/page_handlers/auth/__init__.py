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


def create_auth_page_handlers(injections: PageHandlerInjections) -> Blueprint:
    # view = AuthApiView(logger, metadata)

    routes = Blueprint('auth_routes', __name__)

    injections.logger.debug(" Auth Page Handlers:")

    # Index page: '/'
    injections.logger.debug("=> %s GET /",
                            "Home / index page".ljust(40))

    @routes.route('/', methods=['GET'])
    async def index_page_request():
        return None
        return await view.index_page()

    # Login page (authentication): '/login'
    injections.logger.debug("=> %s POST /login",
                            "Login (authentication)".ljust(40))

    @routes.route('/login', methods=['POST'])
    async def login_page_request_post():
        return None
        return await view.login_page_post()

    # Login page (read): '/login'
    injections.logger.debug("=> %s GET /login",
                            "Login (read page)".ljust(40))

    @routes.route('/login', methods=['GET'])
    async def login_page_request_get():
        return None
        return await view.login_page_get()

    # Logout page: '/logout'
    injections.logger.debug("=> %s GET /logout",
                            "Authentication logout".ljust(40))

    @routes.route('/logout', methods=['GET'])
    async def logout_page_request():
        return None
        return await view.logout_page()

    return routes
