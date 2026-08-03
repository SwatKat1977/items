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
        },
        # Optional — present once the gateway begins reporting it (step 4 of
        # the is_administrator rollout in user_roles_design.md §9.4).
        "is_administrator": {
            "type": "boolean"
        }
    },
    "required": ["status"],
    "additionalProperties": False
}


class SessionAuthMixin:
    """Provides shared session authentication functionality for page handlers.

    This mixin encapsulates common operations related to user session
    management, including authentication cookie handling, session validation,
    and redirect generation. It is intended to be inherited by page handlers
    that require authenticated user sessions.
    """
    # pylint: disable=too-few-public-methods

    COOKIE_TOKEN = "items_token"
    COOKIE_USER = "items_user"

    REDIRECT_URL = "<meta http-equiv=\"Refresh\" content=\"0; url='{0}'\"/>"

    def __init__(self, config: Configuration, rest_client: RestClient) -> None:
        """Initializes the session authentication mixin.

        Args:
            config: Application configuration.
            rest_client: REST client used to communicate with backend services.
        """
        self._config: Configuration = config
        self._rest_client: RestClient = rest_client

    def _generate_redirect(self, redirect_url: str) -> str:
        """Generates an HTML redirect response.

        Args:
            redirect_url: Relative URL to redirect the client to.

        Returns:
            An HTML document that immediately redirects the client to the
            specified URL.
        """
        new_url = f"{request.url_root}{redirect_url}"
        return self.REDIRECT_URL.format(new_url)

    async def _has_auth_cookies(self) -> bool:
        """Determines whether the required authentication cookies exist.

        Returns:
            ``True`` if both the authentication token and username cookies are
            present; otherwise, ``False``.
        """
        retrieved_token = request.cookies.get(self.COOKIE_TOKEN)
        retrieved_username = request.cookies.get(self.COOKIE_USER)
        return retrieved_token is not None and retrieved_username is not None

    async def _validate_cookies(self) -> tuple[bool, bool]:
        """Validates the current authentication session.

        The stored authentication cookies are submitted to the gateway service
        for validation. The response is validated against the expected schema
        before the session status is returned.

        Returns:
            A ``(is_valid, is_administrator)`` tuple. ``is_administrator`` is
            ``False`` whenever the session is not valid.

            Callers must unpack this tuple. Testing the return value directly
            is always true, because any non-empty tuple is truthy - including
            ``(False, False)``.

        Raises:
            BaseItemsException: If the gateway service returns an unexpected
                response or the response schema is invalid.
        """
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

        is_valid = response.body["status"] == "VALID"
        is_administrator = (
            bool(response.body.get("is_administrator", False))
            if is_valid else False
        )
        return is_valid, is_administrator


class PortalPageHandler(SessionAuthMixin, BaseApiRoute):
    """Base class for web portal page handlers.

    This class provides common functionality shared by portal page handlers,
    including session authentication, logging, and template rendering.
    """
    # pylint: disable=too-few-public-methods

    def __init__(self, logger: logging.Logger,
                 config: Configuration,
                 rest_client: RestClient) -> None:
        """Initializes the portal page handler.

        Args:
            logger: Logger instance used for diagnostic and error messages.
            config: Application configuration.
            rest_client: REST client used to communicate with backend services.
        """
        super().__init__(config, rest_client)
        self._logger = logger.getChild(__name__)

    async def _render_page(self, page_file: str, **kwargs) -> str | None:
        """Renders a portal page template.

        Attempts to render the specified Jinja template. If template rendering
        fails, the error is logged and the internal error page is rendered
        instead.

        Args:
            page_file: Template file to render.
            **kwargs: Context variables supplied to the template.

        Returns:
            The rendered HTML page, or the rendered internal error page if
            template rendering fails.
        """
        try:
            return await render_template(page_file, **kwargs)

        except jinja2.TemplateError:
            self._logger.error("Failed to render web page '%s'", page_file)
            return await render_template(pages.TEMPLATE_INTERNAL_ERROR_PAGE)
