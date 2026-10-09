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
from items.services.items_cms.services.case_types_service import (
    CaseTypesService,
)
from items.services.items_cms.repositories.case_types_repository import (
    CaseTypesRepository,
)
from items.shared.service_state import ServiceState

_ROW = (1, "Smoke", "desc", 0)
_DICT = {"id": 1, "name": "Smoke", "description": "desc",
         "is_default": False}


class TestCaseTypesService(unittest.IsolatedAsyncioTestCase):
    """Unit tests for CaseTypesService."""

    async def asyncSetUp(self):
        self.mock_state = MagicMock(spec=ServiceState)
        self.mock_state.is_available.return_value = True
        self.mock_repo = AsyncMock(spec=CaseTypesRepository)
        self.mock_repo.case_type_name_exists.return_value = False
        self.mock_repo.get_case_type.return_value = _ROW
        self.service = CaseTypesService(
            MagicMock(), self.mock_state, self.mock_repo)

    def _assert_internal(self, result):
        self.assertFalse(result.success)
        self.assertTrue(result.is_internal)

    def _assert_db_failed(self, result):
        self._assert_internal(result)
        self.mock_state.mark_database_failed.assert_called_once()

    # ------------------------------------------------------------------
    # get_case_type
    # ------------------------------------------------------------------

    async def test_get_unavailable(self):
        self.mock_state.is_available.return_value = False
        self._assert_internal(await self.service.get_case_type(1))

    async def test_get_db_exception(self):
        self.mock_repo.get_case_type.side_effect = SqliteInterfaceException("e")
        self._assert_db_failed(await self.service.get_case_type(1))

    async def test_get_not_found(self):
        self.mock_repo.get_case_type.return_value = None
        result = await self.service.get_case_type(1)
        self.assertFalse(result.success)
        self.assertTrue(result.not_found)

    async def test_get_success(self):
        self.mock_repo.get_case_type.return_value = _ROW
        result = await self.service.get_case_type(1)
        self.assertTrue(result.success)
        self.assertEqual(result.data, _DICT)

    async def test_get_is_default_is_a_real_boolean(self):
        self.mock_repo.get_case_type.return_value = (4, "Other", "d", 1)
        result = await self.service.get_case_type(4)
        self.assertIs(result.data["is_default"], True)

    # ------------------------------------------------------------------
    # get_all_case_types
    # ------------------------------------------------------------------

    async def test_get_all_unavailable(self):
        self.mock_state.is_available.return_value = False
        self._assert_internal(await self.service.get_all_case_types())

    async def test_get_all_db_exception(self):
        self.mock_repo.get_all_case_types.side_effect = (
            SqliteInterfaceException("e"))
        self._assert_db_failed(await self.service.get_all_case_types())

    async def test_get_all_success(self):
        self.mock_repo.get_all_case_types.return_value = [_ROW]
        result = await self.service.get_all_case_types()
        self.assertTrue(result.success)
        self.assertEqual(result.data, [_DICT])

    # ------------------------------------------------------------------
    # add_case_type
    # ------------------------------------------------------------------

    async def test_add_unavailable(self):
        self.mock_state.is_available.return_value = False
        self._assert_internal(await self.service.add_case_type("A", ""))

    async def test_add_name_conflict(self):
        self.mock_repo.case_type_name_exists.return_value = True
        result = await self.service.add_case_type("A", "")
        self.assertFalse(result.success)
        self.assertTrue(result.is_conflict)
        self.mock_repo.add_case_type.assert_not_called()

    async def test_add_name_check_db_exception(self):
        self.mock_repo.case_type_name_exists.side_effect = (
            SqliteInterfaceException("e"))
        self._assert_db_failed(await self.service.add_case_type("A", ""))

    async def test_add_insert_db_exception(self):
        self.mock_repo.add_case_type.side_effect = SqliteInterfaceException("e")
        self._assert_db_failed(await self.service.add_case_type("A", ""))

    async def test_add_success_returns_id(self):
        self.mock_repo.add_case_type.return_value = 7
        result = await self.service.add_case_type("A", "d")
        self.assertTrue(result.success)
        self.assertEqual(result.data, 7)
        self.mock_repo.add_case_type.assert_awaited_once_with("A", "d")

    async def test_add_trims_name_and_description(self):
        self.mock_repo.add_case_type.return_value = 7
        await self.service.add_case_type("  Smoke ", " d  ")
        self.mock_repo.case_type_name_exists.assert_awaited_once_with(
            "Smoke", exclude_id=None)
        self.mock_repo.add_case_type.assert_awaited_once_with("Smoke", "d")

    async def test_add_whitespace_only_name_is_bad_request(self):
        result = await self.service.add_case_type("   ", "")
        self.assertFalse(result.success)
        self.assertFalse(result.is_internal)
        self.assertFalse(result.is_conflict)
        self.mock_repo.add_case_type.assert_not_called()

    # ------------------------------------------------------------------
    # update_case_type
    # ------------------------------------------------------------------

    async def test_update_unavailable(self):
        self.mock_state.is_available.return_value = False
        self._assert_internal(await self.service.update_case_type(1, "A", ""))

    async def test_update_name_conflict_excludes_own_id(self):
        self.mock_repo.case_type_name_exists.return_value = True
        result = await self.service.update_case_type(3, "A", "")
        self.assertTrue(result.is_conflict)
        self.mock_repo.case_type_name_exists.assert_awaited_once_with(
            "A", exclude_id=3)
        self.mock_repo.update_case_type.assert_not_called()

    async def test_update_missing_type_with_clashing_name_is_not_found(self):
        self.mock_repo.get_case_type.return_value = None
        self.mock_repo.case_type_name_exists.return_value = True
        result = await self.service.update_case_type(99, "Smoke", "")
        self.assertFalse(result.success)
        self.assertTrue(result.not_found)
        self.assertFalse(result.is_conflict)
        self.mock_repo.get_case_type.assert_awaited_once_with(99)
        self.mock_repo.case_type_name_exists.assert_not_called()
        self.mock_repo.update_case_type.assert_not_called()

    async def test_update_lookup_db_exception(self):
        self.mock_repo.get_case_type.side_effect = (
            SqliteInterfaceException("e"))
        self._assert_db_failed(await self.service.update_case_type(1, "A", ""))
        self.mock_repo.update_case_type.assert_not_called()

    async def test_update_db_exception(self):
        self.mock_repo.update_case_type.side_effect = (
            SqliteInterfaceException("e"))
        self._assert_db_failed(await self.service.update_case_type(1, "A", ""))

    async def test_update_not_found(self):
        self.mock_repo.update_case_type.return_value = False
        result = await self.service.update_case_type(1, "A", "")
        self.assertFalse(result.success)
        self.assertTrue(result.not_found)

    async def test_update_success(self):
        self.mock_repo.update_case_type.return_value = True
        result = await self.service.update_case_type(1, "A", "")
        self.assertTrue(result.success)

    async def test_update_trims_name_and_description(self):
        self.mock_repo.update_case_type.return_value = True
        await self.service.update_case_type(1, " Smoke  ", " d ")
        self.mock_repo.update_case_type.assert_awaited_once_with(
            1, "Smoke", "d")

    async def test_update_whitespace_only_name_is_bad_request(self):
        result = await self.service.update_case_type(1, "  ", "")
        self.assertFalse(result.success)
        self.assertFalse(result.is_internal)
        self.mock_repo.update_case_type.assert_not_called()

    # ------------------------------------------------------------------
    # set_default_case_type
    # ------------------------------------------------------------------

    async def test_set_default_unavailable(self):
        self.mock_state.is_available.return_value = False
        self._assert_internal(await self.service.set_default_case_type(1))

    async def test_set_default_db_exception(self):
        self.mock_repo.set_default_case_type.side_effect = (
            SqliteInterfaceException("e"))
        self._assert_db_failed(await self.service.set_default_case_type(1))

    async def test_set_default_not_found(self):
        self.mock_repo.set_default_case_type.return_value = False
        result = await self.service.set_default_case_type(1)
        self.assertTrue(result.not_found)

    async def test_set_default_success(self):
        self.mock_repo.set_default_case_type.return_value = True
        result = await self.service.set_default_case_type(1)
        self.assertTrue(result.success)
