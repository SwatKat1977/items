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
import logging
from typing import Optional
from weaver_framework.database.sqlite_interface import SqliteInterface
from items.services.items_identity.identity_configuration import \
    IdentityConfiguration


class ProjectMemberRepository:
    """
    Provides persistence operations for project membership - which users
    are on which projects, and what role (if any) they hold there.

    v1 is users-only (§7.2 of user_roles_design.md): every row this
    repository writes has ``principal_type = 'user'``, hardcoded rather
    than accepted as a parameter. The schema already supports
    ``principal_type = 'group'`` for when groups arrive, but nothing in
    this v1 API surface needs to expose that yet.

    All methods identify a user by their internal integer id, not their
    UUID - callers resolve the UUID first (see ``UserRepository``), same
    division of responsibility as ``user_auth_details``.
    """

    GET_MEMBERSHIPS_FOR_USER_QUERY: str = (
        "SELECT pm.id, pm.project_id, pm.role_id, r.name "
        "FROM project_members pm "
        "LEFT JOIN roles r ON pm.role_id = r.id "
        "WHERE pm.principal_type = 'user' AND pm.principal_id = ? "
        "ORDER BY pm.project_id")

    GET_MEMBERSHIP_QUERY: str = (
        "SELECT pm.id, pm.role_id, r.name "
        "FROM project_members pm "
        "LEFT JOIN roles r ON pm.role_id = r.id "
        "WHERE pm.principal_type = 'user' AND pm.principal_id = ? "
        "AND pm.project_id = ?")

    INSERT_MEMBERSHIP_QUERY: str = (
        "INSERT INTO project_members "
        "(principal_type, principal_id, project_id, role_id) "
        "VALUES ('user', ?, ?, ?)")

    UPDATE_MEMBERSHIP_ROLE_QUERY: str = (
        "UPDATE project_members SET role_id = ? "
        "WHERE principal_type = 'user' AND principal_id = ? "
        "AND project_id = ?")

    DELETE_MEMBERSHIP_QUERY: str = (
        "DELETE FROM project_members "
        "WHERE principal_type = 'user' AND principal_id = ? "
        "AND project_id = ?")

    def __init__(self,
                 logger: logging.Logger,
                 config: IdentityConfiguration) -> None:
        """Initialise a ProjectMemberRepository instance.

        Args:
            logger: Parent logger used for repository and database logging.
            config: Identity service configuration containing database
                connection settings.
        """
        self._logger: logging.Logger = logger.getChild(__name__)
        self._config: IdentityConfiguration = config

        self._db: SqliteInterface = SqliteInterface(
            self._logger,
            self._config.backend_db_filename)

    async def get_memberships_for_user(self, user_id: int) -> list:
        """Retrieve every project membership held by a user.

        Args:
            user_id: The user's internal primary key.

        Returns:
            A list of ``(id, project_id, role_id, role_name)`` tuples,
            ordered by ``project_id``. ``role_id``/``role_name`` are both
            ``None`` for a membership with no role assigned. Empty list if
            the user has no memberships.

        Raises:
            SqliteInterfaceException: If the database query fails.
        """
        rows = await self._db.run_query(self.GET_MEMBERSHIPS_FOR_USER_QUERY,
                                        (user_id,))
        return rows if rows else []

    async def get_membership(
            self, user_id: int,
            project_id: int) -> Optional[tuple[int, Optional[int],
                                               Optional[str]]]:
        """Retrieve a single membership for a (user, project) pair.

        Args:
            user_id: The user's internal primary key.
            project_id: The project's id (CMS-side, no FK - see class
                docstring on `ProjectMemberRepository`).

        Returns:
            A ``(membership_id, role_id, role_name)`` tuple if the user is
            a member of the project, otherwise ``None``. ``role_id``/
            ``role_name`` are ``None`` if the membership has no role
            assigned.

        Raises:
            SqliteInterfaceException: If the database query fails.
        """
        return await self._db.run_query(self.GET_MEMBERSHIP_QUERY,
                                        (user_id, project_id),
                                        fetch_one=True)

    async def create_membership(self,
                                user_id: int,
                                project_id: int,
                                role_id: Optional[int]) -> int:
        """Insert a new project membership.

        Args:
            user_id: The user's internal primary key.
            project_id: The project's id.
            role_id: The role to assign, or ``None`` for "member, no role
                assigned yet" (§4.3 of user_roles_design.md - a valid
                state, not a placeholder).

        Returns:
            The internal ``id`` of the newly inserted membership row.

        Raises:
            SqliteInterfaceException: If the insert fails - including a
                uniqueness violation if this (user, project) pair already
                has a membership row. Callers should check
                :meth:`get_membership` first for a clean conflict response
                rather than relying on this exception.
        """
        return await self._db.insert_query(
            self.INSERT_MEMBERSHIP_QUERY, (user_id, project_id, role_id))

    async def update_membership_role(self,
                                     user_id: int,
                                     project_id: int,
                                     role_id: Optional[int]) -> None:
        """Change the role assigned to an existing membership.

        Args:
            user_id: The user's internal primary key.
            project_id: The project's id.
            role_id: The new role, or ``None`` to clear back to "member,
                no role assigned".

        Raises:
            SqliteInterfaceException: If the update fails.
        """
        await self._db.run_query(self.UPDATE_MEMBERSHIP_ROLE_QUERY,
                                 (role_id, user_id, project_id),
                                 commit=True)

    async def delete_membership(self, user_id: int, project_id: int) -> None:
        """Remove a project membership entirely.

        Args:
            user_id: The user's internal primary key.
            project_id: The project's id.

        Raises:
            SqliteInterfaceException: If the delete fails.
        """
        await self._db.delete_query(self.DELETE_MEMBERSHIP_QUERY,
                                    (user_id, project_id))
