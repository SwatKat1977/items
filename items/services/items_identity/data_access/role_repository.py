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


class RoleRepository:
    """
    Provides persistence operations for named roles and their per-area
    permission grids.

    A role's grid (`role_permissions`) is always replaced as a whole -
    there is no per-area upsert. Callers send the complete grid they want;
    existing rows for the role are deleted and the new set inserted. This
    matches how a checkbox-grid form naturally submits (full state, not a
    diff) and avoids needing separate insert/update/delete logic per area.
    """

    GET_ALL_ROLES_QUERY: str = "SELECT id, name FROM roles ORDER BY name"

    GET_ROLE_BY_ID_QUERY: str = "SELECT id, name FROM roles WHERE id = ?"

    ROLE_NAME_EXISTS_QUERY: str = "SELECT id FROM roles WHERE name = ?"

    INSERT_ROLE_QUERY: str = "INSERT INTO roles (name) VALUES (?)"

    UPDATE_ROLE_NAME_QUERY: str = "UPDATE roles SET name = ? WHERE id = ?"

    DELETE_ROLE_QUERY: str = "DELETE FROM roles WHERE id = ?"

    GET_ROLE_PERMISSIONS_QUERY: str = (
        "SELECT area, can_read, can_add_modify, can_delete "
        "FROM role_permissions WHERE role_id = ? ORDER BY area")

    DELETE_ROLE_PERMISSIONS_QUERY: str = (
        "DELETE FROM role_permissions WHERE role_id = ?")

    INSERT_ROLE_PERMISSION_QUERY: str = (
        "INSERT INTO role_permissions "
        "(role_id, area, can_read, can_add_modify, can_delete) "
        "VALUES (?, ?, ?, ?, ?)")

    def __init__(self,
                 logger: logging.Logger,
                 config: IdentityConfiguration) -> None:
        """Initialise a RoleRepository instance.

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

    async def get_all_roles(self) -> list:
        """Retrieve all roles ordered by name.

        Returns:
            A list of ``(id, name)`` tuples. Empty list if no roles exist.

        Raises:
            SqliteInterfaceException: If the database query fails.
        """
        rows = await self._db.run_query(self.GET_ALL_ROLES_QUERY, ())
        return rows if rows else []

    async def get_role_by_id(self, role_id: int) -> Optional[tuple[int, str]]:
        """Retrieve a single role's ``(id, name)`` by its primary key.

        Args:
            role_id: The role's primary key.

        Returns:
            A ``(id, name)`` tuple if found, otherwise ``None``.

        Raises:
            SqliteInterfaceException: If the database query fails.
        """
        return await self._db.run_query(self.GET_ROLE_BY_ID_QUERY,
                                        (role_id,), fetch_one=True)

    async def role_name_exists(self, name: str) -> bool:
        """Return True if a role with this exact name already exists.

        Args:
            name: Role name to check.

        Returns:
            True if a row in ``roles`` has this name.

        Raises:
            SqliteInterfaceException: If the database query fails.
        """
        row = await self._db.run_query(self.ROLE_NAME_EXISTS_QUERY,
                                       (name,), fetch_one=True)
        return row is not None

    async def get_role_permissions(self, role_id: int) -> list:
        """Retrieve a role's per-area permission grid.

        Args:
            role_id: The role's primary key.

        Returns:
            A list of ``(area, can_read, can_add_modify, can_delete)``
            tuples, one per area the role has any row for. An area with no
            row has no access, same as an explicit all-false row - the
            caller does not need to distinguish the two.

        Raises:
            SqliteInterfaceException: If the database query fails.
        """
        rows = await self._db.run_query(self.GET_ROLE_PERMISSIONS_QUERY,
                                        (role_id,))
        return rows if rows else []

    async def create_role(self, name: str,
                          permissions: list[tuple]) -> int:
        """Insert a new role and its permission grid.

        Args:
            name: The role's name (must be unique - check via
                :meth:`role_name_exists` first; this method does not
                re-check).
            permissions: List of ``(area, can_read, can_add_modify,
                can_delete)`` tuples to insert for the new role. May be
                empty (a role with no granted areas).

        Returns:
            The internal ``id`` of the newly inserted role.

        Raises:
            SqliteInterfaceException: If either insert fails.
        """
        role_id = await self._db.insert_query(self.INSERT_ROLE_QUERY, (name,))
        await self._replace_permissions(role_id, permissions)
        return role_id

    async def update_role(self,
                          role_id: int,
                          name: Optional[str],
                          permissions: Optional[list[tuple]]) -> None:
        """Update a role's name and/or replace its permission grid.

        Patch-style: ``name`` is only changed if not ``None``.
        ``permissions``, when not ``None``, *replaces* the role's entire
        grid - see the class docstring for why there is no partial/upsert
        path.

        Args:
            role_id: The role's primary key.
            name: New name, or ``None`` to leave unchanged.
            permissions: New complete grid, or ``None`` to leave the
                existing grid unchanged.

        Raises:
            SqliteInterfaceException: If any update/insert fails.
        """
        if name is not None:
            await self._db.run_query(self.UPDATE_ROLE_NAME_QUERY,
                                     (name, role_id), commit=True)

        if permissions is not None:
            await self._replace_permissions(role_id, permissions)

    async def delete_role(self, role_id: int) -> None:
        """Delete a role.

        Its `role_permissions` rows cascade-delete at the database level
        (``ON DELETE CASCADE``). Any `project_members` rows pointing at
        this role have their `role_id` cleared to ``NULL`` rather than
        being deleted (``ON DELETE SET NULL``) - those memberships remain,
        just with no role assigned (a valid state, see §4.3 of
        user_roles_design.md).

        Args:
            role_id: The role's primary key.

        Raises:
            SqliteInterfaceException: If the delete fails.
        """
        await self._db.delete_query(self.DELETE_ROLE_QUERY, (role_id,))

    async def _replace_permissions(self, role_id: int,
                                   permissions: list[tuple]) -> None:
        """Delete a role's existing grid and insert a new one.

        Args:
            role_id: The role's primary key.
            permissions: List of ``(area, can_read, can_add_modify,
                can_delete)`` tuples. May be empty.

        Raises:
            SqliteInterfaceException: If the delete or insert fails.
        """
        await self._db.delete_query(self.DELETE_ROLE_PERMISSIONS_QUERY,
                                    (role_id,))
        if permissions:
            await self._db.bulk_insert_query(
                self.INSERT_ROLE_PERMISSION_QUERY,
                [(role_id, area, can_read, can_add_modify, can_delete)
                 for area, can_read, can_add_modify, can_delete
                 in permissions])
