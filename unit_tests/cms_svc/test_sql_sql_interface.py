import unittest
from unittest.mock import MagicMock, patch
import logging

from sql.sql_interface import SqlInterface


class TestSqlInterface(unittest.TestCase):
    @patch("sql.sql_interface.SqlProjects")
    @patch("sql.sql_interface.SqlTCCustomFields")
    @patch("sql.sql_interface.SqlTestcases")
    @patch("sql.sql_interface.ExtendedSqlInterface.__init__", return_value=None)
    def test_sql_interface_init(self, mock_super_init, mock_testcases, mock_custom_fields, mock_projects):
        mock_logger = MagicMock(spec=logging.Logger)
        mock_state = MagicMock()

        # Create mock instances
        mock_projects_instance = MagicMock()
        mock_custom_fields_instance = MagicMock()
        mock_testcases_instance = MagicMock()

        # Assign the return values of the class mocks
        mock_projects.return_value = mock_projects_instance
        mock_custom_fields.return_value = mock_custom_fields_instance
        mock_testcases.return_value = mock_testcases_instance

        # Instantiate SqlInterface
        iface = SqlInterface(mock_logger, mock_state)

        # Ensure super().__init__ was called correctly
        mock_super_init.assert_called_once_with(mock_logger, mock_state)

        # Ensure SqlProjects, SqlTCCustomFields, and SqlTestcases were instantiated correctly
        mock_projects.assert_called_once_with(mock_logger, mock_state, iface)
        mock_custom_fields.assert_called_once_with(mock_logger, mock_state, iface)
        mock_testcases.assert_called_once_with(mock_logger, mock_state, iface)

        # Ensure attributes were assigned correctly
        self.assertEqual(iface.projects, mock_projects_instance)
        self.assertEqual(iface.tc_custom_fields, mock_custom_fields_instance)
        self.assertEqual(iface.testcases, mock_testcases_instance)
