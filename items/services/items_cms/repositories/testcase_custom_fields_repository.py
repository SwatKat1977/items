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
import enum
import logging
from typing import Optional
from weaver_framework.database.sqlite_interface import SqliteInterface
from items.services.items_cms.cms_configuration import CMSConfiguration
import items.services.items_cms.cms_db_tables as cms_tables


class CustomFieldMoveDirection(enum.Enum):
    """Direction in which a custom field can be moved in the ordered list."""
    UP = 0
    DOWN = 1


class TestcaseCustomFieldsRepository:
    """
    Persistence operations for testcase custom field data.

    Encapsulates all database access for the testcase custom fields domain.
    Raises SqliteInterfaceException on database failures; callers are
    responsible for handling those exceptions and updating service state
    accordingly.
    """

    def __init__(self,
                 logger: logging.Logger,
                 config: CMSConfiguration) -> None:
        self._logger = logger.getChild(__name__)
        self._db = SqliteInterface(self._logger, config.backend_db_filename)

    async def custom_field_name_exists(self, field_name: str,
                                        exclude_id: Optional[int] = None
                                        ) -> bool:
        """Return True if a custom field with the given name already exists.

        Case-insensitive match. Pass ``exclude_id`` when updating an existing
        field so the field's own current name does not trigger a false conflict.

        Args:
            field_name:  Display name to check.
            exclude_id:  ID of the field being updated (excluded from check).

        Raises:
            SqliteInterfaceException: If the database query fails.
        """
        if exclude_id is not None:
            query = (
                f"SELECT 1 FROM {cms_tables.TC_CUSTOM_FIELDS} "
                "WHERE LOWER(field_name) = LOWER(?) AND id != ? LIMIT 1"
            )
            row = await self._db.run_query(query, (field_name, exclude_id),
                                           fetch_one=True)
        else:
            query = (
                f"SELECT 1 FROM {cms_tables.TC_CUSTOM_FIELDS} "
                "WHERE LOWER(field_name) = LOWER(?) LIMIT 1"
            )
            row = await self._db.run_query(query, (field_name,),
                                           fetch_one=True)
        return bool(row)

    async def system_name_exists(self, system_name: str,
                                  exclude_id: Optional[int] = None) -> bool:
        """Return True if a custom field with the given system name exists.

        Case-insensitive match. Pass ``exclude_id`` when updating an existing
        field so the field's own current system name does not trigger a false
        conflict.

        Args:
            system_name: Internal system name to check.
            exclude_id:  ID of the field being updated (excluded from check).

        Raises:
            SqliteInterfaceException: If the database query fails.
        """
        if exclude_id is not None:
            query = (
                f"SELECT 1 FROM {cms_tables.TC_CUSTOM_FIELDS} "
                "WHERE LOWER(system_name) = LOWER(?) AND id != ? LIMIT 1"
            )
            row = await self._db.run_query(query, (system_name, exclude_id),
                                           fetch_one=True)
        else:
            query = (
                f"SELECT 1 FROM {cms_tables.TC_CUSTOM_FIELDS} "
                "WHERE LOWER(system_name) = LOWER(?) LIMIT 1"
            )
            row = await self._db.run_query(query, (system_name,),
                                           fetch_one=True)
        return bool(row)

    async def add_custom_field(self,
                               field_name: str,
                               description: str,
                               system_name: str,
                               field_type: str,
                               enabled: bool,
                               is_required: bool,
                               default_value: str,
                               applies_to_all_projects: bool) -> Optional[int]:
        """Insert a new custom field and return its ID.

        Assigns the next available position automatically.

        Args:
            field_name:              Display name of the field.
            description:             Human-readable description.
            system_name:             Internal identifier (lowercase/underscores).
            field_type:              Type name (must exist in TC_CUSTOM_FIELD_TYPES).
            enabled:                 Whether the field is active.
            is_required:             Whether the field must be filled in.
            default_value:           Default value (may be empty string).
            applies_to_all_projects: If True, the field applies to all projects.

        Returns:
            The ID of the newly inserted row, or None if ``field_type`` is
            not found in the field types table.

        Raises:
            SqliteInterfaceException: If a database query fails.
        """
        # pylint: disable=too-many-arguments, too-many-positional-arguments

        field_type_info = await self._get_field_type_info(field_type)
        if field_type_info is None:
            return None

        type_id, _, _ = field_type_info
        new_position = (await self._get_max_position()) + 1

        query = (
            f"INSERT INTO {cms_tables.TC_CUSTOM_FIELDS}("
            "field_name, description, system_name, field_type_id, "
            "entry_type, enabled, position, is_required, "
            "default_value, applies_to_all_projects) "
            "VALUES(?,?,?,?,?,?,?,?,?,?)"
        )
        values = (
            field_name, description, system_name, type_id,
            "user", enabled, new_position, is_required,
            default_value, applies_to_all_projects,
        )
        return await self._db.insert_query(query, values)

    async def resolve_project_names(
            self,
            project_names: list[str]) -> Optional[list[int]]:
        """Look up project IDs for a list of project names.

        Used to validate project names before any writes are committed.

        Args:
            project_names: Project display names to resolve.

        Returns:
            An ordered list of project IDs if all names are found, or
            None if any name is not found in the database.

        Raises:
            SqliteInterfaceException: If a database query fails.
        """
        project_ids = []
        query = f"SELECT id FROM {cms_tables.PRJ_PROJECTS} WHERE name = ?"
        for name in project_names:
            row = await self._db.run_query(query, (name,), fetch_one=True)
            if not row:
                self._logger.warning("Project name '%s' not found", name)
                return None
            project_ids.append(int(row[0]))
        return project_ids

    async def assign_custom_field_to_projects(
            self,
            field_id: int,
            project_ids: list[int]) -> None:
        """Link a custom field to one or more projects by project ID.

        Caller is responsible for ensuring all IDs are valid before calling
        (use ``resolve_project_names`` to pre-validate).

        Args:
            field_id:    ID of the custom field to assign.
            project_ids: Pre-resolved list of project IDs to link to.

        Raises:
            SqliteInterfaceException: If a database query fails.
        """
        insert_query = (
            f"INSERT INTO {cms_tables.TC_CUSTOM_FIELD_PROJECTS}"
            "(field_id, project_id) VALUES (?, ?)"
        )
        insert_values = [(field_id, pid) for pid in project_ids]
        await self._db.bulk_insert_query(insert_query, insert_values)

    async def move_custom_field(
            self,
            field_id: int,
            direction: CustomFieldMoveDirection) -> Optional[bool]:
        """Swap a custom field with its neighbour in the ordered list.

        Args:
            field_id:  ID of the field to move.
            direction: UP to decrease position, DOWN to increase it.

        Returns:
            True if the swap succeeded, False if the field was not found
            or is already at the boundary, or None on a database error.

        Raises:
            SqliteInterfaceException: If a database query fails.
        """
        pos_query = (
            f"SELECT position FROM {cms_tables.TC_CUSTOM_FIELDS} WHERE id = ?"
        )
        row = await self._db.run_query(pos_query, (field_id,), fetch_one=True)
        if not row:
            return False

        current_position = int(row[0])
        target_position = (
            current_position - 1
            if direction == CustomFieldMoveDirection.UP
            else current_position + 1
        )

        total = await self._count_custom_fields()
        if target_position < 1 or target_position > total:
            return None  # field exists but is already at the boundary

        target_id = await self._get_id_at_position(target_position)
        if target_id is None or target_id == 0:
            return False

        update_query = f"""
            UPDATE {cms_tables.TC_CUSTOM_FIELDS}
            SET position = CASE
                WHEN id = ? THEN ?
                WHEN id = ? THEN ?
            END
            WHERE id IN (?, ?)
        """
        await self._db.run_query(
            update_query,
            (field_id, target_position, target_id, current_position,
             field_id, target_id),
            commit=True)
        return True

    async def get_custom_field(self, field_id: int) -> Optional[tuple]:
        """Retrieve full details for a single custom field by ID.

        Args:
            field_id: Primary key of the custom field.

        Returns:
            A row tuple if found, or None if no field has that ID.

        Raises:
            SqliteInterfaceException: If the database query fails.
        """
        query = f"""
            SELECT
                cf.id,
                cf.field_name,
                cf.description,
                cf.system_name,
                ft.name AS field_type_name,
                cf.entry_type,
                cf.enabled,
                cf.position,
                cf.is_required,
                cf.default_value,
                cf.applies_to_all_projects,
                CASE
                    WHEN cf.applies_to_all_projects = 0 THEN
                         GROUP_CONCAT(p.id || ':' || p.name)
                    ELSE NULL
                END AS linked_projects
            FROM {cms_tables.TC_CUSTOM_FIELDS} AS cf
            LEFT JOIN {cms_tables.TC_CUSTOM_FIELD_TYPES} AS ft
                ON cf.field_type_id = ft.id
            LEFT JOIN {cms_tables.TC_CUSTOM_FIELD_PROJECTS} AS cfp
                ON cf.id = cfp.field_id
            LEFT JOIN {cms_tables.PRJ_PROJECTS} AS p
                ON cfp.project_id = p.id
            WHERE cf.id = ?
            GROUP BY cf.id
        """
        row = await self._db.run_query(query, (field_id,), fetch_one=True)
        return row if row else None

    async def get_all_fields(self) -> Optional[list]:
        """Retrieve all custom fields with their type and project assignments.

        Returns:
            A list of row tuples (possibly empty), or None on DB error.

        Raises:
            SqliteInterfaceException: If the database query fails.
        """
        query = f"""
            SELECT
                cf.id,
                cf.field_name,
                cf.description,
                cf.system_name,
                ft.name AS field_type_name,
                cf.entry_type,
                cf.enabled,
                cf.position,
                cf.is_required,
                cf.default_value,
                cf.applies_to_all_projects,
                CASE
                    WHEN cf.applies_to_all_projects = 0 THEN
                         GROUP_CONCAT(p.id || ':' || p.name)
                    ELSE NULL
                END AS linked_projects
            FROM {cms_tables.TC_CUSTOM_FIELDS} AS cf
            LEFT JOIN {cms_tables.TC_CUSTOM_FIELD_TYPES} AS ft
                ON cf.field_type_id = ft.id
            LEFT JOIN {cms_tables.TC_CUSTOM_FIELD_PROJECTS} AS cfp
                ON cf.id = cfp.field_id
            LEFT JOIN {cms_tables.PRJ_PROJECTS} AS p
                ON cfp.project_id = p.id
            GROUP BY cf.id
            ORDER BY cf.position
        """
        rows = await self._db.run_query(query, ())
        return rows or []

    async def get_fields_for_project(self, project_id: int) -> Optional[list]:
        """Retrieve all custom fields applicable to a specific project.

        Returns fields that either apply to all projects or are explicitly
        linked to the given project.

        Args:
            project_id: ID of the project to filter by.

        Returns:
            A list of row tuples (possibly empty).

        Raises:
            SqliteInterfaceException: If the database query fails.
        """
        query = f"""
            SELECT
                cf.id,
                cf.field_name,
                cf.description,
                cf.system_name,
                ft.name AS field_type_name,
                cf.entry_type,
                cf.enabled,
                cf.position,
                cf.is_required,
                cf.default_value,
                cf.applies_to_all_projects
            FROM {cms_tables.TC_CUSTOM_FIELDS} AS cf
            LEFT JOIN {cms_tables.TC_CUSTOM_FIELD_PROJECTS} AS cfp
                ON cf.id = cfp.field_id AND cfp.project_id = ?
            LEFT JOIN {cms_tables.TC_CUSTOM_FIELD_TYPES} AS ft
                ON cf.field_type_id = ft.id
            WHERE cf.applies_to_all_projects = 1 OR cfp.project_id IS NOT NULL
        """
        rows = await self._db.run_query(query, (project_id,))
        return rows or []

    async def update_custom_field(self,
                                  field_id: int,
                                  field_name: str,
                                  description: str,
                                  system_name: str,
                                  field_type: str,
                                  enabled: bool,
                                  is_required: bool,
                                  default_value: str,
                                  applies_to_all_projects: bool,
                                  project_ids: list[int]) -> Optional[bool]:
        """Update an existing custom field.

        If ``field_type`` changes, any type-specific option rows are cleared
        before the new type is applied. Project associations are replaced in
        full: all existing links are deleted then the new set is inserted.

        Args:
            field_id:                ID of the field to update.
            field_name:              New display name.
            description:             New description.
            system_name:             New internal identifier.
            field_type:              New type name (must exist in types table).
            enabled:                 Whether the field should be active.
            is_required:             Whether the field must be filled in.
            default_value:           New default value (may be empty string).
            applies_to_all_projects: If True, clears per-project links.
            project_ids:             Pre-resolved project IDs to link to.

        Returns:
            True on success, False if no field with ``field_id`` exists, or
            None if ``field_type`` is not found in the types table.

        Raises:
            SqliteInterfaceException: If any database operation fails.
        """
        # pylint: disable=too-many-arguments, too-many-positional-arguments
        # pylint: disable=(too-many-locals

        row = await self._db.run_query(
            f"SELECT field_type_id, entry_type FROM {cms_tables.TC_CUSTOM_FIELDS} "
            "WHERE id = ?",
            (field_id,), fetch_one=True)
        if not row:
            return False

        current_type_id, entry_type = int(row[0]), row[1]
        if entry_type == "system":
            return None

        field_type_info = await self._get_field_type_info(field_type)
        if field_type_info is None:
            return None

        new_type_id, _, _ = field_type_info

        if new_type_id != current_type_id:
            await self._db.run_query(
                f"DELETE FROM {cms_tables.TC_CUSTOM_FIELD_OPTION_VALUES} "
                "WHERE field_id = ?",
                (field_id,), commit=True)
            await self._db.run_query(
                f"DELETE FROM {cms_tables.TC_CUSTOM_FIELD_TYPE_OPTION_VALUES} "
                "WHERE case_field_id = ?",
                (field_id,), commit=True)
            await self._db.run_query(
                f"DELETE FROM {cms_tables.TC_CUSTOM_FIELD_TYPE_OPTIONS} "
                "WHERE field_id = ?",
                (field_id,), commit=True)

        await self._db.run_query(
            f"UPDATE {cms_tables.TC_CUSTOM_FIELDS} "
            "SET field_name = ?, description = ?, system_name = ?, "
            "field_type_id = ?, enabled = ?, is_required = ?, "
            "default_value = ?, applies_to_all_projects = ? "
            "WHERE id = ?",
            (field_name, description, system_name, new_type_id,
             enabled, is_required, default_value, applies_to_all_projects,
             field_id),
            commit=True)

        await self._db.run_query(
            f"DELETE FROM {cms_tables.TC_CUSTOM_FIELD_PROJECTS} "
            "WHERE field_id = ?",
            (field_id,), commit=True)

        if project_ids:
            insert_query = (
                f"INSERT INTO {cms_tables.TC_CUSTOM_FIELD_PROJECTS}"
                "(field_id, project_id) VALUES (?, ?)"
            )
            insert_values = [(field_id, pid) for pid in project_ids]
            await self._db.bulk_insert_query(insert_query, insert_values)

        return True

    async def delete_custom_field(self, field_id: int) -> Optional[bool]:
        """Permanently remove a custom field and all dependent rows.

        System fields (``entry_type = 'system'``) cannot be deleted.
        Deletes in dependency order before removing the field record itself.
        ``TC_CUSTOM_FIELD_OPTION_VALUES`` is omitted because it carries an
        ``ON DELETE CASCADE`` on ``field_id`` and is removed automatically.
        Positions of the remaining fields are compacted after deletion.

        Args:
            field_id: ID of the field to delete.

        Returns:
            True on success, False if no field with that ID exists, or None
            if the field has ``entry_type = 'system'`` and cannot be deleted.

        Raises:
            SqliteInterfaceException: If any database operation fails.
        """
        pos_query = (
            f"SELECT position, entry_type FROM {cms_tables.TC_CUSTOM_FIELDS} "
            "WHERE id = ?"
        )
        row = await self._db.run_query(pos_query, (field_id,), fetch_one=True)
        if not row:
            return False

        position, entry_type = int(row[0]), row[1]
        if entry_type == "system":
            return None

        await self._db.run_query(
            f"DELETE FROM {cms_tables.TC_CUSTOM_FIELD_TYPE_OPTION_VALUES} "
            "WHERE case_field_id = ?",
            (field_id,), commit=True)

        await self._db.run_query(
            f"DELETE FROM {cms_tables.TC_CUSTOM_FIELD_TYPE_OPTIONS} "
            "WHERE field_id = ?",
            (field_id,), commit=True)

        await self._db.run_query(
            f"DELETE FROM {cms_tables.TC_CUSTOM_FIELD_PROJECTS} "
            "WHERE field_id = ?",
            (field_id,), commit=True)

        await self._db.run_query(
            f"DELETE FROM {cms_tables.TC_CUSTOM_FIELDS} WHERE id = ?",
            (field_id,), commit=True)

        await self._db.run_query(
            f"UPDATE {cms_tables.TC_CUSTOM_FIELDS} "
            "SET position = position - 1 WHERE position > ?",
            (position,), commit=True)

        return True

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    async def _count_custom_fields(self) -> int:
        """Return the total number of custom fields.

        Raises:
            SqliteInterfaceException: If the database query fails.
        """
        query = f"SELECT COUNT(*) FROM {cms_tables.TC_CUSTOM_FIELDS}"
        row = await self._db.run_query(query, (), fetch_one=True)
        return int(row[0])

    async def _get_max_position(self) -> int:
        """Return the highest position value, or 0 if the table is empty.

        Raises:
            SqliteInterfaceException: If the database query fails.
        """
        query = f"SELECT MAX(position) FROM {cms_tables.TC_CUSTOM_FIELDS}"
        row = await self._db.run_query(query, (), fetch_one=True)
        return 0 if (row is None or row[0] is None) else int(row[0])

    async def _get_id_at_position(self, position: int) -> Optional[int]:
        """Return the ID of the field at the given position, or 0 if none.

        Raises:
            SqliteInterfaceException: If the database query fails.
        """
        query = (
            f"SELECT id FROM {cms_tables.TC_CUSTOM_FIELDS} WHERE position = ?"
        )
        row = await self._db.run_query(query, (position,), fetch_one=True)
        return 0 if not row else int(row[0])

    async def _get_field_type_info(
            self,
            field_type: str) -> Optional[tuple[int, bool, bool]]:
        """Return (id, supports_default_value, supports_is_required) for a type.

        Args:
            field_type: Type name to look up.

        Returns:
            A tuple of type metadata, or None if the type name is not found.

        Raises:
            SqliteInterfaceException: If the database query fails.
        """
        query = f"""
            SELECT id, supports_default_value, supports_is_required
            FROM {cms_tables.TC_CUSTOM_FIELD_TYPES}
            WHERE name = ?
        """
        row = await self._db.run_query(query, (field_type,), fetch_one=True)
        if not row:
            self._logger.warning("Invalid field type '%s'", field_type)
            return None
        type_id, supports_default_value, supports_is_required = row
        return (int(type_id), bool(supports_default_value),
                bool(supports_is_required))
