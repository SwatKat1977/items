import os
import sqlite3
import tempfile
import unittest
from base_sqlite_interface import BaseSqliteInterface, SqliteInterfaceException


class TestBaseSqliteInterface(unittest.TestCase):
    def setUp(self):
        # Create a valid SQLite temp file for most tests
        self.db_fd, self.db_path = tempfile.mkstemp()
        os.close(self.db_fd)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT);")

        self.interface = BaseSqliteInterface(self.db_path)

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)

    def test_is_valid_database_true(self):
        self.assertTrue(self.interface.is_valid_database())

    def test_is_valid_database_false(self):
        with tempfile.NamedTemporaryFile(delete=False) as temp:
            temp.write(b"Not a SQLite DB")
            temp_path = temp.name
        iface = BaseSqliteInterface(temp_path)
        self.assertFalse(iface.is_valid_database())
        os.unlink(temp_path)

    def test_ensure_valid_valid_file(self):
        self.interface.ensure_valid()  # Should not raise

    def test_ensure_valid_missing_file(self):
        os.unlink(self.db_path)
        with self.assertRaises(SqliteInterfaceException) as ctx:
            self.interface.ensure_valid()
        self.assertEqual(str(ctx.exception), "Database file does not exist")

    def test_ensure_valid_invalid_file(self):
        with open(self.db_path, 'wb') as f:
            f.write(b"invalid")
        with self.assertRaises(SqliteInterfaceException) as ctx:
            self.interface.ensure_valid()
        self.assertEqual(str(ctx.exception), "Database file format is not valid")

    def test_create_table_success(self):
        schema = "CREATE TABLE test2 (id INTEGER);"
        self.interface.create_table(schema, "test2")
        result = self.interface.run_query("SELECT name FROM sqlite_master WHERE type='table';")
        table_names = [row[0] for row in result]
        self.assertIn("test2", table_names)

    def test_create_table_failure(self):
        with self.assertRaises(SqliteInterfaceException) as ctx:
            self.interface.create_table("INVALID SQL", "bad_table")
        self.assertIn("Create table failure", str(ctx.exception))

    def test_run_query_commit(self):
        rows = self.interface.run_query("INSERT INTO test (name) VALUES (?)", ("Alice",), commit=True)
        self.assertEqual(rows, 1)

    def test_run_query_fetch_one(self):
        self.interface.run_query("INSERT INTO test (name) VALUES (?)", ("Bob",), commit=True)
        row = self.interface.run_query("SELECT * FROM test WHERE name=?", ("Bob",), fetch_one=True)
        self.assertEqual(row[1], "Bob")

    def test_run_query_fetch_all(self):
        self.interface.run_query("INSERT INTO test (name) VALUES (?)", ("Eve",), commit=True)
        rows = self.interface.run_query("SELECT * FROM test")
        self.assertTrue(len(rows) > 0)

    def test_run_query_none_result(self):
        result = self.interface.run_query("PRAGMA foreign_keys;")
        self.assertIsInstance(result, list)

    def test_run_query_failure(self):
        with self.assertRaises(SqliteInterfaceException) as ctx:
            self.interface.run_query("INVALID SQL")
        self.assertIn("Query error", str(ctx.exception))

    def test_insert_query_success(self):
        last_id = self.interface.insert_query("INSERT INTO test (name) VALUES (?)", ("Charlie",))
        self.assertIsInstance(last_id, int)

    def test_insert_query_failure(self):
        with self.assertRaises(SqliteInterfaceException) as ctx:
            self.interface.insert_query("INVALID SQL")
        self.assertIn("Insert query failed", str(ctx.exception))

    def test_bulk_insert_query_success(self):
        values = [("Name1",), ("Name2",)]
        self.interface.bulk_insert_query("INSERT INTO test (name) VALUES (?)", values)
        rows = self.interface.run_query("SELECT * FROM test")
        self.assertEqual(len(rows), 2)

    def test_bulk_insert_query_failure(self):
        with self.assertRaises(SqliteInterfaceException) as ctx:
            self.interface.bulk_insert_query("BAD SQL", [("a",)])
        self.assertIn("Bulk insert query failed", str(ctx.exception))

    def test_delete_query_success(self):
        self.interface.insert_query("INSERT INTO test (name) VALUES (?)", ("Temp",))
        self.interface.delete_query("DELETE FROM test WHERE name=?", ("Temp",))
        rows = self.interface.run_query("SELECT * FROM test WHERE name=?", ("Temp",))
        self.assertEqual(len(rows), 0)

    def test_delete_query_failure(self):
        with self.assertRaises(SqliteInterfaceException) as ctx:
            self.interface.delete_query("BAD SQL")
        self.assertIn("Delete query failed", str(ctx.exception))

    def test_is_valid_database_missing_file(self):
        iface = BaseSqliteInterface("/nonexistent/path/to/db.sqlite")
        self.assertFalse(iface.is_valid_database())

    def test_run_query_returns_none_for_non_select_non_commit(self):
        # Use a no-op PRAGMA statement that returns no data
        result = self.interface.run_query("PRAGMA foreign_keys = OFF;")
        self.assertIsNone(result)
