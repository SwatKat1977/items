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


class TestcaseFieldValuesRepository:
    """
    Persistence operations for per-test-case custom field value data.

    Encapsulates all database access for the testcase field values domain.
    Raises SqliteInterfaceException on database failures; callers are
    responsible for handling those exceptions and updating service state
    accordingly.
    """

    def __init__(self,
                 logger: logging.Logger,
                 config: CMSConfiguration) -> None:
        self._logger = logger.getChild(__name__)
        self._db = SqliteInterface(self._logger, config.backend_db_filename)

    async def get_testcase_project_id(self, case_id: int) -> Optional[int]:
        """Return the project ID owning a test case, if it exists.

        Args:
            case_id: ID of the test case to check.

        Returns:
            The test case's project_id if it exists, or None if no test
            case matches.

        Raises:
            SqliteInterfaceException: If the database query fails.
        """
        query = (
            f"SELECT project_id FROM {cms_tables.TC_TEST_CASES} WHERE id = ?"
        )
        row = await self._db.run_query(query, (case_id,), fetch_one=True)
        return row[0] if row else None

    async def get_applicable_fields(self, project_id: int) -> list[dict]:
        """Retrieve every custom field definition applicable to a project.

        A field is applicable if it applies to all projects, or is
        explicitly linked to this project.

        Args:
            project_id: ID of the project to query.

        Returns:
            A list of dicts with ``id``, ``field_name``, ``field_type``,
            ``is_required``, ``default_value``, and ``position``, ordered
            by position.

        Raises:
            SqliteInterfaceException: If the database query fails.
        """
        query = f"""
            SELECT
                cf.id,
                cf.field_name,
                ft.name AS field_type_name,
                cf.is_required,
                cf.default_value,
                cf.position
            FROM {cms_tables.TC_CUSTOM_FIELDS} AS cf
            LEFT JOIN {cms_tables.TC_CUSTOM_FIELD_TYPES} AS ft
                ON cf.field_type_id = ft.id
            LEFT JOIN {cms_tables.TC_CUSTOM_FIELD_PROJECTS} AS cfp
                ON cf.id = cfp.field_id AND cfp.project_id = ?
            WHERE cf.applies_to_all_projects = 1 OR cfp.project_id IS NOT NULL
            ORDER BY cf.position
        """
        rows = await self._db.run_query(query, (project_id,))
        return [
            {
                'id': field_id,
                'field_name': field_name,
                'field_type': field_type,
                'is_required': bool(is_required),
                'default_value': default_value,
                'position': position,
            }
            for field_id, field_name, field_type, is_required,
            default_value, position in (rows or [])
        ]

    async def get_field_values(self, case_id: int) -> dict[int, str]:
        """Retrieve every stored custom field value for a test case.

        Args:
            case_id: ID of the test case to query.

        Returns:
            A dict mapping field_id to its stored value string.

        Raises:
            SqliteInterfaceException: If the database query fails.
        """
        query = (
            f"SELECT field_id, value FROM {cms_tables.TC_CUSTOM_FIELD_OPTION_VALUES} "
            "WHERE test_case_id = ?"
        )
        rows = await self._db.run_query(query, (case_id,))
        return dict(rows or [])

    async def get_field_values_for_testcases(
            self, case_ids: list[int]) -> dict[int, dict[int, str]]:
        """Retrieve stored custom field values for multiple test cases.

        Args:
            case_ids: IDs of the test cases to query.

        Returns:
            A dict mapping test_case_id to a dict of {field_id: value}.
            Test cases with no stored values are omitted.

        Raises:
            SqliteInterfaceException: If the database query fails.
        """
        if not case_ids:
            return {}

        placeholders = ",".join("?" * len(case_ids))
        query = (
            "SELECT test_case_id, field_id, value FROM "
            f"{cms_tables.TC_CUSTOM_FIELD_OPTION_VALUES} "
            f"WHERE test_case_id IN ({placeholders})"
        )
        rows = await self._db.run_query(query, tuple(case_ids))

        result: dict[int, dict[int, str]] = {}
        for test_case_id, field_id, value in (rows or []):
            result.setdefault(test_case_id, {})[field_id] = value
        return result

    async def value_row_exists(self, case_id: int, field_id: int) -> bool:
        """Return True if a stored value already exists for this pair.

        Args:
            case_id:  ID of the test case.
            field_id: ID of the custom field.

        Returns:
            True if a value row already exists.

        Raises:
            SqliteInterfaceException: If the database query fails.
        """
        query = (
            f"SELECT 1 FROM {cms_tables.TC_CUSTOM_FIELD_OPTION_VALUES} "
            "WHERE test_case_id = ? AND field_id = ? LIMIT 1"
        )
        row = await self._db.run_query(
            query, (case_id, field_id), fetch_one=True)
        return bool(row)

    async def insert_field_value(self,
                                 case_id: int,
                                 field_id: int,
                                 value: str) -> None:
        """Insert a new custom field value row for a test case.

        Args:
            case_id:  ID of the test case.
            field_id: ID of the custom field.
            value:    Value to store.

        Raises:
            SqliteInterfaceException: If the database insert fails.
        """
        query = (
            f"INSERT INTO {cms_tables.TC_CUSTOM_FIELD_OPTION_VALUES} "
            "(test_case_id, field_id, value) VALUES (?, ?, ?)"
        )
        await self._db.insert_query(query, (case_id, field_id, value))

    async def update_field_value(self,
                                 case_id: int,
                                 field_id: int,
                                 value: str) -> None:
        """Update an existing custom field value row for a test case.

        Args:
            case_id:  ID of the test case.
            field_id: ID of the custom field.
            value:    New value to store.

        Raises:
            SqliteInterfaceException: If the database update fails.
        """
        query = (
            f"UPDATE {cms_tables.TC_CUSTOM_FIELD_OPTION_VALUES} "
            "SET value = ? WHERE test_case_id = ? AND field_id = ?"
        )
        await self._db.run_query(
            query, (value, case_id, field_id), commit=True)
