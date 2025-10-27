import unittest
from unittest.mock import MagicMock, patch
import logging
import bcrypt
from data_access.user_data_access_layer import UserDataAccessLayer
from items_common.service_state import ServiceState
from account_status import AccountStatus


class TestUserDataAccessLayer(unittest.TestCase):

    def setUp(self):
        # Prepare mock state and logger
        self.state = ServiceState()
        self.logger = logging.getLogger("test")

        # Patch configuration to prevent accessing real config
        config_patcher = patch("data_access.user_data_access_layer.Configuration")
        self.addCleanup(config_patcher.stop)
        mock_config_class = config_patcher.start()
        mock_config_instance = mock_config_class.return_value
        mock_config_instance.backend_db_filename = "test.db"

        # Create the mock DB first
        self.mock_db = MagicMock()

        # Then patch SafeSqliteInterface to return it
        db_patcher = patch("data_access.user_data_access_layer.SafeSqliteInterface", return_value=self.mock_db)

        self.addCleanup(db_patcher.stop)
        db_patcher.start()

        # Create the DAL (this will now use the mocked SafeSqliteInterface)
        self.dal = UserDataAccessLayer(self.state, self.logger)

    # -------------------------------------------------------
    # get_user_for_logon tests
    # -------------------------------------------------------
    def test_get_user_for_logon_returns_internal_error_if_row_none(self):
        self.mock_db.safe_query.return_value = None
        result = self.dal.get_user_for_logon("a@b.com", 1)
        self.assertEqual(result, (None, "Internal error"))

    def test_get_user_for_logon_returns_match_error_if_empty(self):
        self.mock_db.safe_query.return_value = ()
        result = self.dal.get_user_for_logon("a@b.com", 1)
        self.assertEqual(result, (0, "Username/password don't match"))

    def test_get_user_for_logon_incorrect_logon_type(self):
        # Simulate returned row
        self.mock_db.safe_query.return_value = (1, 2, AccountStatus.ACTIVE.value)
        result = self.dal.get_user_for_logon("a@b.com", 1)
        self.assertEqual(result, (0, "Incorrect logon type"))

    def test_get_user_for_logon_inactive_account(self):
        self.mock_db.safe_query.return_value = (
            1, 1, AccountStatus.DISABLED.value
        )
        result = self.dal.get_user_for_logon("a@b.com", 1)
        self.assertEqual(result, (0, "Account is not active"))

    def test_get_user_for_logon_valid_user(self):
        self.mock_db.safe_query.return_value = (
            42, 1, AccountStatus.ACTIVE.value
        )
        result = self.dal.get_user_for_logon("a@b.com", 1)
        self.assertEqual(result, (42, ""))

    # -------------------------------------------------------
    # authenticate_basic_user tests
    # -------------------------------------------------------

    def test_authenticate_basic_user_returns_internal_error_if_none(self):
        self.mock_db.safe_query.return_value = None
        ok, msg = self.dal.authenticate_basic_user(1, "pass")
        self.assertFalse(ok)
        self.assertEqual(msg, "Internal error")

    def test_authenticate_basic_user_returns_invalid_id_if_empty(self):
        self.mock_db.safe_query.return_value = ()
        ok, msg = self.dal.authenticate_basic_user(1, "pass")
        self.assertFalse(ok)
        self.assertEqual(msg, "Invalid user id")

    @patch("data_access.user_data_access_layer.bcrypt.checkpw", return_value=True)
    def test_authenticate_basic_user_success(self, mock_checkpw):
        hashed = bcrypt.hashpw(b"pass", bcrypt.gensalt())
        self.mock_db.safe_query.return_value = (hashed,)
        ok, msg = self.dal.authenticate_basic_user(1, "pass")
        self.assertTrue(ok)
        self.assertEqual(msg, "")
        mock_checkpw.assert_called_once()

    @patch("data_access.user_data_access_layer.bcrypt.checkpw", return_value=False)
    def test_authenticate_basic_user_password_mismatch(self, mock_checkpw):
        hashed = bcrypt.hashpw(b"something", bcrypt.gensalt())
        self.mock_db.safe_query.return_value = (hashed,)
        ok, msg = self.dal.authenticate_basic_user(1, "wrong")
        self.assertFalse(ok)
        self.assertEqual(msg, "Username/password don't match")
        mock_checkpw.assert_called_once()
