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
from enum import Enum
from typing import Optional
from weaver_framework.database.sqlite_interface import SqliteInterface
from items.services.items_cms.cms_configuration import CMSConfiguration
import items.services.items_cms.cms_db_tables as cms_tables


class CaseTypeDeleteOutcome(Enum):
    """Result of a delete attempt, so callers can tell the cases apart."""
    DELETED = "deleted"
    NOT_FOUND = "not_found"
    IS_DEFAULT = "is_default"


class CaseTypesRepository:
    """
    Persistence operations for test case type data.

    Encapsulates all database access for the case types domain.
    Raises SqliteInterfaceException on database failures; callers are
    responsible for handling those exceptions and updating service state
    accordingly.
    """

    def __init__(self,
                 logger: logging.Logger,
                 config: CMSConfiguration) -> None:
        self._logger = logger.getChild(__name__)
        self._db = SqliteInterface(self._logger, config.backend_db_filename)

    async def case_type_name_exists(self,
                                    name: str,
                                    exclude_id: Optional[int] = None) -> bool:
        """Return True if a case type with the given name already exists.

        Case-insensitive match, matching tc_custom_fields' field_name/
        system_name uniqueness convention. Pass ``exclude_id`` when
        updating an existing type so its own current name does not
        trigger a false conflict.

        Args:
            name:       Display name to check.
            exclude_id: ID of the type being updated (excluded from check).

        Returns:
            True if another case type already has this name.

        Raises:
            SqliteInterfaceException: If the database query fails.
        """
        if exclude_id is not None:
            query = (
                f"SELECT 1 FROM {cms_tables.TC_CASE_TYPES} "
                "WHERE LOWER(name) = LOWER(?) AND id != ? LIMIT 1"
            )
            row = await self._db.run_query(query, (name, exclude_id),
                                           fetch_one=True)
        else:
            query = (
                f"SELECT 1 FROM {cms_tables.TC_CASE_TYPES} "
                "WHERE LOWER(name) = LOWER(?) LIMIT 1"
            )
            row = await self._db.run_query(query, (name,), fetch_one=True)
        return bool(row)

    async def add_case_type(self, name: str, description: str) -> int:
        """Insert a new case type and return its ID.

        Always created as non-default - promoting a type to default is a
        separate, dedicated operation (see set_default_case_type).

        Args:
            name:        Display name of the case type.
            description: Human-readable description (may be empty).

        Returns:
            The ID of the newly inserted row.

        Raises:
            SqliteInterfaceException: If the insert fails.
        """
        query = (
            f"INSERT INTO {cms_tables.TC_CASE_TYPES}"
            "(name, description, is_default) VALUES (?, ?, 0)"
        )
        return await self._db.insert_query(query, (name, description))

    async def get_case_type(self, type_id: int) -> Optional[tuple]:
        """Retrieve a single case type by ID.

        Args:
            type_id: Primary key of the case type.

        Returns:
            A ``(id, name, description, is_default)`` row tuple if found,
            or None if no type has that ID.

        Raises:
            SqliteInterfaceException: If the database query fails.
        """
        query = (
            f"SELECT id, name, description, is_default "
            f"FROM {cms_tables.TC_CASE_TYPES} WHERE id = ?"
        )
        row = await self._db.run_query(query, (type_id,), fetch_one=True)
        return row if row else None

    async def get_all_case_types(self) -> list:
        """Retrieve every case type, ordered by name.

        Returns:
            A list of ``(id, name, description, is_default)`` row tuples,
            possibly empty.

        Raises:
            SqliteInterfaceException: If the database query fails.
        """
        query = (
            f"SELECT id, name, description, is_default "
            f"FROM {cms_tables.TC_CASE_TYPES} ORDER BY name"
        )
        rows = await self._db.run_query(query, ())
        return rows or []

    async def update_case_type(self,
                               type_id: int,
                               name: str,
                               description: str) -> bool:
        """Update a case type's name and description.

        Does not touch ``is_default`` - that field is only ever changed
        via set_default_case_type.

        Args:
            type_id:     ID of the case type to update.
            name:        New display name.
            description: New description (may be empty).

        Returns:
            True on success, False if no type with ``type_id`` exists.

        Raises:
            SqliteInterfaceException: If the update fails.
        """
        row = await self._db.run_query(
            f"SELECT id FROM {cms_tables.TC_CASE_TYPES} WHERE id = ?",
            (type_id,), fetch_one=True)
        if not row:
            return False

        await self._db.run_query(
            f"UPDATE {cms_tables.TC_CASE_TYPES} "
            "SET name = ?, description = ? WHERE id = ?",
            (name, description, type_id), commit=True)
        return True

    async def get_default_case_type_id(self) -> Optional[int]:
        """Return the ID of the current default case type.

        Returns:
            The default type's ID, or None if - unexpectedly - no type
            is currently marked default (shouldn't happen given the seed
            data and that the default can never be deleted, but callers
            shouldn't assume it can't).

        Raises:
            SqliteInterfaceException: If the database query fails.
        """
        row = await self._db.run_query(
            f"SELECT id FROM {cms_tables.TC_CASE_TYPES} WHERE is_default = 1",
            (), fetch_one=True)
        return int(row[0]) if row else None

    async def set_default_case_type(self, type_id: int) -> Optional[bool]:
        """Make a case type the default, un-defaulting whichever held it.

        The clear and the set run as one transaction (BEGIN/COMMIT in a
        single script), so the table can never be observed - or left, if
        the process dies part-way - with zero defaults. The clear is
        guarded by an EXISTS check so a missing ``type_id`` cannot strip
        the current default. Two statements are needed rather than one
        UPDATE because the partial unique index is checked row by row,
        so a single swapping UPDATE would be order-dependent.

        ``type_id`` is coerced with ``int()`` before being formatted into
        the script (executescript takes no bound parameters).

        Args:
            type_id: ID of the case type to make the default.

        Returns:
            True if the type is now the default (including if it already
            was - idempotent), False if no type with ``type_id`` exists.

        Raises:
            SqliteInterfaceException: If any database operation fails.
        """
        row = await self._db.run_query(
            f"SELECT is_default FROM {cms_tables.TC_CASE_TYPES} WHERE id = ?",
            (type_id,), fetch_one=True)
        if not row:
            return False

        if row[0]:
            return True  # already the default - nothing to do

        type_id = int(type_id)
        table = cms_tables.TC_CASE_TYPES
        await self._db.run_script(
            "BEGIN IMMEDIATE;"
            f"UPDATE {table} SET is_default = 0 WHERE is_default = 1 "
            f"AND EXISTS (SELECT 1 FROM {table} WHERE id = {type_id});"
            f"UPDATE {table} SET is_default = 1 WHERE id = {type_id};"
            "COMMIT;")
        return True

    async def delete_case_type(self, type_id: int) -> CaseTypeDeleteOutcome:
        """Delete a case type, moving its test cases to the default type.

        The reassignment and the delete run as one transaction (BEGIN/COMMIT
        in a single script), so a test case can never be left pointing at a
        type that no longer exists, and a failure part-way rolls back both
        (the connection is closed with the transaction still open). Both
        statements are guarded on the type not being the default, and
        ``BEGIN IMMEDIATE`` takes the write lock first, so the default
        cannot change underneath the script.

        The default is looked up before running the script so the caller can
        be told *why* nothing was deleted. If the type became the default in
        the gap between that lookup and the script, the guarded statements do
        nothing and the follow-up check reports it as the default rather
        than claiming it was deleted.

        ``type_id`` is coerced with ``int()`` before being formatted into
        the script (executescript takes no bound parameters).

        Args:
            type_id: ID of the case type to delete.

        Returns:
            DELETED if the type was removed, NOT_FOUND if no type has that
            ID, or IS_DEFAULT if it is the default (which is never deleted).

        Raises:
            SqliteInterfaceException: If any database operation fails.
        """
        row = await self._db.run_query(
            f"SELECT is_default FROM {cms_tables.TC_CASE_TYPES} WHERE id = ?",
            (type_id,), fetch_one=True)
        if not row:
            return CaseTypeDeleteOutcome.NOT_FOUND

        if row[0]:
            return CaseTypeDeleteOutcome.IS_DEFAULT

        type_id = int(type_id)
        types = cms_tables.TC_CASE_TYPES
        cases = cms_tables.TC_TEST_CASES
        await self._db.run_script(
            "BEGIN IMMEDIATE;"
            f"UPDATE {cases} SET case_type_id = "
            f"(SELECT id FROM {types} WHERE is_default = 1) "
            f"WHERE case_type_id = {type_id} "
            f"AND EXISTS (SELECT 1 FROM {types} "
            f"WHERE id = {type_id} AND is_default = 0);"
            f"DELETE FROM {types} WHERE id = {type_id} AND is_default = 0;"
            "COMMIT;")

        still_there = await self._db.run_query(
            f"SELECT 1 FROM {types} WHERE id = ?",
            (type_id,), fetch_one=True)
        if still_there:
            return CaseTypeDeleteOutcome.IS_DEFAULT

        return CaseTypeDeleteOutcome.DELETED
