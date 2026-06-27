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
from items.services.items_cms.repositories.testcase_custom_fields_repository import (
    TestcaseCustomFieldsRepository,
    CustomFieldMoveDirection,
)
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
CREATE TABLE tc_custom_field_option_kinds (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    option_name TEXT NOT NULL UNIQUE
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
CREATE TABLE tc_custom_field_type_options (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    field_id INTEGER NOT NULL,
    option_kind_id INTEGER NOT NULL,
    option_value TEXT NOT NULL,
    FOREIGN KEY (field_id) REFERENCES tc_custom_fields(id),
    FOREIGN KEY (option_kind_id) REFERENCES tc_custom_field_option_kinds(id),
    UNIQUE (field_id, option_kind_id)
);
CREATE TABLE tc_custom_field_type_option_values (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    case_field_id INTEGER NOT NULL,
    field_type_option_id INTEGER NOT NULL,
    option_value TEXT NOT NULL,
    FOREIGN KEY (case_field_id) REFERENCES tc_custom_fields(id)
);
CREATE TABLE tc_custom_field_option_values (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    test_case_id INTEGER NOT NULL,
    field_id INTEGER NOT NULL,
    value TEXT NOT NULL,
    FOREIGN KEY (field_id) REFERENCES tc_custom_fields(id) ON DELETE CASCADE,
    UNIQUE(test_case_id, field_id)
);
INSERT INTO tc_custom_field_types (name, supports_default_value, supports_is_required)
VALUES
    ('Checkbox', 1, 0),
    ('Date',     0, 1),
    ('Dropdown', 1, 1),
    ('Integer',  1, 1),
    ('String',   1, 1),
    ('Text',     1, 1),
    ('Url (Link)', 1, 1),
    ('User',     1, 1);
"""

# Type IDs that match the seed order above
_STRING_TYPE_ID = 5
_INTEGER_TYPE_ID = 4


class TestTestcaseCustomFieldsRepository(unittest.IsolatedAsyncioTestCase):
    """Integration tests for TestcaseCustomFieldsRepository against a real SQLite DB."""

    async def asyncSetUp(self):
        fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        conn = sqlite3.connect(self.db_path)
        conn.executescript(_SCHEMA_SQL)
        conn.close()

        mock_config = MagicMock(spec=CMSConfiguration)
        mock_config.backend_db_filename = self.db_path
        self.repo = TestcaseCustomFieldsRepository(MagicMock(), mock_config)

    async def asyncTearDown(self):
        try:
            os.unlink(self.db_path)
        except OSError:
            pass  # Windows may still hold a lock briefly

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

    def _insert_field(self, field_name, system_name,
                      field_type_id=_STRING_TYPE_ID,
                      entry_type="user", position=None,
                      applies_to_all=True):
        if position is None:
            existing = self._db_query(
                "SELECT MAX(position) FROM tc_custom_fields")
            position = (existing[0][0] or 0) + 1
        return self._db_insert(
            "INSERT INTO tc_custom_fields "
            "(field_name, description, system_name, field_type_id, entry_type, "
            "enabled, position, is_required, default_value, applies_to_all_projects) "
            "VALUES (?, '', ?, ?, ?, 1, ?, 0, '', ?)",
            (field_name, system_name, field_type_id, entry_type,
             position, applies_to_all))

    def _insert_project(self, name):
        return self._db_insert(
            "INSERT INTO prj_projects (name) VALUES (?)", (name,))

    def _count_rows(self, table, where="", params=()):
        rows = self._db_query(
            f"SELECT COUNT(*) FROM {table}" + (f" WHERE {where}" if where else ""),
            params)
        return rows[0][0]

    def _get_position(self, field_id):
        rows = self._db_query(
            "SELECT position FROM tc_custom_fields WHERE id = ?", (field_id,))
        return rows[0][0] if rows else None

    # ------------------------------------------------------------------
    # custom_field_name_exists
    # ------------------------------------------------------------------

    async def test_name_exists_returns_false_when_empty(self):
        result = await self.repo.custom_field_name_exists("Priority")
        self.assertFalse(result)

    async def test_name_exists_returns_true_for_match(self):
        self._insert_field("Priority", "priority")
        result = await self.repo.custom_field_name_exists("Priority")
        self.assertTrue(result)

    async def test_name_exists_is_case_insensitive(self):
        self._insert_field("Priority", "priority")
        result = await self.repo.custom_field_name_exists("PRIORITY")
        self.assertTrue(result)

    async def test_name_exists_returns_false_with_own_exclude_id(self):
        field_id = self._insert_field("Priority", "priority")
        result = await self.repo.custom_field_name_exists(
            "Priority", exclude_id=field_id)
        self.assertFalse(result)

    async def test_name_exists_returns_true_with_other_exclude_id(self):
        self._insert_field("Priority", "priority")
        other_id = self._insert_field("Severity", "severity")
        result = await self.repo.custom_field_name_exists(
            "Priority", exclude_id=other_id)
        self.assertTrue(result)

    # ------------------------------------------------------------------
    # system_name_exists
    # ------------------------------------------------------------------

    async def test_system_name_exists_returns_false_when_empty(self):
        result = await self.repo.system_name_exists("priority")
        self.assertFalse(result)

    async def test_system_name_exists_returns_true_for_match(self):
        self._insert_field("Priority", "priority")
        result = await self.repo.system_name_exists("priority")
        self.assertTrue(result)

    async def test_system_name_exists_returns_false_with_own_exclude_id(self):
        field_id = self._insert_field("Priority", "priority")
        result = await self.repo.system_name_exists(
            "priority", exclude_id=field_id)
        self.assertFalse(result)

    # ------------------------------------------------------------------
    # add_custom_field
    # ------------------------------------------------------------------

    async def test_add_custom_field_returns_none_for_unknown_type(self):
        result = await self.repo.add_custom_field(
            "Priority", "desc", "priority", "NotAType",
            True, False, "", True)
        self.assertIsNone(result)
        self.assertEqual(self._count_rows("tc_custom_fields"), 0)

    async def test_add_custom_field_returns_new_id(self):
        result = await self.repo.add_custom_field(
            "Priority", "desc", "priority", "String",
            True, False, "", True)
        self.assertIsNotNone(result)
        self.assertIsInstance(result, int)
        self.assertEqual(self._count_rows("tc_custom_fields"), 1)

    async def test_add_custom_field_entry_type_is_user(self):
        field_id = await self.repo.add_custom_field(
            "Priority", "desc", "priority", "String",
            True, False, "", True)
        rows = self._db_query(
            "SELECT entry_type FROM tc_custom_fields WHERE id = ?", (field_id,))
        self.assertEqual(rows[0][0], "user")

    async def test_add_custom_field_positions_increment(self):
        id1 = await self.repo.add_custom_field(
            "Priority", "desc", "priority", "String",
            True, False, "", True)
        id2 = await self.repo.add_custom_field(
            "Severity", "desc", "severity", "String",
            True, False, "", True)
        self.assertEqual(self._get_position(id1), 1)
        self.assertEqual(self._get_position(id2), 2)

    # ------------------------------------------------------------------
    # resolve_project_names
    # ------------------------------------------------------------------

    async def test_resolve_project_names_returns_none_for_unknown(self):
        result = await self.repo.resolve_project_names(["DoesNotExist"])
        self.assertIsNone(result)

    async def test_resolve_project_names_returns_ids(self):
        pid1 = self._insert_project("Alpha")
        pid2 = self._insert_project("Beta")
        result = await self.repo.resolve_project_names(["Alpha", "Beta"])
        self.assertEqual(result, [pid1, pid2])

    async def test_resolve_project_names_returns_none_if_any_invalid(self):
        self._insert_project("Alpha")
        result = await self.repo.resolve_project_names(["Alpha", "Missing"])
        self.assertIsNone(result)

    # ------------------------------------------------------------------
    # assign_custom_field_to_projects
    # ------------------------------------------------------------------

    async def test_assign_custom_field_to_projects_creates_links(self):
        field_id = self._insert_field("Priority", "priority")
        pid1 = self._insert_project("Alpha")
        pid2 = self._insert_project("Beta")
        await self.repo.assign_custom_field_to_projects(
            field_id, [pid1, pid2])
        self.assertEqual(
            self._count_rows(
                "tc_custom_field_projects", "field_id = ?", (field_id,)),
            2)

    # ------------------------------------------------------------------
    # get_custom_field
    # ------------------------------------------------------------------

    async def test_get_custom_field_returns_none_when_not_found(self):
        result = await self.repo.get_custom_field(999)
        self.assertIsNone(result)

    async def test_get_custom_field_returns_row_when_found(self):
        field_id = self._insert_field("Priority", "priority")
        result = await self.repo.get_custom_field(field_id)
        self.assertIsNotNone(result)
        self.assertEqual(result[0], field_id)
        self.assertEqual(result[1], "Priority")

    async def test_get_custom_field_linked_projects_null_when_global(self):
        field_id = self._insert_field(
            "Priority", "priority", applies_to_all=True)
        result = await self.repo.get_custom_field(field_id)
        self.assertIsNone(result[11])  # linked_projects column

    async def test_get_custom_field_linked_projects_populated(self):
        field_id = self._insert_field(
            "Priority", "priority", applies_to_all=False)
        pid = self._insert_project("Alpha")
        self._db_insert(
            "INSERT INTO tc_custom_field_projects (field_id, project_id) "
            "VALUES (?, ?)", (field_id, pid))
        result = await self.repo.get_custom_field(field_id)
        self.assertIsNotNone(result[11])
        self.assertIn("Alpha", result[11])

    # ------------------------------------------------------------------
    # get_all_fields
    # ------------------------------------------------------------------

    async def test_get_all_fields_returns_empty_list(self):
        result = await self.repo.get_all_fields()
        self.assertEqual(result, [])

    async def test_get_all_fields_returns_rows_in_position_order(self):
        id1 = self._insert_field("Alpha", "alpha", position=1)
        id2 = self._insert_field("Beta", "beta", position=2)
        result = await self.repo.get_all_fields()
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0][0], id1)
        self.assertEqual(result[1][0], id2)

    # ------------------------------------------------------------------
    # get_fields_for_project
    # ------------------------------------------------------------------

    async def test_get_fields_for_project_includes_global_fields(self):
        self._insert_field("Global", "global_f", applies_to_all=True)
        pid = self._insert_project("Alpha")
        result = await self.repo.get_fields_for_project(pid)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][1], "Global")

    async def test_get_fields_for_project_includes_linked_fields(self):
        field_id = self._insert_field(
            "Local", "local_f", applies_to_all=False)
        pid = self._insert_project("Alpha")
        self._db_insert(
            "INSERT INTO tc_custom_field_projects (field_id, project_id) "
            "VALUES (?, ?)", (field_id, pid))
        result = await self.repo.get_fields_for_project(pid)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][1], "Local")

    async def test_get_fields_for_project_excludes_other_project_fields(self):
        field_id = self._insert_field(
            "OtherOnly", "other_f", applies_to_all=False)
        pid_alpha = self._insert_project("Alpha")
        pid_beta = self._insert_project("Beta")
        self._db_insert(
            "INSERT INTO tc_custom_field_projects (field_id, project_id) "
            "VALUES (?, ?)", (field_id, pid_beta))
        result = await self.repo.get_fields_for_project(pid_alpha)
        self.assertEqual(result, [])

    # ------------------------------------------------------------------
    # move_custom_field
    # ------------------------------------------------------------------

    async def test_move_returns_false_when_field_not_found(self):
        result = await self.repo.move_custom_field(
            999, CustomFieldMoveDirection.UP)
        self.assertFalse(result)

    async def test_move_returns_none_at_upper_boundary(self):
        field_id = self._insert_field("Only", "only", position=1)
        result = await self.repo.move_custom_field(
            field_id, CustomFieldMoveDirection.UP)
        self.assertIsNone(result)

    async def test_move_returns_none_at_lower_boundary(self):
        field_id = self._insert_field("Only", "only", position=1)
        result = await self.repo.move_custom_field(
            field_id, CustomFieldMoveDirection.DOWN)
        self.assertIsNone(result)

    async def test_move_up_swaps_positions(self):
        id1 = self._insert_field("First", "first", position=1)
        id2 = self._insert_field("Second", "second", position=2)
        result = await self.repo.move_custom_field(
            id2, CustomFieldMoveDirection.UP)
        self.assertTrue(result)
        self.assertEqual(self._get_position(id2), 1)
        self.assertEqual(self._get_position(id1), 2)

    async def test_move_down_swaps_positions(self):
        id1 = self._insert_field("First", "first", position=1)
        id2 = self._insert_field("Second", "second", position=2)
        result = await self.repo.move_custom_field(
            id1, CustomFieldMoveDirection.DOWN)
        self.assertTrue(result)
        self.assertEqual(self._get_position(id1), 2)
        self.assertEqual(self._get_position(id2), 1)

    # ------------------------------------------------------------------
    # update_custom_field
    # ------------------------------------------------------------------

    async def test_update_returns_false_when_not_found(self):
        result = await self.repo.update_custom_field(
            999, "Name", "desc", "name", "String",
            True, False, "", True, [])
        self.assertFalse(result)

    async def test_update_returns_none_for_system_field(self):
        field_id = self._insert_field(
            "SysField", "sys_field", entry_type="system")
        result = await self.repo.update_custom_field(
            field_id, "SysField", "desc", "sys_field", "String",
            True, False, "", True, [])
        self.assertIsNone(result)

    async def test_update_returns_none_for_invalid_type(self):
        field_id = self._insert_field("Priority", "priority")
        result = await self.repo.update_custom_field(
            field_id, "Priority", "desc", "priority", "NotAType",
            True, False, "", True, [])
        self.assertIsNone(result)

    async def test_update_success_saves_new_values(self):
        field_id = self._insert_field("Priority", "priority")
        result = await self.repo.update_custom_field(
            field_id, "Updated Name", "new desc", "updated_name", "Integer",
            False, True, "0", True, [])
        self.assertTrue(result)
        rows = self._db_query(
            "SELECT field_name, description, system_name, field_type_id, "
            "enabled, is_required, default_value FROM tc_custom_fields "
            "WHERE id = ?", (field_id,))
        self.assertEqual(rows[0][0], "Updated Name")
        self.assertEqual(rows[0][1], "new desc")
        self.assertEqual(rows[0][2], "updated_name")
        self.assertEqual(rows[0][3], _INTEGER_TYPE_ID)

    async def test_update_clears_option_data_on_type_change(self):
        field_id = self._insert_field(
            "Priority", "priority", field_type_id=_STRING_TYPE_ID)
        # seed option values rows that should be cleared on type change
        self._db_insert(
            "INSERT INTO tc_custom_field_option_values "
            "(test_case_id, field_id, value) VALUES (1, ?, 'old')", (field_id,))
        result = await self.repo.update_custom_field(
            field_id, "Priority", "desc", "priority", "Integer",
            True, False, "", True, [])
        self.assertTrue(result)
        self.assertEqual(
            self._count_rows(
                "tc_custom_field_option_values", "field_id = ?", (field_id,)),
            0)

    async def test_update_replaces_project_associations(self):
        field_id = self._insert_field(
            "Priority", "priority", applies_to_all=False)
        pid1 = self._insert_project("Alpha")
        pid2 = self._insert_project("Beta")
        self._db_insert(
            "INSERT INTO tc_custom_field_projects (field_id, project_id) "
            "VALUES (?, ?)", (field_id, pid1))
        result = await self.repo.update_custom_field(
            field_id, "Priority", "desc", "priority", "String",
            True, False, "", False, [pid2])
        self.assertTrue(result)
        rows = self._db_query(
            "SELECT project_id FROM tc_custom_field_projects "
            "WHERE field_id = ?", (field_id,))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][0], pid2)

    # ------------------------------------------------------------------
    # delete_custom_field
    # ------------------------------------------------------------------

    async def test_delete_returns_false_when_not_found(self):
        result = await self.repo.delete_custom_field(999)
        self.assertFalse(result)

    async def test_delete_returns_none_for_system_field(self):
        field_id = self._insert_field(
            "SysField", "sys_field", entry_type="system")
        result = await self.repo.delete_custom_field(field_id)
        self.assertIsNone(result)
        self.assertEqual(self._count_rows("tc_custom_fields"), 1)

    async def test_delete_removes_field(self):
        field_id = self._insert_field("Priority", "priority")
        result = await self.repo.delete_custom_field(field_id)
        self.assertTrue(result)
        self.assertEqual(self._count_rows("tc_custom_fields"), 0)

    async def test_delete_compacts_positions(self):
        self._insert_field("First", "first", position=1)
        id2 = self._insert_field("Second", "second", position=2)
        id3 = self._insert_field("Third", "third", position=3)
        await self.repo.delete_custom_field(id2)
        self.assertEqual(self._get_position(id3), 2)

    async def test_delete_removes_project_links(self):
        field_id = self._insert_field(
            "Priority", "priority", applies_to_all=False)
        pid = self._insert_project("Alpha")
        self._db_insert(
            "INSERT INTO tc_custom_field_projects (field_id, project_id) "
            "VALUES (?, ?)", (field_id, pid))
        await self.repo.delete_custom_field(field_id)
        self.assertEqual(
            self._count_rows(
                "tc_custom_field_projects", "field_id = ?", (field_id,)),
            0)


if __name__ == "__main__":
    unittest.main()
