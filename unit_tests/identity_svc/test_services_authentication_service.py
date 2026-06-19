import unittest
import logging
from unittest.mock import MagicMock, AsyncMock, patch
from weaver_framework.database.sqlite_interface import SqliteInterfaceException
from services.authentication_service import AuthenticationService


class TestAuthenticationService(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.mock_logger = MagicMock(spec=logging.Logger)
        self.mock_child_logger = MagicMock(spec=logging.Logger)
        self.mock_logger.getChild.return_value = self.mock_child_logger

        self.mock_user_repository = MagicMock()
        self.mock_user_repository.get_user_by_email = AsyncMock()
        self.mock_user_repository.get_password_hash = AsyncMock()

        self.mock_state = MagicMock()
        self.mock_state.is_available.return_value = True

        self.auth_service = AuthenticationService(
            self.mock_logger, self.mock_state, self.mock_user_repository)

    async def test_authenticate_service_unavailable(self):
        self.mock_state.is_available.return_value = False
        success, message = await self.auth_service.authenticate_password(
            "a@b.com", "pass")
        self.assertFalse(success)
        self.assertEqual(message, "Authentication service unavailable")

    async def test_authenticate_db_error_on_user_lookup(self):
        self.mock_user_repository.get_user_by_email.side_effect = \
            SqliteInterfaceException("db error")
        success, message = await self.auth_service.authenticate_password(
            "a@b.com", "pass")
        self.assertFalse(success)
        self.assertEqual(message, "Internal authentication error")
        self.mock_child_logger.exception.assert_called_once()

    async def test_authenticate_user_not_found(self):
        self.mock_user_repository.get_user_by_email.return_value = None
        success, message = await self.auth_service.authenticate_password(
            "no@user.com", "pass")
        self.assertFalse(success)
        self.assertEqual(message, "Username/password don't match")

    async def test_authenticate_wrong_logon_type(self):
        # logon_type=1 does not match LogonType.PASSWORD.value (0)
        self.mock_user_repository.get_user_by_email.return_value = (42, 1, 1)
        success, message = await self.auth_service.authenticate_password(
            "a@b.com", "pass")
        self.assertFalse(success)
        self.assertEqual(message, "Username/password don't match")

    async def test_authenticate_inactive_account(self):
        # logon_type=0 (PASSWORD), account_status=0 (DISABLED)
        self.mock_user_repository.get_user_by_email.return_value = (42, 0, 0)
        success, message = await self.auth_service.authenticate_password(
            "a@b.com", "pass")
        self.assertFalse(success)
        self.assertEqual(message, "Account is not active")

    async def test_authenticate_db_error_on_password_lookup(self):
        self.mock_user_repository.get_user_by_email.return_value = (42, 0, 1)
        self.mock_user_repository.get_password_hash.side_effect = \
            SqliteInterfaceException("db error")
        success, message = await self.auth_service.authenticate_password(
            "a@b.com", "pass")
        self.assertFalse(success)
        self.assertEqual(message, "Internal authentication error")
        self.mock_child_logger.exception.assert_called()

    async def test_authenticate_no_password_record(self):
        self.mock_user_repository.get_user_by_email.return_value = (42, 0, 1)
        self.mock_user_repository.get_password_hash.return_value = None
        success, message = await self.auth_service.authenticate_password(
            "a@b.com", "pass")
        self.assertFalse(success)
        self.assertEqual(message, "Internal authentication error")
        self.mock_child_logger.error.assert_called_once()

    @patch("services.authentication_service.bcrypt.checkpw", return_value=True)
    async def test_authenticate_success(self, mock_checkpw):
        # logon_type=0 (PASSWORD), account_status=1 (ACTIVE)
        self.mock_user_repository.get_user_by_email.return_value = (42, 0, 1)
        self.mock_user_repository.get_password_hash.return_value = b"$2b$12$hash"
        success, message = await self.auth_service.authenticate_password(
            "user@example.com", "password")
        self.assertTrue(success)
        self.assertEqual(message, "Authentication successful")
        mock_checkpw.assert_called_once()

    @patch("services.authentication_service.bcrypt.checkpw", return_value=False)
    async def test_authenticate_wrong_password(self, mock_checkpw):
        # logon_type=0 (PASSWORD), account_status=1 (ACTIVE)
        self.mock_user_repository.get_user_by_email.return_value = (42, 0, 1)
        self.mock_user_repository.get_password_hash.return_value = b"$2b$12$hash"
        success, message = await self.auth_service.authenticate_password(
            "user@example.com", "badpass")
        self.assertFalse(success)
        self.assertEqual(message, "Username/password don't match")
        mock_checkpw.assert_called_once()
