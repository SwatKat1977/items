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
from items.services.items_cms.cms_configuration import CMSConfiguration
import items.services.items_cms.cms_db_tables as cms_tables


class TestcaseRepository:
    """
    Persistence operations for test case data.

    Encapsulates all database access for the testcases domain. Raises
    SqliteInterfaceException on database failures; callers are responsible
    for handling those exceptions and updating service state accordingly.
    """

    def __init__(self,
                 logger: logging.Logger,
                 config: CMSConfiguration) -> None:
        self._logger = logger.getChild(__name__)
        self._db = SqliteInterface(self._logger, config.backend_db_filename)

    async def is_valid_project_id(self, project_id: int) -> bool:
        """Return True if the project ID exists in the database.

        Args:
            project_id: ID of the project to check.

        Returns:
            True if the project exists, False otherwise.

        Raises:
            SqliteInterfaceException: If the database query fails.
        """
        query = f"SELECT id FROM {cms_tables.PRJ_PROJECTS} WHERE id = ?"
        row = await self._db.run_query(query, (project_id,), fetch_one=True)
        return bool(row)

    async def get_testcases(self, project_id: int) -> dict:
        """Retrieve folders and test case stubs for a project.

        Builds the full folder hierarchy via a recursive CTE, fetches all
        test case IDs and names for the project, and attaches each test
        case's custom field values inline so a grid/list view doesn't need
        a separate call per test case to render its custom field columns.

        Args:
            project_id: ID of the project to query.

        Returns:
            A dict with two keys:
              - ``folders``: list of ``{id, name, parent_id}`` dicts ordered
                by parent then id.
              - ``test_cases``: list of ``{id, folder_id, name,
                custom_fields}`` dicts ordered by folder then id, where
                ``custom_fields`` is a list of ``{field_id, field_name,
                field_type, position, value}`` dicts ordered by position.

        Raises:
            SqliteInterfaceException: If any database query fails.
        """
        folders_query = f"""
            WITH RECURSIVE folder_hierarchy AS (
                SELECT id, parent_id, name
                FROM {cms_tables.TC_FOLDERS}
                WHERE parent_id IS NULL AND project_id = ?
                UNION ALL
                SELECT f.id, f.parent_id, f.name
                FROM {cms_tables.TC_FOLDERS} f
                JOIN folder_hierarchy h ON f.parent_id = h.id
            )
            SELECT id, parent_id, name
            FROM folder_hierarchy
            ORDER BY parent_id, id
        """

        cases_query = (
            f"SELECT id, folder_id, name "
            f"FROM {cms_tables.TC_TEST_CASES} "
            "WHERE project_id = ? "
            "ORDER BY folder_id, id"
        )

        folder_rows = await self._db.run_query(folders_query, (project_id,))
        cases_rows = await self._db.run_query(cases_query, (project_id,))
        values_by_case = await self._get_custom_field_values(project_id)

        return {
            'folders': [
                {'id': folder_id, 'name': name, 'parent_id': parent_id}
                for folder_id, parent_id, name in (folder_rows or [])
            ],
            'test_cases': [
                {
                    'id': test_id,
                    'folder_id': folder_id,
                    'name': name,
                    'custom_fields': values_by_case.get(test_id, []),
                }
                for test_id, folder_id, name in (cases_rows or [])
            ]
        }

    async def _get_custom_field_values(
            self, project_id: int) -> dict[int, list[dict]]:
        """Retrieve every test case's custom field values for a project.

        A field is included for a test case if it applies to all projects,
        or is explicitly linked to the test case's project. A test case's
        value for a field falls back to that field's default value when no
        value has been stored yet — same fallback used when reading a
        single test case's values.

        Args:
            project_id: ID of the project to query.

        Returns:
            A dict mapping test_case_id to a list of ``{field_id,
            field_name, field_type, position, value}`` dicts, ordered by
            position.

        Raises:
            SqliteInterfaceException: If the database query fails.
        """
        query = f"""
            SELECT
                tc.id AS test_case_id,
                cf.id AS field_id,
                cf.field_name,
                ft.name AS field_type_name,
                cf.position,
                COALESCE(v.value, cf.default_value) AS value
            FROM {cms_tables.TC_TEST_CASES} AS tc
            JOIN {cms_tables.TC_CUSTOM_FIELDS} AS cf
                ON cf.applies_to_all_projects = 1
                OR EXISTS (
                    SELECT 1 FROM {cms_tables.TC_CUSTOM_FIELD_PROJECTS} AS cfp
                    WHERE cfp.field_id = cf.id AND cfp.project_id = tc.project_id
                )
            LEFT JOIN {cms_tables.TC_CUSTOM_FIELD_TYPES} AS ft
                ON cf.field_type_id = ft.id
            LEFT JOIN {cms_tables.TC_CUSTOM_FIELD_OPTION_VALUES} AS v
                ON v.test_case_id = tc.id AND v.field_id = cf.id
            WHERE tc.project_id = ?
            ORDER BY tc.id, cf.position
        """
        rows = await self._db.run_query(query, (project_id,))

        values_by_case: dict[int, list[dict]] = {}
        for test_case_id, field_id, field_name, field_type, position, value \
                in (rows or []):
            values_by_case.setdefault(test_case_id, []).append({
                'field_id': field_id,
                'field_name': field_name,
                'field_type': field_type,
                'position': position,
                'value': value,
            })
        return values_by_case

    async def get_testcase(self, case_id: int) -> Optional[dict]:
        """Retrieve full details for a single test case.

        Args:
            case_id: Primary key of the test case.

        Returns:
            A dict with ``id``, ``project_id``, ``folder_id``, ``name``, and
            ``description`` if found, or None if no row matches.

        Raises:
            SqliteInterfaceException: If the database query fails.
        """
        query = (
            f"SELECT id, project_id, folder_id, name, description "
            f"FROM {cms_tables.TC_TEST_CASES} WHERE id = ?"
        )
        row = await self._db.run_query(query, (case_id,), fetch_one=True)

        if not row:
            return None

        test_id, project_id, folder_id, name, description = row
        return {
            'id': test_id,
            'project_id': project_id,
            'folder_id': folder_id,
            'name': name,
            'description': description
        }

    async def get_folder_project_id(self, folder_id: int) -> Optional[int]:
        """Return the project ID owning a folder, if the folder exists.

        Args:
            folder_id: ID of the folder to check.

        Returns:
            The folder's project_id if it exists, or None if no folder
            matches.

        Raises:
            SqliteInterfaceException: If the database query fails.
        """
        query = (
            f"SELECT project_id FROM {cms_tables.TC_FOLDERS} WHERE id = ?"
        )
        row = await self._db.run_query(query, (folder_id,), fetch_one=True)
        return row[0] if row else None

    async def testcase_name_exists(self,
                                   project_id: int,
                                   folder_id: Optional[int],
                                   name: str,
                                   exclude_id: Optional[int] = None) -> bool:
        """Return True if a sibling test case with the given name exists.

        Case-sensitive match against test cases sharing the same project
        and folder. SQL ``NULL`` never equals ``NULL``, so root-level test
        cases (``folder_id IS NULL``) are compared with an explicit
        ``IS NULL`` clause rather than ``= ?``.

        Args:
            project_id:  Project the test case belongs to.
            folder_id:   Folder ID, or None for a root-level test case.
            name:        Test case name to check.
            exclude_id:  ID of the test case being updated (excluded from
                         the check), or None when creating a new test case.

        Returns:
            True if the name is already taken by a sibling test case.

        Raises:
            SqliteInterfaceException: If the database query fails.
        """
        folder_clause = "folder_id IS NULL" if folder_id is None \
            else "folder_id = ?"
        params: list = [project_id]
        if folder_id is not None:
            params.append(folder_id)
        params.append(name)

        query = (
            f"SELECT 1 FROM {cms_tables.TC_TEST_CASES} "
            f"WHERE project_id = ? AND {folder_clause} AND name = ?"
        )

        if exclude_id is not None:
            query += " AND id != ?"
            params.append(exclude_id)

        query += " LIMIT 1"

        row = await self._db.run_query(query, tuple(params), fetch_one=True)
        return bool(row)

    async def add_testcase(self,
                           project_id: int,
                           folder_id: Optional[int],
                           name: str,
                           description: str) -> int:
        """Insert a new test case and return its ID.

        Args:
            project_id:  Project the test case belongs to.
            folder_id:   Folder ID, or None for a root-level test case.
            name:        Test case name.
            description: Test case description.

        Returns:
            The ID of the newly inserted test case row.

        Raises:
            SqliteInterfaceException: If the database insert fails.
        """
        query = (
            f"INSERT INTO {cms_tables.TC_TEST_CASES} "
            "(project_id, folder_id, name, description) "
            "VALUES (?, ?, ?, ?)"
        )
        return await self._db.insert_query(
            query, (project_id, folder_id, name, description))

    async def update_testcase(self,
                              case_id: int,
                              name: str,
                              description: str) -> None:
        """Rename and/or update the description of an existing test case.

        Args:
            case_id:     ID of the test case to update.
            name:        New test case name.
            description: New test case description.

        Raises:
            SqliteInterfaceException: If the database update fails.
        """
        query = (
            f"UPDATE {cms_tables.TC_TEST_CASES} "
            "SET name = ?, description = ? WHERE id = ?"
        )
        await self._db.run_query(
            query, (name, description, case_id), commit=True)

    async def delete_testcase(self, case_id: int) -> None:
        """Permanently delete a test case from the database.

        Args:
            case_id: ID of the test case to delete.

        Raises:
            SqliteInterfaceException: If the database delete fails.
        """
        query = f"DELETE FROM {cms_tables.TC_TEST_CASES} WHERE id = ?"
        await self._db.run_query(query, (case_id,), commit=True)
