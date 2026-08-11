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
from quart import request
from weaver_framework.microservice.api_response import ApiResponse
from weaver_framework.microservice.rest_client import RestClient
from items.services.items_web_portal.configuration import Configuration
from items.services.items_web_portal.metadata_settings import MetadataSettings
import items.services.items_web_portal.page_locations as pages
from items.services.items_web_portal.portal_page_handler import (
    PortalPageHandler)

_MIN_PASSWORD_LENGTH: int = 8


class AcceptInvitePageHandler(PortalPageHandler):
    """Serves the page an invited person uses to set up their account.

    Deliberately **not** guarded by ``require_session`` or
    ``require_administrator``: the visitor has no account yet, which is the
    whole point. The invite token in the link is what authorises them, and it
    is validated by the gateway rather than trusted here.

    The form intentionally offers a narrow set of fields. The email address is
    fixed by the invite and displayed read-only, and there is no way to choose
    roles or projects - a recipient must not be able to grant themselves
    access. Those remain an administrator's decision.
    """

    def __init__(self,
                 logger: logging.Logger,
                 config: Configuration,
                 rest_client: RestClient,
                 metadata: MetadataSettings):
        """Initialise the accept invite page handler.

        Args:
            logger:      Logger used for diagnostic messages.
            config:      Application configuration.
            rest_client: REST client used to talk to the gateway.
            metadata:    Instance metadata used when rendering pages.
        """
        super().__init__(logger, config, rest_client)
        self._metadata_settings = metadata

    async def accept_invite_get(self):
        """Render the account setup form for an invitation link.

        Returns:
            The setup form when the token is valid, otherwise the same page
            showing that the invitation is no longer usable.
        """
        token: str = request.args.get("token", "")

        if not token:
            return await self._render_invalid("No invitation token supplied.")

        email_address = await self._resolve_token(token)
        if email_address is None:
            return await self._render_invalid(
                "This invitation is no longer valid. It may have expired or "
                "already been used. Please ask an administrator to send a "
                "new one.")

        return await self._render_form(token, email_address)

    async def accept_invite_post(self):
        """Submit the completed form to the gateway to create the account.

        Returns:
            A redirect to the login page on success, or the form re-rendered
            with an error message.
        """
        form = await request.form

        token: str = form.get("token", "")
        full_name: str = (form.get("full_name") or "").strip()
        display_name: str = (form.get("display_name") or "").strip()
        password: str = form.get("password") or ""
        confirm_password: str = form.get("confirm_password") or ""

        if not token:
            return await self._render_invalid("No invitation token supplied.")

        # The address always comes from the invite, never from the form, so a
        # tampered submission cannot create an account for another address.
        email_address = await self._resolve_token(token)
        if email_address is None:
            return await self._render_invalid(
                "This invitation is no longer valid. It may have expired or "
                "already been used.")

        error = self._validate(full_name, display_name, password,
                               confirm_password)
        if error:
            return await self._render_form(token, email_address, error=error)

        base_url: str = self._config.apis_gateway_svc
        response: ApiResponse = await self._rest_client.post(
            f"{base_url}web/accept_invite",
            json_data={"token": token,
                       "full_name": full_name,
                       "display_name": display_name,
                       "password": password})

        if response.status_code != HTTPStatus.CREATED:
            message = "Your account could not be created. Please try again."
            if isinstance(response.body, dict) and response.body.get("error"):
                message = str(response.body["error"])

            self._logger.warning("Invite acceptance failed (status %s): %s",
                                 response.status_code, message)
            return await self._render_form(token, email_address, error=message)

        return await self._render_page(
            pages.PAGE_ACCEPT_INVITE,
            instance_name=self._metadata_settings.instance_name,
            account_created=True)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _validate(full_name: str,
                  display_name: str,
                  password: str,
                  confirm_password: str) -> str | None:
        """Check the submitted fields, returning an error message or None."""
        if not full_name or not display_name:
            return "Please provide both your full name and a display name."

        if len(password) < _MIN_PASSWORD_LENGTH:
            return (f"Your password must be at least {_MIN_PASSWORD_LENGTH} "
                    "characters long.")

        if password != confirm_password:
            return "The passwords entered do not match."

        return None

    async def _resolve_token(self, token: str) -> str | None:
        """Ask the gateway which address an invite was issued to."""
        base_url: str = self._config.apis_gateway_svc
        response: ApiResponse = await self._rest_client.get(
            f"{base_url}web/invites/token/{token}")

        if response.status_code != HTTPStatus.OK:
            return None

        return (response.body or {}).get("email_address")

    async def _render_form(self,
                           token: str,
                           email_address: str,
                           error: str | None = None):
        """Render the account setup form."""
        return await self._render_page(
            pages.PAGE_ACCEPT_INVITE,
            instance_name=self._metadata_settings.instance_name,
            token=token,
            email_address=email_address,
            error_message=error)

    async def _render_invalid(self, message: str):
        """Render the page explaining the invitation cannot be used."""
        return await self._render_page(
            pages.PAGE_ACCEPT_INVITE,
            instance_name=self._metadata_settings.instance_name,
            invalid_message=message)
