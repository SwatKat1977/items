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
import os
import sqlite3
import tempfile
import unittest
from unittest.mock import MagicMock
from items.services.items_cms.repositories.testcase_field_values_repository import (
    TestcaseFieldValuesRepository,
)
from items.services.items_cms.cms_configuration import CMSConfiguration

_SCHEMA_SQL = """
CREATE TABLE prj_projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);
CREATE TABLE tc_test_cases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    folder_id INTEGER NULL,
    name TEXT NOT NULL,
    description TEXT,
    FOREIGN KEY (project_id) REFERENCES prj_projects(id) ON DELETE CASCADE
);
CREATE TABLE tc_custom_field_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    supports_default_value BOOLEAN NOT NULL DEFAULT 0,
    supports_is_required BOOLEAN NOT NULL DEFAULT 0
);
CREATE TABLE tc_custom_fields (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    field_name TEXT NOT NULL UNIQUE,
    description TEXT NOT NULL DEFAULT '',
    system_name TEXT NOT NULL UNIQUE,
    field_type_id INTEGER NOT NULL,
    entry_type TEXT NOT NULL CHECK(entry_type IN ('system', 'user')),
    enabled BOOLEAN NOT NULL,
    position INTEGER NOT NULL,
    is_required BOOLEAN NOT NULL DEFAULT 0,
    default_value TEXT NOT NULL DEFAULT '',
    applies_to_all_projects BOOLEAN NOT NULL DEFAULT 0,
    FOREIGN KEY (field_type_id) REFERENCES tc_custom_field_types(id)
);
CREATE TABLE tc_custom_field_projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    field_id INTEGER NOT NULL,
    project_id INTEGER NOT NULL,
    FOREIGN KEY (field_id) REFERENCES tc_custom_fields(id) ON DELETE CASCADE,
    FOREIGN KEY (project_id) REFERENCES prj_projects(id) ON DELETE CASCADE
);
CREATE TABLE tc_custom_field_option_values (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    test_case_id INTEGER NOT NULL,
    field_id INTEGER NOT NULL,
    value TEXT NOT NULL,
    FOREIGN KEY (test_case_id) REFERENCES tc_test_cases(id) ON DELETE CASCADE,
    FOREIGN KEY (field_id) REFERENCES tc_custom_fields(id) ON DELETE CASCADE,
    UNIQUE(test_case_id, field_id)
);
INSERT INTO tc_custom_field_types (name, supports_default_value, supports_is_required)
VALUES ('String', 1, 1), ('Integer', 1, 1);
"""

_STRING_TYPE_ID = 1


