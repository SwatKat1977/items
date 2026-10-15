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
from items.services.items_identity.data_access.project_member_repository import (
    ProjectMemberRepository)
from items.services.items_identity.data_access.role_repository import (
    RoleRepository)
from items.services.items_identity.data_access.user_repository import (
    UserRepository)
from items.shared.account_status import AccountStatus
from items.shared.permission_area import PermissionArea
from items.shared.service_state import ServiceState


def _area_grant(can_read: bool, can_add_modify: bool,
                can_delete: bool) -> dict:
    """Build one area's grant in the shape the permissions endpoint returns.

    Args:
        can_read: Whether Read is granted.
        can_add_modify: Whether Add/Modify is granted.
        can_delete: Whether Delete is granted.

    Returns:
        ``{"read", "add_modify", "delete"}`` with the three flags as bools.
    """
    return {
        "read": bool(can_read),
        "add_modify": bool(can_add_modify),
        "delete": bool(can_delete),
    }


def _all_areas(granted: bool) -> dict:
    """Build a grid that grants (or denies) everything in every area.

    Args:
        granted: True to grant every flag, False to deny every flag.

    Returns:
        A dict keyed by every :class:`PermissionArea` value.
    """
    return {area.value: _area_grant(granted, granted, granted)
            for area in PermissionArea}


def _membership_row_to_dict(row: tuple) -> dict:
    """Convert a membership row tuple to a dict.

    Args:
        row: ``(id, project_id, role_id, role_name)``

    Returns:
        A dict with ``project_id``, ``role_id``, ``role_name``. The latter
        two are ``None`` when no role is assigned - callers presenting
        this to a user (e.g. the web portal) map that to a display label
        such as "Unassigned" themselves; this service returns the raw,
        undecorated data.
    """
    _, project_id, role_id, role_name = row
    return {
        "project_id": project_id,
        "role_id": role_id,
        "role_name": role_name,
    }


@dataclass
class MembershipListResult:
    """Outcome of a list-a-user's-memberships request.

    Attributes:
        available:    False when the service is unavailable.
        found:        False when no user exists with the requested UUID.
        memberships:  List of ``{"project_id", "role_id", "role_name"}``
                      dicts on success.
    """
    available: bool = True
    found: bool = True
    memberships: list = field(default_factory=list)


@dataclass
class EffectivePermissionsResult:
    """Outcome of an effective-permissions request.

    Attributes:
        available: False when the service is unavailable.
        found:     False when no user exists with the requested UUID.
        areas:     ``{area: {"read", "add_modify", "delete"}}`` for every
                   :class:`PermissionArea` on success. Every flag is False
                   for a user with no access, which is a normal outcome and
                   not an error.
    """
    available: bool = True
    found: bool = True
    areas: dict = field(default_factory=dict)


@dataclass
class MembershipCreateResult:
    """Outcome of an add-project-membership request.

    Attributes:
        available:      False when the service is unavailable.
        found:          False when no user exists with the requested UUID.
        role_not_found: True when a supplied ``role_id`` doesn't exist.
        conflict:       True when the user is already a member of this
                        project.
        success:        True when the membership was created.
    """
    available: bool = True
    found: bool = True
    role_not_found: bool = False
    conflict: bool = False
    success: bool = False


@dataclass
class MembershipUpdateResult:
    """Outcome of a change-membership-role request.

    Attributes:
        available:           False when the service is unavailable.
        found:                False when no user exists with the requested
                              UUID.
        membership_not_found: True when the user is not a member of this
                              project.
        role_not_found:       True when a supplied ``role_id`` doesn't
                              exist.
        success:              True when the role was updated.
    """
    available: bool = True
    found: bool = True
    membership_not_found: bool = False
    role_not_found: bool = False
    success: bool = False


@dataclass
class MembershipDeleteResult:
    """Outcome of a remove-project-membership request.

    Attributes:
        available:            False when the service is unavailable.
        found:                False when no user exists with the requested
                              UUID.
        membership_not_found: True when the user is not a member of this
                              project.
        success:              True when the membership was removed.
    """
    available: bool = True
    found: bool = True
    membership_not_found: bool = False
    success: bool = False


