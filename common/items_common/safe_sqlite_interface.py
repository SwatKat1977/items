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
import sqlite3
import logging
import typing
from items_common.service_state import ServiceState
from base_sqlite_interface import BaseSqliteInterface, SqliteInterfaceException


class SafeSqliteInterface(BaseSqliteInterface):
    """
    Extension of BaseSqliteInterface that provides safe database access with
    integrated error handling, logging, and maintenance-mode enforcement.
    """

    def __init__(self,
                 logger: logging.Logger,
                 state: ServiceState,
                 db_filename: str) -> None:
        super().__init__(db_filename)
        self._logger = logger.getChild(__name__)
        self._state = state

    def _handle_db_error(self, error_message: str, ex: Exception,
                         log_level: int = logging.CRITICAL) -> None:
        """Centralized error handling and state update."""
        self._logger.log(log_level, "%s, reason: %s", error_message, str(ex))
        self._state.mark_database_failed(str(ex))

    def safe_query(self,
                   query: str,
                   values: tuple = (),
                   error_message: str = "",
                   log_level: int = logging.CRITICAL,
                   fetch_one: bool = False,
                   commit: bool = False
                   ) -> typing.Optional[typing.Any]:
        """Safely execute a database query with maintenance-mode enforcement."""
        # pylint: disable=too-many-arguments, too-many-positional-arguments
        if not self._state.is_operational():
            raise RuntimeError("Service in maintenance mode; refusing database operation.")

        try:
            return self.run_query(query, values, fetch_one=fetch_one, commit=commit)
        except (sqlite3.Error, SqliteInterfaceException) as ex:
            self._handle_db_error(error_message, ex, log_level)
            return None

    def safe_insert_query(self,
                          query: str,
                          values: tuple,
                          error_message: str,
                          log_level: int = logging.CRITICAL) -> typing.Optional[int]:
        """Safely execute an INSERT query and return last inserted row ID."""
        if not self._state.is_operational():
            raise RuntimeError("Service in maintenance mode; refusing database operation.")

        try:
            with self._lock, self._get_connection() as conn:
                cursor = conn.execute(query, values)
                conn.commit()
                return cursor.lastrowid
        except sqlite3.Error as ex:
            self._handle_db_error(error_message, ex, log_level)
            return None

    def safe_bulk_insert(self,
                         query: str,
                         value_sets: list[tuple],
                         error_message: str,
                         log_level: int = logging.CRITICAL) -> bool:
        """
        Safely execute a bulk insert operation with maintenance-mode support.
        """
        if not self._state.is_operational():
            raise RuntimeError("Service in maintenance mode; refusing database operation.")

        try:
            return self.bulk_insert_query(query, value_sets)
        except sqlite3.Error as ex:
            self._handle_db_error(error_message, ex, log_level)
            return False
