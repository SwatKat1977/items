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
from items.services.items_cms.repositories.testcase_repository import TestcaseRepository
from items.services.items_cms.cms_configuration import CMSConfiguration

_SCHEMA_SQL = """
CREATE TABLE prj_projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    awaiting_purge BOOLEAN NOT NULL DEFAULT 0,
    announcement TEXT NOT NULL DEFAULT '',
    show_announcement_on_overview INTEGER NOT NULL DEFAULT 0,
    creation_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE tc_folders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    parent_id INTEGER NULL,
    name TEXT NOT NULL,
    FOREIGN KEY (project_id) REFERENCES prj_projects(id) ON DELETE CASCADE,
    FOREIGN KEY (parent_id) REFERENCES tc_folders(id) ON DELETE CASCADE,
    UNIQUE (project_id, parent_id, name)
);
CREATE TABLE tc_test_cases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    folder_id INTEGER NULL,
    name TEXT NOT NULL,
    description TEXT,
    FOREIGN KEY (project_id) REFERENCES prj_projects(id) ON DELETE CASCADE,
    FOREIGN KEY (folder_id) REFERENCES tc_folders(id) ON DELETE CASCADE,
    UNIQUE (project_id, folder_id, name)
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
VALUES ('String', 1, 1);
"""

_STRING_TYPE_ID = 1


