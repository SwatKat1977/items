import unittest
from unittest.mock import MagicMock, patch
import logging
import sqlite3
from sql.extended_sql_interface import ExtendedSqlInterface
from service_health_enums import ComponentDegradationLevel
from threadsafe_configuration import ThreadSafeConfiguration


class TestExtendedSqlInterface(unittest.TestCase):
    def setUp(self):
        self.mock_logger = MagicMock(spec=logging.Logger)
        self.mock_logger.getChild.return_value = self.mock_logger

        # Patch ThreadSafeConfiguration.get_entry just for the test
        self.patcher = patch.object(
            ThreadSafeConfiguration,
            'get_entry',
            return_value=":memory:"
        )
        self.mock_get_entry = self.patcher.start()

        self.mock_state = MagicMock()
        self.ext_iface = ExtendedSqlInterface(self.mock_logger, self.mock_state)

    @patch.object(ExtendedSqlInterface, 'run_query')
    def test_safe_query_success(self, mock_run_query):
        mock_run_query.return_value = [('row1',), ('row2',)]
        result = self.ext_iface.safe_query("SELECT * FROM test", (), "error message")
        self.assertEqual(result, [('row1',), ('row2',)])
        mock_run_query.assert_called_once()

    @patch.object(ExtendedSqlInterface, 'run_query')
    def test_safe_query_failure(self, mock_run_query):
        mock_run_query.side_effect = Exception("boom")  # Not SqliteInterfaceException, won't be caught
        with self.assertRaises(Exception):
            self.ext_iface.safe_query("SELECT * FROM test", (), "error message")

    @patch.object(ExtendedSqlInterface, 'run_query')
    def test_safe_query_sqlite_exception(self, mock_run_query):
        from base_sqlite_interface import SqliteInterfaceException
        mock_run_query.side_effect = SqliteInterfaceException("fail")
        result = self.ext_iface.safe_query("SELECT * FROM test", (), "failed")
        self.assertIsNone(result)
        self.mock_logger.log.assert_called_with(logging.CRITICAL, "%s, reason: %s", "failed", "fail")
        self.assertEqual(self.mock_state.database_health, ComponentDegradationLevel.FULLY_DEGRADED)

    def test_safe_insert_query_success(self):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.lastrowid = 42
        mock_conn.__enter__.return_value = mock_conn
        mock_conn.execute.return_value = mock_cursor

        with patch.object(self.ext_iface, '_get_connection', return_value=mock_conn):
            result = self.ext_iface.safe_insert_query("INSERT INTO test VALUES (?)", (1,), "error msg")
            self.assertEqual(result, 42)
            mock_conn.execute.assert_called_once()
            mock_conn.commit.assert_called_once()

    def test_safe_insert_query_failure(self):
        mock_conn = MagicMock()
        mock_conn.__enter__.return_value.execute.side_effect = sqlite3.Error("bad insert")

        with patch.object(self.ext_iface, '_get_connection', return_value=mock_conn):
            result = self.ext_iface.safe_insert_query("INSERT INTO test VALUES (?)", (1,), "bad insert")
            self.assertIsNone(result)
            self.mock_logger.log.assert_called_with(logging.CRITICAL, "%s, reason: %s", "bad insert", "bad insert")
            self.assertEqual(self.mock_state.database_health, ComponentDegradationLevel.FULLY_DEGRADED)

    @patch.object(ExtendedSqlInterface, 'bulk_insert_query')
    def test_safe_bulk_insert_success(self, mock_bulk):
        mock_bulk.return_value = True
        result = self.ext_iface.safe_bulk_insert("INSERT INTO test VALUES (?)", [(1,), (2,)], "bulk error")
        self.assertTrue(result)
        mock_bulk.assert_called_once()

    @patch.object(ExtendedSqlInterface, 'bulk_insert_query')
    def test_safe_bulk_insert_failure(self, mock_bulk):
        mock_bulk.side_effect = sqlite3.Error("bulk boom")
        result = self.ext_iface.safe_bulk_insert("INSERT INTO test VALUES (?)", [(1,), (2,)], "bulk insert failed")
        self.assertFalse(result)
        self.mock_logger.log.assert_called_with(logging.CRITICAL, "%s, reason: %s", "bulk insert failed", "bulk boom")
        self.assertEqual(self.mock_state.database_health, ComponentDegradationLevel.FULLY_DEGRADED)
