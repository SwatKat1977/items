import sqlite3
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

    # -------------------------------------------------------
    # get_effective_permissions
    # -------------------------------------------------------

    async def test_get_effective_permissions_returns_empty_list_when_none(
            self):
        self.mock_db.run_query.return_value = None
        result = await self.repo.get_effective_permissions(1, 5)
        self.assertEqual(result, [])

    async def test_get_effective_permissions_returns_rows(self):
        expected = [("test_cases", 1, 1, 0), ("milestones", 1, 0, 0)]
        self.mock_db.run_query.return_value = expected
        result = await self.repo.get_effective_permissions(1, 5)
        self.assertEqual(result, expected)

    async def test_get_effective_permissions_passes_correct_query(self):
        self.mock_db.run_query.return_value = []
        await self.repo.get_effective_permissions(9, 4)
        self.mock_db.run_query.assert_called_once_with(
            ProjectMemberRepository.GET_EFFECTIVE_PERMISSIONS_QUERY, (9, 4))


# The two tables the permissions query reads, exactly as the identity database
# builder creates them (tool_identity_db_builder/sql_values.py), minus the
# foreign keys to ``roles`` which the query does not touch.
_CREATE_ROLE_PERMISSIONS = """
    CREATE TABLE role_permissions (
        role_id integer NOT NULL, area text NOT NULL,
        can_read integer NOT NULL DEFAULT 0,
        can_add_modify integer NOT NULL DEFAULT 0,
        can_delete integer NOT NULL DEFAULT 0,
        PRIMARY KEY (role_id, area),
        CHECK (can_add_modify = 0 OR can_read = 1))"""

_CREATE_PROJECT_MEMBERS = """
    CREATE TABLE project_members (
        id integer PRIMARY KEY AUTOINCREMENT,
        principal_type text NOT NULL
            CHECK (principal_type IN ('user', 'group')),
        principal_id integer NOT NULL, project_id integer NOT NULL,
        role_id integer,
        UNIQUE (principal_type, principal_id, project_id))"""


class TestEffectivePermissionsQuery(unittest.TestCase):
    """Runs the real permissions SQL against real tables.

    The mocked repository tests above only prove the query is passed through;
    these prove it returns the right rows, which is the part that decides who
    can do what.
    """

    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        self.addCleanup(self.conn.close)
        self.conn.execute(_CREATE_ROLE_PERMISSIONS)
        self.conn.execute(_CREATE_PROJECT_MEMBERS)

        # Role 1 "Tester": read and edit test cases, read milestones.
        # Role 2 "Lead": everything on test cases.
        self.conn.executemany(
            "INSERT INTO role_permissions VALUES (?, ?, ?, ?, ?)",
            [(1, "test_cases", 1, 1, 0), (1, "milestones", 1, 0, 0),
             (2, "test_cases", 1, 1, 1)])

    def _add_member(self, principal_type, principal_id, project_id, role_id):
        self.conn.execute(
            "INSERT INTO project_members "
            "(principal_type, principal_id, project_id, role_id) "
            "VALUES (?, ?, ?, ?)",
            (principal_type, principal_id, project_id, role_id))

    def _effective(self, user_id, project_id):
        return self.conn.execute(
            ProjectMemberRepository.GET_EFFECTIVE_PERMISSIONS_QUERY,
            (user_id, project_id)).fetchall()

    def test_member_gets_every_area_of_their_role(self):
        self._add_member("user", 7, 5, 1)
        self.assertEqual(self._effective(7, 5),
                         [("milestones", 1, 0, 0), ("test_cases", 1, 1, 0)])

    def test_member_with_no_role_gets_nothing(self):
        self._add_member("user", 7, 5, None)
        self.assertEqual(self._effective(7, 5), [])

    def test_non_member_gets_nothing(self):
        self.assertEqual(self._effective(7, 5), [])

    def test_role_on_another_project_does_not_leak(self):
        self._add_member("user", 7, 6, 2)
        self.assertEqual(self._effective(7, 5), [])

    def test_another_users_role_does_not_leak(self):
        self._add_member("user", 8, 5, 2)
        self.assertEqual(self._effective(7, 5), [])

    def test_group_membership_is_ignored_in_v1(self):
        """v1 is users-only: a group row with the same id must not count."""
        self._add_member("group", 7, 5, 2)
        self.assertEqual(self._effective(7, 5), [])

    def test_a_different_role_gives_that_roles_grid(self):
        self._add_member("user", 7, 5, 2)
        self.assertEqual(self._effective(7, 5), [("test_cases", 1, 1, 1)])


if __name__ == "__main__":
    unittest.main()
