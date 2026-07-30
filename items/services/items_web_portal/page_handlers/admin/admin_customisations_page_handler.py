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

# Field types accepted by the custom-fields API (must match the gateway's
# add/modify request schema enum).
CASE_FIELD_TYPES: list[str] = [
    "Checkbox",
    "Date",
    "Dropdown",
    "Integer",
    "String",
    "Text",
    "Url (Link)",
    "User",
]

# Ordered column indices for a case-field row as returned by
# GET /web/testcase_custom_fields (see the CMS get_all_fields query).
_COL_ID = 0
_COL_FIELD_NAME = 1
_COL_DESCRIPTION = 2
_COL_SYSTEM_NAME = 3
_COL_FIELD_TYPE = 4
_COL_ENTRY_TYPE = 5
_COL_ENABLED = 6
_COL_POSITION = 7
_COL_IS_REQUIRED = 8
_COL_DEFAULT_VALUE = 9
_COL_APPLIES_TO_ALL = 10
_COL_LINKED_PROJECTS = 11


class AdminCustomisationsPageHandler(PortalPageHandler):
    """Handles requests for the administration customisations page.

    Renders the customisations admin page and provides create, read, update,
    delete and reorder operations for testcase custom (case) fields via the
    gateway ``/web/testcase_custom_fields`` API.
    """

    def __init__(self,
                 logger: logging.Logger,
                 config: Configuration,
                 rest_client: RestClient,
                 metadata: MetadataSettings):
        """Initialize the administration customisations page handler.

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
    async def customisations(self):
        """Render the administration customisations page.

        Returns:
            The rendered customisations page response.
        """
        return await self._render_customisations()

    # ------------------------------------------------------------------
    # Write: case fields
    # ------------------------------------------------------------------

    @require_administrator
    async def case_field_add(self):
        """Create a new case field from the submitted form.

        Returns:
            The re-rendered customisations page, showing an error banner if
            the gateway rejects the request.
        """
        payload = await self._build_field_payload()

        base_url: str = self._config.apis_gateway_svc
        url: str = f"{base_url}web/testcase_custom_fields/"
        response: ApiResponse = await self._rest_client.post(
            url, json_data=payload)

        return await self._render_after_write(response, "add")

    @require_administrator
    async def case_field_modify(self, field_id: int):
        """Update an existing case field from the submitted form.

        System fields may only have their active state and project assignment
        changed. For those, the payload's immutable attributes (name, system
        name, type, description, default value, required) are taken from the
        field's current stored values rather than the form, so they cannot be
        altered from the portal regardless of what is submitted.

        Args:
            field_id: ID of the case field to modify.

        Returns:
            The re-rendered customisations page, showing an error banner if
            the gateway rejects the request.
        """
        current = await self._get_case_field(field_id)

        if current is not None and current["is_system"]:
            payload = await self._build_system_field_payload(current)
        else:
            payload = await self._build_field_payload()

        base_url: str = self._config.apis_gateway_svc
        url: str = f"{base_url}web/testcase_custom_fields/{field_id}"
        response: ApiResponse = await self._rest_client.put(
            url, json_data=payload)

        return await self._render_after_write(response, "modify")

    @require_administrator
    async def case_field_delete(self, field_id: int):
        """Delete a case field.

        Args:
            field_id: ID of the case field to delete.

        Returns:
            The re-rendered customisations page, showing an error banner if
            the gateway rejects the request.
        """
        base_url: str = self._config.apis_gateway_svc
        url: str = f"{base_url}web/testcase_custom_fields/{field_id}"
        response: ApiResponse = await self._rest_client.delete(url)

        return await self._render_after_write(response, "delete")

    @require_administrator
    async def case_field_move(self, field_id: int):
        """Move a case field up or down in the ordered list.

        Args:
            field_id: ID of the case field to move.

        Returns:
            The re-rendered customisations page, showing an error banner if
            the gateway rejects the request.
        """
        form = await request.form
        direction = form.get("direction", "")

        base_url: str = self._config.apis_gateway_svc
        url: str = f"{base_url}web/testcase_custom_fields/{field_id}"
        response: ApiResponse = await self._rest_client.patch(
            url, json_data={"direction": direction})

        return await self._render_after_write(response, "move")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    async def _build_field_payload(self) -> dict:
        """Build a case-field request body from the submitted form.

        Checkboxes are absent from the form when unticked, so their presence
        is treated as ``True``. When the field does not apply to all projects,
        the selected project names are included.

        Returns:
            A dict matching the gateway add/modify request schema.
        """
        form = await request.form

        applies_to_all = form.get("applies_to_all_projects") == "on"
        payload: dict = {
            "field_name": (form.get("field_name") or "").strip(),
            "description": form.get("description") or "",
            "system_name": (form.get("system_name") or "").strip(),
            "field_type": form.get("field_type") or "",
            "enabled": form.get("enabled") == "on",
            "is_required": form.get("is_required") == "on",
            "default_value": form.get("default_value") or "",
            "applies_to_all_projects": applies_to_all,
        }

        if not applies_to_all:
            payload["projects"] = form.getlist("projects")

        return payload

    async def _build_system_field_payload(self, current: dict) -> dict:
        """Build a modify payload for a system field.

        Only the active state and project assignment are taken from the
        submitted form; every other attribute is taken from the field's
        current stored values so it cannot be changed from the portal.

        Args:
            current: The field's current values (from ``_get_case_field``).

        Returns:
            A dict matching the gateway modify request schema.
        """
        form = await request.form

        applies_to_all = form.get("applies_to_all_projects") == "on"
        payload: dict = {
            "field_name": current["field_name"],
            "description": current["description"],
            "system_name": current["system_name"],
            "field_type": current["field_type"],
            "enabled": form.get("enabled") == "on",
            "is_required": current["is_required"],
            "default_value": current["default_value"],
            "applies_to_all_projects": applies_to_all,
        }

        if not applies_to_all:
            payload["projects"] = form.getlist("projects")

        return payload

    async def _get_case_field(self, field_id: int) -> Optional[dict]:
        """Fetch a single case field's current values.

        Args:
            field_id: ID of the field to retrieve.

        Returns:
            The mapped field dict, or None if it could not be retrieved.
        """
        base_url: str = self._config.apis_gateway_svc
        response: ApiResponse = await self._rest_client.get(
            f"{base_url}web/testcase_custom_fields/{field_id}")

        if response.status_code != HTTPStatus.OK or not response.body:
            self._logger.warning(
                "Unable to fetch case field %s (status %s)",
                field_id, response.status_code)
            return None

        return self._row_to_field(response.body)

    async def _render_after_write(self, response: ApiResponse,
                                  action: str):
        """Re-render the page after a write, surfacing any gateway error.

        Args:
            response: The gateway response for the write operation.
            action: Short action name used in the error message ("add",
                "modify", "delete", "move").

        Returns:
            The re-rendered customisations page.
        """
        error_message: Optional[str] = None

        if response.status_code != HTTPStatus.OK:
            error_message = self._extract_error(response)
            self._logger.warning(
                "Case field %s failed (status %s): %s",
                action, response.status_code, error_message)

        return await self._render_customisations(error_message=error_message)

    @staticmethod
    def _extract_error(response: ApiResponse) -> str:
        """Extract a human-readable error message from a gateway response."""
        if isinstance(response.body, dict) and response.body.get("error"):
            return str(response.body["error"])
        return "The request could not be completed. Please try again."

    async def _render_customisations(self,
                                     error_message: Optional[str] = None):
        """Fetch case fields and projects, then render the page.

        Args:
            error_message: Optional error banner to display on the page.

        Returns:
            The rendered customisations page, or the internal error page if
            the case fields cannot be retrieved.
        """
        base_url: str = self._config.apis_gateway_svc

        response: ApiResponse = await self._rest_client.get(
            f"{base_url}web/testcase_custom_fields/")

        if response.status_code != HTTPStatus.OK:
            self._logger.critical(
                "Gateway svc request invalid - Reason: %s",
                response.exception_msg)
            return await self._render_page(pages.TEMPLATE_INTERNAL_ERROR_PAGE)

        case_fields = [self._row_to_field(row) for row in (response.body or [])]

        return await self._render_page(
            pages.PAGE_INSTANCE_ADMIN_CUSTOMISATIONS,
            instance_name=self._metadata_settings.instance_name,
            active_page="administration",
            active_admin_page="admin_page_customisations",
            case_fields=case_fields,
            case_field_types=CASE_FIELD_TYPES,
            projects=await self._fetch_project_names(),
            error_message=error_message)

    async def _fetch_project_names(self) -> list[str]:
        """Fetch the list of project names for the per-project selector.

        A failure here is non-fatal: the selector is simply rendered empty so
        the rest of the page still works.

        Returns:
            A sorted list of project names, or an empty list on failure.
        """
        base_url: str = self._config.apis_gateway_svc
        try:
            response: ApiResponse = await self._rest_client.get(
                f"{base_url}web/projects?value_fields=name")
        except Exception:  # pylint: disable=broad-except
            self._logger.warning("Unable to fetch projects for selector")
            return []

        if response.status_code != HTTPStatus.OK:
            self._logger.warning(
                "Unable to fetch projects for selector (status %s)",
                response.status_code)
            return []

        projects = (response.body or {}).get("projects", [])
        names = [p.get("name") for p in projects if p.get("name")]
        return sorted(names)

    @staticmethod
    def _row_to_field(row: list) -> dict:
        """Map a positional case-field row from the API to a named dict.

        Args:
            row: A single row as returned by the list endpoint.

        Returns:
            A dict with named, template-friendly keys.
        """
        linked = row[_COL_LINKED_PROJECTS]
        project_names: list[str] = []
        if linked:
            # Encoded as "id:name,id:name" by the CMS query (GROUP_CONCAT
            # with no escaping). This is inherently ambiguous if a project
            # name contains a comma - there is no way to tell, from the
            # string alone, whether "1:A,B,2:C" means projects "A,B" and
            # "C", or "A" and "B,2:C". Fixing that needs CMS to return
            # structured data instead of a flattened string; not attempted
            # here.
            for entry in str(linked).split(","):
                _, _, name = entry.partition(":")
                if name:
                    project_names.append(name)

        return {
            "id": row[_COL_ID],
            "field_name": row[_COL_FIELD_NAME],
            "description": row[_COL_DESCRIPTION] or "",
            "system_name": row[_COL_SYSTEM_NAME],
            "field_type": row[_COL_FIELD_TYPE],
            "entry_type": row[_COL_ENTRY_TYPE],
            "is_system": str(row[_COL_ENTRY_TYPE]).lower() == "system",
            "enabled": bool(row[_COL_ENABLED]),
            "position": row[_COL_POSITION],
            "is_required": bool(row[_COL_IS_REQUIRED]),
            "default_value": row[_COL_DEFAULT_VALUE] or "",
            "applies_to_all_projects": bool(row[_COL_APPLIES_TO_ALL]),
            "linked_projects": project_names,
            # JSON-encoded for the edit modal's data-projects attribute -
            # a comma-joined string would misparse any project name that
            # itself contains a comma.
            "linked_projects_json": json.dumps(project_names),
        }