class TestTestcaseRepository(unittest.IsolatedAsyncioTestCase):
    """Integration tests for TestcaseRepository against a real SQLite DB."""

    async def asyncSetUp(self):
        fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        conn = sqlite3.connect(self.db_path)
        conn.executescript(_SCHEMA_SQL)
        conn.close()

        mock_config = MagicMock(spec=CMSConfiguration)
        mock_config.backend_db_filename = self.db_path
        self.repo = TestcaseRepository(MagicMock(), mock_config)

    async def asyncTearDown(self):
        try:
            os.unlink(self.db_path)
        except OSError:
            pass

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _insert_project(self, name):
        conn = sqlite3.connect(self.db_path)
        cur = conn.execute("INSERT INTO prj_projects (name) VALUES (?)", (name,))
        row_id = cur.lastrowid
        conn.commit()
        conn.close()
        return row_id

    def _insert_folder(self, project_id, name, parent_id=None):
        conn = sqlite3.connect(self.db_path)
        cur = conn.execute(
            "INSERT INTO tc_folders (project_id, parent_id, name) VALUES (?, ?, ?)",
            (project_id, parent_id, name))
        row_id = cur.lastrowid
        conn.commit()
        conn.close()
        return row_id

    def _insert_testcase(self, project_id, name, folder_id=None, description=""):
        conn = sqlite3.connect(self.db_path)
        cur = conn.execute(
            "INSERT INTO tc_test_cases "
            "(project_id, folder_id, name, description) VALUES (?, ?, ?, ?)",
            (project_id, folder_id, name, description))
        row_id = cur.lastrowid
        conn.commit()
        conn.close()
        return row_id

    def _insert_field(self, field_name, system_name, position,
                      default_value="", applies_to_all=True):
        conn = sqlite3.connect(self.db_path)
        cur = conn.execute(
            "INSERT INTO tc_custom_fields "
            "(field_name, description, system_name, field_type_id, "
            "entry_type, enabled, position, is_required, default_value, "
            "applies_to_all_projects) "
            "VALUES (?, '', ?, ?, 'user', 1, ?, 0, ?, ?)",
            (field_name, system_name, _STRING_TYPE_ID, position,
             default_value, applies_to_all))
        row_id = cur.lastrowid
        conn.commit()
        conn.close()
        return row_id

    def _link_field_to_project(self, field_id, project_id):
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "INSERT INTO tc_custom_field_projects (field_id, project_id) "
            "VALUES (?, ?)", (field_id, project_id))
        conn.commit()
        conn.close()

    def _insert_field_value(self, case_id, field_id, value):
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "INSERT INTO tc_custom_field_option_values "
            "(test_case_id, field_id, value) VALUES (?, ?, ?)",
            (case_id, field_id, value))
        conn.commit()
        conn.close()

    # ------------------------------------------------------------------
    # is_valid_project_id
    # ------------------------------------------------------------------

    async def test_is_valid_project_id_returns_false_when_not_found(self):
        result = await self.repo.is_valid_project_id(999)
        self.assertFalse(result)

    async def test_is_valid_project_id_returns_true_when_found(self):
        pid = self._insert_project("Alpha")
        result = await self.repo.is_valid_project_id(pid)
        self.assertTrue(result)

    # ------------------------------------------------------------------
    # get_testcases
    # ------------------------------------------------------------------

    async def test_get_testcases_returns_empty_dicts_for_empty_project(self):
        pid = self._insert_project("Alpha")
        result = await self.repo.get_testcases(pid)
        self.assertEqual(result["folders"], [])
        self.assertEqual(result["test_cases"], [])

    async def test_get_testcases_returns_folders(self):
        pid = self._insert_project("Alpha")
        fid = self._insert_folder(pid, "Suite A")
        result = await self.repo.get_testcases(pid)
        self.assertEqual(len(result["folders"]), 1)
        self.assertEqual(result["folders"][0]["id"], fid)
        self.assertEqual(result["folders"][0]["name"], "Suite A")
        self.assertIsNone(result["folders"][0]["parent_id"])

    async def test_get_testcases_returns_nested_folders(self):
        pid = self._insert_project("Alpha")
        parent_id = self._insert_folder(pid, "Parent")
        child_id = self._insert_folder(pid, "Child", parent_id=parent_id)
        result = await self.repo.get_testcases(pid)
        self.assertEqual(len(result["folders"]), 2)
        child = next(f for f in result["folders"] if f["id"] == child_id)
        self.assertEqual(child["parent_id"], parent_id)

    async def test_get_testcases_returns_test_cases(self):
        pid = self._insert_project("Alpha")
        fid = self._insert_folder(pid, "Suite A")
        tc_id = self._insert_testcase(pid, "Login Test", folder_id=fid)
        result = await self.repo.get_testcases(pid)
        self.assertEqual(len(result["test_cases"]), 1)
        self.assertEqual(result["test_cases"][0]["id"], tc_id)
        self.assertEqual(result["test_cases"][0]["name"], "Login Test")
        self.assertEqual(result["test_cases"][0]["folder_id"], fid)

    async def test_get_testcases_excludes_other_project_cases(self):
        pid1 = self._insert_project("Alpha")
        pid2 = self._insert_project("Beta")
        self._insert_testcase(pid2, "Beta Test")
        result = await self.repo.get_testcases(pid1)
        self.assertEqual(result["test_cases"], [])

    async def test_get_testcases_includes_no_custom_fields_when_none_defined(self):
        pid = self._insert_project("Alpha")
        self._insert_testcase(pid, "Login Test")
        result = await self.repo.get_testcases(pid)
        self.assertEqual(result["test_cases"][0]["custom_fields"], [])

    async def test_get_testcases_includes_global_field_with_default_value(self):
        pid = self._insert_project("Alpha")
        self._insert_testcase(pid, "Login Test")
        self._insert_field("Priority", "priority", position=1,
                           default_value="Medium")
        result = await self.repo.get_testcases(pid)
        fields = result["test_cases"][0]["custom_fields"]
        self.assertEqual(len(fields), 1)
        self.assertEqual(fields[0]["field_name"], "Priority")
        self.assertEqual(fields[0]["field_type"], "String")
        self.assertEqual(fields[0]["value"], "Medium")
        self.assertEqual(fields[0]["position"], 1)

    async def test_get_testcases_uses_stored_value_over_default(self):
        pid = self._insert_project("Alpha")
        tc_id = self._insert_testcase(pid, "Login Test")
        field_id = self._insert_field("Priority", "priority", position=1,
                                      default_value="Medium")
        self._insert_field_value(tc_id, field_id, "High")
        result = await self.repo.get_testcases(pid)
        fields = result["test_cases"][0]["custom_fields"]
        self.assertEqual(fields[0]["value"], "High")

    async def test_get_testcases_excludes_fields_linked_to_other_projects(self):
        pid1 = self._insert_project("Alpha")
        pid2 = self._insert_project("Beta")
        self._insert_testcase(pid1, "Login Test")
        field_id = self._insert_field("Beta Only", "beta_only", position=1,
                                      applies_to_all=False)
        self._link_field_to_project(field_id, pid2)
        result = await self.repo.get_testcases(pid1)
        self.assertEqual(result["test_cases"][0]["custom_fields"], [])

    async def test_get_testcases_includes_linked_field(self):
        pid = self._insert_project("Alpha")
        self._insert_testcase(pid, "Login Test")
        field_id = self._insert_field("Severity", "severity", position=1,
                                      applies_to_all=False)
        self._link_field_to_project(field_id, pid)
        result = await self.repo.get_testcases(pid)
        fields = result["test_cases"][0]["custom_fields"]
        self.assertEqual(len(fields), 1)
        self.assertEqual(fields[0]["field_name"], "Severity")

    async def test_get_testcases_orders_fields_by_position(self):
        pid = self._insert_project("Alpha")
        self._insert_testcase(pid, "Login Test")
        self._insert_field("Second", "second", position=2)
        self._insert_field("First", "first", position=1)
        result = await self.repo.get_testcases(pid)
        fields = result["test_cases"][0]["custom_fields"]
        self.assertEqual([f["field_name"] for f in fields],
                         ["First", "Second"])

    # ------------------------------------------------------------------
    # get_testcase
    # ------------------------------------------------------------------

    async def test_get_testcase_returns_none_when_not_found(self):
        result = await self.repo.get_testcase(999)
        self.assertIsNone(result)

    async def test_get_testcase_returns_dict_when_found(self):
        pid = self._insert_project("Alpha")
        tc_id = self._insert_testcase(pid, "Login Test", description="Verify login")
        result = await self.repo.get_testcase(tc_id)
        self.assertIsNotNone(result)
        self.assertEqual(result["id"], tc_id)
        self.assertEqual(result["project_id"], pid)
        self.assertEqual(result["name"], "Login Test")
        self.assertEqual(result["description"], "Verify login")
        self.assertIsNone(result["folder_id"])

    # ------------------------------------------------------------------
    # get_folder_project_id
    # ------------------------------------------------------------------

    async def test_get_folder_project_id_returns_none_when_not_found(self):
        result = await self.repo.get_folder_project_id(999)
        self.assertIsNone(result)

    async def test_get_folder_project_id_returns_project_id_when_found(self):
        pid = self._insert_project("Alpha")
        fid = self._insert_folder(pid, "Suite A")
        result = await self.repo.get_folder_project_id(fid)
        self.assertEqual(result, pid)

    # ------------------------------------------------------------------
    # testcase_name_exists
    # ------------------------------------------------------------------

    async def test_name_exists_returns_false_when_empty(self):
        pid = self._insert_project("Alpha")
        result = await self.repo.testcase_name_exists(pid, None, "Login Test")
        self.assertFalse(result)

    async def test_name_exists_returns_true_for_root_level_match(self):
        pid = self._insert_project("Alpha")
        self._insert_testcase(pid, "Login Test")
        result = await self.repo.testcase_name_exists(pid, None, "Login Test")
        self.assertTrue(result)

    async def test_name_exists_returns_true_for_folder_match(self):
        pid = self._insert_project("Alpha")
        fid = self._insert_folder(pid, "Suite A")
        self._insert_testcase(pid, "Login Test", folder_id=fid)
        result = await self.repo.testcase_name_exists(pid, fid, "Login Test")
        self.assertTrue(result)

    async def test_name_exists_does_not_match_different_folder(self):
        pid = self._insert_project("Alpha")
        fid_a = self._insert_folder(pid, "Suite A")
        fid_b = self._insert_folder(pid, "Suite B")
        self._insert_testcase(pid, "Login Test", folder_id=fid_a)
        result = await self.repo.testcase_name_exists(pid, fid_b, "Login Test")
        self.assertFalse(result)

    async def test_name_exists_returns_false_with_own_exclude_id(self):
        pid = self._insert_project("Alpha")
        tc_id = self._insert_testcase(pid, "Login Test")
        result = await self.repo.testcase_name_exists(
            pid, None, "Login Test", exclude_id=tc_id)
        self.assertFalse(result)

    # ------------------------------------------------------------------
    # add_testcase
    # ------------------------------------------------------------------

    async def test_add_testcase_returns_new_id(self):
        pid = self._insert_project("Alpha")
        result = await self.repo.add_testcase(
            pid, None, "Login Test", "Verify login")
        self.assertIsInstance(result, int)
        conn = sqlite3.connect(self.db_path)
        row = conn.execute(
            "SELECT name, description, folder_id FROM tc_test_cases "
            "WHERE id = ?", (result,)).fetchone()
        conn.close()
        self.assertEqual(row, ("Login Test", "Verify login", None))

    async def test_add_testcase_with_folder(self):
        pid = self._insert_project("Alpha")
        fid = self._insert_folder(pid, "Suite A")
        result = await self.repo.add_testcase(
            pid, fid, "Login Test", "")
        conn = sqlite3.connect(self.db_path)
        row = conn.execute(
            "SELECT folder_id FROM tc_test_cases WHERE id = ?",
            (result,)).fetchone()
        conn.close()
        self.assertEqual(row[0], fid)

    # ------------------------------------------------------------------
    # update_testcase
    # ------------------------------------------------------------------

    async def test_update_testcase_renames_and_updates_description(self):
        pid = self._insert_project("Alpha")
        tc_id = self._insert_testcase(pid, "Old", description="Old desc")
        await self.repo.update_testcase(tc_id, "New", "New desc")
        conn = sqlite3.connect(self.db_path)
        row = conn.execute(
            "SELECT name, description FROM tc_test_cases WHERE id = ?",
            (tc_id,)).fetchone()
        conn.close()
        self.assertEqual(row, ("New", "New desc"))

    # ------------------------------------------------------------------
    # delete_testcase
    # ------------------------------------------------------------------

    async def test_delete_testcase_removes_row(self):
        pid = self._insert_project("Alpha")
        tc_id = self._insert_testcase(pid, "Login Test")
        await self.repo.delete_testcase(tc_id)
        conn = sqlite3.connect(self.db_path)
        rows = conn.execute(
            "SELECT id FROM tc_test_cases WHERE id = ?", (tc_id,)).fetchall()
        conn.close()
        self.assertEqual(rows, [])


if __name__ == "__main__":
    unittest.main()
