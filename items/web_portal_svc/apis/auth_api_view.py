"""
Copyright 2025 Integrated Test Management Suite Development Team

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
from base_web_view import BaseWebView
from base_view import ApiResponse
from quart import make_response, request, Response
from base_items_exception import BaseItemsException
import page_locations as pages
from threadsafe_configuration import ThreadSafeConfiguration

class AuthApiView(BaseWebView):

    def __init__(self, logger):
        super().__init__(logger)

    async def index_page(self):
        """
        Handler method for home page (e.g. '/').

        parameters:
            api_request - REST API request object

        returns:
            Instance of Quart Response class.
        """

        try:
            if not self._has_auth_cookies() or not self._validate_cookies():
                redirect = self._generate_redirect('login')
                return await make_response(redirect)

        except BaseItemsException as ex:
            self._logger.error('Internal Error: %s', ex)
            return await self._render_page(pages.TEMPLATE_INTERNAL_ERROR_PAGE)

        return await self._render_page(pages.TEMPLATE_LANDING_PAGE)

    async def login_page_get(self):
        """
        GET Handler method for login page.

        returns:
            Instance of Quart Response class.
        """

        try:
            if self._has_auth_cookies() and self._validate_cookies():
                redirect = self._generate_redirect('')
                response = await make_response(redirect)
                return response

        except BaseItemsException as ex:
            self._logger.error('Internal Error: %s', ex)
            return await self._render_page(pages.TEMPLATE_INTERNAL_ERROR_PAGE)

        return await self._render_page(pages.TEMPLATE_LOGIN_PAGE)

    async def login_page_post(self):
        """
        POST Handler method for login page.

        returns:
            Instance of Quart Response class.
        """

        try:
            if self._has_auth_cookies() and self._validate_cookies():
                redirect = self._generate_redirect('')
                response = await make_response(redirect)
                return response

        except BaseItemsException as ex:
            self._logger.error('Internal Error: %s', ex)
            return await self._render_page(pages.TEMPLATE_INTERNAL_ERROR_PAGE)

        form_data = await self._process_post_form_data(await request.form)

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
        base_url: str = ThreadSafeConfiguration().apis_gateway_svc
        url = f"{base_url}handshake/basic_authenticate"

        response: ApiResponse = await self._call_api_post(url, auth_body)

        if response.status_code != HTTPStatus.OK:
            self._logger.critical("Gateway svc request invalid - Reason: %s",
                                  response.exception_msg)
            error_msg = "Internal Error"
            return await self._render_page(pages.TEMPLATE_LOGIN_PAGE,
                                           generate_error_msg=True,
                                           error_msg=error_msg)

        if response.body.get("status") == 1:
            redirect = self._generate_redirect('')
            login_response: Response = await make_response(redirect)
            login_response.set_cookie(self.COOKIE_USER, user_email)
            login_response.set_cookie(self.COOKIE_TOKEN,
                                      response.body.get("token"))
            return login_response

        error_msg = "Invalid username/password"
        return await self._render_page(pages.TEMPLATE_LOGIN_PAGE,
                                       generate_error_msg = True,
                                       error_msg=error_msg)
