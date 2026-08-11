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
from http import HTTPStatus
from quart import make_response, request, Response
from weaver_framework.microservice.api_response import ApiResponse
from items.services.items_web_portal.portal_page_handler import (
    PortalPageHandler)


class LogoutPageHandler(PortalPageHandler):
    """Handles user logout requests.

    Terminates the current authenticated session and returns the visitor to
    the login page. Deliberately not wrapped in ``require_session`` - logout
    must also work when the session cookies are missing or already stale
    (e.g. a second tab, or a link followed after the session expired), and
    the outcome is the same either way: end up logged out.
    """

    async def logout(self):
        """Handles a logout request.

        If authentication cookies are present, the session is invalidated on
        the gateway first. That call is best-effort: the local cookies are
        cleared and the user is sent to the login page regardless of whether
        it succeeds, since a failed server-side invalidation should not
        strand the user in a state where they can't leave the page they
        asked to leave. A session left behind on the gateway this way is
        harmless - it expires on its own like any other stale session.

        Returns:
            A Quart response that clears the authentication cookies and
            redirects to the login page.
        """
        email_address = request.cookies.get(self.COOKIE_USER)
        token = request.cookies.get(self.COOKIE_TOKEN)

        if email_address and token:
            url = f"{self._config.apis_gateway_svc}web/sessions"
            response: ApiResponse = await self._rest_client.delete(
                url,
                json_data={"email_address": email_address, "token": token},
                timeout=5)

            if response.status_code != HTTPStatus.OK:
                self._logger.warning(
                    "Gateway svc logout request for '%s' failed with "
                    "status %s - clearing local session anyway",
                    email_address, response.status_code)

        redirect = self._generate_redirect('login')
        logout_response: Response = await make_response(redirect)
        logout_response.delete_cookie(self.COOKIE_USER)
        logout_response.delete_cookie(self.COOKIE_TOKEN)
        return logout_response
