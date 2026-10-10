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
from items.services.items_cms.repositories.case_types_repository import (
    CaseTypeDeleteOutcome,
    CaseTypesRepository,
)
from weaver_framework.database.sqlite_interface import SqliteInterfaceException
from items.services.items_cms.cms_configuration import CMSConfiguration
from items.tool_cms_db_builder import db_tables_test_cases as tables


class TestCaseTypesRepository(unittest.IsolatedAsyncioTestCase):
    """Integration tests for CaseTypesRepository against a real SQLite DB.

    The schema (including the one-default partial index) is taken from
    the DB builder so the tests exercise the real DDL.
    """

    async def asyncSetUp(self):
        fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        conn = sqlite3.connect(self.db_path)
        conn.execute(tables.TABLE_SQL_TC_CASE_TYPES)
        conn.execute(tables.INDEX_SQL_TC_CASE_TYPES_ONE_DEFAULT)
        conn.close()

        mock_config = MagicMock(spec=CMSConfiguration)
        mock_config.backend_db_filename = self.db_path
        self.repo = CaseTypesRepository(MagicMock(), mock_config)

    async def asyncTearDown(self):
        try:
            os.unlink(self.db_path)
        except OSError:
            pass  # Windows may still hold a lock briefly

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _db_insert(self, name, is_default=0, description=""):
        conn = sqlite3.connect(self.db_path)
        try:
            cur = conn.execute(
                "INSERT INTO tc_case_types(name, description, is_default) "
                "VALUES (?, ?, ?)", (name, description, is_default))
            row_id = cur.lastrowid
            conn.commit()
            return row_id
        finally:
            conn.close()

    def _defaults(self):
        conn = sqlite3.connect(self.db_path)
        rows = conn.execute(
            "SELECT id FROM tc_case_types WHERE is_default = 1").fetchall()
        conn.close()
        return [r[0] for r in rows]

    # ------------------------------------------------------------------
    # case_type_name_exists
    # ------------------------------------------------------------------

    async def test_name_exists_false_when_empty(self):
        self.assertFalse(await self.repo.case_type_name_exists("Smoke"))

    async def test_name_exists_true_case_insensitive(self):
        self._db_insert("Smoke")
        self.assertTrue(await self.repo.case_type_name_exists("sMoKe"))

    async def test_name_exists_excludes_own_id(self):
        type_id = self._db_insert("Smoke")
        self.assertFalse(await self.repo.case_type_name_exists(
            "Smoke", exclude_id=type_id))

    async def test_name_exists_exclude_other_id_still_conflicts(self):
        self._db_insert("Smoke")
        other = self._db_insert("Sanity")
        self.assertTrue(await self.repo.case_type_name_exists(
            "Smoke", exclude_id=other))

    # ------------------------------------------------------------------
    # add_case_type
    # ------------------------------------------------------------------

    async def test_add_returns_id_and_is_non_default(self):
        type_id = await self.repo.add_case_type("Smoke", "desc")
        row = await self.repo.get_case_type(type_id)
        self.assertEqual(row[1:3], ("Smoke", "desc"))
        self.assertFalse(row[3])

    # ------------------------------------------------------------------
    # get_case_type / get_all_case_types
    # ------------------------------------------------------------------

    async def test_get_case_type_missing_returns_none(self):
        self.assertIsNone(await self.repo.get_case_type(99))

    async def test_get_all_ordered_by_name(self):
        self._db_insert("Zeta")
        self._db_insert("Alpha")
        rows = await self.repo.get_all_case_types()
        self.assertEqual([r[1] for r in rows], ["Alpha", "Zeta"])

    async def test_get_all_empty(self):
        self.assertEqual(await self.repo.get_all_case_types(), [])

    # ------------------------------------------------------------------
    # update_case_type
    # ------------------------------------------------------------------

    async def test_update_changes_name_and_description(self):
        type_id = self._db_insert("Old", description="old")
        self.assertTrue(
            await self.repo.update_case_type(type_id, "New", "new"))
        row = await self.repo.get_case_type(type_id)
        self.assertEqual(row[1:3], ("New", "new"))

    async def test_update_missing_returns_false(self):
        self.assertFalse(await self.repo.update_case_type(99, "x", ""))

    async def test_update_does_not_change_is_default(self):
        type_id = self._db_insert("Other", is_default=1)
        await self.repo.update_case_type(type_id, "Renamed", "")
        self.assertEqual(self._defaults(), [type_id])

    # ------------------------------------------------------------------
    # get_default_case_type_id
    # ------------------------------------------------------------------

    async def test_get_default_id(self):
        self._db_insert("A")
        default_id = self._db_insert("Other", is_default=1)
        self.assertEqual(
            await self.repo.get_default_case_type_id(), default_id)

    async def test_get_default_id_none_when_no_default(self):
        self._db_insert("A")
        self.assertIsNone(await self.repo.get_default_case_type_id())

    # ------------------------------------------------------------------
    # set_default_case_type
    # ------------------------------------------------------------------

    async def test_set_default_swaps_default(self):
        self._db_insert("Other", is_default=1)
        new = self._db_insert("Smoke")
        self.assertTrue(await self.repo.set_default_case_type(new))
        self.assertEqual(self._defaults(), [new])

    async def test_set_default_missing_returns_false_and_keeps_default(self):
        old = self._db_insert("Other", is_default=1)
        self.assertFalse(await self.repo.set_default_case_type(99))
        self.assertEqual(self._defaults(), [old])

    async def test_set_default_already_default_is_idempotent(self):
        old = self._db_insert("Other", is_default=1)
        self.assertTrue(await self.repo.set_default_case_type(old))
        self.assertEqual(self._defaults(), [old])

    async def test_set_default_works_when_no_current_default(self):
        new = self._db_insert("Smoke")
        self.assertTrue(await self.repo.set_default_case_type(new))
        self.assertEqual(self._defaults(), [new])

    async def test_db_rejects_second_default(self):
        self._db_insert("Other", is_default=1)
        with self.assertRaises(sqlite3.IntegrityError):
            self._db_insert("Smoke", is_default=1)


