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

        Builds the full folder hierarchy via a recursive CTE, then
        fetches all test case IDs and names for the project.

        Args:
            project_id: ID of the project to query.

        Returns:
            A dict with two keys:
              - ``folders``: list of ``{id, name, parent_id}`` dicts ordered
                by parent then id.
              - ``test_cases``: list of ``{id, folder_id, name}`` dicts
                ordered by folder then id.

        Raises:
            SqliteInterfaceException: If either database query fails.
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

        return {
            'folders': [
                {'id': folder_id, 'name': name, 'parent_id': parent_id}
                for folder_id, parent_id, name in (folder_rows or [])
            ],
            'test_cases': [
                {'id': test_id, 'folder_id': folder_id, 'name': name}
                for test_id, folder_id, name in (cases_rows or [])
            ]
        }

    async def get_testcase(self, case_id: int) -> Optional[dict]:
        """Retrieve full details for a single test case.

        Args:
            case_id: Primary key of the test case.

        Returns:
            A dict with ``id``, ``folder_id``, ``name``, and
            ``description`` if found, or None if no row matches.

        Raises:
            SqliteInterfaceException: If the database query fails.
        """
        query = (
            f"SELECT id, folder_id, name, description "
            f"FROM {cms_tables.TC_TEST_CASES} WHERE id = ?"
        )
        row = await self._db.run_query(query, (case_id,), fetch_one=True)

        if not row:
            return None

        test_id, folder_id, name, description = row
        return {
            'id': test_id,
            'folder_id': folder_id,
            'name': name,
            'description': description
        }
