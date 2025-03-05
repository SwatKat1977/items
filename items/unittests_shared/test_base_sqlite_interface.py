import os
import sqlite3
import unittest
from unittest.mock import call, MagicMock
import tempfile
from base_sqlite_interface import BaseSqliteInterface, SqliteInterfaceException


class TestBaseSqliteInterface(unittest.TestCase):

    def setUp(self):
        """
        Set up a temporary SQLite database file for testing.
        """
        self.temp_file = tempfile.NamedTemporaryFile(delete=False)
        self.temp_file.close()
        self.interface = BaseSqliteInterface(self.temp_file.name)

        connection = sqlite3.connect(self.temp_file.name)
        connection.execute("CREATE TABLE IF NOT EXISTS test (id INTEGER PRIMARY KEY)")
        connection.close()

    def tearDown(self):
        """
        Clean up the temporary SQLite database file after testing.
        """
        if os.path.exists(self.temp_file.name):
            os.remove(self.temp_file.name)

    def test_is_valid_database_with_valid_file(self):
        """
        Test that is_valid_database returns True for a valid SQLite database.
        """
        self.interface.open()  # Open the database to initialize it
        self.interface.close()
        self.assertTrue(self.interface.is_valid_database())

    def test_is_valid_database_with_invalid_file(self):
        """
        Test that is_valid_database returns False for an invalid SQLite file.
        """
        with open(self.temp_file.name, "wb") as f:
            f.write(b"Invalid content")
        self.assertFalse(self.interface.is_valid_database())

    def test_is_valid_database_with_missing_file(self):
        """
        Test that is_valid_database returns False if the file is missing.
        """
        os.remove(self.temp_file.name)
        self.assertFalse(self.interface.is_valid_database())

    def test_open_and_close_connection(self):
        """
        Test that the open and close methods work correctly.
        """
        self.interface.open()
        self.assertTrue(self.interface.is_connected())
        self.interface.close()
        self.assertFalse(self.interface.is_connected())

    def test_open_with_invalid_file(self):
        """
        Test that opening an invalid file raises SqliteInterfaceException.
        """
        with open(self.temp_file.name, "wb") as f:
            f.write(b"Invalid content")
        with self.assertRaises(SqliteInterfaceException) as context:
            self.interface.open()
        self.assertIn("Database file format is not valid", str(context.exception))

    def test_open_with_missing_file(self):
        """
        Test that opening a missing file raises SqliteInterfaceException.
        """
        os.remove(self.temp_file.name)
        with self.assertRaises(SqliteInterfaceException) as context:
            self.interface.open()
        self.assertIn("Database file cannot be opened", str(context.exception))

    def test_create_table_success(self):
        """
        Test that a table can be created successfully.
        """
        self.interface.open()
        table_schema = "CREATE TABLE test_table (id INTEGER PRIMARY KEY, name TEXT)"
        self.interface.create_table(table_schema, "test_table")
        self.interface.close()

    def test_create_table_failure(self):
        """
        Test that creating a table with an invalid schema raises an exception.
        """
        self.interface.open()
        invalid_schema = "CREATE TABLED test_table (id PRIMARY KEY, name)"
        with self.assertRaises(SqliteInterfaceException) as context:
            self.interface.create_table(invalid_schema, "test_table")
        self.assertIn("Create table failure", str(context.exception))
        self.interface.close()

    def test_insert_query(self):
        """
        Test that an INSERT query works correctly.
        """
        self.interface.open()
        self.interface.create_table("CREATE TABLE insert_query_test (id INTEGER PRIMARY KEY, name TEXT)", "test")
        last_row_id = self.interface.insert_query("INSERT INTO insert_query_test (name) VALUES (?)", ("Alice",))
        self.assertIsNotNone(last_row_id)
        self.interface.close()

    def test_insert_query_failure(self):
        """
        Test that an invalid INSERT query raises an exception.
        """
        self.interface.open()
        with self.assertRaises(SqliteInterfaceException) as context:
            self.interface.insert_query("INSERT INTO non_existing_table (name) VALUES (?)", ("Alice",))
        self.assertIn("Unable perform insert query", str(context.exception))
        self.interface.close()

    def test_query_with_values_fetch_all(self):
        """
        Test that query_with_values fetches all rows correctly.
        """
        self.interface.open()
        self.interface.create_table("CREATE TABLE fetch_all_test (id INTEGER PRIMARY KEY, name TEXT)", "test")
        self.interface.insert_query("INSERT INTO fetch_all_test (name) VALUES (?)", ("Alice",))
        self.interface.insert_query("INSERT INTO fetch_all_test (name) VALUES (?)", ("Bob",))
        results = self.interface.query_with_values("SELECT * FROM fetch_all_test")
        self.assertEqual(len(results), 2)
        self.interface.close()

    def test_query_with_values_fetch_one(self):
        """
        Test that query_with_values fetches one row correctly.
        """
        self.interface.open()
        self.interface.create_table("CREATE TABLE fetch_one_test (id INTEGER PRIMARY KEY, name TEXT)", "test")
        self.interface.insert_query("INSERT INTO fetch_one_test (name) VALUES (?)", ("Alice",))
        result = self.interface.query_with_values("SELECT * FROM fetch_one_test", fetch_one=True)
        self.assertEqual(result[1], "Alice")
        self.interface.close()

    def test_query_with_invalid_query(self):
        """
        Test that an invalid query raises SqliteInterfaceException.
        """
        self.interface.open()
        with self.assertRaises(SqliteInterfaceException) as context:
            self.interface.query_with_values("SELECT * FROM non_existing_table")
        self.assertIn("Error performing query", str(context.exception))
        self.interface.close()

    def test_open_raises_exception_if_already_open(self):
        """
        Test that the open method raises a SqliteInterfaceException if the database is already open.
        """
        self.interface.open()  # Open the database
        with self.assertRaises(SqliteInterfaceException) as context:
            self.interface.open()  # Attempt to open again while already open
        self.assertEqual(str(context.exception), "Database is already open")

    def test_create_table_raises_exception_if_not_open(self):
        """
        Test that create_table raises a SqliteInterfaceException if the database is not open.
        """
        table_schema = "CREATE TABLE test (id INTEGER PRIMARY KEY)"
        table_name = "test"

        with self.assertRaises(SqliteInterfaceException) as context:
            self.interface.create_table(table_schema, table_name)  # Attempt to create table without opening the DB

        self.assertEqual(str(context.exception), "Database is not open")

    def test_delete_query_success(self):
        """Test delete_query executes successfully with foreign key constraints enabled."""
        query = "DELETE FROM projects WHERE id = ?"
        params = (1,)

        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        self.interface._connection = mock_connection

        # Call delete_query
        self.interface.delete_query(query, params)

        # Ensure the foreign key check and delete query were executed
        expected_calls = [
            call.execute("PRAGMA foreign_keys = ON;"),
            call.execute(query, params)
        ]
        mock_cursor.execute.assert_has_calls(expected_calls)
        self.assertEqual(mock_connection.commit.call_count, 2)  # Ensures both commits occurred

    def test_delete_query_failure(self):
        """Test delete_query raises SqliteInterfaceException on database error."""
        query = "DELETE FROM projects WHERE id = ?"
        params = (1,)

        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        self.interface._connection = mock_connection

        # Simulate an SQL execution failure
        mock_cursor.execute.side_effect = sqlite3.Error("Simulated error")

        with self.assertRaises(SqliteInterfaceException) as context:
            self.interface.delete_query(query, params)

        self.assertIn("Error performing query", str(context.exception))
        mock_cursor.execute.assert_called_once_with("PRAGMA foreign_keys = ON;")  # Foreign key enabling was attempted

    def test_query_success_no_commit(self):
        """Test query executes successfully without commit."""
        query = "UPDATE projects SET name = ? WHERE id = ?"
        params = ("New Project Name", 1)

        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        self.interface._connection = mock_connection

        self.interface.query(query, params)

        mock_cursor.execute.assert_called_once_with(query, params)
        mock_connection.commit.assert_not_called()  # Ensure commit is NOT called

    def test_query_success_with_commit(self):
        """Test query executes successfully with commit."""
        query = "UPDATE projects SET name = ? WHERE id = ?"
        params = ("Updated Project", 2)

        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        self.interface._connection = mock_connection

        self.interface.query(query, params, commit=True)

        mock_cursor.execute.assert_called_once_with(query, params)
        mock_connection.commit.assert_called_once()  # Ensure commit is called

    def test_query_failure(self):
        """Test query raises SqliteInterfaceException on database error."""
        query = "UPDATE projects SET name = ? WHERE id = ?"
        params = ("Failure Test", 3)

        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        self.interface._connection = mock_connection

        # Simulate an SQL execution failure
        mock_cursor.execute.side_effect = sqlite3.Error("Simulated SQL error")

        with self.assertRaises(SqliteInterfaceException) as context:
            self.interface.query(query, params)

        self.assertIn("Error performing query", str(context.exception))
        mock_cursor.execute.assert_called_once_with(query, params)
        mock_connection.commit.assert_not_called()  # Ensure commit was never attempted
