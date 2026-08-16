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
import json
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
from items.shared.permission_area import PermissionArea


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

        return await self._render_after_write(
            response, "invite", email=email_address)

    @require_administrator
    async def resend_invite(self):
        """Refresh the token and expiry for a pending invite.

        Returns:
            The re-rendered users and roles page, confirming the resend or
            showing an error banner if the gateway/identity rejects it.
        """
        form = await request.form
        email_address = form.get("email_address", "").strip()

        url = f"{self._config.apis_gateway_svc}web/invites/resend"
        response: ApiResponse = await self._rest_client.post(
            url, json_data={"email_address": email_address})

        return await self._render_after_write(
            response, "resend", email=email_address)

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

        return await self._render_after_write(
            response, "uninvite", email=email_address)

    # ------------------------------------------------------------------
    # Write: roles
    # ------------------------------------------------------------------

    @require_administrator
    async def role_add(self):
        """Create a new role from the submitted form.

        Returns:
            The re-rendered users and roles page, showing an error banner
            if the gateway/identity rejects the request.
        """
        form = await request.form
        name = form.get("name", "").strip()

        if not name:
            return await self._render(
                error_msg_str="Role name is required.", active_tab="roles")

        body = {"name": name,
                "permissions": self._parse_permissions_from_form(form)}

        url = f"{self._config.apis_gateway_svc}web/roles"
        response: ApiResponse = await self._rest_client.post(
            url, json_data=body)

        return await self._render_after_write(
            response, "role_add", name=name)

    @require_administrator
    async def role_modify(self, role_id: int):
        """Update an existing role's name and permission grid.

        Args:
            role_id: The role's primary key (from the URL).

        Returns:
            The re-rendered users and roles page, showing an error banner
            if the gateway/identity rejects the request.
        """
        form = await request.form
        name = form.get("name", "").strip()

        if not name:
            return await self._render(
                error_msg_str="Role name is required.", active_tab="roles")

        body = {"name": name,
                "permissions": self._parse_permissions_from_form(form)}

        url = f"{self._config.apis_gateway_svc}web/roles/{role_id}"
        response: ApiResponse = await self._rest_client.patch(
            url, json_data=body)

        return await self._render_after_write(
            response, "role_modify", name=name)

    @require_administrator
    async def role_delete(self, role_id: int):
        """Delete a role.

        Any project membership using this role has its role cleared to
        "Unassigned" rather than being removed (enforced at the identity
        service, see §4.3/§10.4 of user_roles_design.md) - deleting a role
        never removes a user from a project.

        Args:
            role_id: The role's primary key (from the URL).

        Returns:
            The re-rendered users and roles page, showing an error banner
            if the gateway/identity rejects the request.
        """
        form = await request.form
        name = form.get("name", "").strip() or "Role"

        url = f"{self._config.apis_gateway_svc}web/roles/{role_id}"
        response: ApiResponse = await self._rest_client.delete(url)

        return await self._render_after_write(
            response, "role_delete", name=name)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    # Human-readable labels for the fixed permission areas, in the order
    # they should appear as grid rows. Only TEST_CASES has any enforceable
    # effect today (see PermissionArea's docstring) - the rest are included
    # so the grid looks complete rather than growing rows later.
    _AREA_LABELS: dict = {
        PermissionArea.TEST_CASES.value: "Test Cases",
        PermissionArea.MILESTONES.value: "Milestones",
        PermissionArea.TEST_RUNS.value: "Test Runs",
        PermissionArea.TEST_PLANS.value: "Test Plans",
        PermissionArea.TEST_REPORTS.value: "Test Reports",
        PermissionArea.TEST_RESULTS.value: "Test Results",
    }

    # Confirmation shown after each invite action succeeds. Without these the
    # page re-renders looking identical to having done nothing, so there is no
    # way to tell a successful action from one that silently failed.
    #
    # The resend message mentions the previous link because resending
    # regenerates the token: any invitation already sent stops working, which
    # the administrator cannot otherwise know.
    _SUCCESS_MESSAGES: dict = {
        "invite": "Invitation sent to {email}.",
        "resend": ("Invitation resent to {email}. Any previous invitation "
                   "link is no longer valid."),
        "uninvite": "Invitation for {email} has been cancelled.",
        "role_add": "Role '{name}' created.",
        "role_modify": "Role '{name}' updated.",
        "role_delete": "Role '{name}' deleted.",
    }

    # How long each confirmation stays on screen. Resend gets longer because
    # it reports that the previous link has stopped working - a fact the
    # administrator may need to act on, rather than a simple acknowledgement.
    # Errors are never auto-dismissed; see the template.
    _DEFAULT_DISMISS_MS: int = 10_000
    _SUCCESS_DISMISS_MS: dict = {
        "resend": 20_000,
    }

    # Actions whose write happens from the Roles tab - re-rendering after
    # one of these should land back on Roles rather than the default Users
    # tab, otherwise every add/edit/delete bounces you away from where you
    # were working.
    _ROLE_ACTIONS: frozenset = frozenset(
        {"role_add", "role_modify", "role_delete"})

    async def _render_after_write(self, response: ApiResponse,
                                  action: str,
                                  **format_kwargs):
        """Re-render the page after a write, confirming it or showing an error.

        Args:
            response: The gateway response for the write operation.
            action: Short action name used in logging and to select the
                confirmation message ("invite", "resend", "uninvite",
                "role_add", "role_modify", "role_delete").
            **format_kwargs: Values substituted into the confirmation
                message's placeholders (e.g. ``email="a@b.com"`` or
                ``name="Tester"``).

        Returns:
            The re-rendered users and roles page.
        """
        error_msg_str: Optional[str] = None
        success_msg_str: Optional[str] = None
        success_dismiss_ms: int = self._DEFAULT_DISMISS_MS

        if response.status_code not in (HTTPStatus.OK, HTTPStatus.CREATED):
            error_msg_str = self._extract_error(response)
            self._logger.warning(
                "%s failed (status %s): %s",
                action, response.status_code, error_msg_str)
        else:
            template = self._SUCCESS_MESSAGES.get(action)
            if template:
                success_msg_str = template.format(**format_kwargs)
                success_dismiss_ms = self._SUCCESS_DISMISS_MS.get(
                    action, self._DEFAULT_DISMISS_MS)

        active_tab = "roles" if action in self._ROLE_ACTIONS else "users"

        return await self._render(error_msg_str=error_msg_str,
                                  success_msg_str=success_msg_str,
                                  success_dismiss_ms=success_dismiss_ms,
                                  active_tab=active_tab)

    @staticmethod
    def _extract_error(response: ApiResponse) -> str:
        """Extract a human-readable error message from a gateway response."""
        if isinstance(response.body, dict) and response.body.get("error"):
            return str(response.body["error"])
        return "The request could not be completed. Please try again."

    async def _render(self, error_msg_str: Optional[str] = None,
                      success_msg_str: Optional[str] = None,
                      success_dismiss_ms: int = _DEFAULT_DISMISS_MS,
                      active_tab: str = "users"):
        """Fetch users and pending invites, then render the page.

        Args:
            error_msg_str: Optional error banner to display on the page.
            success_msg_str: Optional confirmation banner to display on the
                page.
            success_dismiss_ms: How long the confirmation stays on screen
                before dismissing itself.
            active_tab: Which tab ("users" or "roles") should be shown as
                active on render - so a role write lands back on Roles
                rather than always resetting to the default Users tab.

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
        roles = await self._fetch_roles()

        return await self._render_page(
            pages.PAGE_INSTANCE_ADMIN_USERS_AND_ROLES,
            instance_name=self._metadata_settings.instance_name,
            active_page="administration",
            active_admin_page="admin_page_users_roles",
            users=users,
            invites=invites,
            roles=roles,
            permission_areas=self._AREA_LABELS,
            active_tab=active_tab,
            error_msg_str=error_msg_str,
            success_msg_str=success_msg_str,
            success_dismiss_ms=success_dismiss_ms)

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

    async def _fetch_roles(self) -> list[dict]:
        """Fetch every role together with its full permission grid.

        The list endpoint (``GET /roles``) deliberately returns names only
        - each role's grid is fetched individually via
        ``_fetch_role_detail``. Mirrors ``_fetch_pending_invites``: a
        failure fetching the list is non-fatal and simply renders the
        table empty, and a failure fetching one role's grid still leaves
        that role listed, just with an empty grid.

        Returns:
            A list of ``{"id", "name", "permissions_by_area",
            "permissions_json"}`` dicts. ``permissions_by_area`` is keyed
            by ``PermissionArea`` value for template lookups;
            ``permissions_json`` is the same data JSON-encoded for the
            edit button's ``data-permissions`` attribute (see
            ``instance_admin_customisations.html``'s ``data-projects``
            for the precedent this follows).
        """
        url = f"{self._config.apis_gateway_svc}web/roles"
        try:
            response = await self._rest_client.get(url)
        except Exception:  # pylint: disable=broad-except
            self._logger.warning("Unable to fetch roles")
            return []

        if response.status_code != HTTPStatus.OK:
            self._logger.warning(
                "Unable to fetch roles (status %s)", response.status_code)
            return []

        roles = []
        for summary in response.body.get("roles", []):
            role_id = summary.get("id")
            detail = await self._fetch_role_detail(role_id)
            permissions = detail.get("permissions", []) if detail else []
            permissions_by_area = {p["area"]: p for p in permissions}
            roles.append({
                "id": role_id,
                "name": summary.get("name", ""),
                "permissions_by_area": permissions_by_area,
                "permissions_json": json.dumps(permissions_by_area),
            })
        return roles

    async def _fetch_role_detail(self, role_id) -> Optional[dict]:
        """Fetch a single role's full permission grid.

        Args:
            role_id: The role's primary key.

        Returns:
            The role dict (``id``, ``name``, ``permissions``), or ``None``
            on failure.
        """
        url = f"{self._config.apis_gateway_svc}web/roles/{role_id}"
        try:
            response = await self._rest_client.get(url)
        except Exception:  # pylint: disable=broad-except
            self._logger.warning("Unable to fetch role %s", role_id)
            return None

        if response.status_code != HTTPStatus.OK:
            self._logger.warning(
                "Unable to fetch role %s (status %s)",
                role_id, response.status_code)
            return None

        return response.body

    @staticmethod
    def _parse_permissions_from_form(form) -> list[dict]:
        """Build a role's permission grid from the submitted checkbox form.

        Checkbox fields are named ``perm_<area>_read``,
        ``perm_<area>_add_modify`` and ``perm_<area>_delete``; a checkbox
        is absent from the form entirely when unticked. An area with
        nothing ticked is omitted rather than sent as an explicit
        all-false row - the two are equivalent to the backend (an area
        with no row has no access, see ``RoleRepository.get_role_permissions``),
        so omitting keeps the payload to only what was actually granted.

        Args:
            form: The submitted form (werkzeug/quart MultiDict).

        Returns:
            A list of ``{"area", "can_read", "can_add_modify",
            "can_delete"}`` dicts, one per area with at least one
            permission ticked.
        """
        permissions: list[dict] = []
        for area in PermissionArea:
            can_read = form.get(f"perm_{area.value}_read") == "on"
            can_add_modify = form.get(f"perm_{area.value}_add_modify") == "on"
            can_delete = form.get(f"perm_{area.value}_delete") == "on"
            if can_read or can_add_modify or can_delete:
                permissions.append({
                    "area": area.value,
                    "can_read": can_read,
                    "can_add_modify": can_add_modify,
                    "can_delete": can_delete,
                })
        return permissions
