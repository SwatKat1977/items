import unittest
from unittest.mock import MagicMock, patch
import logging
from sqlite_interface import SqliteInterface

class TestSqliteInterface(unittest.TestCase):
    @patch("base_sqlite_interface.BaseSqliteInterface.__init__")
    def test_initialization(self, mock_base_init):
        """Test that SqliteInterface initializes correctly."""
        # Mock the logger
        mock_logger = MagicMock(spec=logging.Logger)

        # Create an instance of SqliteInterface
        db_file = "test.db"
        instance = SqliteInterface(logger=mock_logger, db_file=db_file)

        # Assert BaseSqliteInterface's __init__ was called with db_file
        mock_base_init.assert_called_once_with(db_file)

        # Assert the logger was correctly set up as a child logger
        mock_logger.getChild.assert_called_once_with("sqlite_interface")
        self.assertEqual(instance._logger, mock_logger.getChild.return_value)

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