class ProjectMembershipService:
    """Manage which projects a user belongs to, and their role on each.

    Distinct from :class:`RoleManagementService`, which manages role
    *definitions* - this service only manages the assignment of an
    existing role to a (user, project) membership.

    All public-facing methods identify users by UUID, resolved to the
    internal integer id before touching :class:`ProjectMemberRepository` -
    same convention as :class:`UserManagementService`.
    """

    def __init__(self,
                 logger: logging.Logger,
                 state: ServiceState,
                 member_repository: ProjectMemberRepository,
                 user_repository: UserRepository,
                 role_repository: RoleRepository) -> None:
        """Initialise the project membership service.

        Args:
            logger:            Parent logger.
            state:              Shared service state.
            member_repository: Repository providing membership data access.
            user_repository:   Repository used to resolve a UUID to the
                               user's internal id.
            role_repository:   Repository used to validate a supplied
                               ``role_id`` actually exists before writing
                               it - without this check an invalid
                               ``role_id`` would surface as a raw foreign
                               key failure instead of a clean error.
        """
        self._logger = logger.getChild(__name__)
        self._state: ServiceState = state
        self._repo: ProjectMemberRepository = member_repository
        self._user_repo: UserRepository = user_repository
        self._role_repo: RoleRepository = role_repository

    async def _resolve_user_id(self, user_uuid: str) -> Optional[int]:
        """Resolve a user's UUID to their internal id.

        Args:
            user_uuid: The user's public UUID string.

        Returns:
            The internal id if found, otherwise ``None``.

        Raises:
            SqliteInterfaceException: If the database query fails.
        """
        row = await self._user_repo.get_user_by_uuid(user_uuid)
        return row[0] if row else None

    async def get_memberships(self, user_uuid: str) -> MembershipListResult:
        """Return every project membership held by a user.

        Args:
            user_uuid: The user's public UUID string.

        Returns:
            A :class:`MembershipListResult`.
        """
        if not self._state.is_available():
            return MembershipListResult(available=False)

        try:
            user_id = await self._resolve_user_id(user_uuid)
            if user_id is None:
                return MembershipListResult(found=False)

            rows = await self._repo.get_memberships_for_user(user_id)

        except SqliteInterfaceException as ex:
            self._logger.exception(
                "Database failure listing memberships for user %s: %s",
                user_uuid, ex)
            self._state.set_service_degraded(
                "Membership list database unavailable")
            return MembershipListResult(available=False)

        return MembershipListResult(
            memberships=[_membership_row_to_dict(r) for r in rows])

    async def get_effective_permissions(
            self, user_uuid: str,
            project_id: int) -> EffectivePermissionsResult:
        """Resolve what a user may do in a project, per area.

        Implements §8 of user_roles_design.md: a disabled account gets
        nothing, an administrator gets everything, otherwise the result is
        the union of the grids of the roles the user holds on the project -
        nothing if they are not a member, or a member with no role.

        Args:
            user_uuid:  The user's public UUID string.
            project_id: The project's id.

        Returns:
            An :class:`EffectivePermissionsResult` whose ``areas`` covers
            every area, so callers never need to guess at a missing key.
        """
        if not self._state.is_available():
            return EffectivePermissionsResult(available=False)

        try:
            user = await self._user_repo.get_user_by_uuid(user_uuid)
            if user is None:
                return EffectivePermissionsResult(found=False)

            user_id, account_status, is_administrator = (
                user[0], user[5], user[7])

            if account_status != AccountStatus.ACTIVE.value:
                return EffectivePermissionsResult(areas=_all_areas(False))

            if is_administrator:
                return EffectivePermissionsResult(areas=_all_areas(True))

            rows = await self._repo.get_effective_permissions(
                user_id, project_id)

        except SqliteInterfaceException as ex:
            self._logger.exception(
                "Database failure resolving permissions for user %s on "
                "project %d: %s", user_uuid, project_id, ex)
            self._state.set_service_degraded(
                "Permission lookup database unavailable")
            return EffectivePermissionsResult(available=False)

        areas = _all_areas(False)
        for area, can_read, can_add_modify, can_delete in rows:
            # A row for an area this version doesn't know about is ignored,
            # so the response always has exactly the known set of areas.
            if area in areas:
                areas[area] = _area_grant(can_read, can_add_modify,
                                          can_delete)

        return EffectivePermissionsResult(areas=areas)

    async def add_membership(self,
                             user_uuid: str,
                             project_id: int,
                             role_id: Optional[int] = None
                             ) -> MembershipCreateResult:
        """Add a user to a project, optionally assigning a role.

        Args:
            user_uuid:  The user's public UUID string.
            project_id: The project's id.
            role_id:    The role to assign, or ``None`` for "member, no
                       role assigned yet" (a valid state - see §4.3 of
                       user_roles_design.md).

        Returns:
            A :class:`MembershipCreateResult`. ``conflict`` is True if the
            user is already a member of this project. ``role_not_found``
            is True if a supplied ``role_id`` doesn't exist.
        """
        if not self._state.is_available():
            return MembershipCreateResult(available=False)

        try:
            user_id = await self._resolve_user_id(user_uuid)
            if user_id is None:
                return MembershipCreateResult(found=False)

            if role_id is not None:
                if await self._role_repo.get_role_by_id(role_id) is None:
                    return MembershipCreateResult(role_not_found=True)

            if await self._repo.get_membership(user_id, project_id) is not None:
                return MembershipCreateResult(conflict=True)

            await self._repo.create_membership(user_id, project_id, role_id)

        except SqliteInterfaceException as ex:
            self._logger.exception(
                "Database failure adding user %s to project %d: %s",
                user_uuid, project_id, ex)
            self._state.set_service_degraded(
                "Membership creation database unavailable")
            return MembershipCreateResult(available=False)

        return MembershipCreateResult(success=True)

    async def update_membership_role(self,
                                     user_uuid: str,
                                     project_id: int,
                                     role_id: Optional[int]
                                     ) -> MembershipUpdateResult:
        """Change (or clear) the role on an existing membership.

        Args:
            user_uuid:  The user's public UUID string.
            project_id: The project's id.
            role_id:    The new role, or ``None`` to clear back to
                       "member, no role assigned".

        Returns:
            A :class:`MembershipUpdateResult`. ``membership_not_found`` is
            True if the user is not a member of this project.
            ``role_not_found`` is True if a supplied ``role_id`` doesn't
            exist.
        """
        if not self._state.is_available():
            return MembershipUpdateResult(available=False)

        try:
            user_id = await self._resolve_user_id(user_uuid)
            if user_id is None:
                return MembershipUpdateResult(found=False)

            if role_id is not None:
                if await self._role_repo.get_role_by_id(role_id) is None:
                    return MembershipUpdateResult(role_not_found=True)

            if await self._repo.get_membership(user_id, project_id) is None:
                return MembershipUpdateResult(membership_not_found=True)

            await self._repo.update_membership_role(
                user_id, project_id, role_id)

        except SqliteInterfaceException as ex:
            self._logger.exception(
                "Database failure updating membership role for user %s "
                "on project %d: %s", user_uuid, project_id, ex)
            self._state.set_service_degraded(
                "Membership update database unavailable")
            return MembershipUpdateResult(available=False)

        return MembershipUpdateResult(success=True)

    async def remove_membership(self,
                                user_uuid: str,
                                project_id: int) -> MembershipDeleteResult:
        """Remove a user's membership of a project entirely.

        Args:
            user_uuid:  The user's public UUID string.
            project_id: The project's id.

        Returns:
            A :class:`MembershipDeleteResult`. ``membership_not_found`` is
            True if the user is not a member of this project.
        """
        if not self._state.is_available():
            return MembershipDeleteResult(available=False)

        try:
            user_id = await self._resolve_user_id(user_uuid)
            if user_id is None:
                return MembershipDeleteResult(found=False)

            if await self._repo.get_membership(user_id, project_id) is None:
                return MembershipDeleteResult(membership_not_found=True)

            await self._repo.delete_membership(user_id, project_id)

        except SqliteInterfaceException as ex:
            self._logger.exception(
                "Database failure removing user %s from project %d: %s",
                user_uuid, project_id, ex)
            self._state.set_service_degraded(
                "Membership deletion database unavailable")
            return MembershipDeleteResult(available=False)

        return MembershipDeleteResult(success=True)
