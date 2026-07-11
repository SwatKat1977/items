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
import logging
import jinja2
import jsonschema
from quart import request, render_template
from weaver_framework.microservice.api_response import ApiResponse
from weaver_framework.microservice.base_api_route import BaseApiRoute
from weaver_framework.microservice.rest_client import RestClient
from items.shared.base_items_exception import BaseItemsException
from items.services.items_web_portal.configuration import Configuration
import items.services.items_web_portal.page_locations as pages

SCHEMA_SESSION_VALIDATE_RESPONSE = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "properties": {
        "status": {
            "type": "string",
            "enum": ["VALID", "INVALID"]
        }
    },
    "required": ["status"],
    "additionalProperties": False
}


class SessionAuthMixin:
    """
    Cookie/session authentication helpers mixed into PortalPageHandler.
    """

    COOKIE_TOKEN = "items_token"
    COOKIE_USER = "items_user"

    REDIRECT_URL = "<meta http-equiv=\"Refresh\" content=\"0; url='{0}'\"/>"

    def __init__(self, config: Configuration, rest_client: RestClient) -> None:
        self._config: Configuration = config
        self._rest_client: RestClient = rest_client

    async def _generate_redirect(self, redirect_url) -> str:
        new_url = f"{request.url_root}{redirect_url}"
        return self.REDIRECT_URL.format(new_url)

    async def _has_auth_cookies(self) -> bool:
        retrieved_token = request.cookies.get(self.COOKIE_TOKEN)
        retrieved_username = request.cookies.get(self.COOKIE_USER)
        return retrieved_token is not None and retrieved_username is not None

    async def _validate_cookies(self) -> bool:
        token = request.cookies.get(self.COOKIE_TOKEN)
        username = request.cookies.get(self.COOKIE_USER)

        url = f"{self._config.apis_gateway_svc}web/sessions/validate"

        request_body: dict = {
            "email_address": username,
            "token": token
        }
        response: ApiResponse = await self._rest_client.post(
            url,
            json_data=request_body,
            timeout=5)

        if response.status_code != HTTPStatus.OK:
            detail = f": {response.exception_msg}" if response.exception_msg \
                else ""
            raise BaseItemsException(
                f"Gateway svc session validate failed with status "
                f"{response.status_code}{detail}")

        try:
            jsonschema.validate(instance=response.body,
                                schema=SCHEMA_SESSION_VALIDATE_RESPONSE)

        except jsonschema.exceptions.ValidationError as ex:
            raise BaseItemsException(
                "Schema for gateway svc session validate response "
                "invalid!") from ex

        return response.body["status"] == "VALID"


class PortalPageHandler(SessionAuthMixin, BaseApiRoute):
    def __init__(self, logger: logging.Logger,
                 config: Configuration,
                 rest_client: RestClient) -> None:
        super().__init__(config, rest_client)
        self._logger = logger.getChild(__name__)

    async def _render_page(self, page_file: str, **kwargs) -> str | None:
        """
        Python unittest and coverage hate quart.render_template so it is
        getting excluded from unittests for now.
        """
        try:
            return await render_template(page_file, **kwargs)

        except jinja2.TemplateError:
            self._logger.error("Failed to render web page '%s'", page_file)
            return await render_template(pages.TEMPLATE_INTERNAL_ERROR_PAGE)
