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
    CaseTypesRepository,
)
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
