import unittest
from unittest.mock import MagicMock, AsyncMock, patch
import logging
from data_access.role_repository import RoleRepository


class TestRoleRepository(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.logger = logging.getLogger("test")
        self.mock_config = MagicMock()
        self.mock_config.backend_db_filename = "test.db"

        self.mock_db = MagicMock()
        self.mock_db.run_query = AsyncMock()
        self.mock_db.insert_query = AsyncMock()
        self.mock_db.delete_query = AsyncMock()
        self.mock_db.bulk_insert_query = AsyncMock()

        patcher = patch("data_access.role_repository.SqliteInterface",
                        return_value=self.mock_db)
        self.addCleanup(patcher.stop)
        patcher.start()

        self.repo = RoleRepository(self.logger, self.mock_config)

    # -------------------------------------------------------
    # get_all_roles
    # -------------------------------------------------------

    async def test_get_all_roles_returns_empty_list_when_none(self):
        self.mock_db.run_query.return_value = None
        result = await self.repo.get_all_roles()
        self.assertEqual(result, [])

    async def test_get_all_roles_returns_rows(self):
        expected = [(1, "Tester"), (2, "Lead")]
        self.mock_db.run_query.return_value = expected
        result = await self.repo.get_all_roles()
        self.assertEqual(result, expected)

    async def test_get_all_roles_passes_correct_query(self):
        self.mock_db.run_query.return_value = []
        await self.repo.get_all_roles()
        self.mock_db.run_query.assert_called_once_with(
            RoleRepository.GET_ALL_ROLES_QUERY, ())

    # -------------------------------------------------------
    # get_role_by_id
    # -------------------------------------------------------

    async def test_get_role_by_id_returns_none_when_not_found(self):
        self.mock_db.run_query.return_value = None
        result = await self.repo.get_role_by_id(999)
        self.assertIsNone(result)

    async def test_get_role_by_id_returns_row(self):
        self.mock_db.run_query.return_value = (1, "Tester")
        result = await self.repo.get_role_by_id(1)
        self.assertEqual(result, (1, "Tester"))

    async def test_get_role_by_id_passes_correct_query(self):
        self.mock_db.run_query.return_value = None
        await self.repo.get_role_by_id(5)
        self.mock_db.run_query.assert_called_once_with(
            RoleRepository.GET_ROLE_BY_ID_QUERY, (5,), fetch_one=True)

    # -------------------------------------------------------
    # role_name_exists
    # -------------------------------------------------------

    async def test_role_name_exists_returns_false_when_not_found(self):
        self.mock_db.run_query.return_value = None
        result = await self.repo.role_name_exists("Tester")
        self.assertFalse(result)

    async def test_role_name_exists_returns_true_when_found(self):
        self.mock_db.run_query.return_value = (1,)
        result = await self.repo.role_name_exists("Tester")
        self.assertTrue(result)

    # -------------------------------------------------------
    # get_role_permissions
    # -------------------------------------------------------

    async def test_get_role_permissions_returns_empty_list_when_none(self):
        self.mock_db.run_query.return_value = None
        result = await self.repo.get_role_permissions(1)
        self.assertEqual(result, [])

    async def test_get_role_permissions_returns_rows(self):
        expected = [("test_cases", 1, 1, 0)]
        self.mock_db.run_query.return_value = expected
        result = await self.repo.get_role_permissions(1)
        self.assertEqual(result, expected)

    async def test_get_role_permissions_passes_correct_query(self):
        self.mock_db.run_query.return_value = []
        await self.repo.get_role_permissions(7)
        self.mock_db.run_query.assert_called_once_with(
            RoleRepository.GET_ROLE_PERMISSIONS_QUERY, (7,))

    # -------------------------------------------------------
    # create_role
    # -------------------------------------------------------

    async def test_create_role_inserts_role_and_returns_id(self):
        self.mock_db.insert_query.return_value = 42
        role_id = await self.repo.create_role("Tester", [])
        self.assertEqual(role_id, 42)
        self.mock_db.insert_query.assert_awaited_once_with(
            RoleRepository.INSERT_ROLE_QUERY, ("Tester",))

    async def test_create_role_with_permissions_inserts_grid(self):
        self.mock_db.insert_query.return_value = 1
        permissions = [("test_cases", True, True, False)]
        await self.repo.create_role("Tester", permissions)
        self.mock_db.bulk_insert_query.assert_awaited_once_with(
            RoleRepository.INSERT_ROLE_PERMISSION_QUERY,
            [(1, "test_cases", True, True, False)])

    async def test_create_role_with_empty_permissions_does_not_bulk_insert(self):
        self.mock_db.insert_query.return_value = 1
        await self.repo.create_role("Tester", [])
        self.mock_db.bulk_insert_query.assert_not_called()

    async def test_create_role_always_clears_existing_permissions_first(self):
        """New role, so nothing to clear - but the replace-then-insert
        sequence must still run delete first, insert second, every time."""
        self.mock_db.insert_query.return_value = 1
        await self.repo.create_role("Tester", [("test_cases", 1, 0, 0)])
        self.mock_db.delete_query.assert_awaited_once_with(
            RoleRepository.DELETE_ROLE_PERMISSIONS_QUERY, (1,))

    # -------------------------------------------------------
    # update_role
    # -------------------------------------------------------

    async def test_update_role_name_only_updates_name(self):
        await self.repo.update_role(1, "New Name", None)
        self.mock_db.run_query.assert_awaited_once_with(
            RoleRepository.UPDATE_ROLE_NAME_QUERY, ("New Name", 1),
            commit=True)
        self.mock_db.delete_query.assert_not_called()

    async def test_update_role_name_none_does_not_update_name(self):
        await self.repo.update_role(1, None, None)
        self.mock_db.run_query.assert_not_called()

    async def test_update_role_permissions_replaces_grid(self):
        permissions = [("test_cases", True, False, False)]
        await self.repo.update_role(1, None, permissions)
        self.mock_db.delete_query.assert_awaited_once_with(
            RoleRepository.DELETE_ROLE_PERMISSIONS_QUERY, (1,))
        self.mock_db.bulk_insert_query.assert_awaited_once_with(
            RoleRepository.INSERT_ROLE_PERMISSION_QUERY,
            [(1, "test_cases", True, False, False)])

    async def test_update_role_permissions_none_leaves_grid_untouched(self):
        await self.repo.update_role(1, "New Name", None)
        self.mock_db.delete_query.assert_not_called()
        self.mock_db.bulk_insert_query.assert_not_called()

    async def test_update_role_empty_permissions_list_clears_grid(self):
        """An explicit empty list (not None) means "this role now grants
        nothing" - distinct from omitting permissions entirely."""
        await self.repo.update_role(1, None, [])
        self.mock_db.delete_query.assert_awaited_once_with(
            RoleRepository.DELETE_ROLE_PERMISSIONS_QUERY, (1,))
        self.mock_db.bulk_insert_query.assert_not_called()

    # -------------------------------------------------------
    # delete_role
    # -------------------------------------------------------

    async def test_delete_role_passes_correct_query(self):
        await self.repo.delete_role(3)
        self.mock_db.delete_query.assert_awaited_once_with(
            RoleRepository.DELETE_ROLE_QUERY, (3,))


if __name__ == "__main__":
    unittest.main()
