import unittest
from unittest.mock import MagicMock, AsyncMock, patch
import logging
from data_access.user_repository import UserRepository


class TestUserRepository(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.logger = logging.getLogger("test")
        self.mock_config = MagicMock()
        self.mock_config.backend_db_filename = "test.db"

        self.mock_db = MagicMock()
        self.mock_db.run_query = AsyncMock()

        patcher = patch("data_access.user_repository.SqliteInterface",
                        return_value=self.mock_db)
        self.addCleanup(patcher.stop)
        patcher.start()

        self.repo = UserRepository(self.logger, self.mock_config)

    # -------------------------------------------------------
    # get_user_by_email tests
    # -------------------------------------------------------

    async def test_get_user_by_email_returns_none_when_not_found(self):
        self.mock_db.run_query.return_value = None
        result = await self.repo.get_user_by_email("a@b.com")
        self.assertIsNone(result)

    async def test_get_user_by_email_returns_row(self):
        expected = (42, 0, 1)
        self.mock_db.run_query.return_value = expected
        result = await self.repo.get_user_by_email("a@b.com")
        self.assertEqual(result, expected)

    async def test_get_user_by_email_passes_correct_query(self):
        self.mock_db.run_query.return_value = None
        await self.repo.get_user_by_email("test@example.com")
        self.mock_db.run_query.assert_called_once_with(
            UserRepository.GET_USER_FOR_LOGON_QUERY,
            ("test@example.com",),
            fetch_one=True)

    # -------------------------------------------------------
    # get_user_profile_by_email tests
    # -------------------------------------------------------

    async def test_get_user_profile_returns_none_when_not_found(self):
        self.mock_db.run_query.return_value = None
        result = await self.repo.get_user_profile_by_email("a@b.com")
        self.assertIsNone(result)

    async def test_get_user_profile_returns_row(self):
        expected = (1, "admin@localhost", "Local Admin", "Local Admin", 1, 0, 1)
        self.mock_db.run_query.return_value = expected
        result = await self.repo.get_user_profile_by_email("admin@localhost")
        self.assertEqual(result, expected)

    async def test_get_user_profile_passes_correct_query(self):
        self.mock_db.run_query.return_value = None
        await self.repo.get_user_profile_by_email("test@example.com")
        self.mock_db.run_query.assert_called_once_with(
            UserRepository.GET_USER_PROFILE_QUERY,
            ("test@example.com",),
            fetch_one=True)

    async def test_profile_query_selects_is_administrator(self):
        """The admin flag is the reason this query exists."""
        self.assertIn("is_administrator",
                      UserRepository.GET_USER_PROFILE_QUERY)

    # -------------------------------------------------------
    # get_password_hash tests
    # -------------------------------------------------------

    async def test_get_password_hash_returns_none_when_no_record(self):
        self.mock_db.run_query.return_value = None
        result = await self.repo.get_password_hash(1)
        self.assertIsNone(result)

    async def test_get_password_hash_returns_hash_str(self):
        expected_hash = "$argon2id$v=19$somehash"
        self.mock_db.run_query.return_value = (expected_hash,)
        result = await self.repo.get_password_hash(1)
        self.assertEqual(result, expected_hash)

    async def test_get_password_hash_passes_correct_query(self):
        self.mock_db.run_query.return_value = None
        await self.repo.get_password_hash(42)
        self.mock_db.run_query.assert_called_once_with(
            UserRepository.GET_PASSWORD_HASH_QUERY,
            (42,),
            fetch_one=True)
