from hashlib import sha256
import unittest
from unittest.mock import MagicMock, Mock, patch
import logging
from account_status import AccountStatus
from sql.sqlite_interface import SqliteInterface
from state_object import StateObject
from threadsafe_configuration import ThreadSafeConfiguration


class TestSqliteInterface(unittest.TestCase):

    def setUp(self):
        self.mock_logger = MagicMock(spec=logging.Logger)
        self.mock_logger.getChild.return_value = self.mock_logger
        self.state_object = StateObject()

        # Patch ThreadSafeConfiguration.get_entry just for the test
        self.patcher = patch.object(
            ThreadSafeConfiguration,
            'get_entry',
            return_value=":memory:"
        )
        self.mock_get_entry = self.patcher.start()

    @patch("base_sqlite_interface.BaseSqliteInterface.__init__")
    def test_initialization(self, mock_base_init):
        """Test that SqliteInterface initializes correctly."""

        # Create an instance of SqliteInterface
        interface = SqliteInterface(logger=self.mock_logger,
                                    state_object=self.state_object)

        # Assert BaseSqliteInterface's __init__ was called with db_file
        mock_base_init.assert_called_once_with(":memory:")

        # Assert the logger was correctly set up as a child logger
        self.mock_logger.getChild.assert_called_once_with("sql.extended_sql_interface")
        self.assertEqual(interface._logger, self.mock_logger.getChild.return_value)

    def test_logger_usage(self):
        """Test that the logger in SqliteInterface is used correctly."""
        # Mock the logger
        mock_logger = MagicMock(spec=logging.Logger)
        mock_child_logger = mock_logger.getChild.return_value

        interface = SqliteInterface(logger=mock_logger,
                                    state_object=self.state_object)

        # Use the logger within the class (you'll replace this with actual usage in methods)
        interface._logger.info("Testing logger usage")

        # Assert the child logger logged the message
        mock_child_logger.info.assert_called_once_with("Testing logger usage")

    def test_valid_user_to_logon_success(self):
        # Create an instance of SqliteInterface
        interface = SqliteInterface(logger=self.mock_logger,
                                    state_object=self.state_object)

        # logon_type matches the argument (2)
        interface.safe_query = MagicMock(return_value=(1, 2, AccountStatus.ACTIVE.value))

        user_id, error_str = interface.valid_user_to_logon('test@example.com', 2)  # logon_type is 2

        self.assertEqual(user_id, 1)
        self.assertEqual(error_str, '')
        interface.safe_query.assert_called_once_with(
            "SELECT id, logon_type, account_status FROM user_profile WHERE email_address = ?",
            ('test@example.com',),
            'Query failed for basic user auth', 50, fetch_one=True)

    def test_valid_user_to_logon_incorrect_logon_type(self):
        # Create an instance of SqliteInterface
        interface = SqliteInterface(logger=self.mock_logger,
                                    state_object=self.state_object)

        # logon_type matches the argument (2)
        interface.safe_query = MagicMock(return_value=(1, 3, AccountStatus.ACTIVE))

        user_id, error_str = interface.valid_user_to_logon('test@example.com', 2)

        self.assertEqual(user_id, 0)
        self.assertEqual(error_str, 'Incorrect logon type')

    def test_valid_user_to_logon_account_not_active(self):
        # Create an instance of SqliteInterface
        interface = SqliteInterface(logger=self.mock_logger,
                                    state_object=self.state_object)

        # logon_type matches the argument (2)
        interface.safe_query = MagicMock(return_value=(1, 2, AccountStatus.DISABLED))

        user_id, error_str = interface.valid_user_to_logon('test@example.com', 2)

        self.assertEqual(user_id, 0)
        self.assertEqual(error_str, 'Account is not active')

    def test_valid_user_to_logon_unknown_email(self):
        # Create an instance of SqliteInterface
        interface = SqliteInterface(logger=self.mock_logger,
                                    state_object=self.state_object)

        # logon_type matches the argument (2)
        interface.safe_query = MagicMock(return_value=[])

        user_id, error_str = interface.valid_user_to_logon('unknown@example.com', 2)

        self.assertEqual(user_id, 0)
        self.assertEqual(error_str, "Username/password don't match")

    def test_valid_user_to_logon_query_failed(self):
        # Create SqliteInterface instance
        interface = SqliteInterface(logger=self.mock_logger,
                                    state_object=self.state_object)

        interface.safe_query = MagicMock(return_value=None)

        # Call the method
        user_id, error_str = interface.valid_user_to_logon('test@example.com', 2)

        # Assertions
        self.assertEqual(user_id, None)
        self.assertEqual(error_str, 'Internal error')

        interface.safe_query.assert_called_once_with(
            "SELECT id, logon_type, account_status FROM user_profile WHERE email_address = ?",
            ('test@example.com',),
            'Query failed for basic user auth', 50, fetch_one=True)

    def test_basic_user_authenticate_success(self):
        # Create an instance of SqliteInterface
        interface = SqliteInterface(logger=self.mock_logger,
                                    state_object=self.state_object)

        interface.safe_query = MagicMock(return_value=(sha256("passwordsalt".encode('UTF-8')).hexdigest(), "salt"))

        status, error_str = interface.basic_user_authenticate(1, "password")

        self.assertTrue(status)
        self.assertEqual(error_str, '')
        interface.safe_query.assert_called_once_with(
            "SELECT password, password_salt FROM user_auth_details WHERE user_id = ?",
            (1,), 'Query failed for basic user auth', 50, fetch_one=True)

    def test_basic_user_authenticate_invalid_user_id(self):
        # Create an instance of SqliteInterface
        interface = SqliteInterface(logger=self.mock_logger,
                                    state_object=self.state_object)

        interface.safe_query = MagicMock(return_value=[])

        status, error_str = interface.basic_user_authenticate(99, "password")

        self.assertFalse(status)
        self.assertEqual(error_str, 'Invalid user id')
        interface.safe_query.assert_called_once_with(
            "SELECT password, password_salt FROM user_auth_details WHERE user_id = ?",
            (99,), 'Query failed for basic user auth', 50, fetch_one=True)

    def test_basic_user_authenticate_incorrect_password(self):
        # Create an instance of SqliteInterface
        interface = SqliteInterface(logger=self.mock_logger,
                                    state_object=self.state_object)

        interface.safe_query = MagicMock(return_value=(sha256("wrongpasswordsalt".encode('UTF-8')).hexdigest(), "salt"))

        status, error_str = interface.basic_user_authenticate(1, "password")

        self.assertFalse(status)
        self.assertEqual(error_str, "Username/password don't match")

    def test_basic_user_authenticate_query_exception(self):
        # Create an instance of SqliteInterface
        interface = SqliteInterface(logger=self.mock_logger,
                                    state_object=self.state_object)

        interface.safe_query = MagicMock(return_value=None)

        status, error_str = interface.basic_user_authenticate(1, "password")

        self.assertFalse(status)
        self.assertEqual(error_str, 'Internal error')
