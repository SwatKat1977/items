import unittest
from unittest.mock import patch, Mock
from sql.sql_testcases import SqlTestcases
from sql.sql_interface import SqlInterface


class TestSqlTestcases(unittest.TestCase):
    def setUp(self):
        self.logger = Mock()
        self.state = Mock()
        self.parent = Mock(spec=SqlInterface)
        self.sql_testcases = SqlTestcases(self.logger, self.state, self.parent)

    @patch.object(SqlTestcases, 'safe_query')
    def test_get_testcase_overviews_success(self, mock_safe_query):
        # Mock folder rows and test case rows
        folder_rows = [
            (1, None, "Root Folder"),
            (2, 1, "Child Folder")
        ]
        test_case_rows = [
            (101, 1, "Login Test"),
            (102, 2, "Logout Test")
        ]

        # Side effect to simulate two queries
        mock_safe_query.side_effect = [folder_rows, test_case_rows]

        result = self.sql_testcases.get_testcase_overviews(project_id=123)

        self.assertIsInstance(result, dict)
        self.assertIn('folders', result)
        self.assertIn('test_cases', result)
        self.assertEqual(len(result['folders']), 2)
        self.assertEqual(len(result['test_cases']), 2)
        self.assertEqual(result['folders'][0]['id'], 1)
        self.assertEqual(result['test_cases'][0]['id'], 101)

    @patch.object(SqlTestcases, 'safe_query')
    def test_get_testcase_overviews_folders_query_fails(self, mock_safe_query):
        # Simulate DB failure on first query
        mock_safe_query.return_value = None
        result = self.sql_testcases.get_testcase_overviews(project_id=123)
        self.assertIsNone(result)

    @patch.object(SqlTestcases, 'safe_query')
    def test_get_testcase_overviews_cases_query_fails(self, mock_safe_query):
        # Simulate successful folder query, then failing test case query
        mock_safe_query.side_effect = [[(1, None, "Root")], None]
        result = self.sql_testcases.get_testcase_overviews(project_id=123)
        self.assertIsNone(result)

    @patch.object(SqlTestcases, 'safe_query')
    def test_get_testcase_success(self, mock_safe_query):
        # Simulate a successful result
        mock_safe_query.return_value = {
            'id': 5, 'folder_id': 1, 'name': "Signup", 'description': "Tests signup flow"
        }

        result = self.sql_testcases.get_testcase(case_id=5, project_id=100)
        self.assertIsNotNone(result)
        self.assertEqual(result['name'], "Signup")

    @patch.object(SqlTestcases, 'safe_query')
    def test_get_testcase_query_failure(self, mock_safe_query):
        # Simulate query returning None
        mock_safe_query.return_value = None
        result = self.sql_testcases.get_testcase(case_id=999, project_id=123)
        self.assertIsNone(result)
