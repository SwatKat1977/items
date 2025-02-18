from hashlib import sha256
import unittest
from unittest.mock import MagicMock, patch
import logging
from sqlite_interface import SqliteInterface, SqliteInterfaceException
from service_health_enums import ComponentDegradationLevel

class TestSqliteInterface(unittest.TestCase):

    def setUp(self):
        self.mock_logger = MagicMock(spec=logging.Logger)
        self.db_file = 'test.db'
        self.mock_logger.getChild.return_value = self.mock_logger  # getChild should return itself
        self.mock_state_object = MagicMock()
        self.mock_query = MagicMock()

    @patch("base_sqlite_interface.BaseSqliteInterface.__init__")
    def test_initialization(self, mock_base_init):
        """Test that SqliteInterface initializes correctly."""

        # Create an instance of SqliteInterface
        interface = SqliteInterface(logger=self.mock_logger,
                                    db_file=self.db_file,
                                    state_object=self.mock_state_object)

        # Assert BaseSqliteInterface's __init__ was called with db_file
        mock_base_init.assert_called_once_with(self.db_file)

        # Assert the logger was correctly set up as a child logger
        self.mock_logger.getChild.assert_called_once_with("sqlite_interface")
        self.assertEqual(interface._logger, self.mock_logger.getChild.return_value)

    def test_get_testcase_overviews_success(self):
        """Test successful query execution and response handling."""
        mock_result = [
            {"level": 0, "folder_id": 1, "folder_name": "Root", "test_cases": '[{"id": 101, "name": "Test A"}]'},
            {"level": 1, "folder_id": 2, "folder_name": "Subfolder", "test_cases": '[{"id": 102, "name": "Test B"}]'}
        ]
        self.mock_query.return_value = mock_result

        project_id = 123

        # Create an instance of SqliteInterface
        interface = SqliteInterface(logger=self.mock_logger,
                                    db_file=self.db_file,
                                    state_object=self.mock_state_object)
        interface.query_with_values = self.mock_query

        result = interface.get_testcase_overviews(project_id)

        self.assertEqual(result, mock_result)
        self.mock_query.assert_called_once_with(interface.query_with_values.call_args[0][0],
                                                (project_id,))

    def test_get_testcase_overviews_failure(self):
        """Test exception handling when query fails."""
        self.mock_query.side_effect = SqliteInterfaceException("DB error")

        project_id = 123

        # Create an instance of SqliteInterface
        interface = SqliteInterface(logger=self.mock_logger,
                                    db_file=self.db_file,
                                    state_object=self.mock_state_object)
        interface.query_with_values = self.mock_query
        result = interface.get_testcase_overviews(project_id)

        self.assertIsNone(result)
        self.mock_logger.critical.assert_called_once_with("Query failed, reason: %s", "DB error")
        self.assertEqual(self.mock_state_object.database_health, ComponentDegradationLevel.FULLY_DEGRADED)
        self.assertEqual(self.mock_state_object.database_health_state_str, "Fatal SQL failure")
