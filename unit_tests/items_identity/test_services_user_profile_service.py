import unittest
from unittest.mock import MagicMock, AsyncMock
import logging
from weaver_framework.database.sqlite_interface import SqliteInterfaceException
from services.user_profile_service import UserProfileService

_ADMIN_UUID = "550e8400-e29b-41d4-a716-446655440000"
_NON_ADMIN_UUID = "660e8400-e29b-41d4-a716-446655440000"

# A full profile row as returned by
# UserRepository.get_user_profile_by_email():
#   (id, uuid, email, full_name, display_name, account_status, logon_type,
#    is_administrator)
ADMIN_ROW = (1, _ADMIN_UUID, "admin@localhost", "Local Admin", "Local Admin",
             1, 0, 1)
NON_ADMIN_ROW = (7, _NON_ADMIN_UUID, "gemma@localhost", "Gemma", "Gemma",
                 1, 0, 0)


class TestUserProfileService(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.mock_logger = MagicMock(spec=logging.Logger)
        self.mock_logger.getChild.return_value = MagicMock(spec=logging.Logger)
        self.mock_state = MagicMock()
        self.mock_state.is_available.return_value = True
        self.mock_repository = MagicMock()
        self.mock_repository.get_user_profile_by_email = AsyncMock()

        self.service = UserProfileService(self.mock_logger,
                                          self.mock_state,
                                          self.mock_repository)

    async def test_unavailable_when_service_not_available(self):
        self.mock_state.is_available.return_value = False

        result = await self.service.get_profile_by_email("admin@localhost")

        self.assertFalse(result.available)
        self.assertIsNone(result.profile)
        self.mock_repository.get_user_profile_by_email.assert_not_called()

    async def test_not_found_when_no_such_user(self):
        self.mock_repository.get_user_profile_by_email.return_value = None

        result = await self.service.get_profile_by_email("nobody@localhost")

        self.assertTrue(result.available)
        self.assertFalse(result.found)
        self.assertIsNone(result.profile)

    async def test_database_failure_reports_unavailable_not_not_found(self):
        """A DB outage must not be reported as a missing account."""
        self.mock_repository.get_user_profile_by_email.side_effect = \
            SqliteInterfaceException("boom")

        result = await self.service.get_profile_by_email("admin@localhost")

        self.assertFalse(result.available)
        # 'found' stays True so callers keying off it cannot mistake an
        # outage for a deleted user.
        self.assertTrue(result.found)
        self.assertIsNone(result.profile)
        self.mock_state.set_service_degraded.assert_called_once()

    async def test_administrator_profile_returned(self):
        self.mock_repository.get_user_profile_by_email.return_value = ADMIN_ROW

        result = await self.service.get_profile_by_email("admin@localhost")

        self.assertTrue(result.available)
        self.assertTrue(result.found)
        self.assertEqual(result.profile, {
            "id": _ADMIN_UUID,
            "email_address": "admin@localhost",
            "full_name": "Local Admin",
            "display_name": "Local Admin",
            "account_status": 1,
            "logon_type": 0,
            "is_administrator": True,
        })

    async def test_non_administrator_flag_is_false(self):
        self.mock_repository.get_user_profile_by_email.return_value = \
            NON_ADMIN_ROW

        result = await self.service.get_profile_by_email("gemma@localhost")

        self.assertFalse(result.profile["is_administrator"])

    async def test_is_administrator_is_a_bool_not_an_int(self):
        """Callers should not have to know the 0/1 storage representation."""
        self.mock_repository.get_user_profile_by_email.return_value = ADMIN_ROW

        result = await self.service.get_profile_by_email("admin@localhost")

        self.assertIsInstance(result.profile["is_administrator"], bool)

    async def test_email_is_passed_through_to_repository(self):
        self.mock_repository.get_user_profile_by_email.return_value = None

        await self.service.get_profile_by_email("someone@example.com")

        self.mock_repository.get_user_profile_by_email.assert_called_once_with(
            "someone@example.com")
