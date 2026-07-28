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
import unittest
from unittest.mock import AsyncMock, MagicMock
from weaver_framework.database.sqlite_interface import SqliteInterfaceException
from items.services.items_cms.services.testcase_custom_fields_service import (
    TestcaseCustomFieldsService,
    TestcaseCustomFieldResult,
)
from items.services.items_cms.repositories.testcase_custom_fields_repository\
    import TestcaseCustomFieldsRepository, CustomFieldMoveDirection
from items.shared.service_state import ServiceState


def _field_row(field_id=1, field_name="Old Name", description="old desc",
               system_name="old_name", field_type="String",
               entry_type="user", enabled=True, position=1,
               is_required=False, default_value="", applies_to_all=True,
               linked_projects=None):
    """Build a get_custom_field-shaped row tuple for mocking."""
    return (field_id, field_name, description, system_name, field_type,
           entry_type, enabled, position, is_required, default_value,
           applies_to_all, linked_projects)


class TestTestcaseCustomFieldsService(unittest.IsolatedAsyncioTestCase):
    """Unit tests for TestcaseCustomFieldsService."""

    async def asyncSetUp(self):
        self.mock_logger = MagicMock()
        self.mock_state = MagicMock(spec=ServiceState)
        self.mock_state.is_available.return_value = True
        self.mock_repo = AsyncMock(spec=TestcaseCustomFieldsRepository)
        # Most update_custom_field tests exercise the non-system path; the
        # small number of system-field tests override this explicitly.
        self.mock_repo.get_custom_field.return_value = _field_row()
        self.service = TestcaseCustomFieldsService(
            self.mock_logger, self.mock_state, self.mock_repo)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    async def _add_field(self, **kwargs):
        defaults = dict(
            field_name="My Field",
            description="desc",
            system_name="my_field",
            field_type="String",
            enabled=True,
            is_required=False,
            default_value="",
            applies_to_all_projects=True,
            projects=None,
        )
        defaults.update(kwargs)
        return await self.service.add_custom_field(**defaults)

    async def _update_field(self, **kwargs):
        defaults = dict(
            field_id=1,
            field_name="Updated Field",
            description="new desc",
            system_name="updated_field",
            field_type="String",
            enabled=True,
            is_required=False,
            default_value="",
            applies_to_all_projects=True,
            projects=None,
        )
        defaults.update(kwargs)
        return await self.service.update_custom_field(**defaults)

    # ------------------------------------------------------------------
    # get_custom_field
    # ------------------------------------------------------------------

    async def test_get_custom_field_service_unavailable(self):
        self.mock_state.is_available.return_value = False
        result = await self.service.get_custom_field(1)
        self.assertFalse(result.success)
        self.assertTrue(result.is_internal)

    async def test_get_custom_field_db_exception(self):
        self.mock_repo.get_custom_field.side_effect = (
            SqliteInterfaceException("err"))
        result = await self.service.get_custom_field(1)
        self.assertFalse(result.success)
        self.assertTrue(result.is_internal)
        self.mock_state.mark_database_failed.assert_called_once()

    async def test_get_custom_field_not_found(self):
        self.mock_repo.get_custom_field.return_value = None
        result = await self.service.get_custom_field(1)
        self.assertFalse(result.success)
        self.assertTrue(result.not_found)

    async def test_get_custom_field_success(self):
        row = (1, "Test", "desc", "test", "String",
               "user", True, 1, False, "", True, None)
        self.mock_repo.get_custom_field.return_value = row
        result = await self.service.get_custom_field(1)
        self.assertTrue(result.success)
        self.assertEqual(result.data, row)

    # ------------------------------------------------------------------
    # get_custom_fields
    # ------------------------------------------------------------------

    async def test_get_custom_fields_service_unavailable(self):
        self.mock_state.is_available.return_value = False
        result = await self.service.get_custom_fields()
        self.assertFalse(result.success)
        self.assertTrue(result.is_internal)

    async def test_get_all_fields_db_exception(self):
        self.mock_repo.get_all_fields.side_effect = (
            SqliteInterfaceException("err"))
        result = await self.service.get_custom_fields()
        self.assertFalse(result.success)
        self.assertTrue(result.is_internal)
        self.mock_state.mark_database_failed.assert_called_once()

    async def test_get_fields_for_project_invalid_project_id_db_exception(self):
        self.mock_repo.is_valid_project_id.side_effect = (
            SqliteInterfaceException("err"))
        result = await self.service.get_custom_fields(project_id=5)
        self.assertFalse(result.success)
        self.assertTrue(result.is_internal)
        self.mock_state.mark_database_failed.assert_called_once()
        self.mock_repo.get_fields_for_project.assert_not_called()

    async def test_get_fields_for_project_invalid_project_id_returns_not_found(self):
        self.mock_repo.is_valid_project_id.return_value = False
        result = await self.service.get_custom_fields(project_id=5)
        self.assertFalse(result.success)
        self.assertTrue(result.not_found)
        self.mock_repo.get_fields_for_project.assert_not_called()

    async def test_get_fields_for_project_db_exception(self):
        self.mock_repo.is_valid_project_id.return_value = True
        self.mock_repo.get_fields_for_project.side_effect = (
            SqliteInterfaceException("err"))
        result = await self.service.get_custom_fields(project_id=5)
        self.assertFalse(result.success)
        self.assertTrue(result.is_internal)
        self.mock_state.mark_database_failed.assert_called_once()

    async def test_get_all_fields_success(self):
        rows = [(1, "F1"), (2, "F2")]
        self.mock_repo.get_all_fields.return_value = rows
        result = await self.service.get_custom_fields()
        self.assertTrue(result.success)
        self.assertEqual(result.data, rows)
        self.mock_repo.get_all_fields.assert_called_once()
        self.mock_repo.get_fields_for_project.assert_not_called()

    async def test_get_fields_for_project_success(self):
        rows = [(1, "F1")]
        self.mock_repo.get_fields_for_project.return_value = rows
        result = await self.service.get_custom_fields(project_id=3)
        self.assertTrue(result.success)
        self.assertEqual(result.data, rows)
        self.mock_repo.get_fields_for_project.assert_called_once_with(3)
        self.mock_repo.get_all_fields.assert_not_called()

    async def test_get_all_fields_returns_empty_list(self):
        self.mock_repo.get_all_fields.return_value = []
        result = await self.service.get_custom_fields()
        self.assertTrue(result.success)
        self.assertEqual(result.data, [])

    # ------------------------------------------------------------------
    # add_custom_field / _validate_add_request
    # ------------------------------------------------------------------

    async def test_add_field_service_unavailable(self):
        self.mock_state.is_available.return_value = False
        result = await self._add_field()
        self.assertFalse(result.success)
        self.assertTrue(result.is_internal)

    async def test_add_field_name_conflict(self):
        self.mock_repo.custom_field_name_exists.return_value = True
        result = await self._add_field()
        self.assertFalse(result.success)
        self.assertTrue(result.is_conflict)
        self.assertIn("My Field", result.error_msg)

    async def test_add_field_name_check_db_exception(self):
        self.mock_repo.custom_field_name_exists.side_effect = (
            SqliteInterfaceException("err"))
        result = await self._add_field()
        self.assertFalse(result.success)
        self.assertTrue(result.is_internal)
        self.mock_state.mark_database_failed.assert_called_once()

    async def test_add_field_system_name_conflict(self):
        self.mock_repo.custom_field_name_exists.return_value = False
        self.mock_repo.system_name_exists.return_value = True
        result = await self._add_field()
        self.assertFalse(result.success)
        self.assertTrue(result.is_conflict)
        self.assertIn("my_field", result.error_msg)

    async def test_add_field_system_name_check_db_exception(self):
        self.mock_repo.custom_field_name_exists.return_value = False
        self.mock_repo.system_name_exists.side_effect = (
            SqliteInterfaceException("err"))
        result = await self._add_field()
        self.assertFalse(result.success)
        self.assertTrue(result.is_internal)

    async def test_add_field_missing_projects_when_not_global(self):
        self.mock_repo.custom_field_name_exists.return_value = False
        self.mock_repo.system_name_exists.return_value = False
        result = await self._add_field(
            applies_to_all_projects=False, projects=None)
        self.assertFalse(result.success)
        self.assertFalse(result.is_internal)
        self.assertFalse(result.is_conflict)
        self.assertIn("projects is required", result.error_msg)

    async def test_add_field_duplicate_projects(self):
        self.mock_repo.custom_field_name_exists.return_value = False
        self.mock_repo.system_name_exists.return_value = False
        result = await self._add_field(
            applies_to_all_projects=False,
            projects=["Alpha", "Beta", "Alpha"])
        self.assertFalse(result.success)
        self.assertIn("Duplicate", result.error_msg)

    async def test_add_field_invalid_project_names(self):
        self.mock_repo.custom_field_name_exists.return_value = False
        self.mock_repo.system_name_exists.return_value = False
        self.mock_repo.resolve_project_names.return_value = None
        result = await self._add_field(
            applies_to_all_projects=False,
            projects=["DoesNotExist"])
        self.assertFalse(result.success)
        self.assertIn("invalid", result.error_msg)

    async def test_add_field_resolve_projects_db_exception(self):
        self.mock_repo.custom_field_name_exists.return_value = False
        self.mock_repo.system_name_exists.return_value = False
        self.mock_repo.resolve_project_names.side_effect = (
            SqliteInterfaceException("err"))
        result = await self._add_field(
            applies_to_all_projects=False,
            projects=["Alpha"])
        self.assertFalse(result.success)
        self.assertTrue(result.is_internal)

    async def test_add_field_unknown_field_type(self):
        self.mock_repo.custom_field_name_exists.return_value = False
        self.mock_repo.system_name_exists.return_value = False
        self.mock_repo.add_custom_field.return_value = None
        result = await self._add_field()
        self.assertFalse(result.success)
        self.assertFalse(result.is_internal)
        self.assertIn("String", result.error_msg)

    async def test_add_field_insert_db_exception(self):
        self.mock_repo.custom_field_name_exists.return_value = False
        self.mock_repo.system_name_exists.return_value = False
        self.mock_repo.add_custom_field.side_effect = (
            SqliteInterfaceException("err"))
        result = await self._add_field()
        self.assertFalse(result.success)
        self.assertTrue(result.is_internal)

    async def test_add_field_assign_projects_db_exception(self):
        self.mock_repo.custom_field_name_exists.return_value = False
        self.mock_repo.system_name_exists.return_value = False
        self.mock_repo.resolve_project_names.return_value = [1, 2]
        self.mock_repo.add_custom_field.return_value = 10
        self.mock_repo.assign_custom_field_to_projects.side_effect = (
            SqliteInterfaceException("err"))
        result = await self._add_field(
            applies_to_all_projects=False,
            projects=["Alpha", "Beta"])
        self.assertFalse(result.success)
        self.assertTrue(result.is_internal)

    async def test_add_field_success_global(self):
        self.mock_repo.custom_field_name_exists.return_value = False
        self.mock_repo.system_name_exists.return_value = False
        self.mock_repo.add_custom_field.return_value = 10
        result = await self._add_field(applies_to_all_projects=True)
        self.assertTrue(result.success)
        self.assertEqual(result.data, 10)
        self.mock_repo.assign_custom_field_to_projects.assert_not_called()

    async def test_add_field_success_with_projects(self):
        self.mock_repo.custom_field_name_exists.return_value = False
        self.mock_repo.system_name_exists.return_value = False
        self.mock_repo.resolve_project_names.return_value = [1, 2]
        self.mock_repo.add_custom_field.return_value = 11
        result = await self._add_field(
            applies_to_all_projects=False,
            projects=["Alpha", "Beta"])
        self.assertTrue(result.success)
        self.assertEqual(result.data, 11)
        self.mock_repo.assign_custom_field_to_projects.assert_called_once_with(
            11, [1, 2])

    # ------------------------------------------------------------------
    # delete_custom_field
    # ------------------------------------------------------------------

    async def test_delete_field_service_unavailable(self):
        self.mock_state.is_available.return_value = False
        result = await self.service.delete_custom_field(1)
        self.assertFalse(result.success)
        self.assertTrue(result.is_internal)

    async def test_delete_field_db_exception(self):
        self.mock_repo.delete_custom_field.side_effect = (
            SqliteInterfaceException("err"))
        result = await self.service.delete_custom_field(1)
        self.assertFalse(result.success)
        self.assertTrue(result.is_internal)
        self.mock_state.mark_database_failed.assert_called_once()

    async def test_delete_field_not_found(self):
        self.mock_repo.delete_custom_field.return_value = False
        result = await self.service.delete_custom_field(1)
        self.assertFalse(result.success)
        self.assertTrue(result.not_found)

    async def test_delete_field_system_field_rejected(self):
        self.mock_repo.delete_custom_field.return_value = None
        result = await self.service.delete_custom_field(1)
        self.assertFalse(result.success)
        self.assertFalse(result.not_found)
        self.assertFalse(result.is_internal)
        self.assertIn("System", result.error_msg)

    async def test_delete_field_success(self):
        self.mock_repo.delete_custom_field.return_value = True
        result = await self.service.delete_custom_field(1)
        self.assertTrue(result.success)

    # ------------------------------------------------------------------
    # move_custom_field
    # ------------------------------------------------------------------

    async def test_move_field_service_unavailable(self):
        self.mock_state.is_available.return_value = False
        result = await self.service.move_custom_field(1, "up")
        self.assertFalse(result.success)
        self.assertTrue(result.is_internal)

    async def test_move_field_db_exception(self):
        self.mock_repo.move_custom_field.side_effect = (
            SqliteInterfaceException("err"))
        result = await self.service.move_custom_field(1, "up")
        self.assertFalse(result.success)
        self.assertTrue(result.is_internal)
        self.mock_state.mark_database_failed.assert_called_once()

    async def test_move_field_not_found(self):
        self.mock_repo.move_custom_field.return_value = False
        result = await self.service.move_custom_field(1, "up")
        self.assertFalse(result.success)
        self.assertTrue(result.not_found)

    async def test_move_field_at_boundary(self):
        self.mock_repo.move_custom_field.return_value = None
        result = await self.service.move_custom_field(1, "up")
        self.assertFalse(result.success)
        self.assertFalse(result.not_found)
        self.assertIn("boundary", result.error_msg)

    async def test_move_field_up_passes_correct_direction(self):
        self.mock_repo.move_custom_field.return_value = True
        result = await self.service.move_custom_field(5, "up")
        self.assertTrue(result.success)
        self.mock_repo.move_custom_field.assert_called_once_with(
            5, CustomFieldMoveDirection.UP)

    async def test_move_field_down_passes_correct_direction(self):
        self.mock_repo.move_custom_field.return_value = True
        result = await self.service.move_custom_field(5, "down")
        self.assertTrue(result.success)
        self.mock_repo.move_custom_field.assert_called_once_with(
            5, CustomFieldMoveDirection.DOWN)

    # ------------------------------------------------------------------
    # update_custom_field / _validate_update_request
    # ------------------------------------------------------------------

    async def test_update_field_service_unavailable(self):
        self.mock_state.is_available.return_value = False
        result = await self._update_field()
        self.assertFalse(result.success)
        self.assertTrue(result.is_internal)

    async def test_update_field_lookup_db_exception(self):
        self.mock_repo.get_custom_field.side_effect = (
            SqliteInterfaceException("err"))
        result = await self._update_field()
        self.assertFalse(result.success)
        self.assertTrue(result.is_internal)
        self.mock_state.mark_database_failed.assert_called_once()

    async def test_update_field_not_found(self):
        self.mock_repo.get_custom_field.return_value = None
        result = await self._update_field()
        self.assertFalse(result.success)
        self.assertTrue(result.not_found)

    async def test_update_field_name_conflict(self):
        self.mock_repo.custom_field_name_exists.return_value = True
        result = await self._update_field()
        self.assertFalse(result.success)
        self.assertTrue(result.is_conflict)
        self.assertIn("Updated Field", result.error_msg)

    async def test_update_field_system_name_conflict(self):
        self.mock_repo.custom_field_name_exists.return_value = False
        self.mock_repo.system_name_exists.return_value = True
        result = await self._update_field()
        self.assertFalse(result.success)
        self.assertTrue(result.is_conflict)
        self.assertIn("updated_field", result.error_msg)

    async def test_update_uniqueness_checks_exclude_current_field(self):
        self.mock_repo.custom_field_name_exists.return_value = False
        self.mock_repo.system_name_exists.return_value = False
        self.mock_repo.update_custom_field.return_value = True
        await self._update_field(field_id=7)
        self.mock_repo.custom_field_name_exists.assert_called_once_with(
            "Updated Field", exclude_id=7)
        self.mock_repo.system_name_exists.assert_called_once_with(
            "updated_field", exclude_id=7)

    async def test_update_field_missing_projects_when_not_global(self):
        self.mock_repo.custom_field_name_exists.return_value = False
        self.mock_repo.system_name_exists.return_value = False
        result = await self._update_field(
            applies_to_all_projects=False, projects=None)
        self.assertFalse(result.success)
        self.assertFalse(result.is_internal)
        self.assertFalse(result.is_conflict)
        self.assertIn("projects is required", result.error_msg)

    async def test_update_field_invalid_project_names(self):
        self.mock_repo.custom_field_name_exists.return_value = False
        self.mock_repo.system_name_exists.return_value = False
        self.mock_repo.resolve_project_names.return_value = None
        result = await self._update_field(
            applies_to_all_projects=False,
            projects=["DoesNotExist"])
        self.assertFalse(result.success)
        self.assertIn("invalid", result.error_msg)

    async def test_update_field_race_deleted_before_write(self):
        # get_custom_field found it, but it was deleted before the write.
        self.mock_repo.custom_field_name_exists.return_value = False
        self.mock_repo.system_name_exists.return_value = False
        self.mock_repo.update_custom_field.return_value = False
        result = await self._update_field()
        self.assertFalse(result.success)
        self.assertTrue(result.not_found)

    async def test_update_field_unknown_type(self):
        self.mock_repo.custom_field_name_exists.return_value = False
        self.mock_repo.system_name_exists.return_value = False
        self.mock_repo.update_custom_field.return_value = None
        result = await self._update_field(field_type="NotAType")
        self.assertFalse(result.success)
        self.assertFalse(result.not_found)
        self.assertFalse(result.is_internal)
        self.assertIn("NotAType", result.error_msg)

    async def test_update_field_db_exception(self):
        self.mock_repo.custom_field_name_exists.return_value = False
        self.mock_repo.system_name_exists.return_value = False
        self.mock_repo.update_custom_field.side_effect = (
            SqliteInterfaceException("err"))
        result = await self._update_field()
        self.assertFalse(result.success)
        self.assertTrue(result.is_internal)
        self.mock_state.mark_database_failed.assert_called_once()

    async def test_update_field_success(self):
        self.mock_repo.custom_field_name_exists.return_value = False
        self.mock_repo.system_name_exists.return_value = False
        self.mock_repo.update_custom_field.return_value = True
        result = await self._update_field()
        self.assertTrue(result.success)

    async def test_update_field_name_check_db_exception(self):
        self.mock_repo.custom_field_name_exists.side_effect = (
            SqliteInterfaceException("err"))
        result = await self._update_field()
        self.assertFalse(result.success)
        self.assertTrue(result.is_internal)
        self.mock_state.mark_database_failed.assert_called_once()

    async def test_update_field_system_name_check_db_exception(self):
        self.mock_repo.custom_field_name_exists.return_value = False
        self.mock_repo.system_name_exists.side_effect = (
            SqliteInterfaceException("err"))
        result = await self._update_field()
        self.assertFalse(result.success)
        self.assertTrue(result.is_internal)
        self.mock_state.mark_database_failed.assert_called_once()

    async def test_update_field_duplicate_projects(self):
        self.mock_repo.custom_field_name_exists.return_value = False
        self.mock_repo.system_name_exists.return_value = False
        result = await self._update_field(
            applies_to_all_projects=False,
            projects=["Alpha", "Beta", "Alpha"])
        self.assertFalse(result.success)
        self.assertIn("Duplicate", result.error_msg)

    async def test_update_field_resolve_projects_db_exception(self):
        self.mock_repo.custom_field_name_exists.return_value = False
        self.mock_repo.system_name_exists.return_value = False
        self.mock_repo.resolve_project_names.side_effect = (
            SqliteInterfaceException("err"))
        result = await self._update_field(
            applies_to_all_projects=False,
            projects=["Alpha"])
        self.assertFalse(result.success)
        self.assertTrue(result.is_internal)
        self.mock_state.mark_database_failed.assert_called_once()

    async def test_update_field_success_with_projects(self):
        self.mock_repo.custom_field_name_exists.return_value = False
        self.mock_repo.system_name_exists.return_value = False
        self.mock_repo.resolve_project_names.return_value = [3, 4]
        self.mock_repo.update_custom_field.return_value = True
        result = await self._update_field(
            applies_to_all_projects=False,
            projects=["Gamma", "Delta"])
        self.assertTrue(result.success)
        self.mock_repo.update_custom_field.assert_called_once()
        call_kwargs = self.mock_repo.update_custom_field.call_args.kwargs
        self.assertEqual(call_kwargs["project_ids"], [3, 4])

    # ------------------------------------------------------------------
    # update_custom_field - system fields
    # ------------------------------------------------------------------
    # System fields may only have `enabled` and project assignment changed;
    # everything else submitted in the request must be ignored in favour
    # of the field's current stored values.

    async def test_update_system_field_locks_immutable_attributes(self):
        self.mock_repo.get_custom_field.return_value = _field_row(
            field_name="Milestone", description="A milestone",
            system_name="milestone", field_type="String",
            entry_type="system", is_required=True, default_value="",
            applies_to_all=True)
        self.mock_repo.update_custom_field.return_value = True

        await self._update_field(
            field_name="Hacked Name", description="hacked",
            system_name="hacked_name", field_type="Integer",
            is_required=False, default_value="999", enabled=False)

        call_kwargs = self.mock_repo.update_custom_field.call_args.kwargs
        self.assertEqual(call_kwargs["field_name"], "Milestone")
        self.assertEqual(call_kwargs["description"], "A milestone")
        self.assertEqual(call_kwargs["system_name"], "milestone")
        self.assertEqual(call_kwargs["field_type"], "String")
        self.assertTrue(call_kwargs["is_required"])
        self.assertEqual(call_kwargs["default_value"], "")
        # enabled is one of the two attributes a system field CAN change.
        self.assertFalse(call_kwargs["enabled"])

    async def test_update_system_field_skips_uniqueness_checks(self):
        self.mock_repo.get_custom_field.return_value = _field_row(
            entry_type="system")
        self.mock_repo.update_custom_field.return_value = True

        await self._update_field()

        self.mock_repo.custom_field_name_exists.assert_not_called()
        self.mock_repo.system_name_exists.assert_not_called()

    async def test_update_system_field_still_validates_project_assignment(self):
        self.mock_repo.get_custom_field.return_value = _field_row(
            entry_type="system")

        result = await self._update_field(
            applies_to_all_projects=False, projects=None)

        self.assertFalse(result.success)
        self.assertIn("projects is required", result.error_msg)
        self.mock_repo.update_custom_field.assert_not_called()

    async def test_update_system_field_success_changes_projects(self):
        self.mock_repo.get_custom_field.return_value = _field_row(
            entry_type="system", applies_to_all=True)
        self.mock_repo.resolve_project_names.return_value = [9]
        self.mock_repo.update_custom_field.return_value = True

        result = await self._update_field(
            applies_to_all_projects=False, projects=["Zulu"])

        self.assertTrue(result.success)
        call_kwargs = self.mock_repo.update_custom_field.call_args.kwargs
        self.assertEqual(call_kwargs["project_ids"], [9])
        self.assertFalse(call_kwargs["applies_to_all_projects"])


if __name__ == "__main__":
    unittest.main()
