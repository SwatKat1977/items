import unittest
from unittest.mock import MagicMock, AsyncMock, patch
import logging
from data_access.project_member_repository import ProjectMemberRepository


class TestProjectMemberRepository(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.logger = logging.getLogger("test")
        self.mock_config = MagicMock()
        self.mock_config.backend_db_filename = "test.db"

        self.mock_db = MagicMock()
        self.mock_db.run_query = AsyncMock()
        self.mock_db.insert_query = AsyncMock()
        self.mock_db.delete_query = AsyncMock()

        patcher = patch(
            "data_access.project_member_repository.SqliteInterface",
            return_value=self.mock_db)
        self.addCleanup(patcher.stop)
        patcher.start()

        self.repo = ProjectMemberRepository(self.logger, self.mock_config)

    # -------------------------------------------------------
    # get_memberships_for_user
    # -------------------------------------------------------

    async def test_get_memberships_for_user_returns_empty_list_when_none(self):
        self.mock_db.run_query.return_value = None
        result = await self.repo.get_memberships_for_user(1)
        self.assertEqual(result, [])

    async def test_get_memberships_for_user_returns_rows(self):
        expected = [(1, 5, 2, "Tester"), (2, 7, None, None)]
        self.mock_db.run_query.return_value = expected
        result = await self.repo.get_memberships_for_user(1)
        self.assertEqual(result, expected)

    async def test_get_memberships_for_user_passes_correct_query(self):
        self.mock_db.run_query.return_value = []
        await self.repo.get_memberships_for_user(9)
        self.mock_db.run_query.assert_called_once_with(
            ProjectMemberRepository.GET_MEMBERSHIPS_FOR_USER_QUERY, (9,))

    # -------------------------------------------------------
    # get_membership
    # -------------------------------------------------------

    async def test_get_membership_returns_none_when_not_found(self):
        self.mock_db.run_query.return_value = None
        result = await self.repo.get_membership(1, 5)
        self.assertIsNone(result)

    async def test_get_membership_returns_row(self):
        self.mock_db.run_query.return_value = (1, 2, "Tester")
        result = await self.repo.get_membership(1, 5)
        self.assertEqual(result, (1, 2, "Tester"))

    async def test_get_membership_passes_correct_query(self):
        self.mock_db.run_query.return_value = None
        await self.repo.get_membership(1, 5)
        self.mock_db.run_query.assert_called_once_with(
            ProjectMemberRepository.GET_MEMBERSHIP_QUERY, (1, 5),
            fetch_one=True)

    # -------------------------------------------------------
    # create_membership
    # -------------------------------------------------------

    async def test_create_membership_returns_new_id(self):
        self.mock_db.insert_query.return_value = 42
        result = await self.repo.create_membership(1, 5, 2)
        self.assertEqual(result, 42)

    async def test_create_membership_passes_correct_query(self):
        self.mock_db.insert_query.return_value = 1
        await self.repo.create_membership(1, 5, 2)
        self.mock_db.insert_query.assert_awaited_once_with(
            ProjectMemberRepository.INSERT_MEMBERSHIP_QUERY, (1, 5, 2))

    async def test_create_membership_with_no_role(self):
        self.mock_db.insert_query.return_value = 1
        await self.repo.create_membership(1, 5, None)
        self.mock_db.insert_query.assert_awaited_once_with(
            ProjectMemberRepository.INSERT_MEMBERSHIP_QUERY, (1, 5, None))

    async def test_membership_insert_always_uses_user_principal_type(self):
        """v1 is users-only - the query hardcodes 'user', not a parameter."""
        self.assertIn("'user'",
                      ProjectMemberRepository.INSERT_MEMBERSHIP_QUERY)

    # -------------------------------------------------------
    # update_membership_role
    # -------------------------------------------------------

    async def test_update_membership_role_passes_correct_query(self):
        await self.repo.update_membership_role(1, 5, 3)
        self.mock_db.run_query.assert_awaited_once_with(
            ProjectMemberRepository.UPDATE_MEMBERSHIP_ROLE_QUERY,
            (3, 1, 5), commit=True)

    async def test_update_membership_role_can_clear_to_none(self):
        await self.repo.update_membership_role(1, 5, None)
        self.mock_db.run_query.assert_awaited_once_with(
            ProjectMemberRepository.UPDATE_MEMBERSHIP_ROLE_QUERY,
            (None, 1, 5), commit=True)

    # -------------------------------------------------------
    # delete_membership
    # -------------------------------------------------------

    async def test_delete_membership_passes_correct_query(self):
        await self.repo.delete_membership(1, 5)
        self.mock_db.delete_query.assert_awaited_once_with(
            ProjectMemberRepository.DELETE_MEMBERSHIP_QUERY, (1, 5))


if __name__ == "__main__":
    unittest.main()
