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
from items.shared.base_items_exception import BaseItemsException
import items.services.items_web_portal.page_locations as pages
from items.services.items_web_portal.portal_page_handler import (
    PortalPageHandler)


class LoginPostPageHandler(PortalPageHandler):
    """Handles HTTP POST requests for user login.

    This handler processes login form submissions, authenticates the supplied
    credentials with the gateway service, and establishes an authenticated
    session by setting the appropriate cookies. If authentication fails or an
    error occurs, the login page is re-rendered with an appropriate error
    message.
    """

    async def login_post(self):
        """Handles a POST request for user authentication.

        The handler performs the following steps:

        - Verifies whether the user already has a valid authenticated session.
        - Reads and validates the submitted login form.
        - Sends the credentials to the gateway authentication service.
        - Creates an authenticated session by setting login cookies when
          authentication succeeds.
        - Re-renders the login page with an error message if authentication
          fails or an internal error occurs.

        Returns:
            A Quart response containing either:

            - A redirect to the authenticated landing page.
            - The login page with validation or authentication errors.
            - The internal error page if an unexpected exception occurs.
        """
        # pylint: disable=too-many-return-statements
        try:
            if await self._has_auth_cookies() and await self._validate_cookies():
                redirect = self._generate_redirect('')
                response: Response = await make_response(redirect)
                return response

        except BaseItemsException as ex:
            self._logger.error('Internal Error: %s', ex)
            return await self._render_page(pages.TEMPLATE_INTERNAL_ERROR_PAGE)

        form_data = dict(await request.form)

        user_email = form_data.get('user_email')
        password = form_data.get('password')

        if not user_email or not password:
            error_msg = "Invalid username/password"
            return await self._render_page(pages.TEMPLATE_LOGIN_PAGE,
                                           generate_error_msg=True,
                                           error_msg=error_msg)

        auth_body: dict = {
                "email_address": user_email,
                "password": password
        }
        base_url: str = self._config.apis_gateway_svc

        response: ApiResponse = await self._rest_client.post(
            url,
            json_data=auth_body)
        print("Response body        : ", response.body)
        print("Response status code : ", response.status_code)
        print("Response exception   : ", response.exception_msg)

        if response.status_code == HTTPStatus.UNAUTHORIZED:
            error_msg = "Invalid username/password"
            return await self._render_page(pages.TEMPLATE_LOGIN_PAGE,
                                           generate_error_msg=True,
                                           error_msg=error_msg)

        if response.status_code != HTTPStatus.OK:
            reason = response.exception_msg or response.body or \
                HTTPStatus(response.status_code).phrase
            self._logger.critical(
                "Gateway svc request invalid - Status: %s Reason: %s",
                response.status_code, reason)
            error_msg = "Internal Error"
            return await self._render_page(pages.TEMPLATE_LOGIN_PAGE,
                                           generate_error_msg=True,
                                           error_msg=error_msg)

        if response.body.get("status") == 1:
            redirect = await self._generate_redirect('')
            login_response: Response = await make_response(redirect)
            login_response.set_cookie(self.COOKIE_USER, user_email)
            login_response.set_cookie(self.COOKIE_TOKEN,
                                      response.body.get("token"))
            return login_response

        error_msg = "Invalid username/password"
        return await self._render_page(pages.TEMPLATE_LOGIN_PAGE,
                                       generate_error_msg = True,
                                       error_msg=error_msg)
