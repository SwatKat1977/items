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
    # user management: reads
    # -------------------------------------------------------

    async def test_list_users_returns_empty_list_when_none(self):
        self.mock_db.run_query.return_value = None
        self.assertEqual(await self.repo.list_users(), [])

    async def test_list_users_returns_rows(self):
        rows = [(1, "a@b.com", "A", "A", 1, 1, 0, 1)]
        self.mock_db.run_query.return_value = rows
        self.assertEqual(await self.repo.list_users(), rows)

    async def test_get_user_by_id_passes_correct_query(self):
        self.mock_db.run_query.return_value = None
        await self.repo.get_user_by_id(42)
        self.mock_db.run_query.assert_called_once_with(
            UserRepository.GET_USER_BY_ID_QUERY, (42,), fetch_one=True)

    async def test_email_exists_true_when_row_returned(self):
        self.mock_db.run_query.return_value = (1,)
        self.assertTrue(await self.repo.email_address_exists("a@b.com"))

    async def test_email_exists_false_when_no_row(self):
        self.mock_db.run_query.return_value = None
        self.assertFalse(await self.repo.email_address_exists("a@b.com"))

    async def test_email_exists_excludes_supplied_id(self):
        """Updating a user must not conflict with its own current address."""
        self.mock_db.run_query.return_value = None
        await self.repo.email_address_exists("a@b.com", 7)
        self.mock_db.run_query.assert_called_once_with(
            UserRepository.EMAIL_EXISTS_EXCLUDING_QUERY,
            ("a@b.com", 7), fetch_one=True)

    async def test_count_active_administrators(self):
        self.mock_db.run_query.return_value = (3,)
        self.assertEqual(await self.repo.count_active_administrators(1), 3)

    async def test_count_active_administrators_zero_when_no_row(self):
        self.mock_db.run_query.return_value = None
        self.assertEqual(await self.repo.count_active_administrators(1), 0)

    # -------------------------------------------------------
    # user management: writes
    # -------------------------------------------------------

    async def test_create_user_inserts_profile_then_credentials(self):
        self.mock_db.insert_query = AsyncMock(return_value=5)

        user_id = await self.repo.create_user(
            email="a@b.com", full_name="A", display_name="A",
            account_status=1, logon_type=0, is_administrator=True,
            password_hash="$argon2-hash")

        self.assertEqual(user_id, 5)
        self.assertEqual(self.mock_db.insert_query.await_count, 2)

        profile_call, auth_call = self.mock_db.insert_query.await_args_list
        self.assertEqual(profile_call.args[0],
                         UserRepository.ADD_USER_PROFILE_QUERY)
        self.assertEqual(auth_call.args[0],
                         UserRepository.ADD_USER_AUTH_DETAILS_QUERY)
        # Credentials are linked to the newly created profile.
        self.assertEqual(auth_call.args[1], ("$argon2-hash", 5))

    async def test_create_user_records_a_real_insertion_date(self):
        """insertion_date was previously hardcoded to 0."""
        self.mock_db.insert_query = AsyncMock(return_value=5)

        with patch("data_access.user_repository.time.time",
                   return_value=1785000000.9):
            await self.repo.create_user(
                email="a@b.com", full_name="A", display_name="A",
                account_status=1, logon_type=0, is_administrator=False,
                password_hash="h")

        params = self.mock_db.insert_query.await_args_list[0].args[1]
        self.assertEqual(params[3], 1785000000)

    async def test_create_user_converts_admin_flag_to_int(self):
        self.mock_db.insert_query = AsyncMock(return_value=5)

        await self.repo.create_user(
            email="a@b.com", full_name="A", display_name="A",
            account_status=1, logon_type=0, is_administrator=True,
            password_hash="h")

        params = self.mock_db.insert_query.await_args_list[0].args[1]
        self.assertEqual(params[6], 1)

    async def test_update_user_commits(self):
        await self.repo.update_user(
            user_id=7, email="a@b.com", full_name="A", display_name="A",
            account_status=0, is_administrator=False)

        self.mock_db.run_query.assert_called_once_with(
            UserRepository.UPDATE_USER_PROFILE_QUERY,
            ("a@b.com", "A", "A", 0, 0, 7),
            commit=True)

    async def test_update_password_hash_commits(self):
        await self.repo.update_password_hash(7, "$argon2-new")

        self.mock_db.run_query.assert_called_once_with(
            UserRepository.UPDATE_PASSWORD_QUERY,
            ("$argon2-new", 7),
            commit=True)

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
