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
from quart import make_response
from items.shared.base_items_exception import BaseItemsException
import items.services.items_web_portal.page_locations as pages
from items.services.items_web_portal.portal_page_handler import (
    PortalPageHandler)


class LoginGetPageHandler(PortalPageHandler):
    """Handles HTTP GET requests for the login page.

    This handler determines whether the user already has a valid authenticated
    session. If valid authentication cookies are present, the user is redirected
    to the portal home page. Otherwise, the login page is rendered.

    Attributes:
        _logger: Logger used for diagnostic and error messages.
        _config: Application configuration.
        _rest_client: REST client used for backend communication.
    """

    async def login_get(self):
        """Handles a GET request for the login page.

        If the user has authentication cookies and they are successfully
        validated, the user is redirected to the application's default page.
        Otherwise, the login page is rendered.

        If an internal error occurs while validating the session, an error is
        logged and the internal error page is returned.

        Returns:
            A Quart response containing either:
                - A redirect to the authenticated landing page.
                - The login page.
                - The internal error page if an exception occurs.
        """
        try:
            if await self._has_auth_cookies():
                # _validate_cookies returns (is_valid, is_administrator). The
                # tuple must be unpacked - testing it directly is always true,
                # because any non-empty tuple is truthy, which would redirect
                # users with stale cookies to a page that bounces them
                # straight back here.
                is_valid, _ = await self._validate_cookies()
                if is_valid:
                    redirect = self._generate_redirect('')
                    response = await make_response(redirect)
                    return response

        except BaseItemsException as ex:
            self._logger.error('Internal Error: %s', ex)
            return await self._render_page(pages.TEMPLATE_INTERNAL_ERROR_PAGE)

        return await self._render_page(pages.TEMPLATE_LOGIN_PAGE)
