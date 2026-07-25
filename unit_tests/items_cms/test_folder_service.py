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
from items.services.items_cms.services.folder_service import (
    FolderService, FolderResult)
from items.services.items_cms.repositories.folder_repository import (
    FolderRepository)
from items.shared.service_state import ServiceState

_FOLDER = {"id": 1, "project_id": 5, "parent_id": None, "name": "Root"}


class TestFolderService(unittest.IsolatedAsyncioTestCase):
    """Unit tests for FolderService."""

    async def asyncSetUp(self):
        self.mock_logger = MagicMock()
        self.mock_state = MagicMock(spec=ServiceState)
        self.mock_state.is_available.return_value = True
        self.mock_repo = AsyncMock(spec=FolderRepository)
        self.service = FolderService(
            self.mock_logger, self.mock_state, self.mock_repo)

    # ------------------------------------------------------------------
    # get_folder
    # ------------------------------------------------------------------

    async def test_get_folder_service_unavailable(self):
        self.mock_state.is_available.return_value = False
        result = await self.service.get_folder(1)
        self.assertFalse(result.success)
        self.assertTrue(result.is_internal)

    async def test_get_folder_db_exception(self):
        self.mock_repo.get_folder.side_effect = SqliteInterfaceException("err")
        result = await self.service.get_folder(1)
        self.assertFalse(result.success)
        self.assertTrue(result.is_internal)
        self.mock_state.mark_database_failed.assert_called_once()

    async def test_get_folder_not_found(self):
        self.mock_repo.get_folder.return_value = None
        result = await self.service.get_folder(1)
        self.assertFalse(result.success)
        self.assertTrue(result.not_found)

    async def test_get_folder_success(self):
        self.mock_repo.get_folder.return_value = _FOLDER
        result = await self.service.get_folder(1)
        self.assertTrue(result.success)
        self.assertEqual(result.data, _FOLDER)

    # ------------------------------------------------------------------
    # list_folders
    # ------------------------------------------------------------------

    async def test_list_folders_service_unavailable(self):
        self.mock_state.is_available.return_value = False
        result = await self.service.list_folders(5)
        self.assertFalse(result.success)
        self.assertTrue(result.is_internal)

    async def test_list_folders_invalid_project_db_exception(self):
        self.mock_repo.is_valid_project_id.side_effect = (
            SqliteInterfaceException("err"))
        result = await self.service.list_folders(5)
        self.assertFalse(result.success)
        self.assertTrue(result.is_internal)
        self.mock_state.mark_database_failed.assert_called_once()

    async def test_list_folders_invalid_project_not_found(self):
        self.mock_repo.is_valid_project_id.return_value = False
        result = await self.service.list_folders(5)
        self.assertFalse(result.success)
        self.assertTrue(result.not_found)
        self.mock_repo.get_folders.assert_not_called()

    async def test_list_folders_db_exception(self):
        self.mock_repo.is_valid_project_id.return_value = True
        self.mock_repo.get_folders.side_effect = SqliteInterfaceException("err")
        result = await self.service.list_folders(5)
        self.assertFalse(result.success)
        self.assertTrue(result.is_internal)

    async def test_list_folders_success(self):
        self.mock_repo.is_valid_project_id.return_value = True
        self.mock_repo.get_folders.return_value = [_FOLDER]
        result = await self.service.list_folders(5)
        self.assertTrue(result.success)
        self.assertEqual(result.data, [_FOLDER])

    # ------------------------------------------------------------------
    # create_folder
    # ------------------------------------------------------------------

    async def test_create_folder_service_unavailable(self):
        self.mock_state.is_available.return_value = False
        result = await self.service.create_folder(5, None, "Root")
        self.assertFalse(result.success)
        self.assertTrue(result.is_internal)

    async def test_create_folder_project_check_db_exception(self):
        self.mock_repo.is_valid_project_id.side_effect = (
            SqliteInterfaceException("err"))
        result = await self.service.create_folder(5, None, "Root")
        self.assertFalse(result.success)
        self.assertTrue(result.is_internal)
        self.mock_state.mark_database_failed.assert_called_once()

    async def test_create_folder_invalid_project(self):
        self.mock_repo.is_valid_project_id.return_value = False
        result = await self.service.create_folder(5, None, "Root")
        self.assertFalse(result.success)
        self.assertTrue(result.not_found)

    async def test_create_folder_parent_check_db_exception(self):
        self.mock_repo.is_valid_project_id.return_value = True
        self.mock_repo.get_folder.side_effect = SqliteInterfaceException("err")
        result = await self.service.create_folder(5, 1, "Child")
        self.assertFalse(result.success)
        self.assertTrue(result.is_internal)

    async def test_create_folder_invalid_parent(self):
        self.mock_repo.is_valid_project_id.return_value = True
        self.mock_repo.get_folder.return_value = None
        result = await self.service.create_folder(5, 999, "Child")
        self.assertFalse(result.success)
        self.assertTrue(result.not_found)
        self.assertIn("Parent folder", result.error_msg)

    async def test_create_folder_parent_belongs_to_different_project(self):
        self.mock_repo.is_valid_project_id.return_value = True
        self.mock_repo.get_folder.return_value = {
            **_FOLDER, "project_id": 999}
        result = await self.service.create_folder(5, 1, "Child")
        self.assertFalse(result.success)
        self.assertFalse(result.not_found)
        self.assertFalse(result.is_internal)
        self.assertFalse(result.is_conflict)

    async def test_create_folder_name_check_db_exception(self):
        self.mock_repo.is_valid_project_id.return_value = True
        self.mock_repo.folder_name_exists.side_effect = (
            SqliteInterfaceException("err"))
        result = await self.service.create_folder(5, None, "Root")
        self.assertFalse(result.success)
        self.assertTrue(result.is_internal)

    async def test_create_folder_name_conflict(self):
        self.mock_repo.is_valid_project_id.return_value = True
        self.mock_repo.folder_name_exists.return_value = True
        result = await self.service.create_folder(5, None, "Root")
        self.assertFalse(result.success)
        self.assertTrue(result.is_conflict)

    async def test_create_folder_insert_db_exception(self):
        self.mock_repo.is_valid_project_id.return_value = True
        self.mock_repo.folder_name_exists.return_value = False
        self.mock_repo.add_folder.side_effect = SqliteInterfaceException("err")
        result = await self.service.create_folder(5, None, "Root")
        self.assertFalse(result.success)
        self.assertTrue(result.is_internal)

    async def test_create_folder_success_root_level(self):
        self.mock_repo.is_valid_project_id.return_value = True
        self.mock_repo.folder_name_exists.return_value = False
        self.mock_repo.add_folder.return_value = 42
        result = await self.service.create_folder(5, None, "Root")
        self.assertTrue(result.success)
        self.assertEqual(result.data, 42)
        self.mock_repo.get_folder.assert_not_called()

    async def test_create_folder_success_with_valid_parent(self):
        self.mock_repo.is_valid_project_id.return_value = True
        self.mock_repo.get_folder.return_value = _FOLDER
        self.mock_repo.folder_name_exists.return_value = False
        self.mock_repo.add_folder.return_value = 43
        result = await self.service.create_folder(
            _FOLDER["project_id"], 1, "Child")
        self.assertTrue(result.success)
        self.assertEqual(result.data, 43)

    # ------------------------------------------------------------------
    # update_folder
    # ------------------------------------------------------------------

    async def test_update_folder_service_unavailable(self):
        self.mock_state.is_available.return_value = False
        result = await self.service.update_folder(1, "New")
        self.assertFalse(result.success)
        self.assertTrue(result.is_internal)

    async def test_update_folder_lookup_db_exception(self):
        self.mock_repo.get_folder.side_effect = SqliteInterfaceException("err")
        result = await self.service.update_folder(1, "New")
        self.assertFalse(result.success)
        self.assertTrue(result.is_internal)

    async def test_update_folder_not_found(self):
        self.mock_repo.get_folder.return_value = None
        result = await self.service.update_folder(1, "New")
        self.assertFalse(result.success)
        self.assertTrue(result.not_found)

    async def test_update_folder_same_name_skips_conflict_check(self):
        self.mock_repo.get_folder.return_value = _FOLDER
        result = await self.service.update_folder(1, _FOLDER["name"])
        self.assertTrue(result.success)
        self.mock_repo.folder_name_exists.assert_not_called()

    async def test_update_folder_name_check_db_exception(self):
        self.mock_repo.get_folder.return_value = _FOLDER
        self.mock_repo.folder_name_exists.side_effect = (
            SqliteInterfaceException("err"))
        result = await self.service.update_folder(1, "New")
        self.assertFalse(result.success)
        self.assertTrue(result.is_internal)

    async def test_update_folder_name_conflict(self):
        self.mock_repo.get_folder.return_value = _FOLDER
        self.mock_repo.folder_name_exists.return_value = True
        result = await self.service.update_folder(1, "New")
        self.assertFalse(result.success)
        self.assertTrue(result.is_conflict)

    async def test_update_folder_rename_db_exception(self):
        self.mock_repo.get_folder.return_value = _FOLDER
        self.mock_repo.folder_name_exists.return_value = False
        self.mock_repo.update_folder_name.side_effect = (
            SqliteInterfaceException("err"))
        result = await self.service.update_folder(1, "New")
        self.assertFalse(result.success)
        self.assertTrue(result.is_internal)

    async def test_update_folder_success(self):
        self.mock_repo.get_folder.return_value = _FOLDER
        self.mock_repo.folder_name_exists.return_value = False
        result = await self.service.update_folder(1, "New")
        self.assertTrue(result.success)
        self.mock_repo.update_folder_name.assert_called_once_with(1, "New")

    # ------------------------------------------------------------------
    # delete_folder
    # ------------------------------------------------------------------

    async def test_delete_folder_service_unavailable(self):
        self.mock_state.is_available.return_value = False
        result = await self.service.delete_folder(1)
        self.assertFalse(result.success)
        self.assertTrue(result.is_internal)

    async def test_delete_folder_lookup_db_exception(self):
        self.mock_repo.get_folder.side_effect = SqliteInterfaceException("err")
        result = await self.service.delete_folder(1)
        self.assertFalse(result.success)
        self.assertTrue(result.is_internal)
        self.mock_state.mark_database_failed.assert_called_once()

    async def test_delete_folder_not_found(self):
        self.mock_repo.get_folder.return_value = None
        result = await self.service.delete_folder(1)
        self.assertFalse(result.success)
        self.assertTrue(result.not_found)

    async def test_delete_folder_db_exception(self):
        self.mock_repo.get_folder.return_value = _FOLDER
        self.mock_repo.delete_folder.side_effect = SqliteInterfaceException("err")
        result = await self.service.delete_folder(1)
        self.assertFalse(result.success)
        self.assertTrue(result.is_internal)

    async def test_delete_folder_success(self):
        self.mock_repo.get_folder.return_value = _FOLDER
        result = await self.service.delete_folder(1)
        self.assertTrue(result.success)


if __name__ == "__main__":
    unittest.main()
