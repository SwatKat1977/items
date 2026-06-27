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
"""


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
        self.assertEqual(result["name"], "Login Test")
        self.assertEqual(result["description"], "Verify login")
        self.assertIsNone(result["folder_id"])


if __name__ == "__main__":
    unittest.main()
