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
import http
from http import HTTPStatus
import logging
from typing import Optional
from quart import make_response, request
from weaver_framework.microservice.api_response import ApiResponse
from weaver_framework.microservice.rest_client import RestClient
from items.services.items_web_portal.configuration import Configuration
from items.services.items_web_portal.decorators import require_administrator
from items.services.items_web_portal.metadata_settings import MetadataSettings
import items.services.items_web_portal.page_locations as pages
from items.services.items_web_portal.portal_page_handler import (
    PortalPageHandler)


class AdminModifyUserPageHandler(PortalPageHandler):
    """Handles requests for editing an existing user.

    Fetches the current user data from the gateway on GET and submits a
    patch-style update on POST. Also owns the Projects tab: listing,
    adding, changing the role on, and removing this user's project
    memberships.
    """

    _DEFAULT_ACTIVE_TAB: str = "tab-user"

    def __init__(self,
                 logger: logging.Logger,
                 config: Configuration,
                 rest_client: RestClient,
                 metadata: MetadataSettings):
        """Initialise the modify user page handler.

        Args:
            logger: Logger used to record diagnostic and operational messages.
            config: Application configuration settings.
            rest_client: REST client used to communicate with backend services.
            metadata: Instance metadata used to populate page content.
        """
        super().__init__(logger, config, rest_client)
        self._metadata_settings = metadata

    # ------------------------------------------------------------------
    # Read / write: core user fields (User and Access tabs)
    # ------------------------------------------------------------------

    @require_administrator
    async def modify_user_get(self, user_id: str):
        """Render the edit user page pre-populated with current user data.

        Args:
            user_id: The ID of the user to edit.

        Returns:
            The rendered edit user page, or an error page if the user is
            not found or the gateway is unavailable.
        """
        url = f"{self._config.apis_gateway_svc}web/users/{user_id}"
        response: ApiResponse = await self._rest_client.get(url)

        if response.status_code == http.HTTPStatus.NOT_FOUND:
            return await self._render(
                user_id=user_id,
                form_data={},
                error_msg_str="User not found.")

        if response.status_code != http.HTTPStatus.OK:
            self._logger.error(
                "Gateway GET /web/users/%s failed: status=%s",
                user_id, response.status_code)
            return await self._render(
                user_id=user_id,
                form_data={},
                error_msg_str="Could not load user — please try again.")

        form_data = self._user_to_form_data(response.body)
        return await self._render(user_id=user_id, form_data=form_data)

    @require_administrator
    async def modify_user_post(self, user_id: str):
        """Process an edit user submission.

        Sends a PATCH request to the gateway with the supplied fields.
        Redirects to the user list on success; re-renders the form with an
        error message on failure.

        Args:
            user_id: The ID of the user to update.

        Returns:
            A redirect to /admin/users_roles on success, or the rendered
            edit page with an error message on failure.
        """
        form = await request.form
        form_data = form.to_dict()

        full_name: str = form.get("full_name", "").strip()
        display_name: str = form.get("display_name", "").strip()
        account_status: int = 1 if form.get("account_status") == "1" else 0
        is_administrator: bool = form.get("is_administrator") == "1"

        # Re-inject checkbox fields for template re-population - unlike text
        # inputs, an unchecked checkbox is simply absent from form_data.
        form_data["account_status"] = account_status
        form_data["is_administrator"] = is_administrator

        if not all([full_name, display_name]):
            return await self._render(
                user_id=user_id,
                form_data=form_data,
                error_msg_str="Full name and display name are required.")

        gateway_body: dict = {
            "full_name": full_name,
            "display_name": display_name,
            "account_status": account_status,
            "is_administrator": is_administrator,
        }

        url = f"{self._config.apis_gateway_svc}web/users/{user_id}"
        response: ApiResponse = await self._rest_client.patch(
            url, json_data=gateway_body)

        if response.status_code == http.HTTPStatus.FORBIDDEN:
            return await self._render(
                user_id=user_id,
                form_data=form_data,
                error_msg_str="This change would leave no active "
                             "administrator - there must always be at "
                             "least one.")

        if response.status_code == http.HTTPStatus.NOT_FOUND:
            return await self._render(
                user_id=user_id,
                form_data=form_data,
                error_msg_str="User not found.")

        if response.status_code != http.HTTPStatus.OK:
            self._logger.error(
                "Gateway PATCH /web/users/%s failed: status=%s body=%s",
                user_id, response.status_code, response.body)
            return await self._render(
                user_id=user_id,
                form_data=form_data,
                error_msg_str="An unexpected error occurred. Please try again.")

        return await make_response(
            self._generate_redirect('/admin/users_roles'))

    # ------------------------------------------------------------------
    # Write: project membership (Projects tab)
    # ------------------------------------------------------------------

    _PROJECT_SUCCESS_MESSAGES: dict = {
        "add": "Project access added.",
        "modify": "Role updated.",
        "remove": "Project access removed.",
    }

    @require_administrator
    async def add_user_project(self, user_id: str):
        """Add a project membership for the user from the submitted form.

        Args:
            user_id: The ID of the user being granted access.

        Returns:
            The re-rendered edit user page, on the Projects tab.
        """
        form = await request.form
        project_id_str = form.get("project_id", "").strip()
        role_id_str = form.get("role_id", "").strip()

        if not project_id_str:
            return await self._render_projects_after_write(
                user_id, error_msg_str="Select a project.")

        try:
            project_id = int(project_id_str)
        except ValueError:
            return await self._render_projects_after_write(
                user_id, error_msg_str="Invalid project.")

        body: dict = {"project_id": project_id}
        if role_id_str:
            try:
                body["role_id"] = int(role_id_str)
            except ValueError:
                return await self._render_projects_after_write(
                    user_id, error_msg_str="Invalid role.")

        url = f"{self._config.apis_gateway_svc}web/users/{user_id}/projects"
        response: ApiResponse = await self._rest_client.post(
            url, json_data=body)

        return await self._render_projects_after_write(
            user_id, response=response, action="add")

    @require_administrator
    async def modify_user_project(self, user_id: str, project_id: int):
        """Change (or clear) the role on an existing project membership.

        Args:
            user_id: The ID of the user whose membership is being changed.
            project_id: The project the membership belongs to.

        Returns:
            The re-rendered edit user page, on the Projects tab.
        """
        form = await request.form
        role_id_str = form.get("role_id", "").strip()

        role_id: Optional[int] = None
        if role_id_str:
            try:
                role_id = int(role_id_str)
            except ValueError:
                return await self._render_projects_after_write(
                    user_id, error_msg_str="Invalid role.")

        url = (f"{self._config.apis_gateway_svc}web/users/{user_id}"
               f"/projects/{project_id}")
        response: ApiResponse = await self._rest_client.patch(
            url, json_data={"role_id": role_id})

        return await self._render_projects_after_write(
            user_id, response=response, action="modify")

    @require_administrator
    async def remove_user_project(self, user_id: str, project_id: int):
        """Remove a project membership.

        Args:
            user_id: The ID of the user losing access.
            project_id: The project the membership belongs to.

        Returns:
            The re-rendered edit user page, on the Projects tab.
        """
        url = (f"{self._config.apis_gateway_svc}web/users/{user_id}"
               f"/projects/{project_id}")
        response: ApiResponse = await self._rest_client.delete(url)

        return await self._render_projects_after_write(
            user_id, response=response, action="remove")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _user_to_form_data(user: dict) -> dict:
        """Map a gateway user body to the template's form_data shape."""
        return {
            "full_name": user.get("full_name", ""),
            "display_name": user.get("display_name", ""),
            "email_address": user.get("email_address", ""),
            "account_status": user.get("account_status", 1),
            "is_administrator": bool(user.get("is_administrator", False)),
        }

    async def _render_projects_after_write(
            self, user_id: str,
            response: Optional[ApiResponse] = None,
            action: Optional[str] = None,
            error_msg_str: Optional[str] = None):
        """Re-render the edit user page after a project-membership write.

        Always lands back on the Projects tab, confirming the write or
        showing an error - mirrors the Roles admin page's
        _render_after_write.

        Args:
            user_id: The ID of the user whose memberships were changed.
            response: The gateway response for the write, or None if the
                request never reached the gateway (form validation failed
                first).
            action: Short action name used to select the confirmation
                message ("add", "modify", "remove"). Ignored if response
                is None.
            error_msg_str: Error to show directly, for validation failures
                that happened before any gateway call.

        Returns:
            The re-rendered edit user page, on the Projects tab.
        """
        success_msg_str: Optional[str] = None

        if response is not None:
            if response.status_code not in (HTTPStatus.OK, HTTPStatus.CREATED):
                error_msg_str = self._extract_error(response)
                self._logger.warning(
                    "Project %s failed for user %s (status %s): %s",
                    action, user_id, response.status_code, error_msg_str)
            else:
                success_msg_str = self._PROJECT_SUCCESS_MESSAGES.get(action)

        form_data = await self._current_form_data(user_id)

        return await self._render(
            user_id=user_id,
            form_data=form_data,
            error_msg_str=error_msg_str,
            success_msg_str=success_msg_str,
            active_tab="tab-projects")

    async def _current_form_data(self, user_id: str) -> dict:
        """Re-fetch the user's core fields to re-populate the User/Access
        tabs after a project-membership write (which doesn't touch them,
        but the shared form still needs correct values to show).

        A failure here is non-fatal: the User/Access tabs would simply show
        blank fields rather than the Projects tab write itself failing.
        """
        url = f"{self._config.apis_gateway_svc}web/users/{user_id}"
        response: ApiResponse = await self._rest_client.get(url)
        if response.status_code != HTTPStatus.OK:
            return {}
        return self._user_to_form_data(response.body)

    @staticmethod
    def _extract_error(response: ApiResponse) -> str:
        """Extract a human-readable error message from a gateway response."""
        if isinstance(response.body, dict) and response.body.get("error"):
            return str(response.body["error"])
        return "The request could not be completed. Please try again."

    async def _fetch_projects(self) -> list[dict]:
        """Fetch every project's id and name, for the Add Project picker.

        A failure here is non-fatal: the picker is simply rendered empty
        so the rest of the page still works.

        Returns:
            A list of ``{"id", "name"}`` dicts, or [] on failure.
        """
        url = f"{self._config.apis_gateway_svc}web/projects?value_fields=name"
        try:
            response = await self._rest_client.get(url)
        except Exception:  # pylint: disable=broad-except
            self._logger.warning("Unable to fetch projects")
            return []

        if response.status_code != HTTPStatus.OK:
            self._logger.warning(
                "Unable to fetch projects (status %s)", response.status_code)
            return []

        projects = (response.body or {}).get("projects", [])
        return [{"id": p.get("id"), "name": p.get("name", "")}
                for p in projects if p.get("id") is not None]

    async def _fetch_roles(self) -> list[dict]:
        """Fetch every role's id and name, for the role picker dropdowns.

        A failure here is non-fatal: the dropdowns are simply rendered
        with no options beyond "Unassigned" so the rest of the page still
        works.

        Returns:
            A list of ``{"id", "name"}`` dicts, or [] on failure.
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

        return (response.body or {}).get("roles", [])

    async def _fetch_memberships(self, user_id: str) -> list[dict]:
        """Fetch the user's project memberships.

        A failure here is non-fatal: the Projects tab is simply rendered
        with no rows so the rest of the page still works.

        Returns:
            A list of ``{"project_id", "role_id", "role_name"}`` dicts, or
            [] on failure.
        """
        url = f"{self._config.apis_gateway_svc}web/users/{user_id}/projects"
        try:
            response = await self._rest_client.get(url)
        except Exception:  # pylint: disable=broad-except
            self._logger.warning(
                "Unable to fetch project memberships for %s", user_id)
            return []

        if response.status_code != HTTPStatus.OK:
            self._logger.warning(
                "Unable to fetch project memberships for %s (status %s)",
                user_id, response.status_code)
            return []

        return (response.body or {}).get("memberships", [])

    async def _render(self,
                      user_id: str,
                      form_data: dict,
                      error_msg_str: Optional[str] = None,
                      success_msg_str: Optional[str] = None,
                      active_tab: str = _DEFAULT_ACTIVE_TAB):
        """Render the edit user page, including the Projects tab's data.

        Args:
            user_id: ID of the user being edited (used in the form action).
            form_data: Values used to pre-populate the User/Access tabs.
            error_msg_str: Optional error message to display.
            success_msg_str: Optional confirmation message to display.
            active_tab: Which tab ("tab-user", "tab-access" or
                "tab-projects") should be shown as active on render - so a
                project-membership write lands back on Projects rather
                than always resetting to the first tab.

        Returns:
            The rendered edit user page response.
        """
        all_projects = await self._fetch_projects()
        project_names_by_id = {p["id"]: p["name"] for p in all_projects}

        memberships = await self._fetch_memberships(user_id)
        for membership in memberships:
            project_id = membership.get("project_id")
            membership["project_name"] = project_names_by_id.get(
                project_id, f"Project {project_id}")

        assigned_ids = {m.get("project_id") for m in memberships}
        available_projects = [
            p for p in all_projects if p["id"] not in assigned_ids]

        roles = await self._fetch_roles()

        return await self._render_page(
            pages.PAGE_INSTANCE_ADMIN_MODIFY_USER,
            instance_name=self._metadata_settings.instance_name,
            active_page="administration",
            active_admin_page="admin_page_users_roles",
            user_id=user_id,
            form_data=form_data,
            memberships=memberships,
            roles=roles,
            available_projects=available_projects,
            active_tab=active_tab,
            error_msg_str=error_msg_str,
            success_msg_str=success_msg_str)
