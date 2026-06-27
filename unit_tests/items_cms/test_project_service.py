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
from items.services.items_cms.services.project_service import ProjectService
from items.services.items_cms.repositories.project_repository import (
    ProjectRepository,
)
from items.shared.service_state import ServiceState


class TestProjectService(unittest.IsolatedAsyncioTestCase):
    """Unit tests for ProjectService."""

    async def asyncSetUp(self):
        self.mock_logger = MagicMock()
        self.mock_state = MagicMock(spec=ServiceState)
        self.mock_state.is_available.return_value = True
        self.mock_repo = AsyncMock(spec=ProjectRepository)
        self.service = ProjectService(
            self.mock_logger, self.mock_state, self.mock_repo)

    # ------------------------------------------------------------------
    # get_project
    # ------------------------------------------------------------------

    async def test_get_project_service_unavailable(self):
        self.mock_state.is_available.return_value = False
        result = await self.service.get_project(1)
        self.assertFalse(result.success)
        self.assertTrue(result.is_internal)

    async def test_get_project_db_exception(self):
        self.mock_repo.get_project_details.side_effect = (
            SqliteInterfaceException("err"))
        result = await self.service.get_project(1)
        self.assertFalse(result.success)
        self.assertTrue(result.is_internal)
        self.mock_state.mark_database_failed.assert_called_once()

    async def test_get_project_not_found(self):
        self.mock_repo.get_project_details.return_value = None
        result = await self.service.get_project(1)
        self.assertFalse(result.success)
        self.assertTrue(result.not_found)

    async def test_get_project_success(self):
        details = {"id": 1, "name": "Alpha", "announcement": ""}
        self.mock_repo.get_project_details.return_value = details
        result = await self.service.get_project(1)
        self.assertTrue(result.success)
        self.assertEqual(result.data, details)

    # ------------------------------------------------------------------
    # list_projects
    # ------------------------------------------------------------------

    async def test_list_projects_service_unavailable(self):
        self.mock_state.is_available.return_value = False
        result = await self.service.list_projects(["name"], False, False)
        self.assertFalse(result.success)
        self.assertTrue(result.is_internal)

    async def test_list_projects_db_exception(self):
        self.mock_repo.get_projects.side_effect = (
            SqliteInterfaceException("err"))
        result = await self.service.list_projects(["name"], False, False)
        self.assertFalse(result.success)
        self.assertTrue(result.is_internal)
        self.mock_state.mark_database_failed.assert_called_once()

    async def test_list_projects_empty(self):
        self.mock_repo.get_projects.return_value = []
        result = await self.service.list_projects(["name"], False, False)
        self.assertTrue(result.success)
        self.assertEqual(result.data, [])

    async def test_list_projects_rows_mapped_to_dicts(self):
        self.mock_repo.get_projects.return_value = [
            (1, "Alpha"), (2, "Beta")]
        result = await self.service.list_projects(["name"], False, False)
        self.assertTrue(result.success)
        self.assertEqual(result.data, [
            {"id": 1, "name": "Alpha"},
            {"id": 2, "name": "Beta"},
        ])
        self.mock_repo.get_no_of_milestones_for_project.assert_not_called()
        self.mock_repo.get_no_of_testruns_for_project.assert_not_called()

    async def test_list_projects_count_milestones(self):
        self.mock_repo.get_projects.return_value = [(1, "Alpha"), (2, "Beta")]
        self.mock_repo.get_no_of_milestones_for_project.return_value = 3
        result = await self.service.list_projects(["name"], True, False)
        self.assertTrue(result.success)
        self.assertEqual(result.data[0]["no_of_milestones"], 3)
        self.assertEqual(result.data[1]["no_of_milestones"], 3)
        self.mock_repo.get_no_of_testruns_for_project.assert_not_called()

    async def test_list_projects_count_test_runs(self):
        self.mock_repo.get_projects.return_value = [(1, "Alpha")]
        self.mock_repo.get_no_of_testruns_for_project.return_value = 7
        result = await self.service.list_projects(["name"], False, True)
        self.assertTrue(result.success)
        self.assertEqual(result.data[0]["no_of_test_runs"], 7)
        self.mock_repo.get_no_of_milestones_for_project.assert_not_called()

    async def test_list_projects_both_counts(self):
        self.mock_repo.get_projects.return_value = [(1, "Alpha")]
        self.mock_repo.get_no_of_milestones_for_project.return_value = 2
        self.mock_repo.get_no_of_testruns_for_project.return_value = 5
        result = await self.service.list_projects(["name"], True, True)
        self.assertTrue(result.success)
        self.assertEqual(result.data[0]["no_of_milestones"], 2)
        self.assertEqual(result.data[0]["no_of_test_runs"], 5)

    async def test_list_projects_counts_called_with_correct_id(self):
        self.mock_repo.get_projects.return_value = [(42, "Alpha")]
        self.mock_repo.get_no_of_milestones_for_project.return_value = 0
        self.mock_repo.get_no_of_testruns_for_project.return_value = 0
        await self.service.list_projects(["name"], True, True)
        self.mock_repo.get_no_of_milestones_for_project.assert_called_once_with(
            42)
        self.mock_repo.get_no_of_testruns_for_project.assert_called_once_with(
            42)

    # ------------------------------------------------------------------
    # create_project
    # ------------------------------------------------------------------

    async def test_create_project_service_unavailable(self):
        self.mock_state.is_available.return_value = False
        result = await self.service.create_project("Alpha", "", False)
        self.assertFalse(result.success)
        self.assertTrue(result.is_internal)

    async def test_create_project_name_check_db_exception(self):
        self.mock_repo.project_name_exists.side_effect = (
            SqliteInterfaceException("err"))
        result = await self.service.create_project("Alpha", "", False)
        self.assertFalse(result.success)
        self.assertTrue(result.is_internal)
        self.mock_state.mark_database_failed.assert_called_once()

    async def test_create_project_name_conflict(self):
        self.mock_repo.project_name_exists.return_value = True
        result = await self.service.create_project("Alpha", "", False)
        self.assertFalse(result.success)
        self.assertFalse(result.is_internal)
        self.assertFalse(result.not_found)
        self.assertIn("already exists", result.error_msg)
        self.mock_repo.add_project.assert_not_called()

    async def test_create_project_insert_db_exception(self):
        self.mock_repo.project_name_exists.return_value = False
        self.mock_repo.add_project.side_effect = (
            SqliteInterfaceException("err"))
        result = await self.service.create_project("Alpha", "", False)
        self.assertFalse(result.success)
        self.assertTrue(result.is_internal)
        self.mock_state.mark_database_failed.assert_called_once()

    async def test_create_project_success(self):
        self.mock_repo.project_name_exists.return_value = False
        self.mock_repo.add_project.return_value = 5
        result = await self.service.create_project(
            "Alpha", "Welcome!", True)
        self.assertTrue(result.success)
        self.assertEqual(result.data, 5)
        self.mock_repo.add_project.assert_called_once_with(
            "Alpha", "Welcome!", True)

    # ------------------------------------------------------------------
    # modify_project
    # ------------------------------------------------------------------

    async def test_modify_project_service_unavailable(self):
        self.mock_state.is_available.return_value = False
        result = await self.service.modify_project(1, "Alpha", "", False)
        self.assertFalse(result.success)
        self.assertTrue(result.is_internal)

    async def test_modify_project_get_details_db_exception(self):
        self.mock_repo.get_project_details.side_effect = (
            SqliteInterfaceException("err"))
        result = await self.service.modify_project(1, "Alpha", "", False)
        self.assertFalse(result.success)
        self.assertTrue(result.is_internal)
        self.mock_state.mark_database_failed.assert_called_once()

    async def test_modify_project_not_found(self):
        self.mock_repo.get_project_details.return_value = None
        result = await self.service.modify_project(1, "Alpha", "", False)
        self.assertFalse(result.success)
        self.assertTrue(result.not_found)

    async def test_modify_project_name_unchanged_skips_uniqueness_check(self):
        self.mock_repo.get_project_details.return_value = {
            "id": 1, "name": "Alpha", "announcement": ""}
        result = await self.service.modify_project(1, "Alpha", "new ann", True)
        self.assertTrue(result.success)
        self.mock_repo.project_name_exists.assert_not_called()
        self.mock_repo.modify_project.assert_called_once_with(
            1, "new ann", True, None)

    async def test_modify_project_name_changed_uniqueness_db_exception(self):
        self.mock_repo.get_project_details.return_value = {
            "id": 1, "name": "Alpha", "announcement": ""}
        self.mock_repo.project_name_exists.side_effect = (
            SqliteInterfaceException("err"))
        result = await self.service.modify_project(1, "Beta", "", False)
        self.assertFalse(result.success)
        self.assertTrue(result.is_internal)
        self.mock_state.mark_database_failed.assert_called_once()

    async def test_modify_project_name_changed_name_conflict(self):
        self.mock_repo.get_project_details.return_value = {
            "id": 1, "name": "Alpha", "announcement": ""}
        self.mock_repo.project_name_exists.return_value = True
        result = await self.service.modify_project(1, "Beta", "", False)
        self.assertFalse(result.success)
        self.assertFalse(result.is_internal)
        self.assertFalse(result.not_found)
        self.assertIn("already exists", result.error_msg)
        self.mock_repo.modify_project.assert_not_called()

    async def test_modify_project_update_db_exception(self):
        self.mock_repo.get_project_details.return_value = {
            "id": 1, "name": "Alpha", "announcement": ""}
        self.mock_repo.project_name_exists.return_value = False
        self.mock_repo.modify_project.side_effect = (
            SqliteInterfaceException("err"))
        result = await self.service.modify_project(1, "Beta", "", False)
        self.assertFalse(result.success)
        self.assertTrue(result.is_internal)
        self.mock_state.mark_database_failed.assert_called_once()

    async def test_modify_project_name_changed_success(self):
        self.mock_repo.get_project_details.return_value = {
            "id": 1, "name": "Alpha", "announcement": ""}
        self.mock_repo.project_name_exists.return_value = False
        result = await self.service.modify_project(1, "Beta", "ann", True)
        self.assertTrue(result.success)
        self.mock_repo.modify_project.assert_called_once_with(
            1, "ann", True, "Beta")

    # ------------------------------------------------------------------
    # delete_project
    # ------------------------------------------------------------------

    async def test_delete_project_service_unavailable(self):
        self.mock_state.is_available.return_value = False
        result = await self.service.delete_project(1, False)
        self.assertFalse(result.success)
        self.assertTrue(result.is_internal)

    async def test_delete_project_id_check_db_exception(self):
        self.mock_repo.is_valid_project_id.side_effect = (
            SqliteInterfaceException("err"))
        result = await self.service.delete_project(1, False)
        self.assertFalse(result.success)
        self.assertTrue(result.is_internal)
        self.mock_state.mark_database_failed.assert_called_once()

    async def test_delete_project_invalid_id(self):
        self.mock_repo.is_valid_project_id.return_value = False
        result = await self.service.delete_project(1, False)
        self.assertFalse(result.success)
        self.assertTrue(result.not_found)

    async def test_delete_project_soft_delete(self):
        self.mock_repo.is_valid_project_id.return_value = True
        result = await self.service.delete_project(1, False)
        self.assertTrue(result.success)
        self.mock_repo.mark_project_for_purge.assert_called_once_with(1)
        self.mock_repo.hard_delete_project.assert_not_called()

    async def test_delete_project_hard_delete(self):
        self.mock_repo.is_valid_project_id.return_value = True
        result = await self.service.delete_project(1, True)
        self.assertTrue(result.success)
        self.mock_repo.hard_delete_project.assert_called_once_with(1)
        self.mock_repo.mark_project_for_purge.assert_not_called()

    async def test_delete_project_delete_db_exception(self):
        self.mock_repo.is_valid_project_id.return_value = True
        self.mock_repo.hard_delete_project.side_effect = (
            SqliteInterfaceException("err"))
        result = await self.service.delete_project(1, True)
        self.assertFalse(result.success)
        self.assertTrue(result.is_internal)
        self.mock_state.mark_database_failed.assert_called_once()


if __name__ == "__main__":
    unittest.main()