_DELETE_SCHEMA_SQL = """
CREATE TABLE prj_projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);
CREATE TABLE tc_folders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    parent_id INTEGER NULL,
    name TEXT NOT NULL
);
"""


class TestCaseTypesRepositoryDelete(unittest.IsolatedAsyncioTestCase):
    """Integration tests for CaseTypesRepository.delete_case_type.

    Uses the real DDL for case types and test cases (including the
    NOT NULL / ON DELETE RESTRICT foreign key), so the tests prove that
    reassignment really is what lets the delete through.
    """

    async def asyncSetUp(self):
        fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        conn = sqlite3.connect(self.db_path)
        conn.executescript(_DELETE_SCHEMA_SQL)
        conn.execute(tables.TABLE_SQL_TC_CASE_TYPES)
        conn.execute(tables.INDEX_SQL_TC_CASE_TYPES_ONE_DEFAULT)
        conn.execute(tables.TABLE_SQL_TC_TEST_CASES)
        conn.execute("INSERT INTO prj_projects (name) VALUES ('Alpha')")
        conn.commit()
        conn.close()

        mock_config = MagicMock(spec=CMSConfiguration)
        mock_config.backend_db_filename = self.db_path
        self.repo = CaseTypesRepository(MagicMock(), mock_config)

        self.default_id = self._insert_type("Other", is_default=1)
        self.smoke_id = self._insert_type("Smoke")
        self.sanity_id = self._insert_type("Sanity")

    async def asyncTearDown(self):
        try:
            os.unlink(self.db_path)
        except OSError:
            pass  # Windows may still hold a lock briefly

    def _insert_type(self, name, is_default=0):
        conn = sqlite3.connect(self.db_path)
        cur = conn.execute(
            "INSERT INTO tc_case_types (name, description, is_default) "
            "VALUES (?, '', ?)", (name, is_default))
        row_id = cur.lastrowid
        conn.commit()
        conn.close()
        return row_id

    def _insert_case(self, name, case_type_id):
        conn = sqlite3.connect(self.db_path)
        cur = conn.execute(
            "INSERT INTO tc_test_cases "
            "(project_id, folder_id, case_type_id, name, description) "
            "VALUES (1, NULL, ?, ?, '')", (case_type_id, name))
        row_id = cur.lastrowid
        conn.commit()
        conn.close()
        return row_id

    def _case_type_of(self, case_id):
        conn = sqlite3.connect(self.db_path)
        row = conn.execute(
            "SELECT case_type_id FROM tc_test_cases WHERE id = ?",
            (case_id,)).fetchone()
        conn.close()
        return row[0]

    def _type_ids(self):
        conn = sqlite3.connect(self.db_path)
        rows = conn.execute(
            "SELECT id FROM tc_case_types ORDER BY id").fetchall()
        conn.close()
        return [r[0] for r in rows]

    async def test_delete_unused_type(self):
        result = await self.repo.delete_case_type(self.smoke_id)
        self.assertIs(result, CaseTypeDeleteOutcome.DELETED)
        self.assertNotIn(self.smoke_id, self._type_ids())

    async def test_delete_moves_its_test_cases_to_the_default(self):
        case_a = self._insert_case("A", self.smoke_id)
        case_b = self._insert_case("B", self.smoke_id)
        result = await self.repo.delete_case_type(self.smoke_id)
        self.assertIs(result, CaseTypeDeleteOutcome.DELETED)
        self.assertEqual(self._case_type_of(case_a), self.default_id)
        self.assertEqual(self._case_type_of(case_b), self.default_id)

    async def test_delete_leaves_other_types_test_cases_alone(self):
        smoke_case = self._insert_case("A", self.smoke_id)
        sanity_case = self._insert_case("B", self.sanity_id)
        default_case = self._insert_case("C", self.default_id)
        await self.repo.delete_case_type(self.smoke_id)
        self.assertEqual(self._case_type_of(sanity_case), self.sanity_id)
        self.assertEqual(self._case_type_of(default_case), self.default_id)
        self.assertEqual(self._case_type_of(smoke_case), self.default_id)

    async def test_delete_moves_to_the_current_default_not_a_fixed_one(self):
        """The target is whichever type is default at delete time."""
        case = self._insert_case("A", self.smoke_id)
        conn = sqlite3.connect(self.db_path)
        conn.execute("UPDATE tc_case_types SET is_default = 0 "
                     "WHERE is_default = 1")
        conn.execute("UPDATE tc_case_types SET is_default = 1 WHERE id = ?",
                     (self.sanity_id,))
        conn.commit()
        conn.close()
        await self.repo.delete_case_type(self.smoke_id)
        self.assertEqual(self._case_type_of(case), self.sanity_id)

    async def test_delete_missing_type_reports_not_found(self):
        result = await self.repo.delete_case_type(999)
        self.assertIs(result, CaseTypeDeleteOutcome.NOT_FOUND)
        self.assertEqual(len(self._type_ids()), 3)

    async def test_delete_default_is_refused_and_changes_nothing(self):
        case = self._insert_case("A", self.default_id)
        result = await self.repo.delete_case_type(self.default_id)
        self.assertIs(result, CaseTypeDeleteOutcome.IS_DEFAULT)
        self.assertIn(self.default_id, self._type_ids())
        self.assertEqual(self._case_type_of(case), self.default_id)

    async def test_type_that_became_default_before_the_script_is_kept(self):
        """If the type is made the default between the lookup and the
        script, the guarded statements do nothing and it is reported as
        the default, not as deleted."""
        case = self._insert_case("A", self.smoke_id)
        db_path = self.db_path
        smoke_id = self.smoke_id

        class _PromoteAfterLookup:
            """Stands in for the repository's database: runs the real
            lookup, then makes the type the default before the script."""

            def __init__(self, real):
                self._real = real

            async def run_query(self, query, params=(), **kwargs):
                result = await self._real.run_query(query, params, **kwargs)
                if query.startswith("SELECT is_default"):
                    conn = sqlite3.connect(db_path)
                    conn.execute("UPDATE tc_case_types SET is_default = 0 "
                                 "WHERE is_default = 1")
                    conn.execute("UPDATE tc_case_types SET is_default = 1 "
                                 "WHERE id = ?", (smoke_id,))
                    conn.commit()
                    conn.close()
                return result

            async def run_script(self, query):
                return await self._real.run_script(query)

        self.repo._db = _PromoteAfterLookup(self.repo._db)  # pylint: disable=protected-access
        result = await self.repo.delete_case_type(self.smoke_id)

        self.assertIs(result, CaseTypeDeleteOutcome.IS_DEFAULT)
        self.assertIn(self.smoke_id, self._type_ids())
        self.assertEqual(self._case_type_of(case), self.smoke_id)

    async def test_failure_part_way_rolls_back_both_steps(self):
        """No default to move the test cases to: the UPDATE violates NOT
        NULL, so the script fails and the delete must not have happened."""
        case = self._insert_case("A", self.smoke_id)
        conn = sqlite3.connect(self.db_path)
        conn.execute("UPDATE tc_case_types SET is_default = 0")
        conn.commit()
        conn.close()
        with self.assertRaises(SqliteInterfaceException):
            await self.repo.delete_case_type(self.smoke_id)
        self.assertIn(self.smoke_id, self._type_ids())
        self.assertEqual(self._case_type_of(case), self.smoke_id)
