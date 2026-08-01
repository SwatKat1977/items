import unittest
import logging
from unittest.mock import MagicMock, AsyncMock, patch
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError
from weaver_framework.database.sqlite_interface import SqliteInterfaceException
from services.user_management_service import (
    UserManagementService,
    UserListResult,
    UserLookupResult,
    UserCreateResult,
    UserUpdateResult,
    PasswordResult,
)

_USER_ROW = (1, "a@b.com", "Full Name", "Display", 1, 0, 1)
_USER_DICT = {
    "id": 1,
    "email_address": "a@b.com",
    "full_name": "Full Name",
    "display_name": "Display",
    "account_status": 1,
    "logon_type": 0,
    "is_administrator": True,
}


class TestUserManagementService(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.mock_logger = MagicMock(spec=logging.Logger)
        self.mock_logger.getChild.return_value = MagicMock(spec=logging.Logger)

        self.mock_state = MagicMock()
        self.mock_state.is_available.return_value = True

        self.mock_repo = MagicMock()
        self.mock_repo.get_all_users = AsyncMock()
        self.mock_repo.get_user_by_id = AsyncMock()
        self.mock_repo.email_exists = AsyncMock()
        self.mock_repo.create_user = AsyncMock()
        self.mock_repo.create_user_auth = AsyncMock()
        self.mock_repo.update_user = AsyncMock()
        self.mock_repo.update_password = AsyncMock()
        self.mock_repo.get_password_hash = AsyncMock()

        self.svc = UserManagementService(
            self.mock_logger, self.mock_state, self.mock_repo)

    # -------------------------------------------------------
    # get_all_users tests
    # -------------------------------------------------------

    async def test_get_all_users_returns_unavailable_when_state_unavailable(self):
        self.mock_state.is_available.return_value = False
        result = await self.svc.get_all_users()
        self.assertFalse(result.available)

    async def test_get_all_users_returns_empty_list_when_no_users(self):
        self.mock_repo.get_all_users.return_value = []
        result = await self.svc.get_all_users()
        self.assertTrue(result.available)
        self.assertEqual(result.users, [])

    async def test_get_all_users_returns_users_with_is_administrator_as_bool(self):
        self.mock_repo.get_all_users.return_value = [_USER_ROW]
        result = await self.svc.get_all_users()
        self.assertEqual(len(result.users), 1)
        self.assertIs(type(result.users[0]["is_administrator"]), bool)
        self.assertTrue(result.users[0]["is_administrator"])

    async def test_get_all_users_returns_unavailable_on_db_exception(self):
        self.mock_repo.get_all_users.side_effect = SqliteInterfaceException("err")
        result = await self.svc.get_all_users()
        self.assertFalse(result.available)
        self.mock_state.set_service_degraded.assert_called_once()

    # -------------------------------------------------------
    # get_user_by_id tests
    # -------------------------------------------------------

    async def test_get_user_by_id_returns_unavailable_when_state_unavailable(self):
        self.mock_state.is_available.return_value = False
        result = await self.svc.get_user_by_id(1)
        self.assertFalse(result.available)

    async def test_get_user_by_id_returns_not_found_when_none(self):
        self.mock_repo.get_user_by_id.return_value = None
        result = await self.svc.get_user_by_id(99)
        self.assertTrue(result.available)
        self.assertFalse(result.found)

    async def test_get_user_by_id_returns_user_dict(self):
        self.mock_repo.get_user_by_id.return_value = _USER_ROW
        result = await self.svc.get_user_by_id(1)
        self.assertTrue(result.found)
        self.assertEqual(result.user, _USER_DICT)

    async def test_get_user_by_id_converts_is_administrator_to_bool(self):
        row_non_admin = (2, "b@c.com", "B", "B", 1, 0, 0)
        self.mock_repo.get_user_by_id.return_value = row_non_admin
        result = await self.svc.get_user_by_id(2)
        self.assertIs(type(result.user["is_administrator"]), bool)
        self.assertFalse(result.user["is_administrator"])

    async def test_get_user_by_id_returns_unavailable_on_db_exception(self):
        self.mock_repo.get_user_by_id.side_effect = SqliteInterfaceException("err")
        result = await self.svc.get_user_by_id(1)
        self.assertFalse(result.available)
        self.mock_state.set_service_degraded.assert_called_once()

    # -------------------------------------------------------
    # create_user tests
    # -------------------------------------------------------

    async def test_create_user_returns_unavailable_when_state_unavailable(self):
        self.mock_state.is_available.return_value = False
        result = await self.svc.create_user(
            "a@b.com", "Full", "Display", "password", False)
        self.assertFalse(result.available)

    async def test_create_user_returns_conflict_when_email_exists(self):
        self.mock_repo.email_exists.return_value = True
        result = await self.svc.create_user(
            "existing@b.com", "Full", "Display", "password", False)
        self.assertTrue(result.conflict)
        self.mock_repo.create_user.assert_not_called()

    async def test_create_user_returns_user_id_on_success(self):
        self.mock_repo.email_exists.return_value = False
        self.mock_repo.create_user.return_value = 7
        result = await self.svc.create_user(
            "new@b.com", "Full", "Display", "password", False)
        self.assertFalse(result.conflict)
        self.assertEqual(result.user_id, 7)

    async def test_create_user_hashes_password_before_storing(self):
        self.mock_repo.email_exists.return_value = False
        self.mock_repo.create_user.return_value = 7
        await self.svc.create_user("a@b.com", "F", "D", "plaintext", False)
        stored_hash = self.mock_repo.create_user_auth.call_args[0][1]
        self.assertTrue(stored_hash.startswith("$argon2"))

    async def test_create_user_creates_auth_record_with_new_user_id(self):
        self.mock_repo.email_exists.return_value = False
        self.mock_repo.create_user.return_value = 99
        await self.svc.create_user("a@b.com", "F", "D", "pw", True)
        self.mock_repo.create_user_auth.assert_awaited_once()
        self.assertEqual(self.mock_repo.create_user_auth.call_args[0][0], 99)

    async def test_create_user_returns_unavailable_on_db_exception(self):
        self.mock_repo.email_exists.side_effect = SqliteInterfaceException("err")
        result = await self.svc.create_user(
            "a@b.com", "F", "D", "pw", False)
        self.assertFalse(result.available)
        self.mock_state.set_service_degraded.assert_called_once()

    # -------------------------------------------------------
    # update_user tests
    # -------------------------------------------------------

    async def test_update_user_returns_unavailable_when_state_unavailable(self):
        self.mock_state.is_available.return_value = False
        result = await self.svc.update_user(1, "F", "D", 1, True, 2)
        self.assertFalse(result.available)

    async def test_update_user_returns_not_found_when_user_missing(self):
        self.mock_repo.get_user_by_id.return_value = None
        result = await self.svc.update_user(99, "F", "D", 1, True, 2)
        self.assertFalse(result.found)

    async def test_update_user_forbids_self_demotion(self):
        """Admin cannot remove their own is_administrator flag."""
        # row[6] = 1 (currently admin), is_administrator=False, user_id == requesting_user_id
        self.mock_repo.get_user_by_id.return_value = _USER_ROW  # id=1, is_admin=1
        result = await self.svc.update_user(
            user_id=1,
            full_name="F",
            display_name="D",
            account_status=1,
            is_administrator=False,
            requesting_user_id=1)
        self.assertTrue(result.forbidden)
        self.mock_repo.update_user.assert_not_called()

    async def test_update_user_allows_admin_to_demote_other_user(self):
        """Admin can remove another user's admin flag."""
        other_admin_row = (2, "b@c.com", "B", "B", 1, 0, 1)
        self.mock_repo.get_user_by_id.return_value = other_admin_row
        result = await self.svc.update_user(
            user_id=2,
            full_name="B",
            display_name="B",
            account_status=1,
            is_administrator=False,
            requesting_user_id=1)  # different user making the request
        self.assertFalse(result.forbidden)
        self.assertTrue(result.success)

    async def test_update_user_allows_self_update_without_demotion(self):
        """Admin updating own name/status without changing admin flag is fine."""
        self.mock_repo.get_user_by_id.return_value = _USER_ROW  # id=1, is_admin=1
        result = await self.svc.update_user(
            user_id=1,
            full_name="New Name",
            display_name="New Display",
            account_status=1,
            is_administrator=True,  # keeping the flag
            requesting_user_id=1)
        self.assertFalse(result.forbidden)
        self.assertTrue(result.success)

    async def test_update_user_returns_success(self):
        self.mock_repo.get_user_by_id.return_value = _USER_ROW
        result = await self.svc.update_user(1, "F", "D", 1, True, 2)
        self.assertTrue(result.success)
        self.mock_repo.update_user.assert_awaited_once()

    async def test_update_user_returns_unavailable_on_db_exception(self):
        self.mock_repo.get_user_by_id.side_effect = SqliteInterfaceException("err")
        result = await self.svc.update_user(1, "F", "D", 1, True, 2)
        self.assertFalse(result.available)
        self.mock_state.set_service_degraded.assert_called_once()

    # -------------------------------------------------------
    # reset_password tests
    # -------------------------------------------------------

    async def test_reset_password_returns_unavailable_when_state_unavailable(self):
        self.mock_state.is_available.return_value = False
        result = await self.svc.reset_password(1, "newpass")
        self.assertFalse(result.available)

    async def test_reset_password_returns_not_found_when_user_missing(self):
        self.mock_repo.get_user_by_id.return_value = None
        result = await self.svc.reset_password(99, "newpass")
        self.assertFalse(result.found)

    async def test_reset_password_hashes_new_password(self):
        self.mock_repo.get_user_by_id.return_value = _USER_ROW
        await self.svc.reset_password(1, "plaintext")
        stored_hash = self.mock_repo.update_password.call_args[0][1]
        self.assertTrue(stored_hash.startswith("$argon2"))

    async def test_reset_password_returns_success(self):
        self.mock_repo.get_user_by_id.return_value = _USER_ROW
        result = await self.svc.reset_password(1, "newpass")
        self.assertTrue(result.success)

    async def test_reset_password_returns_unavailable_on_db_exception(self):
        self.mock_repo.get_user_by_id.side_effect = SqliteInterfaceException("err")
        result = await self.svc.reset_password(1, "newpass")
        self.assertFalse(result.available)
        self.mock_state.set_service_degraded.assert_called_once()

    # -------------------------------------------------------
    # change_own_password tests
    # -------------------------------------------------------

    async def test_change_own_password_returns_unavailable_when_state_unavailable(self):
        self.mock_state.is_available.return_value = False
        result = await self.svc.change_own_password(1, "old", "new")
        self.assertFalse(result.available)

    async def test_change_own_password_returns_not_found_when_user_missing(self):
        self.mock_repo.get_user_by_id.return_value = None
        result = await self.svc.change_own_password(99, "old", "new")
        self.assertFalse(result.found)

    async def test_change_own_password_returns_unavailable_when_no_hash_record(self):
        self.mock_repo.get_user_by_id.return_value = _USER_ROW
        self.mock_repo.get_password_hash.return_value = None
        result = await self.svc.change_own_password(1, "old", "new")
        self.assertFalse(result.available)

    async def test_change_own_password_returns_wrong_password_on_mismatch(self):
        self.mock_repo.get_user_by_id.return_value = _USER_ROW
        self.mock_repo.get_password_hash.return_value = "$argon2id$hash"
        with patch.object(PasswordHasher, "verify",
                          side_effect=VerifyMismatchError()):
            result = await self.svc.change_own_password(1, "wrongpass", "new")
        self.assertTrue(result.wrong_password)
        self.mock_repo.update_password.assert_not_called()

    async def test_change_own_password_returns_unavailable_on_verification_error(self):
        self.mock_repo.get_user_by_id.return_value = _USER_ROW
        self.mock_repo.get_password_hash.return_value = "$argon2id$hash"
        with patch.object(PasswordHasher, "verify",
                          side_effect=VerificationError()):
            result = await self.svc.change_own_password(1, "old", "new")
        self.assertFalse(result.available)

    async def test_change_own_password_returns_unavailable_on_invalid_hash_error(self):
        self.mock_repo.get_user_by_id.return_value = _USER_ROW
        self.mock_repo.get_password_hash.return_value = "not-a-hash"
        with patch.object(PasswordHasher, "verify",
                          side_effect=InvalidHashError()):
            result = await self.svc.change_own_password(1, "old", "new")
        self.assertFalse(result.available)

    async def test_change_own_password_updates_with_new_hash(self):
        self.mock_repo.get_user_by_id.return_value = _USER_ROW
        self.mock_repo.get_password_hash.return_value = "$argon2id$hash"
        with patch.object(PasswordHasher, "verify", return_value=True):
            result = await self.svc.change_own_password(1, "old", "newpass")
        self.assertTrue(result.success)
        stored_hash = self.mock_repo.update_password.call_args[0][1]
        self.assertTrue(stored_hash.startswith("$argon2"))

    async def test_change_own_password_returns_unavailable_on_db_exception(self):
        self.mock_repo.get_user_by_id.side_effect = SqliteInterfaceException("err")
        result = await self.svc.change_own_password(1, "old", "new")
        self.assertFalse(result.available)
        self.mock_state.set_service_degraded.assert_called_once()