class TestTestcaseFieldValuesRepository(unittest.IsolatedAsyncioTestCase):
    """Integration tests for TestcaseFieldValuesRepository against a real SQLite DB."""

    async def asyncSetUp(self):
        fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        conn = sqlite3.connect(self.db_path)
        conn.executescript(_SCHEMA_SQL)
        conn.close()

        mock_config = MagicMock(spec=CMSConfiguration)
        mock_config.backend_db_filename = self.db_path
        self.repo = TestcaseFieldValuesRepository(MagicMock(), mock_config)

        self.project_id = self._insert_project("Alpha")
        self.case_id = self._insert_testcase(self.project_id, "Login Test")

    async def asyncTearDown(self):
        try:
            os.unlink(self.db_path)
        except OSError:
            pass

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _db_insert(self, sql, params=()):
        conn = sqlite3.connect(self.db_path)
        cur = conn.execute(sql, params)
        row_id = cur.lastrowid
        conn.commit()
        conn.close()
        return row_id

    def _db_query(self, sql, params=()):
        conn = sqlite3.connect(self.db_path)
        rows = conn.execute(sql, params).fetchall()
        conn.close()
        return rows

    def _insert_project(self, name):
        return self._db_insert(
            "INSERT INTO prj_projects (name) VALUES (?)", (name,))

    def _insert_testcase(self, project_id, name):
        return self._db_insert(
            "INSERT INTO tc_test_cases (project_id, name) VALUES (?, ?)",
            (project_id, name))

    def _insert_field(self, field_name, system_name, position,
                      field_type_id=_STRING_TYPE_ID, is_required=False,
                      default_value="", applies_to_all=True):
        return self._db_insert(
            "INSERT INTO tc_custom_fields "
            "(field_name, description, system_name, field_type_id, "
            "entry_type, enabled, position, is_required, default_value, "
            "applies_to_all_projects) "
            "VALUES (?, '', ?, ?, 'user', 1, ?, ?, ?, ?)",
            (field_name, system_name, field_type_id, position,
             is_required, default_value, applies_to_all))

    def _link_field_to_project(self, field_id, project_id):
        self._db_insert(
            "INSERT INTO tc_custom_field_projects (field_id, project_id) "
            "VALUES (?, ?)", (field_id, project_id))

    def _insert_value(self, case_id, field_id, value):
        return self._db_insert(
            "INSERT INTO tc_custom_field_option_values "
            "(test_case_id, field_id, value) VALUES (?, ?, ?)",
            (case_id, field_id, value))

    # ------------------------------------------------------------------
    # get_testcase_project_id
    # ------------------------------------------------------------------

    async def test_get_testcase_project_id_returns_none_when_not_found(self):
        result = await self.repo.get_testcase_project_id(999)
        self.assertIsNone(result)

    async def test_get_testcase_project_id_returns_id_when_found(self):
        result = await self.repo.get_testcase_project_id(self.case_id)
        self.assertEqual(result, self.project_id)

    # ------------------------------------------------------------------
    # get_applicable_fields
    # ------------------------------------------------------------------

    async def test_get_applicable_fields_returns_empty_when_none(self):
        result = await self.repo.get_applicable_fields(self.project_id)
        self.assertEqual(result, [])

    async def test_get_applicable_fields_includes_global_fields(self):
        self._insert_field("Priority", "priority", position=1,
                           applies_to_all=True)
        result = await self.repo.get_applicable_fields(self.project_id)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["field_name"], "Priority")
        self.assertEqual(result[0]["field_type"], "String")
        self.assertFalse(result[0]["is_required"])

    async def test_get_applicable_fields_includes_linked_fields(self):
        field_id = self._insert_field("Severity", "severity", position=1,
                                      applies_to_all=False)
        self._link_field_to_project(field_id, self.project_id)
        result = await self.repo.get_applicable_fields(self.project_id)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["field_name"], "Severity")

    async def test_get_applicable_fields_excludes_unlinked_fields(self):
        self._insert_field("OtherProjectOnly", "other", position=1,
                           applies_to_all=False)
        result = await self.repo.get_applicable_fields(self.project_id)
        self.assertEqual(result, [])

    async def test_get_applicable_fields_ordered_by_position(self):
        self._insert_field("Second", "second", position=2)
        self._insert_field("First", "first", position=1)
        result = await self.repo.get_applicable_fields(self.project_id)
        self.assertEqual([f["field_name"] for f in result],
                         ["First", "Second"])

    # ------------------------------------------------------------------
    # get_field_values
    # ------------------------------------------------------------------

    async def test_get_field_values_returns_empty_when_none(self):
        result = await self.repo.get_field_values(self.case_id)
        self.assertEqual(result, {})

    async def test_get_field_values_returns_stored_values(self):
        field_id = self._insert_field("Priority", "priority", position=1)
        self._insert_value(self.case_id, field_id, "High")
        result = await self.repo.get_field_values(self.case_id)
        self.assertEqual(result, {field_id: "High"})

    # ------------------------------------------------------------------
    # get_field_values_for_testcases
    # ------------------------------------------------------------------

    async def test_get_field_values_for_testcases_returns_empty_for_empty_input(self):
        result = await self.repo.get_field_values_for_testcases([])
        self.assertEqual(result, {})

    async def test_get_field_values_for_testcases_groups_by_case(self):
        other_case_id = self._insert_testcase(self.project_id, "Other Test")
        field_id = self._insert_field("Priority", "priority", position=1)
        self._insert_value(self.case_id, field_id, "High")
        self._insert_value(other_case_id, field_id, "Low")

        result = await self.repo.get_field_values_for_testcases(
            [self.case_id, other_case_id])

        self.assertEqual(result, {
            self.case_id: {field_id: "High"},
            other_case_id: {field_id: "Low"},
        })

    async def test_get_field_values_for_testcases_omits_cases_without_values(self):
        other_case_id = self._insert_testcase(self.project_id, "Other Test")
        field_id = self._insert_field("Priority", "priority", position=1)
        self._insert_value(self.case_id, field_id, "High")

        result = await self.repo.get_field_values_for_testcases(
            [self.case_id, other_case_id])

        self.assertEqual(result, {self.case_id: {field_id: "High"}})

    # ------------------------------------------------------------------
    # value_row_exists
    # ------------------------------------------------------------------

    async def test_value_row_exists_returns_false_when_absent(self):
        field_id = self._insert_field("Priority", "priority", position=1)
        result = await self.repo.value_row_exists(self.case_id, field_id)
        self.assertFalse(result)

    async def test_value_row_exists_returns_true_when_present(self):
        field_id = self._insert_field("Priority", "priority", position=1)
        self._insert_value(self.case_id, field_id, "High")
        result = await self.repo.value_row_exists(self.case_id, field_id)
        self.assertTrue(result)

    # ------------------------------------------------------------------
    # insert_field_value / update_field_value
    # ------------------------------------------------------------------

    async def test_insert_field_value_creates_row(self):
        field_id = self._insert_field("Priority", "priority", position=1)
        await self.repo.insert_field_value(self.case_id, field_id, "High")
        rows = self._db_query(
            "SELECT value FROM tc_custom_field_option_values "
            "WHERE test_case_id = ? AND field_id = ?",
            (self.case_id, field_id))
        self.assertEqual(rows[0][0], "High")

    async def test_update_field_value_changes_existing_row(self):
        field_id = self._insert_field("Priority", "priority", position=1)
        self._insert_value(self.case_id, field_id, "High")
        await self.repo.update_field_value(self.case_id, field_id, "Low")
        rows = self._db_query(
            "SELECT value FROM tc_custom_field_option_values "
            "WHERE test_case_id = ? AND field_id = ?",
            (self.case_id, field_id))
        self.assertEqual(rows[0][0], "Low")


if __name__ == "__main__":
    unittest.main()
