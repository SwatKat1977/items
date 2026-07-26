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
from items.services.items_cms.services.testcase_field_values_service import (
    TestcaseFieldValuesService,
)
from items.services.items_cms.repositories.testcase_field_values_repository import (
    TestcaseFieldValuesRepository,
)
from items.shared.service_state import ServiceState

_PRIORITY_FIELD = {
    "id": 1,
    "field_name": "Priority",
    "field_type": "String",
    "is_required": False,
    "default_value": "Medium",
    "position": 1,
}

_SEVERITY_FIELD = {
    "id": 2,
    "field_name": "Severity",
    "field_type": "Integer",
    "is_required": True,
    "default_value": "",
    "position": 2,
}


class TestTestcaseFieldValuesService(unittest.IsolatedAsyncioTestCase):
    """Unit tests for TestcaseFieldValuesService."""

    async def asyncSetUp(self):
        self.mock_logger = MagicMock()
        self.mock_state = MagicMock(spec=ServiceState)
        self.mock_state.is_available.return_value = True
        self.mock_repo = AsyncMock(spec=TestcaseFieldValuesRepository)
        self.mock_repo.get_testcase_project_id.return_value = 5
        self.service = TestcaseFieldValuesService(
            self.mock_logger, self.mock_state, self.mock_repo)

    # ------------------------------------------------------------------
    # get_field_values
    # ------------------------------------------------------------------

    async def test_get_field_values_service_unavailable(self):
        self.mock_state.is_available.return_value = False
        result = await self.service.get_field_values(1)
        self.assertFalse(result.success)
        self.assertTrue(result.is_internal)

    async def test_get_field_values_project_lookup_db_exception(self):
        self.mock_repo.get_testcase_project_id.side_effect = (
            SqliteInterfaceException("err"))
        result = await self.service.get_field_values(1)
        self.assertFalse(result.success)
        self.assertTrue(result.is_internal)
        self.mock_state.mark_database_failed.assert_called_once()

    async def test_get_field_values_testcase_not_found(self):
        self.mock_repo.get_testcase_project_id.return_value = None
        result = await self.service.get_field_values(1)
        self.assertFalse(result.success)
        self.assertTrue(result.not_found)

    async def test_get_field_values_fields_db_exception(self):
        self.mock_repo.get_applicable_fields.side_effect = (
            SqliteInterfaceException("err"))
        result = await self.service.get_field_values(1)
        self.assertFalse(result.success)
        self.assertTrue(result.is_internal)

    async def test_get_field_values_values_db_exception(self):
        self.mock_repo.get_applicable_fields.return_value = [_PRIORITY_FIELD]
        self.mock_repo.get_field_values.side_effect = (
            SqliteInterfaceException("err"))
        result = await self.service.get_field_values(1)
        self.assertFalse(result.success)
        self.assertTrue(result.is_internal)

    async def test_get_field_values_uses_default_when_unset(self):
        self.mock_repo.get_applicable_fields.return_value = [_PRIORITY_FIELD]
        self.mock_repo.get_field_values.return_value = {}
        result = await self.service.get_field_values(1)
        self.assertTrue(result.success)
        self.assertEqual(result.data[0]["value"], "Medium")

    async def test_get_field_values_uses_stored_value_when_set(self):
        self.mock_repo.get_applicable_fields.return_value = [_PRIORITY_FIELD]
        self.mock_repo.get_field_values.return_value = {1: "High"}
        result = await self.service.get_field_values(1)
        self.assertTrue(result.success)
        self.assertEqual(result.data[0]["value"], "High")
        self.assertEqual(result.data[0]["position"], 1)

    # ------------------------------------------------------------------
    # set_field_values
    # ------------------------------------------------------------------

    async def test_set_field_values_service_unavailable(self):
        self.mock_state.is_available.return_value = False
        result = await self.service.set_field_values(1, {1: "High"})
        self.assertFalse(result.success)
        self.assertTrue(result.is_internal)

    async def test_set_field_values_project_lookup_db_exception(self):
        self.mock_repo.get_testcase_project_id.side_effect = (
            SqliteInterfaceException("err"))
        result = await self.service.set_field_values(1, {1: "High"})
        self.assertFalse(result.success)
        self.assertTrue(result.is_internal)

    async def test_set_field_values_testcase_not_found(self):
        self.mock_repo.get_testcase_project_id.return_value = None
        result = await self.service.set_field_values(1, {1: "High"})
        self.assertFalse(result.success)
        self.assertTrue(result.not_found)

    async def test_set_field_values_fields_db_exception(self):
        self.mock_repo.get_applicable_fields.side_effect = (
            SqliteInterfaceException("err"))
        result = await self.service.set_field_values(1, {1: "High"})
        self.assertFalse(result.success)
        self.assertTrue(result.is_internal)

    async def test_set_field_values_unknown_field_rejected(self):
        self.mock_repo.get_applicable_fields.return_value = [_PRIORITY_FIELD]
        result = await self.service.set_field_values(1, {999: "High"})
        self.assertFalse(result.success)
        self.assertFalse(result.is_internal)
        self.assertFalse(result.not_found)
        self.assertIn("999", result.error_msg)
        self.mock_repo.insert_field_value.assert_not_called()

    async def test_set_field_values_required_field_empty_rejected(self):
        self.mock_repo.get_applicable_fields.return_value = [_SEVERITY_FIELD]
        result = await self.service.set_field_values(1, {2: "   "})
        self.assertFalse(result.success)
        self.assertIn("Severity", result.error_msg)

    async def test_set_field_values_type_validation_failure_rejected(self):
        self.mock_repo.get_applicable_fields.return_value = [_SEVERITY_FIELD]
        result = await self.service.set_field_values(1, {2: "not-a-number"})
        self.assertFalse(result.success)
        self.assertIn("Severity", result.error_msg)

    async def test_set_field_values_optional_empty_value_allowed(self):
        self.mock_repo.get_applicable_fields.return_value = [_PRIORITY_FIELD]
        self.mock_repo.value_row_exists.return_value = False
        result = await self.service.set_field_values(1, {1: ""})
        self.assertTrue(result.success)

    async def test_set_field_values_write_db_exception(self):
        self.mock_repo.get_applicable_fields.return_value = [_PRIORITY_FIELD]
        self.mock_repo.value_row_exists.side_effect = (
            SqliteInterfaceException("err"))
        result = await self.service.set_field_values(1, {1: "High"})
        self.assertFalse(result.success)
        self.assertTrue(result.is_internal)
        self.mock_state.mark_database_failed.assert_called_once()

    async def test_set_field_values_inserts_when_no_existing_row(self):
        self.mock_repo.get_applicable_fields.return_value = [_PRIORITY_FIELD]
        self.mock_repo.value_row_exists.return_value = False
        result = await self.service.set_field_values(1, {1: "High"})
        self.assertTrue(result.success)
        self.mock_repo.insert_field_value.assert_called_once_with(1, 1, "High")
        self.mock_repo.update_field_value.assert_not_called()

    async def test_set_field_values_updates_when_existing_row(self):
        self.mock_repo.get_applicable_fields.return_value = [_PRIORITY_FIELD]
        self.mock_repo.value_row_exists.return_value = True
        result = await self.service.set_field_values(1, {1: "High"})
        self.assertTrue(result.success)
        self.mock_repo.update_field_value.assert_called_once_with(1, 1, "High")
        self.mock_repo.insert_field_value.assert_not_called()


if __name__ == "__main__":
    unittest.main()
