import unittest
from unittest.mock import MagicMock, AsyncMock, patch
import logging
from weaver_framework.database.sqlite_interface import SqliteInterfaceException
from services.user_management_service import (
    UserManagementService, generate_password)

# A user row as returned by the repository:
#   (id, email, full_name, display_name, insertion_date, account_status,
#    logon_type, is_administrator)
ACTIVE_ADMIN = (1, "admin@localhost", "Local Admin", "Local Admin",
                1700000000, 1, 0, 1)
ACTIVE_USER = (2, "gemma@localhost", "Gemma", "Gemma", 1700000001, 1, 0, 0)
DISABLED_ADMIN = (3, "old@localhost", "Old", "Old", 1700000002, 0, 0, 1)


class TestUserManagementService(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.mock_logger = MagicMock(spec=logging.Logger)
        self.mock_logger.getChild.return_value = MagicMock(spec=logging.Logger)
        self.mock_state = MagicMock()
        self.mock_state.is_available.return_value = True

        self.repo = MagicMock()
        self.repo.list_users = AsyncMock(return_value=[ACTIVE_ADMIN])
        self.repo.get_user_by_id = AsyncMock(return_value=ACTIVE_USER)
        self.repo.email_address_exists = AsyncMock(return_value=False)
        self.repo.count_active_administrators = AsyncMock(return_value=2)
        self.repo.create_user = AsyncMock(return_value=2)
        self.repo.update_user = AsyncMock()
        self.repo.update_password_hash = AsyncMock()

        self.service = UserManagementService(self.mock_logger,
                                             self.mock_state,
                                             self.repo)

    # ------------------------------------------------------------------
    # Availability
    # ------------------------------------------------------------------

    async def test_all_operations_unavailable_when_service_down(self):
        self.mock_state.is_available.return_value = False

        for label, coro in (
                ("list", self.service.list_users()),
                ("get", self.service.get_user(1)),
                ("create", self.service.create_user("a@b.com", "A", "A")),
                ("update", self.service.update_user(1, full_name="X")),
                ("password", self.service.set_password(1, "secret123")),
        ):
            with self.subTest(operation=label):
                result = await coro
                self.assertFalse(result.available)
                self.assertFalse(result.success)

    async def test_database_failure_is_unavailable_not_not_found(self):
        """An outage must never be reported as a missing account."""
        self.repo.list_users.side_effect = SqliteInterfaceException("boom")

        result = await self.service.list_users()

        self.assertFalse(result.available)
        self.assertTrue(result.found)
        self.mock_state.set_service_degraded.assert_called_once()

    # ------------------------------------------------------------------
    # Reads
    # ------------------------------------------------------------------

    async def test_list_users_maps_rows(self):
        result = await self.service.list_users()

        self.assertTrue(result.success)
        self.assertEqual(len(result.users), 1)
        self.assertEqual(result.users[0]["email_address"], "admin@localhost")
        self.assertIs(result.users[0]["is_administrator"], True)

    async def test_get_user_not_found(self):
        self.repo.get_user_by_id.return_value = None

        result = await self.service.get_user(99)

        self.assertTrue(result.available)
        self.assertFalse(result.found)

    async def test_is_administrator_is_bool_not_int(self):
        result = await self.service.get_user(2)
        self.assertIsInstance(result.user["is_administrator"], bool)

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    async def test_create_rejects_duplicate_email_as_conflict(self):
        """A duplicate must be a conflict, not a database exception."""
        self.repo.email_address_exists.return_value = True

        result = await self.service.create_user("gemma@localhost", "G", "G")

        self.assertIsNotNone(result.conflict)
        self.assertFalse(result.success)
        self.assertTrue(result.available)
        self.repo.create_user.assert_not_called()
        # Crucially, a duplicate must not degrade the service.
        self.mock_state.set_service_degraded.assert_not_called()

    async def test_create_generates_password_when_omitted(self):
        result = await self.service.create_user("a@b.com", "A", "A")

        self.assertIsNotNone(result.generated_password)
        self.assertGreaterEqual(len(result.generated_password), 12)

    async def test_create_does_not_generate_when_password_supplied(self):
        result = await self.service.create_user("a@b.com", "A", "A",
                                                password="supplied-secret")

        self.assertIsNone(result.generated_password)

    async def test_create_stores_a_hash_not_the_plaintext(self):
        await self.service.create_user("a@b.com", "A", "A",
                                       password="plaintext-secret")

        stored = self.repo.create_user.call_args.kwargs["password_hash"]
        self.assertNotIn("plaintext-secret", stored)
        self.assertTrue(stored.startswith("$argon2"))

    async def test_create_defaults_to_non_administrator_and_enabled(self):
        await self.service.create_user("a@b.com", "A", "A")

        kwargs = self.repo.create_user.call_args.kwargs
        self.assertFalse(kwargs["is_administrator"])
        self.assertEqual(kwargs["account_status"], 1)

    async def test_create_can_be_disabled_at_creation(self):
        await self.service.create_user("a@b.com", "A", "A", enabled=False)

        self.assertEqual(
            self.repo.create_user.call_args.kwargs["account_status"], 0)

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    async def test_update_only_changes_supplied_fields(self):
        await self.service.update_user(2, full_name="New Name")

        kwargs = self.repo.update_user.call_args.kwargs
        self.assertEqual(kwargs["full_name"], "New Name")
        self.assertEqual(kwargs["display_name"], "Gemma")
        self.assertEqual(kwargs["email"], "gemma@localhost")

    async def test_update_not_found(self):
        self.repo.get_user_by_id.return_value = None

        result = await self.service.update_user(99, full_name="X")

        self.assertFalse(result.found)
        self.repo.update_user.assert_not_called()

    async def test_update_rejects_duplicate_email(self):
        self.repo.email_address_exists.return_value = True

        result = await self.service.update_user(2,
                                                email="admin@localhost")

        self.assertIsNotNone(result.conflict)
        self.repo.update_user.assert_not_called()

    async def test_update_keeping_own_email_is_not_a_conflict(self):
        """exclude_id must stop a user's own address conflicting with itself."""
        await self.service.update_user(2, email="gemma@localhost")

        self.repo.email_address_exists.assert_awaited_with("gemma@localhost", 2)
        self.repo.update_user.assert_called_once()

    async def test_update_does_not_check_email_when_not_changing_it(self):
        await self.service.update_user(2, full_name="Only Name")

        self.repo.email_address_exists.assert_not_called()

    # ------------------------------------------------------------------
    # Last-administrator guard
    # ------------------------------------------------------------------

    async def test_cannot_demote_the_last_active_administrator(self):
        self.repo.get_user_by_id.return_value = ACTIVE_ADMIN
        self.repo.count_active_administrators.return_value = 1

        result = await self.service.update_user(1, is_administrator=False)

        self.assertIsNotNone(result.conflict)
        self.assertIn("administrator", result.conflict)
        self.repo.update_user.assert_not_called()

    async def test_cannot_deactivate_the_last_active_administrator(self):
        self.repo.get_user_by_id.return_value = ACTIVE_ADMIN
        self.repo.count_active_administrators.return_value = 1

        result = await self.service.update_user(1, enabled=False)

        self.assertIsNotNone(result.conflict)
        self.repo.update_user.assert_not_called()

    async def test_can_demote_an_administrator_when_others_remain(self):
        self.repo.get_user_by_id.return_value = ACTIVE_ADMIN
        self.repo.count_active_administrators.return_value = 2

        result = await self.service.update_user(1, is_administrator=False)

        self.assertIsNone(result.conflict)
        self.repo.update_user.assert_called_once()

    async def test_guard_ignores_non_administrators(self):
        """A normal user can always be deactivated, whatever the admin count."""
        self.repo.get_user_by_id.return_value = ACTIVE_USER
        self.repo.count_active_administrators.return_value = 1

        result = await self.service.update_user(2, enabled=False)

        self.assertIsNone(result.conflict)
        self.repo.count_active_administrators.assert_not_called()

    async def test_guard_ignores_already_disabled_administrators(self):
        """An inactive admin isn't protecting anything, so it can be changed."""
        self.repo.get_user_by_id.return_value = DISABLED_ADMIN
        self.repo.count_active_administrators.return_value = 1

        result = await self.service.update_user(3, is_administrator=False)

        self.assertIsNone(result.conflict)

    async def test_renaming_the_last_administrator_is_allowed(self):
        """The guard must only trigger on losing admin rights or activity."""
        self.repo.get_user_by_id.return_value = ACTIVE_ADMIN
        self.repo.count_active_administrators.return_value = 1

        result = await self.service.update_user(1, full_name="Renamed")

        self.assertIsNone(result.conflict)
        self.repo.update_user.assert_called_once()

    # ------------------------------------------------------------------
    # Passwords
    # ------------------------------------------------------------------

    async def test_set_password_not_found(self):
        self.repo.get_user_by_id.return_value = None

        result = await self.service.set_password(99, "secret123")

        self.assertFalse(result.found)
        self.repo.update_password_hash.assert_not_called()

    async def test_set_password_stores_a_hash(self):
        await self.service.set_password(2, "plaintext-secret")

        _, stored = self.repo.update_password_hash.call_args.args
        self.assertNotIn("plaintext-secret", stored)
        self.assertTrue(stored.startswith("$argon2"))

    async def test_set_password_generates_when_omitted(self):
        result = await self.service.set_password(2)

        self.assertIsNotNone(result.generated_password)

    # ------------------------------------------------------------------
    # Password generation
    # ------------------------------------------------------------------

    async def test_generated_passwords_are_not_predictable(self):
        self.assertNotEqual(generate_password(), generate_password())

    async def test_generated_password_honours_length(self):
        self.assertEqual(len(generate_password(24)), 24)
