"""
Copyright 2025-2026 Integrated Test Management Suite Development Team

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
from dataclasses import dataclass, field
import logging
from typing import Optional
from weaver_framework.database.sqlite_interface import SqliteInterfaceException
from items.services.items_identity.data_access.role_repository import (
    RoleRepository)
from items.shared.service_state import ServiceState


def _permission_row_to_dict(row: tuple) -> dict:
    """Convert a ``role_permissions`` row tuple to a permission dict.

    Args:
        row: ``(area, can_read, can_add_modify, can_delete)``

    Returns:
        A dict with the same fields, the three flags converted to bool.
    """
    area, can_read, can_add_modify, can_delete = row
    return {
        "area": area,
        "can_read": bool(can_read),
        "can_add_modify": bool(can_add_modify),
        "can_delete": bool(can_delete),
    }


def _permissions_to_rows(permissions: list[dict]) -> list[tuple]:
    """Convert permission dicts (as received from a request body) to the
    ``(area, can_read, can_add_modify, can_delete)`` tuple shape the
    repository expects.

    Args:
        permissions: List of permission dicts, each with ``area``,
            ``can_read``, ``can_add_modify``, ``can_delete``.

    Returns:
        The equivalent list of tuples.
    """
    return [(p["area"], p["can_read"], p["can_add_modify"], p["can_delete"])
            for p in permissions]


def _permissions_are_valid(permissions: list[dict]) -> bool:
    """Validate a permission grid against invariants the JSON schema can't
    express on its own.

    Args:
        permissions: List of permission dicts to validate.

    Returns:
        False if any entry grants Add/Modify without Read (§4.1 of
        user_roles_design.md), or if the same area appears more than once
        (would otherwise violate the ``(role_id, area)`` primary key at
        the database layer with a raw, unhelpful error). True otherwise.
    """
    seen_areas = set()
    for entry in permissions:
        if entry["can_add_modify"] and not entry["can_read"]:
            return False
        if entry["area"] in seen_areas:
            return False
        seen_areas.add(entry["area"])
    return True


@dataclass
class RoleListResult:
    """Outcome of a list-all-roles request.

    Attributes:
        available: False when the service is unavailable.
        roles:     List of ``{"id": ..., "name": ...}`` dicts.
    """
    available: bool = True
    roles: list = field(default_factory=list)


@dataclass
class RoleLookupResult:
    """Outcome of a single-role lookup.

    Attributes:
        available: False when the service is unavailable.
        found:     False when no role exists with the requested id.
        role:      ``{"id", "name", "permissions"}`` dict on success -
                   ``permissions`` is the full per-area grid.
    """
    available: bool = True
    found: bool = True
    role: Optional[dict] = field(default=None)


@dataclass
class RoleCreateResult:
    """Outcome of a create-role request.

    Attributes:
        available: False when the service is unavailable.
        conflict:  True when the role name is already in use.
        invalid:   True when the supplied grid violates the
                   Add/Modify-implies-Read invariant, or repeats an area.
        role_id:   The newly created role's id on success.
    """
    available: bool = True
    conflict: bool = False
    invalid: bool = False
    role_id: Optional[int] = field(default=None)


@dataclass
class RoleUpdateResult:
    """Outcome of an update-role request.

    Attributes:
        available: False when the service is unavailable.
        found:     False when no role exists with the requested id.
        conflict:  True when renaming to a name already in use.
        invalid:   True when the supplied grid violates the
                   Add/Modify-implies-Read invariant, or repeats an area.
        success:   True when the update was applied.
    """
    available: bool = True
    found: bool = True
    conflict: bool = False
    invalid: bool = False
    success: bool = False


@dataclass
class RoleDeleteResult:
    """Outcome of a delete-role request.

    Attributes:
        available: False when the service is unavailable.
        found:     False when no role exists with the requested id.
        success:   True when the role was deleted.
    """
    available: bool = True
    found: bool = True
    success: bool = False


class RoleManagementService:
    """Create, modify, and delete named roles and their permission grids.

    A role is a name plus a per-area Read/Add-Modify/Delete grid
    (§4/§7 of user_roles_design.md). Assigning a role to a project
    membership is a separate concern, handled elsewhere - this service
    only manages role *definitions*.
    """

    def __init__(self,
                 logger: logging.Logger,
                 state: ServiceState,
                 role_repository: RoleRepository) -> None:
        """Initialise the role management service.

        Args:
            logger:          Parent logger.
            state:           Shared service state.
            role_repository: Repository providing role data access.
        """
        self._logger = logger.getChild(__name__)
        self._state: ServiceState = state
        self._repo: RoleRepository = role_repository

    async def get_all_roles(self) -> RoleListResult:
        """Return all roles (name only - not their grids).

        Returns:
            A :class:`RoleListResult`. Database failures are reported as
            unavailable.
        """
        if not self._state.is_available():
            return RoleListResult(available=False)

        try:
            rows = await self._repo.get_all_roles()
        except SqliteInterfaceException as ex:
            self._logger.exception("Database failure listing roles: %s", ex)
            self._state.set_service_degraded("Role list database unavailable")
            return RoleListResult(available=False)

        return RoleListResult(
            roles=[{"id": role_id, "name": name} for role_id, name in rows])

    async def get_role(self, role_id: int) -> RoleLookupResult:
        """Return a single role, including its full permission grid.

        Args:
            role_id: The role's id.

        Returns:
            A :class:`RoleLookupResult`.
        """
        if not self._state.is_available():
            return RoleLookupResult(available=False)

        try:
            row = await self._repo.get_role_by_id(role_id)
            if row is None:
                return RoleLookupResult(found=False)

            permission_rows = await self._repo.get_role_permissions(role_id)

        except SqliteInterfaceException as ex:
            self._logger.exception(
                "Database failure fetching role %d: %s", role_id, ex)
            self._state.set_service_degraded("Role lookup database unavailable")
            return RoleLookupResult(available=False)

        found_id, name = row
        return RoleLookupResult(role={
            "id": found_id,
            "name": name,
            "permissions": [_permission_row_to_dict(r)
                           for r in permission_rows],
        })

    async def create_role(self, name: str,
                          permissions: list[dict]) -> RoleCreateResult:
        """Create a new role with the supplied permission grid.

        Args:
            name: The role's name (must be unique).
            permissions: The role's initial grid - a list of permission
                dicts. May be empty (a role granting nothing yet).

        Returns:
            A :class:`RoleCreateResult`. ``conflict`` is True if the name
            is already in use. ``invalid`` is True if the grid violates
            Add/Modify-implies-Read or repeats an area.
        """
        if not self._state.is_available():
            return RoleCreateResult(available=False)

        if not _permissions_are_valid(permissions):
            return RoleCreateResult(invalid=True)

        try:
            if await self._repo.role_name_exists(name):
                return RoleCreateResult(conflict=True)

            role_id = await self._repo.create_role(
                name, _permissions_to_rows(permissions))

        except SqliteInterfaceException as ex:
            self._logger.exception(
                "Database failure creating role %s: %s", name, ex)
            self._state.set_service_degraded(
                "Role creation database unavailable")
            return RoleCreateResult(available=False)

        return RoleCreateResult(role_id=role_id)

    async def update_role(self,
                          role_id: int,
                          name: Optional[str] = None,
                          permissions: Optional[list[dict]] = None
                          ) -> RoleUpdateResult:
        """Update a role's name and/or replace its permission grid.

        Patch-style: only the fields supplied are changed. ``permissions``,
        when supplied, *replaces* the entire grid - see
        :class:`RoleRepository`'s docstring for why there is no partial
        update.

        Args:
            role_id: The role's id.
            name: New name, or ``None`` to leave unchanged.
            permissions: New complete grid, or ``None`` to leave the
                existing grid unchanged.

        Returns:
            A :class:`RoleUpdateResult`.
        """
        if not self._state.is_available():
            return RoleUpdateResult(available=False)

        if permissions is not None and not _permissions_are_valid(permissions):
            return RoleUpdateResult(invalid=True)

        try:
            row = await self._repo.get_role_by_id(role_id)
            if row is None:
                return RoleUpdateResult(found=False)

            if name is not None and await self._repo.role_name_exists(name):
                _, current_name = row
                if name != current_name:
                    return RoleUpdateResult(conflict=True)

            permission_rows = (
                _permissions_to_rows(permissions)
                if permissions is not None else None)
            await self._repo.update_role(role_id, name, permission_rows)

        except SqliteInterfaceException as ex:
            self._logger.exception(
                "Database failure updating role %d: %s", role_id, ex)
            self._state.set_service_degraded(
                "Role update database unavailable")
            return RoleUpdateResult(available=False)

        return RoleUpdateResult(success=True)

    async def delete_role(self, role_id: int) -> RoleDeleteResult:
        """Delete a role.

        Any project membership holding this role has its role assignment
        cleared (not deleted) - see :meth:`RoleRepository.delete_role`.

        Args:
            role_id: The role's id.

        Returns:
            A :class:`RoleDeleteResult`.
        """
        if not self._state.is_available():
            return RoleDeleteResult(available=False)

        try:
            row = await self._repo.get_role_by_id(role_id)
            if row is None:
                return RoleDeleteResult(found=False)

            await self._repo.delete_role(role_id)

        except SqliteInterfaceException as ex:
            self._logger.exception(
                "Database failure deleting role %d: %s", role_id, ex)
            self._state.set_service_degraded(
                "Role deletion database unavailable")
            return RoleDeleteResult(available=False)

        return RoleDeleteResult(success=True)
