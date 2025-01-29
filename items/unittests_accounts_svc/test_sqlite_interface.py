from hashlib import sha256
import unittest
from unittest.mock import MagicMock, Mock, patch
import logging
from account_status import AccountStatus
from sqlite_interface import SqliteInterface
from base_sqlite_interface import SqliteInterfaceException

class TestSqliteInterface(unittest.TestCase):

    def setUp(self):
        self.mock_logger = MagicMock(spec=logging.Logger)
        self.db_file = 'test.db'
        self.mock_logger.getChild.return_value = self.mock_logger  # getChild should return itself

    @patch("base_sqlite_interface.BaseSqliteInterface.__init__")
    def test_initialization(self, mock_base_init):
        """Test that SqliteInterface initializes correctly."""

        # Create an instance of SqliteInterface
        interface = SqliteInterface(logger=self.mock_logger, db_file=self.db_file)

        # Assert BaseSqliteInterface's __init__ was called with db_file
        mock_base_init.assert_called_once_with(self.db_file)

        # Assert the logger was correctly set up as a child logger
        self.mock_logger.getChild.assert_called_once_with("sqlite_interface")
        self.assertEqual(interface._logger, self.mock_logger.getChild.return_value)

    def test_logger_usage(self):
        """Test that the logger in SqliteInterface is used correctly."""
        # Mock the logger
        mock_logger = MagicMock(spec=logging.Logger)
        mock_child_logger = mock_logger.getChild.return_value

        # Create an instance of SqliteInterface
        db_file = "test.db"
        instance = SqliteInterface(logger=mock_logger, db_file=db_file)

        # Use the logger within the class (you'll replace this with actual usage in methods)
        instance._logger.info("Testing logger usage")

        # Assert the child logger logged the message
        mock_child_logger.info.assert_called_once_with("Testing logger usage")

    @patch.object(SqliteInterface, 'query_with_values')
    def test_valid_user_to_logon_success(self, mock_query):
        # Mock query results
        mock_query.return_value = [(1, 2, AccountStatus.ACTIVE.value)]  # logon_type matches the argument (2)

        # Create an instance of SqliteInterface
        interface = SqliteInterface(logger=self.mock_logger, db_file=self.db_file)

        user_id, error_str = interface.valid_user_to_logon('test@example.com', 2)  # logon_type is 2

        self.assertEqual(user_id, 1)
        self.assertEqual(error_str, '')
        mock_query.assert_called_once_with(
            "SELECT id, logon_type, account_status FROM user_profile WHERE email_address = ?",
            ('test@example.com',)
        )

    @patch.object(SqliteInterface, 'query_with_values')
    def test_valid_user_to_logon_incorrect_logon_type(self, mock_query):
        mock_query.return_value = [(1, 3, AccountStatus.ACTIVE)]

        # Create an instance of SqliteInterface
        interface = SqliteInterface(logger=self.mock_logger, db_file=self.db_file)

        user_id, error_str = interface.valid_user_to_logon('test@example.com', 2)

        self.assertEqual(user_id, 0)
        self.assertEqual(error_str, 'Incorrect logon type')

    @patch.object(SqliteInterface, 'query_with_values')
    def test_valid_user_to_logon_account_not_active(self, mock_query):
        mock_query.return_value = [(1, 2, AccountStatus.DISABLED.value)]

        # Create an instance of SqliteInterface
        interface = SqliteInterface(logger=self.mock_logger, db_file=self.db_file)

        user_id, error_str = interface.valid_user_to_logon('test@example.com', 2)

        self.assertEqual(user_id, 0)
        self.assertEqual(error_str, 'Account not active')

    @patch.object(SqliteInterface, 'query_with_values')
    def test_valid_user_to_logon_unknown_email(self, mock_query):
        mock_query.return_value = None

        # Create an instance of SqliteInterface
        interface = SqliteInterface(logger=self.mock_logger, db_file=self.db_file)

        user_id, error_str = interface.valid_user_to_logon('unknown@example.com', 2)

        self.assertIsNone(user_id)
        self.assertEqual(error_str, 'Unknown e-mail address')

    @patch.object(SqliteInterface, 'query_with_values')
    def test_valid_user_to_logon_query_exception(self, mock_query):
        # Simulate exception from query_with_values
        mock_query.side_effect = SqliteInterfaceException("Database error")

        # Create SqliteInterface instance
        interface = SqliteInterface(logger=self.mock_logger, db_file=self.db_file)

        # Call the method
        result = interface.valid_user_to_logon('test@example.com', 2)

        # Assertions
        self.assertIsNone(result)  # Check the result is None
        mock_query.assert_called_once_with(
            "SELECT id, logon_type, account_status FROM user_profile WHERE email_address = ?",
            ('test@example.com',)
        )
        self.mock_logger.critical.assert_called_once_with(
            "Query failed, reason: %s", "Database error"
        )

    @patch.object(SqliteInterface, 'query_with_values')
    def test_basic_user_authenticate_success(self, mock_query):
        mock_query.return_value = [(sha256("passwordsalt".encode('UTF-8')).hexdigest(), "salt")]

        # Create an instance of SqliteInterface
        interface = SqliteInterface(logger=self.mock_logger, db_file=self.db_file)

        status, error_str = interface.basic_user_authenticate(1, "password")

        self.assertTrue(status)
        self.assertEqual(error_str, '')
        mock_query.assert_called_once_with(
            "SELECT password, password_salt FROM user_auth_details WHERE user_id = ?",
            (1,)
        )

    @patch.object(SqliteInterface, 'query_with_values')
    def test_basic_user_authenticate_invalid_user_id(self, mock_query):
        mock_query.return_value = None

        # Create an instance of SqliteInterface
        interface = SqliteInterface(logger=self.mock_logger, db_file=self.db_file)

        with self.assertRaises(SqliteInterfaceException) as context:
            interface.basic_user_authenticate(99, "password")

        self.assertEqual(str(context.exception), 'Invalid user id')

    @patch.object(SqliteInterface, 'query_with_values')
    def test_basic_user_authenticate_incorrect_password(self, mock_query):
        mock_query.return_value = [(sha256("wrongpasswordsalt".encode('UTF-8')).hexdigest(), "salt")]

        # Create an instance of SqliteInterface
        interface = SqliteInterface(logger=self.mock_logger, db_file=self.db_file)

        status, error_str = interface.basic_user_authenticate(1, "password")

        self.assertFalse(status)
        self.assertEqual(error_str, "Username/password don't match")

    @patch.object(SqliteInterface, 'query_with_values')
    def test_basic_user_authenticate_query_exception(self, mock_query):
        mock_query.side_effect = SqliteInterfaceException("Database error")

        # Create an instance of SqliteInterface
        interface = SqliteInterface(logger=self.mock_logger, db_file=self.db_file)

        result = interface.basic_user_authenticate(1, "password")

        self.assertIsNone(result)
        self.mock_logger.critical.assert_called_once_with(
            "Query failed, reason: %s", "Database error"
        )
