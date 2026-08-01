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
        self.mock_db.insert_query = AsyncMock()

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

    async def test_password_update_does_not_insert_a_second_row(self):
        """user_auth_details.user_id is UNIQUE - this must UPDATE, not INSERT."""
        self.assertIn("UPDATE", UserRepository.UPDATE_PASSWORD_QUERY.upper())
        self.assertNotIn("INSERT", UserRepository.UPDATE_PASSWORD_QUERY.upper())

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

    # -------------------------------------------------------
    # get_all_users tests
    # -------------------------------------------------------

    async def test_get_all_users_returns_empty_list_when_no_rows(self):
        self.mock_db.run_query.return_value = None
        result = await self.repo.get_all_users()
        self.assertEqual(result, [])

    async def test_get_all_users_returns_rows(self):
        rows = [
            (1, "a@b.com", "A", "A", 1, 0, 1),
            (2, "c@d.com", "C", "C", 1, 0, 0),
        ]
        self.mock_db.run_query.return_value = rows
        result = await self.repo.get_all_users()
        self.assertEqual(result, rows)

    async def test_get_all_users_passes_correct_query(self):
        self.mock_db.run_query.return_value = None
        await self.repo.get_all_users()
        self.mock_db.run_query.assert_called_once_with(
            UserRepository.GET_ALL_USERS_QUERY, ())

    # -------------------------------------------------------
    # get_user_by_id tests
    # -------------------------------------------------------

    async def test_get_user_by_id_returns_none_when_not_found(self):
        self.mock_db.run_query.return_value = None
        result = await self.repo.get_user_by_id(99)
        self.assertIsNone(result)

    async def test_get_user_by_id_returns_row_when_found(self):
        row = (1, "a@b.com", "Full", "Display", 1, 0, 1)
        self.mock_db.run_query.return_value = row
        result = await self.repo.get_user_by_id(1)
        self.assertEqual(result, row)

    async def test_get_user_by_id_passes_correct_query(self):
        self.mock_db.run_query.return_value = None
        await self.repo.get_user_by_id(5)
        self.mock_db.run_query.assert_called_once_with(
            UserRepository.GET_USER_BY_ID_QUERY, (5,), fetch_one=True)

    # -------------------------------------------------------
    # email_exists tests
    # -------------------------------------------------------

    async def test_email_exists_returns_false_when_count_zero(self):
        self.mock_db.run_query.return_value = (0,)
        result = await self.repo.email_exists("new@example.com")
        self.assertFalse(result)

    async def test_email_exists_returns_true_when_count_nonzero(self):
        self.mock_db.run_query.return_value = (1,)
        result = await self.repo.email_exists("existing@example.com")
        self.assertTrue(result)

    async def test_email_exists_returns_false_when_db_returns_none(self):
        self.mock_db.run_query.return_value = None
        result = await self.repo.email_exists("new@example.com")
        self.assertFalse(result)

    async def test_email_exists_passes_correct_query(self):
        self.mock_db.run_query.return_value = (0,)
        await self.repo.email_exists("test@example.com")
        self.mock_db.run_query.assert_called_once_with(
            UserRepository.EMAIL_EXISTS_QUERY, ("test@example.com",),
            fetch_one=True)

    # -------------------------------------------------------
    # create_user tests
    # -------------------------------------------------------

    async def test_create_user_returns_new_user_id(self):
        self.mock_db.insert_query.return_value = 42
        result = await self.repo.create_user(
            "a@b.com", "Full Name", "Display", 1, 0, False)
        self.assertEqual(result, 42)

    async def test_create_user_passes_correct_query(self):
        self.mock_db.insert_query.return_value = 1
        with patch("data_access.user_repository.time") as mock_time:
            mock_time.time.return_value = 1000000
            await self.repo.create_user("a@b.com", "Full", "Display", 1, 0, True)

        args = self.mock_db.insert_query.call_args
        self.assertEqual(args[0][0], UserRepository.INSERT_USER_PROFILE_QUERY)
        params = args[0][1]
        self.assertEqual(params[0], "a@b.com")
        self.assertEqual(params[1], "Full")
        self.assertEqual(params[2], "Display")
        self.assertEqual(params[3], 1000000)   # insertion_date
        self.assertEqual(params[4], 1)          # account_status
        self.assertEqual(params[5], 0)          # logon_type
        self.assertEqual(params[6], 1)          # is_administrator cast to int

    async def test_create_user_converts_is_administrator_to_int(self):
        self.mock_db.insert_query.return_value = 1
        with patch("data_access.user_repository.time"):
            await self.repo.create_user("a@b.com", "F", "D", 1, 0, False)
        params = self.mock_db.insert_query.call_args[0][1]
        self.assertEqual(params[6], 0)

    # -------------------------------------------------------
    # create_user_auth tests
    # -------------------------------------------------------

    async def test_create_user_auth_calls_insert_with_correct_args(self):
        self.mock_db.insert_query.return_value = 1
        await self.repo.create_user_auth(7, "$argon2id$hash")
        self.mock_db.insert_query.assert_called_once_with(
            UserRepository.INSERT_USER_AUTH_QUERY, ("$argon2id$hash", 7))

    # -------------------------------------------------------
    # update_user tests
    # -------------------------------------------------------

    async def test_update_user_calls_run_query_with_commit(self):
        self.mock_db.run_query.return_value = None
        await self.repo.update_user(3, "New Full", "New Display", 1, True)
        self.mock_db.run_query.assert_called_once_with(
            UserRepository.UPDATE_USER_QUERY,
            ("New Full", "New Display", 1, 1, 3),
            commit=True)

    async def test_update_user_converts_is_administrator_to_int(self):
        self.mock_db.run_query.return_value = None
        await self.repo.update_user(3, "Full", "Display", 1, False)
        params = self.mock_db.run_query.call_args[0][1]
        self.assertEqual(params[3], 0)   # int(False)

    # -------------------------------------------------------
    # update_password tests
    # -------------------------------------------------------

    async def test_update_password_calls_run_query_with_commit(self):
        self.mock_db.run_query.return_value = None
        await self.repo.update_password(5, "$argon2id$newhash")
        self.mock_db.run_query.assert_called_once_with(
            UserRepository.UPDATE_PASSWORD_QUERY,
            ("$argon2id$newhash", 5),
            commit=True)

    # -------------------------------------------------------
    # count_active_administrators tests
    # -------------------------------------------------------

    async def test_count_active_admins_returns_count_from_db(self):
        self.mock_db.run_query.return_value = (3,)
        result = await self.repo.count_active_administrators(1)
        self.assertEqual(result, 3)

    async def test_count_active_admins_returns_zero_when_db_returns_none(self):
        self.mock_db.run_query.return_value = None
        result = await self.repo.count_active_administrators(1)
        self.assertEqual(result, 0)

    async def test_count_active_admins_passes_correct_query(self):
        self.mock_db.run_query.return_value = (0,)
        await self.repo.count_active_administrators(1)
        self.mock_db.run_query.assert_called_once_with(
            UserRepository.COUNT_ACTIVE_ADMINS_QUERY,
            (1,),
            fetch_one=True)
