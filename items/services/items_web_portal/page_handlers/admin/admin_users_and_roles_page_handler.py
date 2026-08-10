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
from datetime import datetime, timezone
from http import HTTPStatus
import logging
from typing import Optional
from quart import request
from weaver_framework.microservice.api_response import ApiResponse
from weaver_framework.microservice.rest_client import RestClient
from items.services.items_web_portal.configuration import Configuration
from items.services.items_web_portal.decorators import require_administrator
from items.services.items_web_portal.metadata_settings import MetadataSettings
import items.services.items_web_portal.page_locations as pages
from items.services.items_web_portal.portal_page_handler import (
    PortalPageHandler)


class AdminUsersAndRolesPageHandler(PortalPageHandler):
    """Handles requests for the administration users and roles page.

    This handler fetches the current list of users and pending invites from
    the gateway and renders the administration page used to manage user
    accounts, role assignments, and outstanding invites.
    """

    def __init__(self,
                 logger: logging.Logger,
                 config: Configuration,
                 rest_client: RestClient,
                 metadata: MetadataSettings):
        """Initialize the administration users and roles page handler.

        Args:
            logger: Logger used to record diagnostic and operational messages.
            config: Application configuration settings.
            rest_client: REST client used to communicate with backend services.
            metadata: Instance metadata used to populate page content.
        """
        super().__init__(logger, config, rest_client)
        self._metadata_settings = metadata

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    @require_administrator
    async def users_and_roles(self):
        """Render the administration users and roles page.

        Returns:
            The rendered administration users and roles page response.
        """
        return await self._render()

    # ------------------------------------------------------------------
    # Write: invites
    # ------------------------------------------------------------------

    @require_administrator
    async def invite_user(self):
        """Create a new pending invite from the submitted form.

        Returns:
            The re-rendered users and roles page, showing an error banner
            if the gateway/identity rejects the request.
        """
        form = await request.form
        email_address = form.get("email_address", "").strip()

        if not email_address:
            return await self._render(
                error_msg_str="Email address is required.")

        url = f"{self._config.apis_gateway_svc}web/invites"
        response: ApiResponse = await self._rest_client.post(
            url, json_data={"email_address": email_address})

        return await self._render_after_write(response, "invite")

    @require_administrator
    async def resend_invite(self):
        """Refresh the token and expiry for a pending invite.

        Returns:
            The re-rendered users and roles page, showing an error banner
            if the gateway/identity rejects the request.
        """
        form = await request.form
        email_address = form.get("email_address", "").strip()

        url = f"{self._config.apis_gateway_svc}web/invites/resend"
        response: ApiResponse = await self._rest_client.post(
            url, json_data={"email_address": email_address})

        return await self._render_after_write(response, "resend")

    @require_administrator
    async def uninvite(self):
        """Cancel a pending invite.

        Returns:
            The re-rendered users and roles page, showing an error banner
            if the gateway/identity rejects the request.
        """
        form = await request.form
        email_address = form.get("email_address", "").strip()

        url = f"{self._config.apis_gateway_svc}web/invites/uninvite"
        response: ApiResponse = await self._rest_client.post(
            url, json_data={"email_address": email_address})

        return await self._render_after_write(response, "uninvite")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    async def _render_after_write(self, response: ApiResponse,
                                  action: str):
        """Re-render the page after a write, surfacing any gateway error.

        Args:
            response: The gateway response for the write operation.
            action: Short action name used in logging ("invite", "resend",
                "uninvite").

        Returns:
            The re-rendered users and roles page.
        """
        error_msg_str: Optional[str] = None

        if response.status_code not in (HTTPStatus.OK, HTTPStatus.CREATED):
            error_msg_str = self._extract_error(response)
            self._logger.warning(
                "Invite %s failed (status %s): %s",
                action, response.status_code, error_msg_str)

        return await self._render(error_msg_str=error_msg_str)

    @staticmethod
    def _extract_error(response: ApiResponse) -> str:
        """Extract a human-readable error message from a gateway response."""
        if isinstance(response.body, dict) and response.body.get("error"):
            return str(response.body["error"])
        return "The request could not be completed. Please try again."

    async def _render(self, error_msg_str: Optional[str] = None):
        """Fetch users and pending invites, then render the page.

        Args:
            error_msg_str: Optional error banner to display on the page.

        Returns:
            The rendered users and roles page response.
        """
        base_url = self._config.apis_gateway_svc

        users_response = await self._rest_client.get(f"{base_url}web/users")
        if users_response.status_code == HTTPStatus.OK:
            users = users_response.body.get("users", [])
        else:
            self._logger.error(
                "Failed to fetch users from gateway: status=%s",
                users_response.status_code)
            users = []
            error_msg_str = error_msg_str or (
                "Could not load users — please try again.")

        invites = await self._fetch_pending_invites()

        return await self._render_page(
            pages.PAGE_INSTANCE_ADMIN_USERS_AND_ROLES,
            instance_name=self._metadata_settings.instance_name,
            active_page="administration",
            active_admin_page="admin_page_users_roles",
            users=users,
            invites=invites,
            error_msg_str=error_msg_str)

    async def _fetch_pending_invites(self) -> list[dict]:
        """Fetch the list of pending invites from the gateway.

        A failure here is non-fatal: the table is simply rendered empty so
        the rest of the page still works.

        Returns:
            A list of ``{"email_address", "created_at", "expires_at",
            "created_display", "expires_display"}`` dicts, or an empty
            list on failure. The ``*_display`` fields are pre-formatted,
            human-readable strings - there's no date-formatting Jinja
            filter registered anywhere in this codebase yet, so this is
            done here rather than introducing one for a single page.
        """
        url = f"{self._config.apis_gateway_svc}web/invites"
        try:
            response = await self._rest_client.get(url)
        except Exception:  # pylint: disable=broad-except
            self._logger.warning("Unable to fetch pending invites")
            return []

        if response.status_code != HTTPStatus.OK:
            self._logger.warning(
                "Unable to fetch pending invites (status %s)",
                response.status_code)
            return []

        invites = response.body.get("invites", [])
        for invite in invites:
            invite["created_display"] = self._format_epoch(
                invite.get("created_at"))
            invite["expires_display"] = self._format_epoch(
                invite.get("expires_at"))
        return invites

    @staticmethod
    def _format_epoch(epoch_seconds: Optional[int]) -> str:
        """Format an epoch-seconds timestamp for display.

        Args:
            epoch_seconds: Seconds since the Unix epoch, or None.

        Returns:
            A ``"YYYY-MM-DD HH:MM UTC"`` string, or ``""`` if not given.
        """
        if epoch_seconds is None:
            return ""
        return datetime.fromtimestamp(
            epoch_seconds, tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
