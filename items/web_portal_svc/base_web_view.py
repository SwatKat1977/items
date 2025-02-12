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
import json
import typing
import jinja2
import jsonschema
import requests
from quart import request, render_template
from base_view import BaseView
from threadsafe_configuration import ThreadSafeConfiguration as Configuration
from base_items_exception import BaseItemsException
from interfaces.gateway.handshake import SCHEMA_IS_VALID_TOKEN_RESPONSE
import page_locations as pages


class BaseWebView(BaseView):
    """ Base class for views that serve web pages """
    # pylint: disable=too-few-public-methods

    COOKIE_TOKEN = "items_token"
    COOKIE_USER = "items_user"

    REDIRECT_URL = "<meta http-equiv=\"Refresh\" content=\"0; url='{0}\"/>"

    def __init__(self, logger):
        self._logger = logger.getChild(__name__)

    def _generate_redirect(self, redirect_url) -> str:
        new_url = f"{request.url_root}{redirect_url}"
        return self.REDIRECT_URL.format(new_url)

    def _has_auth_cookies(self) -> bool:
        retrieved_token = request.cookies.get(self.COOKIE_TOKEN)
        retrieved_username = request.cookies.get(self.COOKIE_USER)
        return retrieved_token is not None and retrieved_username is not None

    def _validate_cookies(self) -> bool:

        token = request.cookies.get(self.COOKIE_TOKEN)
        username = request.cookies.get(self.COOKIE_USER)

        url = f"{Configuration().apis_gateway_svc}/handshake/is_token_valid"

        request_body: dict = {
            "email_address": username,
            "token": token
        }

        try:
            response = requests.post(url, json=request_body, timeout=1)

        except requests.exceptions.ConnectionError as ex:
            raise BaseItemsException('Connection to gateway api timed out')\
                from ex

        if response is None:
            raise BaseItemsException(
                "Missing/invalid JSON body for gateway svc is_token_valid")

        try:
            json_data = json.loads(response.text)

        except (TypeError, json.JSONDecodeError) as ex:
            raise BaseItemsException(
                "Invalid JSON body type for gateway svc is_token_valid")\
                from ex

        try:
            jsonschema.validate(instance=json_data,
                                schema=SCHEMA_IS_VALID_TOKEN_RESPONSE)

        except jsonschema.exceptions.ValidationError as ex:
            raise BaseItemsException(
                "Schema for accounts service health check invalid!") from ex

        return json_data["status"] == "VALID"

    async def _render_page(self,
                           page_file:
                           str, *args, **kwargs) -> typing.Optional[str]:
        try:
            return await render_template(page_file, *args, **kwargs)

        except jinja2.TemplateError:
            self._logger.error("Failed to render web page '%s'", page_file)
            return await render_template(pages.TEMPLATE_INTERNAL_ERROR_PAGE)

    async def _process_post_form_data(self, form_data):
        return {key: value for key, value in form_data.items()}
