from hashlib import sha256
import unittest
from unittest.mock import call, MagicMock, patch
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

        folders_mock_result = [(1, None, "Folder 1")]
        cases_mock_result = []
        expected_result = {'folders': [
            {'id': 1, 'name': 'Folder 1', 'parent_id': None}],
            'test_cases': []}
        self.mock_query.side_effect = [folders_mock_result,
                                       cases_mock_result]

        project_id = 123

        # Create an instance of SqliteInterface
        interface = SqliteInterface(logger=self.mock_logger,
                                    db_file=self.db_file,
                                    state_object=self.mock_state_object)
        interface.query_with_values = self.mock_query

        result = interface.get_testcase_overviews(project_id)

        self.assertEqual(result, expected_result)

        expected_calls = [
            call(interface.query_with_values.call_args_list[0][0][0], (project_id,)),  # First call
            call(interface.query_with_values.call_args_list[1][0][0], (project_id,)),  # Second call (if exists)
            # Add more if needed
        ]
        self.mock_query.assert_has_calls(expected_calls, any_order=False)  # Set `True` if order doesn't matter

    def test_get_testcase_overviews_folders_query_failure(self):
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
        self.mock_logger.critical.assert_called_once_with(
            "Test cases folder query failed, reason: %s", "DB error")
        self.assertEqual(self.mock_state_object.database_health,
                         ComponentDegradationLevel.FULLY_DEGRADED)
        self.assertEqual(self.mock_state_object.database_health_state_str,
                         "Fatal SQL failure")

    def test_get_testcase_overviews_test_cases_query_failure(self):
        """Test exception handling when query fails."""

        mock_result = [("Test Case 1", "Description 1"), ("Test Case 2", "Description 2")]
        self.mock_query.side_effect = [mock_result,
                                       SqliteInterfaceException("DB error on cases query")]

        project_id = 123

        # Create an instance of SqliteInterface
        interface = SqliteInterface(logger=self.mock_logger,
                                    db_file=self.db_file,
                                    state_object=self.mock_state_object)
        interface.query_with_values = self.mock_query
        result = interface.get_testcase_overviews(project_id)

        self.assertIsNone(result)
        self.mock_logger.critical.assert_called_once_with(
            "Test cases query failed, reason: %s", "DB error on cases query")
        self.assertEqual(self.mock_state_object.database_health,
                         ComponentDegradationLevel.FULLY_DEGRADED)
        self.assertEqual(self.mock_state_object.database_health_state_str,
                         "Fatal SQL failure")

    def test_is_valid_project_id_valid(self):
        """Test when project ID exists in the database."""
        self.mock_query.return_value = [{"id": 123}]

        project_id = 123

        # Create an instance of SqliteInterface
        interface = SqliteInterface(logger=self.mock_logger,
                                    db_file=self.db_file,
                                    state_object=self.mock_state_object)
        interface.query_with_values = self.mock_query
        result = interface.is_valid_project_id(project_id)

        self.assertTrue(result)
        self.mock_query.assert_called_once_with("SELECT id FROM projects WHERE id = ?", (project_id,))

    def test_is_valid_project_id_invalid(self):
        """Test when project ID does not exist in the database (empty result)."""
        self.mock_query.return_value = []

        project_id = 999

        # Create an instance of SqliteInterface
        interface = SqliteInterface(logger=self.mock_logger,
                                    db_file=self.db_file,
                                    state_object=self.mock_state_object)
        interface.query_with_values = self.mock_query
        result = interface.is_valid_project_id(project_id)

        self.assertFalse(result)
        self.mock_query.assert_called_once_with("SELECT id FROM projects WHERE id = ?", (project_id,))

    def test_is_valid_project_id_sqlite_exception(self):
        """Test that a SqliteInterfaceException is handled correctly."""
        self.mock_query.side_effect = SqliteInterfaceException("Database failure")

        project_id = 456

        # Create an instance of SqliteInterface
        interface = SqliteInterface(logger=self.mock_logger,
                                    db_file=self.db_file,
                                    state_object=self.mock_state_object)
        interface.query_with_values = self.mock_query
        result = interface.is_valid_project_id(project_id)

        # Ensure function returns None
        self.assertIsNone(result)

        # Ensure the logger recorded the critical failure
        self.mock_logger.critical.assert_called_once_with("Query failed, reason: %s", "Database failure")

        # Ensure database health is marked as fully degraded
        self.assertEqual(self.mock_state_object.database_health, ComponentDegradationLevel.FULLY_DEGRADED)
        self.assertEqual(self.mock_state_object.database_health_state_str, "Fatal SQL failure")

    def test_get_testcase_valid(self):
        """Test when a valid test case is found."""
        self.mock_query.return_value = [(0, 1, 'Functional Tests', '[{"id":5,"name":"Invalid Login Test"}]')]

        case_id = 1
        project_id: int = 1

        # Create an instance of SqliteInterface
        interface = SqliteInterface(logger=self.mock_logger,
                                    db_file=self.db_file,
                                    state_object=self.mock_state_object)
        interface.query_with_values = self.mock_query
        result = interface.get_testcase(case_id, project_id)

        expected = [(0, 1, 'Functional Tests', '[{"id":5,"name":"Invalid Login Test"}]')]
        self.assertEqual(result, expected)
        self.mock_query.assert_called_once_with(
            "SELECT id, folder_id, name, description FROM test_cases WHERE id=? AND project_id=?",
            (case_id, project_id))

    def test_get_testcase_not_found(self):
        """Test when the test case ID does not exist in the database."""
        self.mock_query.return_value = None

        case_id = 999
        project_id = 1

        # Create an instance of SqliteInterface
        interface = SqliteInterface(logger=self.mock_logger,
                                    db_file=self.db_file,
                                    state_object=self.mock_state_object)
        interface.query_with_values = self.mock_query
        result = interface.get_testcase(case_id, project_id)

        self.assertIsNone(result)
        self.mock_query.assert_called_once_with(
            "SELECT id, folder_id, name, description FROM test_cases WHERE id=? AND project_id=?",
            (case_id, project_id)
        )

    def test_get_testcase_sqlite_exception(self):
        """Test that a SqliteInterfaceException is handled correctly."""
        self.mock_query.side_effect = SqliteInterfaceException("Database failure")

        case_id: int = 456
        project_id: int = 1

        # Create an instance of SqliteInterface
        interface = SqliteInterface(logger=self.mock_logger,
                                    db_file=self.db_file,
                                    state_object=self.mock_state_object)
        interface.query_with_values = self.mock_query
        result = interface.get_testcase(case_id, project_id)

        # Ensure function returns None
        self.assertIsNone(result)

        # Ensure the logger recorded the critical failure
        self.mock_logger.critical.assert_called_once_with("Query failed, reason: %s", "Database failure")

        # Ensure database health is marked as fully degraded
        self.assertEqual(self.mock_state_object.database_health, ComponentDegradationLevel.FULLY_DEGRADED)
        self.assertEqual(self.mock_state_object.database_health_state_str, "Fatal SQL failure")

    def test_get_testcase_generic_exception(self):
        """Test that a generic exception is raised."""
        self.mock_query.side_effect = Exception("Unexpected error")

        case_id = 789
        project_id: int = 1

        # Create an instance of SqliteInterface
        interface = SqliteInterface(logger=self.mock_logger,
                                    db_file=self.db_file,
                                    state_object=self.mock_state_object)
        interface.query_with_values = self.mock_query

        with self.assertRaises(Exception) as context:
            interface.get_testcase(case_id, project_id)

        self.assertEqual(str(context.exception), "Unexpected error")

    def test_get_no_of_milestones_for_project_success(self):
        # Create an instance of SqliteInterface
        interface = SqliteInterface(logger=self.mock_logger,
                                    db_file=self.db_file,
                                    state_object=self.mock_state_object)

        count: int = interface.get_no_of_milestones_for_project(10)
        self.assertEqual(count, 0)

    def test_get_no_of_testruns_for_project_success(self):
        # Create an instance of SqliteInterface
        interface = SqliteInterface(logger=self.mock_logger,
                                    db_file=self.db_file,
                                    state_object=self.mock_state_object)

        count: int = interface.get_no_of_testruns_for_project(10)
        self.assertEqual(count, 0)