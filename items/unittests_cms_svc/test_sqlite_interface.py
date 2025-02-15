from hashlib import sha256
import unittest
from unittest.mock import MagicMock, patch
import logging
from sqlite_interface import SqliteInterface


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
