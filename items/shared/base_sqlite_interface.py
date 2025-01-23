"""
Copyright 2014-2025 Integrated Test Management Suite

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
from typing import AnyStr, Optional


class SqliteInterfaceException(Exception):
    """
    Custom exception for errors encountered while interacting with the SQLite database.

    Args:
        message (str): A descriptive error message for the exception.
    """

    def __init__(self, message):
        """
        Initialize the SqliteInterfaceException with the given error message.

        Args:
            message (str): The error message for the exception.
        """
        super().__init__(message)


class BaseSqliteInterface:
    """
    A class to manage SQLite database interactions.

    Attributes:
        SQLITE_HEADER (bytes): The expected header for valid SQLite database files.
    """

    __slots__ = ['_connection', '_db_filename']
    SQLITE_HEADER = b"SQLite format 3\x00"

    def __init__(self, db_filename: str) -> None:
        """
        Initialize the SqliteInterface with the given database filename.

        Args:
            db_filename (str): The path to the SQLite database file.
        """
        self._db_filename: str = db_filename
        self._connection: Optional[sqlite3.Connection] = None

    def is_connected(self) -> bool:
        """
        Check if a connection to the database is currently open.

        Returns:
            bool: True if connected, False otherwise.
        """
        return self._connection is not None

    def is_valid_database(self) -> bool:
        """
        Verify whether the database file is a valid SQLite file.

        Returns:
            bool: True if the file is a valid SQLite database, False otherwise.
        """
        try:
            with open(self._db_filename, "rb") as file:
                return file.read(len(self.SQLITE_HEADER)) == self.SQLITE_HEADER
        except (OSError, FileNotFoundError):
            return False

    def open(self):
        """
        Open a connection to the SQLite database.

        Raises:
            SqliteInterfaceException: If the database is already open,
                                      cannot be opened, or is invalid.
        """

        if self._connection:
            raise SqliteInterfaceException("Database is already open")

        if not os.path.exists(self._db_filename):
            raise SqliteInterfaceException("Database file cannot be opened")

        if not self.is_valid_database():
            raise SqliteInterfaceException("Database file format is not valid")

        self._connection = sqlite3.connect(self._db_filename)

    def close(self) -> None:
        """
        Close the connection to the SQLite database if open.
        """
        if self._connection:
            self._connection.close()
            self._connection = None

    def create_table(self, table_schema, table_name):
        """
        Create a table in the SQLite database.

        Args:
            table_schema (str): The SQL statement defining the table schema.
            table_name (str): The name of the table being created.

        Raises:
            SqliteInterfaceException: If the database is not open or table creation fails.
        """
        if self._connection is None:
            raise SqliteInterfaceException("Database is not open")

        cursor = self._connection.cursor()

        try:
            cursor.execute(table_schema)
        except sqlite3.Error as ex:
            raise SqliteInterfaceException(
                f"Create table failure for {table_name}: {str(ex)}") from ex

    def insert_query(self, query: str, params: tuple = ()) -> Optional[int]:
        """
        Execute an INSERT query on the SQLite database.

        Args:
            query (str): The SQL INSERT query to execute.
            params (tuple, optional): The parameters to bind to the query. Defaults to ().

        Returns:
            Optional[int]: The ID of the last inserted row, or None if no row was inserted.

        Raises:
            SqliteInterfaceException: If the query fails.
        """

        cursor: sqlite3.Cursor = self._connection.cursor()

        try:
            cursor.execute(query, params)
            self._connection.commit()
            return cursor.lastrowid
        except sqlite3.Error as ex:
            raise SqliteInterfaceException(
                f"Unable perform insert query: {str(ex)}") from ex

    def query_with_values(self, query: str,
                          params: tuple = (),
                          fetch_one: bool = False):
        """
        Execute a query and fetch results from the SQLite database.

        Args:
            query (str): The SQL query to execute.
            params (tuple, optional): The parameters to bind to the query.
                                      Defaults to ().
            fetch_one (bool, optional): If True, fetch a single row; otherwise
                                        fetch all rows. Defaults to False.

        Returns:
            Any: The result of the query, either a single row or a list of rows.

        Raises:
            SqliteInterfaceException: If the query execution fails.
        """
        cursor = self._connection.cursor()
        try:
            cursor.execute(query, params)
            return cursor.fetchone() if fetch_one else cursor.fetchall()

        except sqlite3.Error as ex:
            raise SqliteInterfaceException(
                f"Error querying user ID: {str(ex)}") from ex


CREATE_USER_AUTH_DETAILS_TABLE = """
CREATE TABLE IF NOT EXISTS user_auth_details (
    id INTEGER PRIMARY KEY,
    password TEXT NOT NULL,
    password_salt TEXT NOT NULL,
    user_id INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES user_profile (id)
);
"""

'''
boop = SqliteInterface('womble.test')
#boop = SqliteInterface('.DS_Store')
print(f"Is connected : {boop.is_connected()}")
print(f"Is valid db  : {boop.is_valid_database()}")
boop.open()
x = boop.insert_query(CREATE_USER_AUTH_DETAILS_TABLE)
print(f"LAST ID: {x}")
'''

'''
x = boop.insert_query("INSERT INTO user_auth_details (password, password_salt," +
                      "user_id) VALUES (?, ?, ?)", ('a1', 'b_01', 'ca'))
x = boop.insert_query("INSERT INTO user_auth_details (password, password_salt," +
                      "user_id) VALUES (?, ?, ?)", ('a2', 'b_02', 'cb'))
x = boop.insert_query("INSERT INTO user_auth_details (password, password_salt," +
                      "user_id) VALUES (?, ?, ?)", ('a3', 'b_03', 'cc'))
x = boop.insert_query("INSERT INTO user_auth_details (password, password_salt," +
                      "user_id) VALUES (?, ?, ?)", ('a4', 'b_04', 'cd'))
print(f"LAST ID: {x}")
'''

'''
print(boop.query_with_values("SELECT * from user_auth_details"))
#boop.open()
boop.close()
boop.create_table(";;", "iii")
'''