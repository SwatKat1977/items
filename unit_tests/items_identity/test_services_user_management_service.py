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

_UUID = "550e8400-e29b-41d4-a716-446655440000"
_UUID2 = "660e8400-e29b-41d4-a716-446655440000"

# Row tuple: (id, uuid, email_address, full_name, display_name,
#             account_status, logon_type, is_administrator)
_USER_ROW = (1, _UUID, "a@b.com", "Full Name", "Display", 1, 0, 1)
_USER_DICT = {
    "id": _UUID,        # public id is the UUID string
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
        self.mock_repo.get_user_by_uuid = AsyncMock()
        self.mock_repo.email_exists = AsyncMock()
        self.mock_repo.create_user = AsyncMock()
        self.mock_repo.create_user_auth = AsyncMock()
        self.mock_repo.update_user = AsyncMock()
        self.mock_repo.update_password = AsyncMock()
        self.mock_repo.get_password_hash = AsyncMock()
        self.mock_repo.count_active_administrators = AsyncMock(return_value=2)

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

    async def test_get_all_users_returns_users_with_uuid_as_id(self):
        self.mock_repo.get_all_users.return_value = [_USER_ROW]
        result = await self.svc.get_all_users()
        self.assertEqual(len(result.users), 1)
        self.assertEqual(result.users[0]["id"], _UUID)

    async def test_get_all_users_returns_users_with_is_administrator_as_bool(self):
        self.mock_repo.get_all_users.return_value = [_USER_ROW]
        result = await self.svc.get_all_users()
        self.assertIs(type(result.users[0]["is_administrator"]), bool)
        self.assertTrue(result.users[0]["is_administrator"])

    async def test_get_all_users_returns_unavailable_on_db_exception(self):
        self.mock_repo.get_all_users.side_effect = SqliteInterfaceException("err")
        result = await self.svc.get_all_users()
        self.assertFalse(result.available)
        self.mock_state.set_service_degraded.assert_called_once()

    # -------------------------------------------------------
    # get_user_by_uuid tests
    # -------------------------------------------------------

    async def test_get_user_by_uuid_returns_unavailable_when_state_unavailable(self):
        self.mock_state.is_available.return_value = False
        result = await self.svc.get_user_by_uuid(_UUID)
        self.assertFalse(result.available)

    async def test_get_user_by_uuid_returns_not_found_when_none(self):
        self.mock_repo.get_user_by_uuid.return_value = None
        result = await self.svc.get_user_by_uuid(_UUID)
        self.assertTrue(result.available)
        self.assertFalse(result.found)

    async def test_get_user_by_uuid_returns_user_dict(self):
        self.mock_repo.get_user_by_uuid.return_value = _USER_ROW
        result = await self.svc.get_user_by_uuid(_UUID)
        self.assertTrue(result.found)
        self.assertEqual(result.user, _USER_DICT)

    async def test_get_user_by_uuid_id_field_is_uuid_string(self):
        self.mock_repo.get_user_by_uuid.return_value = _USER_ROW
        result = await self.svc.get_user_by_uuid(_UUID)
        self.assertIsInstance(result.user["id"], str)
        self.assertEqual(result.user["id"], _UUID)

    async def test_get_user_by_uuid_converts_is_administrator_to_bool(self):
        row_non_admin = (2, _UUID2, "b@c.com", "B", "B", 1, 0, 0)
        self.mock_repo.get_user_by_uuid.return_value = row_non_admin
        result = await self.svc.get_user_by_uuid(_UUID2)
        self.assertIs(type(result.user["is_administrator"]), bool)
        self.assertFalse(result.user["is_administrator"])

    async def test_get_user_by_uuid_returns_unavailable_on_db_exception(self):
        self.mock_repo.get_user_by_uuid.side_effect = SqliteInterfaceException("err")
        result = await self.svc.get_user_by_uuid(_UUID)
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

    async def test_create_user_returns_uuid_on_success(self):
        self.mock_repo.email_exists.return_value = False
        self.mock_repo.create_user.return_value = 7
        result = await self.svc.create_user(
            "new@b.com", "Full", "Display", "password", False)
        self.assertFalse(result.conflict)
        self.assertIsNotNone(result.user_uuid)
        # UUID should look like a UUID
        self.assertEqual(len(result.user_uuid), 36)

    async def test_create_user_passes_uuid_to_repository(self):
        self.mock_repo.email_exists.return_value = False
        self.mock_repo.create_user.return_value = 7
        await self.svc.create_user("new@b.com", "Full", "Display", "pw", False)
        call_kwargs = self.mock_repo.create_user.call_args[1]
        self.assertIn("user_uuid", call_kwargs)
        self.assertEqual(len(call_kwargs["user_uuid"]), 36)

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

    async def test_create_user_generates_password_when_none_supplied(self):
        self.mock_repo.email_exists.return_value = False
        self.mock_repo.create_user.return_value = 3
        result = await self.svc.create_user("a@b.com", "F", "D", None, False)
        self.assertIsNotNone(result.generated_password)
        self.assertGreater(len(result.generated_password), 0)

    async def test_create_user_stores_hash_of_generated_password(self):
        self.mock_repo.email_exists.return_value = False
        self.mock_repo.create_user.return_value = 3
        result = await self.svc.create_user("a@b.com", "F", "D", None, False)
        stored_hash = self.mock_repo.create_user_auth.call_args[0][1]
        # The generated password must verify against the stored hash.
        from argon2 import PasswordHasher as _PH
        _PH().verify(stored_hash, result.generated_password)  # raises on mismatch

    async def test_create_user_no_generated_password_when_password_supplied(self):
        self.mock_repo.email_exists.return_value = False
        self.mock_repo.create_user.return_value = 3
        result = await self.svc.create_user("a@b.com", "F", "D", "mypass", False)
        self.assertIsNone(result.generated_password)

    # -------------------------------------------------------
    # update_user tests
    # -------------------------------------------------------

    async def test_update_user_returns_unavailable_when_state_unavailable(self):
        self.mock_state.is_available.return_value = False
        result = await self.svc.update_user(_UUID)
        self.assertFalse(result.available)

    async def test_update_user_returns_not_found_when_user_missing(self):
        self.mock_repo.get_user_by_uuid.return_value = None
        result = await self.svc.update_user(_UUID)
        self.assertFalse(result.found)

    async def test_update_user_forbids_removing_last_admin_flag(self):
        """Cannot remove admin flag if only one active admin remains."""
        self.mock_repo.get_user_by_uuid.return_value = _USER_ROW  # is_admin=1, status=1
        self.mock_repo.count_active_administrators.return_value = 1
        result = await self.svc.update_user(
            user_uuid=_UUID, is_administrator=False)
        self.assertTrue(result.forbidden)
        self.mock_repo.update_user.assert_not_called()

    async def test_update_user_forbids_deactivating_last_admin(self):
        """Cannot deactivate an account if it is the only active admin."""
        self.mock_repo.get_user_by_uuid.return_value = _USER_ROW  # is_admin=1, status=1
        self.mock_repo.count_active_administrators.return_value = 1
        result = await self.svc.update_user(
            user_uuid=_UUID, account_status=0)
        self.assertTrue(result.forbidden)
        self.mock_repo.update_user.assert_not_called()

    async def test_update_user_allows_removing_admin_flag_when_others_exist(self):
        """Admin flag may be removed when other active admins exist."""
        self.mock_repo.get_user_by_uuid.return_value = _USER_ROW
        self.mock_repo.count_active_administrators.return_value = 2
        result = await self.svc.update_user(user_uuid=_UUID, is_administrator=False)
        self.assertFalse(result.forbidden)
        self.assertTrue(result.success)

    async def test_update_user_skips_last_admin_check_for_non_admin(self):
        """No guard check when the target user is not currently an admin."""
        non_admin_row = (2, _UUID2, "b@c.com", "B", "B", 1, 0, 0)  # is_admin=0
        self.mock_repo.get_user_by_uuid.return_value = non_admin_row
        result = await self.svc.update_user(user_uuid=_UUID2, is_administrator=False)
        self.mock_repo.count_active_administrators.assert_not_called()
        self.assertTrue(result.success)

    async def test_update_user_merges_supplied_fields_over_current(self):
        """Only the supplied field is updated; others keep their current values."""
        self.mock_repo.get_user_by_uuid.return_value = _USER_ROW
        # Supply only full_name; rest should come from _USER_ROW.
        await self.svc.update_user(user_uuid=_UUID, full_name="Changed")
        call_args = self.mock_repo.update_user.call_args[0]
        # (user_id, full_name, display_name, account_status, is_administrator)
        self.assertEqual(call_args[1], "Changed")
        self.assertEqual(call_args[2], "Display")   # unchanged
        self.assertEqual(call_args[3], 1)            # unchanged
        self.assertTrue(call_args[4])                # unchanged

    async def test_update_user_returns_success(self):
        self.mock_repo.get_user_by_uuid.return_value = _USER_ROW
        result = await self.svc.update_user(_UUID, full_name="F")
        self.assertTrue(result.success)
        self.mock_repo.update_user.assert_awaited_once()

    async def test_update_user_returns_unavailable_on_db_exception(self):
        self.mock_repo.get_user_by_uuid.side_effect = SqliteInterfaceException("err")
        result = await self.svc.update_user(_UUID)
        self.assertFalse(result.available)
        self.mock_state.set_service_degraded.assert_called_once()

    # -------------------------------------------------------
    # reset_password tests
    # -------------------------------------------------------

    async def test_reset_password_returns_unavailable_when_state_unavailable(self):
        self.mock_state.is_available.return_value = False
        result = await self.svc.reset_password(_UUID, "newpass")
        self.assertFalse(result.available)

    async def test_reset_password_returns_not_found_when_user_missing(self):
        self.mock_repo.get_user_by_uuid.return_value = None
        result = await self.svc.reset_password(_UUID, "newpass")
        self.assertFalse(result.found)

    async def test_reset_password_hashes_new_password(self):
        self.mock_repo.get_user_by_uuid.return_value = _USER_ROW
        await self.svc.reset_password(_UUID, "plaintext")
        stored_hash = self.mock_repo.update_password.call_args[0][1]
        self.assertTrue(stored_hash.startswith("$argon2"))

    async def test_reset_password_uses_internal_id_for_update(self):
        """update_password should receive the integer PK, not the UUID."""
        self.mock_repo.get_user_by_uuid.return_value = _USER_ROW  # id=1 at index 0
        await self.svc.reset_password(_UUID, "newpass")
        internal_id = self.mock_repo.update_password.call_args[0][0]
        self.assertEqual(internal_id, 1)

    async def test_reset_password_returns_success(self):
        self.mock_repo.get_user_by_uuid.return_value = _USER_ROW
        result = await self.svc.reset_password(_UUID, "newpass")
        self.assertTrue(result.success)

    async def test_reset_password_returns_unavailable_on_db_exception(self):
        self.mock_repo.get_user_by_uuid.side_effect = SqliteInterfaceException("err")
        result = await self.svc.reset_password(_UUID, "newpass")
        self.assertFalse(result.available)
        self.mock_state.set_service_degraded.assert_called_once()

    # -------------------------------------------------------
    # change_own_password tests
    # -------------------------------------------------------

    async def test_change_own_password_returns_unavailable_when_state_unavailable(self):
        self.mock_state.is_available.return_value = False
        result = await self.svc.change_own_password(_UUID, "old", "new")
        self.assertFalse(result.available)

    async def test_change_own_password_returns_not_found_when_user_missing(self):
        self.mock_repo.get_user_by_uuid.return_value = None
        result = await self.svc.change_own_password(_UUID, "old", "new")
        self.assertFalse(result.found)

    async def test_change_own_password_returns_unavailable_when_no_hash_record(self):
        self.mock_repo.get_user_by_uuid.return_value = _USER_ROW
        self.mock_repo.get_password_hash.return_value = None
        result = await self.svc.change_own_password(_UUID, "old", "new")
        self.assertFalse(result.available)

    async def test_change_own_password_returns_wrong_password_on_mismatch(self):
        self.mock_repo.get_user_by_uuid.return_value = _USER_ROW
        self.mock_repo.get_password_hash.return_value = "$argon2id$hash"
        with patch.object(PasswordHasher, "verify",
                          side_effect=VerifyMismatchError()):
            result = await self.svc.change_own_password(_UUID, "wrongpass", "new")
        self.assertTrue(result.wrong_password)
        self.mock_repo.update_password.assert_not_called()

    async def test_change_own_password_returns_unavailable_on_verification_error(self):
        self.mock_repo.get_user_by_uuid.return_value = _USER_ROW
        self.mock_repo.get_password_hash.return_value = "$argon2id$hash"
        with patch.object(PasswordHasher, "verify",
                          side_effect=VerificationError()):
            result = await self.svc.change_own_password(_UUID, "old", "new")
        self.assertFalse(result.available)

    async def test_change_own_password_returns_unavailable_on_invalid_hash_error(self):
        self.mock_repo.get_user_by_uuid.return_value = _USER_ROW
        self.mock_repo.get_password_hash.return_value = "not-a-hash"
        with patch.object(PasswordHasher, "verify",
                          side_effect=InvalidHashError()):
            result = await self.svc.change_own_password(_UUID, "old", "new")
        self.assertFalse(result.available)

    async def test_change_own_password_updates_with_new_hash(self):
        self.mock_repo.get_user_by_uuid.return_value = _USER_ROW
        self.mock_repo.get_password_hash.return_value = "$argon2id$hash"
        with patch.object(PasswordHasher, "verify", return_value=True):
            result = await self.svc.change_own_password(_UUID, "old", "newpass")
        self.assertTrue(result.success)
        stored_hash = self.mock_repo.update_password.call_args[0][1]
        self.assertTrue(stored_hash.startswith("$argon2"))

    async def test_change_own_password_uses_internal_id_for_hash_lookup(self):
        """get_password_hash should receive the integer PK, not the UUID."""
        self.mock_repo.get_user_by_uuid.return_value = _USER_ROW  # id=1 at index 0
        self.mock_repo.get_password_hash.return_value = "$argon2id$hash"
        with patch.object(PasswordHasher, "verify", return_value=True):
            await self.svc.change_own_password(_UUID, "old", "newpass")
        internal_id = self.mock_repo.get_password_hash.call_args[0][0]
        self.assertEqual(internal_id, 1)

    async def test_change_own_password_returns_unavailable_on_db_exception(self):
        self.mock_repo.get_user_by_uuid.side_effect = SqliteInterfaceException("err")
        result = await self.svc.change_own_password(_UUID, "old", "new")
        self.assertFalse(result.available)
        self.mock_state.set_service_degraded.assert_called_once()
