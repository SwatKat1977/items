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
import logging
import sqlite3
import typing
from threadsafe_configuration import ThreadSafeConfiguration as Configuration
from base_sqlite_interface import BaseSqliteInterface, SqliteInterfaceException
from service_health_enums import ComponentDegradationLevel
from state_object import StateObject


class ExtendedSqlInterface(BaseSqliteInterface):
    def __init__(self, logger: logging.Logger,
                 state_object: StateObject) -> None:
        super().__init__(Configuration().backend_db_filename)
        self._logger = logger.getChild(__name__)
        self._state_object: StateObject = state_object

    def safe_query(self,
                   query: str,
                   values: tuple,
                   error_message: str,
                   log_level: int = logging.CRITICAL,
                   fetch_one: bool = False,
                   commit: bool = False
                   ) -> typing.Optional[typing.Any]:
        """
        Safely execute a database query with standardized exception handling,
        logging, and database health state updates.

        Args:
            query (str): SQL query string to execute.
            values (tuple): Parameter values for the query.
            error_message (str): Description for the logger on failure.
            log_level (int): Logging level (e.g., logging.CRITICAL).
            fetch_one (bool): If True, fetch only one result. Default is False.
            commit (bool): If True, commit changes (for INSERT/UPDATE/DELETE).

        Returns:
            Optional[Any]: Query result (single row, list of rows, or None).
        """
        try:
            return self.run_query(query, values, fetch_one=fetch_one, commit=commit)

        except SqliteInterfaceException as ex:
            self._logger.log(log_level, "%s, reason: %s", error_message, str(ex))
            self._state_object.database_health = ComponentDegradationLevel.FULLY_DEGRADED
            self._state_object.database_health_state_str = "Fatal SQL failure"
            return None

    def safe_insert_query(self,
                          query: str,
                          values: tuple,
                          error_message: str,
                          log_level: int = logging.CRITICAL
                          ) -> typing.Optional[int]:
        """
        Safely execute an INSERT query and return the last inserted row ID.

        Args:
            query (str): The INSERT SQL statement.
            values (tuple): Parameters for the query.
            error_message (str): Description for the logger on failure.
            log_level (int): Logging level (e.g., logging.CRITICAL).

        Returns:
            Optional[int]: ID of the last inserted row, or None on failure.
        """
        with self._lock, self._get_connection() as conn:
            try:
                cursor = conn.execute(query, values)
                conn.commit()
                return cursor.lastrowid
            except sqlite3.Error as ex:
                self._logger.log(log_level, "%s, reason: %s", error_message, str(ex))
                self._state_object.database_health = ComponentDegradationLevel.FULLY_DEGRADED
                self._state_object.database_health_state_str = "Fatal SQL failure"
                return None
