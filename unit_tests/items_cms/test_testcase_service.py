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
from items.services.items_cms.services.testcase_service import TestcaseService
from items.services.items_cms.repositories.testcase_repository import (
    TestcaseRepository,
)
from items.shared.service_state import ServiceState


class TestTestcaseService(unittest.IsolatedAsyncioTestCase):
    """Unit tests for TestcaseService."""

    async def asyncSetUp(self):
        self.mock_logger = MagicMock()
        self.mock_state = MagicMock(spec=ServiceState)
        self.mock_state.is_available.return_value = True
        self.mock_repo = AsyncMock(spec=TestcaseRepository)
        self.service = TestcaseService(
            self.mock_logger, self.mock_state, self.mock_repo)

    # ------------------------------------------------------------------
    # list_testcases
    # ------------------------------------------------------------------

    async def test_list_testcases_service_unavailable(self):
        self.mock_state.is_available.return_value = False
        result = await self.service.list_testcases(1)
        self.assertFalse(result.success)
        self.assertTrue(result.is_internal)

    async def test_list_testcases_project_id_check_db_exception(self):
        self.mock_repo.is_valid_project_id.side_effect = (
            SqliteInterfaceException("err"))
        result = await self.service.list_testcases(1)
        self.assertFalse(result.success)
        self.assertTrue(result.is_internal)
        self.mock_state.mark_database_failed.assert_called_once()

    async def test_list_testcases_invalid_project_id(self):
        self.mock_repo.is_valid_project_id.return_value = False
        result = await self.service.list_testcases(1)
        self.assertFalse(result.success)
        self.assertTrue(result.not_found)
        self.mock_repo.get_testcases.assert_not_called()

    async def test_list_testcases_get_testcases_db_exception(self):
        self.mock_repo.is_valid_project_id.return_value = True
        self.mock_repo.get_testcases.side_effect = (
            SqliteInterfaceException("err"))
        result = await self.service.list_testcases(1)
        self.assertFalse(result.success)
        self.assertTrue(result.is_internal)
        self.mock_state.mark_database_failed.assert_called_once()

    async def test_list_testcases_success(self):
        self.mock_repo.is_valid_project_id.return_value = True
        payload = {
            "folders": [{"id": 1, "name": "Suite A", "parent_id": None}],
            "test_cases": [{"id": 10, "folder_id": 1, "name": "TC-1"}],
        }
        self.mock_repo.get_testcases.return_value = payload
        result = await self.service.list_testcases(5)
        self.assertTrue(result.success)
        self.assertEqual(result.data, payload)
        self.mock_repo.get_testcases.assert_called_once_with(5)

    # ------------------------------------------------------------------
    # get_testcase
    # ------------------------------------------------------------------

    async def test_get_testcase_service_unavailable(self):
        self.mock_state.is_available.return_value = False
        result = await self.service.get_testcase(1)
        self.assertFalse(result.success)
        self.assertTrue(result.is_internal)

    async def test_get_testcase_db_exception(self):
        self.mock_repo.get_testcase.side_effect = (
            SqliteInterfaceException("err"))
        result = await self.service.get_testcase(1)
        self.assertFalse(result.success)
        self.assertTrue(result.is_internal)
        self.mock_state.mark_database_failed.assert_called_once()

    async def test_get_testcase_not_found(self):
        self.mock_repo.get_testcase.return_value = None
        result = await self.service.get_testcase(1)
        self.assertFalse(result.success)
        self.assertTrue(result.not_found)

    async def test_get_testcase_success(self):
        tc = {"id": 42, "folder_id": 1, "name": "Login test",
              "description": "Verify login works"}
        self.mock_repo.get_testcase.return_value = tc
        result = await self.service.get_testcase(42)
        self.assertTrue(result.success)
        self.assertEqual(result.data, tc)


if __name__ == "__main__":
    unittest.main()
