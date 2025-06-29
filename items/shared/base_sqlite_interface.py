"""
Copyright 2025 Integrated Test Management Suite Development Team

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
import os
import sqlite3
import threading
from typing import Any, Optional


class SqliteInterfaceException(Exception):
    """
    Exception for errors encountered during SQLite database interaction.

    Args:
        message (str): A descriptive error message for the exception.
    """

    def __init__(self, message: str) -> None:
        super().__init__(message)


class BaseSqliteInterface:
    """
    Manages thread-safe interactions with a SQLite database file.
    """

    __slots__ = ['_db_filename', '_lock']
    SQLITE_HEADER = b"SQLite format 3\x00"

    def __init__(self, db_filename: str) -> None:
        """
        Initialize with the path to the SQLite database file.

        Args:
            db_filename (str): The path to the SQLite database file.
        """
        self._db_filename: str = db_filename
        self._lock = threading.RLock()

    def is_valid_database(self) -> bool:
        """
        Check whether the file is a valid SQLite database.

        Returns:
            bool: True if the file is a valid SQLite DB, False otherwise.
        """
        try:
            with open(self._db_filename, "rb") as file:
                return file.read(len(self.SQLITE_HEADER)) == self.SQLITE_HEADER
        except (OSError, FileNotFoundError):
            return False

    def ensure_valid(self) -> None:
        """
        Raise an exception if the database file is missing or invalid.

        Raises:
            SqliteInterfaceException: If file is missing or not a valid DB.
        """
        if not os.path.exists(self._db_filename):
            raise SqliteInterfaceException("Database file does not exist")

        if not self.is_valid_database():
            raise SqliteInterfaceException(
                "Database file format is not valid"
            )

    def _get_connection(self,
                        validate: bool = True) -> sqlite3.Connection:
        """
        Create a fresh SQLite connection for the current operation.

        Returns:
            sqlite3.Connection: A new database connection.

        Raises:
            SqliteInterfaceException: If database is invalid or missing.
        """
        if validate:
            self.ensure_valid()

        return sqlite3.connect(
            self._db_filename,
            check_same_thread=False,
            isolation_level=None,
            detect_types=sqlite3.PARSE_DECLTYPES
        )

    def create_table(self, schema: str, table_name: str) -> None:
        """
        Create a table in the SQLite database.

        Args:
            schema (str): SQL schema definition for the table.
            table_name (str): The name of the table.

        Raises:
            SqliteInterfaceException: If table creation fails.
        """
        with self._lock, self._get_connection(validate=False) as conn:
            try:
                conn.execute(schema)
            except sqlite3.Error as ex:
                raise SqliteInterfaceException(
                    f"Create table failure for {table_name}: {str(ex)}"
                ) from ex

    def run_query(self,
                  query: str,
                  params: tuple = (),
                  fetch_one: bool = False,
                  commit: bool = False) -> Any:
        """
        Execute a SQL query with optional fetching or committing.

        Args:
            query (str): SQL query to execute.
            params (tuple): Query parameters.
            fetch_one (bool): If True, return one row.
            commit (bool): If True, commit the transaction.

        Returns:
            Any:
                - If commit: returns number of affected rows (int).
                - If fetch_one: returns tuple if a row exists, else an empty tuple ().
                - If SELECT: returns list of rows (may be empty).
                - Otherwise: returns None.

        Raises:
            SqliteInterfaceException: On SQLite error.
        """
        with self._lock, self._get_connection() as conn:
            try:
                cursor = conn.execute(query, params)
                if commit:
                    conn.commit()
                    return cursor.rowcount  # int (0 if nothing changed)

                if fetch_one:
                    row = cursor.fetchone()
                    return row if row is not None else ()  # Always return something

                if cursor.description:
                    return cursor.fetchall()  # May return empty list

                return None
            except sqlite3.Error as ex:
                raise SqliteInterfaceException(f"Query error: {str(ex)}") from ex

    def insert_query(self, query: str, params: tuple = ()) -> Optional[int]:
        """
        Execute an INSERT statement and return the new row ID.

        Args:
            query (str): The INSERT SQL statement.
            params (tuple): Parameters for the query.

        Returns:
            Optional[int]: The ID of the last inserted row.

        Raises:
            SqliteInterfaceException: If the query fails.
        """
        with self._lock, self._get_connection() as conn:
            try:
                cursor = conn.execute(query, params)
                conn.commit()
                return cursor.lastrowid
            except sqlite3.Error as ex:
                raise SqliteInterfaceException(
                    f"Insert query failed: {str(ex)}"
                ) from ex

    def bulk_insert_query(self,
                          query: str,
                          value_sets: list[tuple]) -> bool:
        """
        Execute a bulk INSERT operation using a single transaction.

        Args:
            query (str): The INSERT SQL statement with placeholders.
            value_sets (list[tuple]): List of parameter tuples to insert.

        Returns:
            bool: True if the insert succeeds, False otherwise.

        Raises:
            SqliteInterfaceException: If the insert operation fails.
        """
        with self._lock, self._get_connection() as conn:
            try:
                conn.executemany(query, value_sets)
                conn.commit()
                return True
            except sqlite3.Error as ex:
                raise SqliteInterfaceException(
                    f"Bulk insert query failed: {str(ex)}") from ex

    def delete_query(self, query: str, params: tuple = ()) -> None:
        """
        Execute a DELETE query, enforcing foreign key constraints.

        Args:
            query (str): The DELETE SQL statement.
            params (tuple): Parameters for the query.

        Raises:
            SqliteInterfaceException: If the query fails.
        """
        with self._lock, self._get_connection() as conn:
            try:
                conn.execute("PRAGMA foreign_keys = ON;")
                conn.execute(query, params)
                conn.commit()
            except sqlite3.Error as ex:
                raise SqliteInterfaceException(
                    f"Delete query failed: {str(ex)}"
                ) from ex
