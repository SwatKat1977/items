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
from items.services.items_cms.repositories.project_repository import ProjectRepository
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
"""


class TestProjectRepository(unittest.IsolatedAsyncioTestCase):
    """Integration tests for ProjectRepository against a real SQLite DB."""

    async def asyncSetUp(self):
        fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        conn = sqlite3.connect(self.db_path)
        conn.executescript(_SCHEMA_SQL)
        conn.close()

        mock_config = MagicMock(spec=CMSConfiguration)
        mock_config.backend_db_filename = self.db_path
        self.repo = ProjectRepository(MagicMock(), mock_config)

    async def asyncTearDown(self):
        try:
            os.unlink(self.db_path)
        except OSError:
            pass

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _insert_project(self, name, awaiting_purge=False, announcement="",
                        show_on_overview=False):
        conn = sqlite3.connect(self.db_path)
        cur = conn.execute(
            "INSERT INTO prj_projects "
            "(name, awaiting_purge, announcement, show_announcement_on_overview) "
            "VALUES (?, ?, ?, ?)",
            (name, int(awaiting_purge), announcement, int(show_on_overview)))
        row_id = cur.lastrowid
        conn.commit()
        conn.close()
        return row_id

    def _query(self, sql, params=()):
        conn = sqlite3.connect(self.db_path)
        rows = conn.execute(sql, params).fetchall()
        conn.close()
        return rows

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
    # get_project_details
    # ------------------------------------------------------------------

    async def test_get_project_details_returns_none_when_not_found(self):
        result = await self.repo.get_project_details(999)
        self.assertIsNone(result)

    async def test_get_project_details_returns_none_when_awaiting_purge(self):
        pid = self._insert_project("Alpha", awaiting_purge=True)
        result = await self.repo.get_project_details(pid)
        self.assertIsNone(result)

    async def test_get_project_details_returns_dict_when_found(self):
        pid = self._insert_project(
            "Alpha", announcement="Hello", show_on_overview=True)
        result = await self.repo.get_project_details(pid)
        self.assertIsNotNone(result)
        self.assertEqual(result["id"], pid)
        self.assertEqual(result["name"], "Alpha")
        self.assertEqual(result["announcement"], "Hello")
        self.assertEqual(result["show_announcement_on_overview"], 1)

    # ------------------------------------------------------------------
    # get_projects
    # ------------------------------------------------------------------

    async def test_get_projects_returns_empty_list_when_no_projects(self):
        result = await self.repo.get_projects(["name"])
        self.assertEqual(result, [])

    async def test_get_projects_excludes_awaiting_purge(self):
        self._insert_project("Active")
        self._insert_project("Purged", awaiting_purge=True)
        result = await self.repo.get_projects(["name"])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][1], "Active")

    async def test_get_projects_returns_requested_fields(self):
        self._insert_project("Alpha", announcement="msg")
        result = await self.repo.get_projects(["name", "announcement"])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][1], "Alpha")
        self.assertEqual(result[0][2], "msg")

    # ------------------------------------------------------------------
    # get_no_of_milestones_for_project / get_no_of_testruns_for_project
    # ------------------------------------------------------------------

    async def test_get_no_of_milestones_always_returns_zero(self):
        pid = self._insert_project("Alpha")
        result = await self.repo.get_no_of_milestones_for_project(pid)
        self.assertEqual(result, 0)

    async def test_get_no_of_testruns_always_returns_zero(self):
        pid = self._insert_project("Alpha")
        result = await self.repo.get_no_of_testruns_for_project(pid)
        self.assertEqual(result, 0)

    # ------------------------------------------------------------------
    # project_name_exists
    # ------------------------------------------------------------------

    async def test_project_name_exists_returns_false_when_empty(self):
        result = await self.repo.project_name_exists("Alpha")
        self.assertFalse(result)

    async def test_project_name_exists_returns_true_for_match(self):
        self._insert_project("Alpha")
        result = await self.repo.project_name_exists("Alpha")
        self.assertTrue(result)

    # ------------------------------------------------------------------
    # add_project
    # ------------------------------------------------------------------

    async def test_add_project_returns_new_id(self):
        result = await self.repo.add_project("Alpha", "msg", True)
        self.assertIsInstance(result, int)
        rows = self._query("SELECT name FROM prj_projects WHERE id = ?", (result,))
        self.assertEqual(rows[0][0], "Alpha")

    # ------------------------------------------------------------------
    # modify_project
    # ------------------------------------------------------------------

    async def test_modify_project_without_name_updates_other_fields(self):
        pid = self._insert_project("Alpha")
        await self.repo.modify_project(pid, "new announcement", True, name=None)
        rows = self._query(
            "SELECT name, announcement, show_announcement_on_overview "
            "FROM prj_projects WHERE id = ?", (pid,))
        self.assertEqual(rows[0][0], "Alpha")   # name unchanged
        self.assertEqual(rows[0][1], "new announcement")
        self.assertEqual(rows[0][2], 1)

    async def test_modify_project_with_name_updates_all_fields(self):
        pid = self._insert_project("Alpha")
        await self.repo.modify_project(pid, "ann", False, name="Beta")
        rows = self._query(
            "SELECT name, announcement FROM prj_projects WHERE id = ?", (pid,))
        self.assertEqual(rows[0][0], "Beta")
        self.assertEqual(rows[0][1], "ann")

    # ------------------------------------------------------------------
    # mark_project_for_purge
    # ------------------------------------------------------------------

    async def test_mark_project_for_purge_sets_flag(self):
        pid = self._insert_project("Alpha")
        await self.repo.mark_project_for_purge(pid)
        rows = self._query(
            "SELECT awaiting_purge FROM prj_projects WHERE id = ?", (pid,))
        self.assertEqual(rows[0][0], 1)

    # ------------------------------------------------------------------
    # hard_delete_project
    # ------------------------------------------------------------------

    async def test_hard_delete_project_removes_row(self):
        pid = self._insert_project("Alpha")
        await self.repo.hard_delete_project(pid)
        rows = self._query("SELECT id FROM prj_projects WHERE id = ?", (pid,))
        self.assertEqual(rows, [])

    # ------------------------------------------------------------------
    # get_project_id_by_name
    # ------------------------------------------------------------------

    async def test_get_project_id_by_name_returns_none_when_not_found(self):
        result = await self.repo.get_project_id_by_name("Missing")
        self.assertIsNone(result)

    async def test_get_project_id_by_name_returns_id(self):
        pid = self._insert_project("Alpha")
        result = await self.repo.get_project_id_by_name("Alpha")
        self.assertEqual(result, pid)


if __name__ == "__main__":
    unittest.main()
