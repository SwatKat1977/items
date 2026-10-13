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
from items.services.items_cms.repositories.folder_repository import (
    FolderRepository)
from items.services.items_cms.cms_configuration import CMSConfiguration

_SCHEMA_SQL = """
CREATE TABLE prj_projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
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
CREATE TABLE tc_case_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT NOT NULL DEFAULT '',
    is_default INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE tc_test_cases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    folder_id INTEGER NULL,
    case_type_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    FOREIGN KEY (project_id) REFERENCES prj_projects(id) ON DELETE CASCADE,
    FOREIGN KEY (folder_id) REFERENCES tc_folders(id) ON DELETE CASCADE,
    FOREIGN KEY (case_type_id) REFERENCES tc_case_types(id) ON DELETE RESTRICT,
    UNIQUE (project_id, folder_id, name)
);
INSERT INTO tc_case_types (name, is_default) VALUES ('Other', 1);
"""


class TestFolderRepository(unittest.IsolatedAsyncioTestCase):
    """Integration tests for FolderRepository against a real SQLite DB."""

    async def asyncSetUp(self):
        fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        conn = sqlite3.connect(self.db_path)
        conn.executescript(_SCHEMA_SQL)
        conn.close()

        mock_config = MagicMock(spec=CMSConfiguration)
        mock_config.backend_db_filename = self.db_path
        self.repo = FolderRepository(MagicMock(), mock_config)

        self.project_id = self._insert_project("Alpha")

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
        cur = conn.execute(
            "INSERT INTO prj_projects (name) VALUES (?)", (name,))
        row_id = cur.lastrowid
        conn.commit()
        conn.close()
        return row_id

    def _insert_folder(self, project_id, parent_id, name):
        conn = sqlite3.connect(self.db_path)
        cur = conn.execute(
            "INSERT INTO tc_folders (project_id, parent_id, name) "
            "VALUES (?, ?, ?)", (project_id, parent_id, name))
        row_id = cur.lastrowid
        conn.commit()
        conn.close()
        return row_id

    def _insert_testcase(self, folder_id, name):
        conn = sqlite3.connect(self.db_path)
        cur = conn.execute(
            "INSERT INTO tc_test_cases "
            "(project_id, folder_id, case_type_id, name, description) "
            "VALUES (?, ?, 1, ?, '')", (self.project_id, folder_id, name))
        row_id = cur.lastrowid
        conn.commit()
        conn.close()
        return row_id

    def _testcase_ids(self):
        return [r[0] for r in self._query(
            "SELECT id FROM tc_test_cases ORDER BY id")]

    def _folder_ids(self):
        return [r[0] for r in self._query(
            "SELECT id FROM tc_folders ORDER BY id")]

    def _query(self, sql, params=()):
        conn = sqlite3.connect(self.db_path)
        rows = conn.execute(sql, params).fetchall()
        conn.close()
        return rows

    # ------------------------------------------------------------------
    # is_valid_project_id
    # ------------------------------------------------------------------

    async def test_is_valid_project_id_returns_true_when_found(self):
        result = await self.repo.is_valid_project_id(self.project_id)
        self.assertTrue(result)

    async def test_is_valid_project_id_returns_false_when_not_found(self):
        result = await self.repo.is_valid_project_id(999)
        self.assertFalse(result)

    # ------------------------------------------------------------------
    # get_folder
    # ------------------------------------------------------------------

    async def test_get_folder_returns_none_when_not_found(self):
        result = await self.repo.get_folder(999)
        self.assertIsNone(result)

    async def test_get_folder_returns_dict_when_found(self):
        fid = self._insert_folder(self.project_id, None, "Root")
        result = await self.repo.get_folder(fid)
        self.assertEqual(result, {
            "id": fid,
            "project_id": self.project_id,
            "parent_id": None,
            "name": "Root"
        })

    # ------------------------------------------------------------------
    # get_folders
    # ------------------------------------------------------------------

    async def test_get_folders_returns_empty_list_when_none(self):
        result = await self.repo.get_folders(self.project_id)
        self.assertEqual(result, [])

    async def test_get_folders_returns_flat_list(self):
        root_id = self._insert_folder(self.project_id, None, "Root")
        child_id = self._insert_folder(self.project_id, root_id, "Child")
        result = await self.repo.get_folders(self.project_id)
        self.assertEqual(result, [
            {"id": root_id, "parent_id": None, "name": "Root"},
            {"id": child_id, "parent_id": root_id, "name": "Child"},
        ])

    async def test_get_folders_scoped_to_project(self):
        other_project_id = self._insert_project("Beta")
        self._insert_folder(self.project_id, None, "MineOnly")
        self._insert_folder(other_project_id, None, "NotMine")
        result = await self.repo.get_folders(self.project_id)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["name"], "MineOnly")

    # ------------------------------------------------------------------
    # folder_name_exists
    # ------------------------------------------------------------------

    async def test_name_exists_returns_false_when_empty(self):
        result = await self.repo.folder_name_exists(
            self.project_id, None, "Root")
        self.assertFalse(result)

    async def test_name_exists_returns_true_for_root_level_match(self):
        self._insert_folder(self.project_id, None, "Root")
        result = await self.repo.folder_name_exists(
            self.project_id, None, "Root")
        self.assertTrue(result)

    async def test_name_exists_returns_true_for_nested_match(self):
        root_id = self._insert_folder(self.project_id, None, "Root")
        self._insert_folder(self.project_id, root_id, "Child")
        result = await self.repo.folder_name_exists(
            self.project_id, root_id, "Child")
        self.assertTrue(result)

    async def test_name_exists_does_not_match_different_parent(self):
        root_a = self._insert_folder(self.project_id, None, "RootA")
        root_b = self._insert_folder(self.project_id, None, "RootB")
        self._insert_folder(self.project_id, root_a, "Child")
        result = await self.repo.folder_name_exists(
            self.project_id, root_b, "Child")
        self.assertFalse(result)

    async def test_name_exists_returns_false_with_own_exclude_id(self):
        fid = self._insert_folder(self.project_id, None, "Root")
        result = await self.repo.folder_name_exists(
            self.project_id, None, "Root", exclude_id=fid)
        self.assertFalse(result)

    # ------------------------------------------------------------------
    # add_folder
    # ------------------------------------------------------------------

    async def test_add_folder_returns_new_id(self):
        result = await self.repo.add_folder(self.project_id, None, "Root")
        self.assertIsInstance(result, int)
        rows = self._query(
            "SELECT name, parent_id FROM tc_folders WHERE id = ?", (result,))
        self.assertEqual(rows[0], ("Root", None))

    async def test_add_folder_with_parent(self):
        root_id = self._insert_folder(self.project_id, None, "Root")
        result = await self.repo.add_folder(self.project_id, root_id, "Child")
        rows = self._query(
            "SELECT parent_id FROM tc_folders WHERE id = ?", (result,))
        self.assertEqual(rows[0][0], root_id)

    # ------------------------------------------------------------------
    # update_folder_name
    # ------------------------------------------------------------------

    async def test_update_folder_name_renames(self):
        fid = self._insert_folder(self.project_id, None, "Old")
        await self.repo.update_folder_name(fid, "New")
        rows = self._query("SELECT name FROM tc_folders WHERE id = ?", (fid,))
        self.assertEqual(rows[0][0], "New")

    # ------------------------------------------------------------------
    # delete_folder
    # ------------------------------------------------------------------

    async def test_delete_folder_removes_row(self):
        fid = self._insert_folder(self.project_id, None, "Root")
        await self.repo.delete_folder(fid)
        rows = self._query("SELECT id FROM tc_folders WHERE id = ?", (fid,))
        self.assertEqual(rows, [])

    async def test_delete_folder_cascades_to_children(self):
        root_id = self._insert_folder(self.project_id, None, "Root")
        child_id = self._insert_folder(self.project_id, root_id, "Child")
        await self.repo.delete_folder(root_id)
        rows = self._query(
            "SELECT id FROM tc_folders WHERE id IN (?, ?)",
            (root_id, child_id))
        self.assertEqual(rows, [])

    # ------------------------------------------------------------------
    # delete_folder must not destroy test cases unless told to
    # ------------------------------------------------------------------

    # ------------------------------------------------------------------
    # count_testcases_in_subtree
    # ------------------------------------------------------------------

    async def test_count_is_zero_for_an_empty_folder(self):
        fid = self._insert_folder(self.project_id, None, "Root")
        self.assertEqual(await self.repo.count_testcases_in_subtree(fid), 0)

    async def test_count_includes_test_cases_directly_in_the_folder(self):
        fid = self._insert_folder(self.project_id, None, "Root")
        self._insert_testcase(fid, "A")
        self._insert_testcase(fid, "B")
        self.assertEqual(await self.repo.count_testcases_in_subtree(fid), 2)

    async def test_count_includes_deeply_nested_descendants(self):
        root_id = self._insert_folder(self.project_id, None, "Root")
        child_id = self._insert_folder(self.project_id, root_id, "Child")
        grand_id = self._insert_folder(self.project_id, child_id, "Grand")
        self._insert_testcase(root_id, "R")
        self._insert_testcase(child_id, "C")
        self._insert_testcase(grand_id, "G1")
        self._insert_testcase(grand_id, "G2")
        self.assertEqual(
            await self.repo.count_testcases_in_subtree(root_id), 4)
        self.assertEqual(
            await self.repo.count_testcases_in_subtree(child_id), 3)
        self.assertEqual(
            await self.repo.count_testcases_in_subtree(grand_id), 2)

    async def test_count_ignores_siblings_and_root_level_test_cases(self):
        a_id = self._insert_folder(self.project_id, None, "A")
        b_id = self._insert_folder(self.project_id, None, "B")
        self._insert_testcase(a_id, "InA")
        self._insert_testcase(b_id, "InB")
        self._insert_testcase(None, "NoFolder")
        self.assertEqual(await self.repo.count_testcases_in_subtree(a_id), 1)

    # ------------------------------------------------------------------
    # delete_folder without cascade
    # ------------------------------------------------------------------

    async def test_empty_folder_is_deleted_and_returns_zero(self):
        fid = self._insert_folder(self.project_id, None, "Root")
        self.assertEqual(await self.repo.delete_folder(fid), 0)
        self.assertEqual(self._folder_ids(), [])

    async def test_empty_tree_is_deleted_whole(self):
        root_id = self._insert_folder(self.project_id, None, "Root")
        self._insert_folder(self.project_id, root_id, "Child")
        self.assertEqual(await self.repo.delete_folder(root_id), 0)
        self.assertEqual(self._folder_ids(), [])

    async def test_folder_with_test_cases_is_refused_and_untouched(self):
        fid = self._insert_folder(self.project_id, None, "Root")
        tc_id = self._insert_testcase(fid, "Keep me")
        self.assertEqual(await self.repo.delete_folder(fid), 1)
        self.assertEqual(self._folder_ids(), [fid])
        self.assertEqual(self._testcase_ids(), [tc_id])

    async def test_test_case_in_a_descendant_blocks_the_delete(self):
        root_id = self._insert_folder(self.project_id, None, "Root")
        child_id = self._insert_folder(self.project_id, root_id, "Child")
        tc_id = self._insert_testcase(child_id, "Deep")
        self.assertEqual(await self.repo.delete_folder(root_id), 1)
        self.assertEqual(self._folder_ids(), [root_id, child_id])
        self.assertEqual(self._testcase_ids(), [tc_id])

    async def test_refusal_reports_the_whole_subtree_count(self):
        root_id = self._insert_folder(self.project_id, None, "Root")
        child_id = self._insert_folder(self.project_id, root_id, "Child")
        self._insert_testcase(root_id, "R")
        self._insert_testcase(child_id, "C1")
        self._insert_testcase(child_id, "C2")
        self.assertEqual(await self.repo.delete_folder(root_id), 3)

    async def test_deleting_an_empty_folder_leaves_other_folders_alone(self):
        empty_id = self._insert_folder(self.project_id, None, "Empty")
        full_id = self._insert_folder(self.project_id, None, "Full")
        tc_id = self._insert_testcase(full_id, "Keep")
        self.assertEqual(await self.repo.delete_folder(empty_id), 0)
        self.assertEqual(self._folder_ids(), [full_id])
        self.assertEqual(self._testcase_ids(), [tc_id])

    # ------------------------------------------------------------------
    # delete_folder with cascade
    # ------------------------------------------------------------------

    async def test_cascade_deletes_the_folder_and_its_test_cases(self):
        fid = self._insert_folder(self.project_id, None, "Root")
        self._insert_testcase(fid, "Gone")
        self.assertEqual(await self.repo.delete_folder(fid, cascade=True), 0)
        self.assertEqual(self._folder_ids(), [])
        self.assertEqual(self._testcase_ids(), [])

    async def test_cascade_deletes_descendants_and_their_test_cases(self):
        root_id = self._insert_folder(self.project_id, None, "Root")
        child_id = self._insert_folder(self.project_id, root_id, "Child")
        self._insert_testcase(root_id, "R")
        self._insert_testcase(child_id, "C")
        await self.repo.delete_folder(root_id, cascade=True)
        self.assertEqual(self._folder_ids(), [])
        self.assertEqual(self._testcase_ids(), [])

    async def test_cascade_leaves_unrelated_test_cases_alone(self):
        gone_id = self._insert_folder(self.project_id, None, "Gone")
        keep_id = self._insert_folder(self.project_id, None, "Keep")
        self._insert_testcase(gone_id, "Gone")
        keep_tc = self._insert_testcase(keep_id, "Keep")
        root_tc = self._insert_testcase(None, "NoFolder")
        await self.repo.delete_folder(gone_id, cascade=True)
        self.assertEqual(self._testcase_ids(), [keep_tc, root_tc])

    # ------------------------------------------------------------------
    # The race: a test case arrives after the count
    # ------------------------------------------------------------------

    async def test_a_test_case_added_after_the_count_is_not_destroyed(self):
        """The count said empty, then someone added a test case to a
        sub-folder before the delete ran. The guarded delete must not
        remove it, and the caller is told it was blocked."""
        root_id = self._insert_folder(self.project_id, None, "Root")
        child_id = self._insert_folder(self.project_id, root_id, "Child")
        test = self
        new_tc = {}

        class _AddTestcaseAfterCount:
            """Runs the real count, then adds a test case to the child."""

            def __init__(self, real):
                self._real = real

            async def run_query(self, query, params=(), **kwargs):
                result = await self._real.run_query(query, params, **kwargs)
                if query.startswith("WITH RECURSIVE") and not new_tc:
                    new_tc["id"] = test._insert_testcase(child_id, "Late")
                return result

            async def run_script(self, query):
                return await self._real.run_script(query)

        self.repo._db = _AddTestcaseAfterCount(self.repo._db)
        blocking = await self.repo.delete_folder(root_id)

        self.assertEqual(blocking, 1)
        self.assertEqual(self._folder_ids(), [root_id, child_id])
        self.assertEqual(self._testcase_ids(), [new_tc["id"]])


if __name__ == "__main__":
    unittest.main()
