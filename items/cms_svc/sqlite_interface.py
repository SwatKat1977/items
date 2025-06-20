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
import enum
import logging
import typing
from base_sqlite_interface import BaseSqliteInterface, SqliteInterfaceException
from service_health_enums import ComponentDegradationLevel
from state_object import StateObject


class SqliteInterface(BaseSqliteInterface):
    """
    Interface for interacting with a SQLite database, extending the
    functionality of the `BaseSqliteInterface`. Provides methods for verifying
    user logon eligibility and other database-related operations.

    Args:
        logger (logging.Logger): A logger instance for logging database-related events.
        db_file (str): Path to the SQLite database file.
    """

    def __init__(self, logger: logging.Logger, db_file: str,
                 state_object: StateObject) -> None:
        super().__init__(db_file)
        self._logger = logger.getChild(__name__)
        self._state_object: StateObject = state_object

    def is_valid_custom_test_case_field(self, field_id: int) \
            -> typing.Optional[bool]:
        """
        Check if a custom test case field exists in the database.

        This method queries the `test_case_custom_fields` table to determine
        whether a field with the given `field_id` exists. If the query fails
        due to a database error, it logs  the critical failure, updates the
        database health status, and returns `None`.

        Args:
            field_id (int): The ID of the custom test case field to check.

        Returns:
            Optional[bool]:
                - `True` if the field exists.
                - `False` if the field does not exist.
                - `None` if a database error occurs.
        """
        query: str = (f"SELECT COUNT(*) FROM {cms_tables.TC_CUSTOM_FIELDS} "
                      "WHERE id = ?")

        try:
            rows: dict = self.query_with_values(query, (field_id,))

        except SqliteInterfaceException as ex:
            self._logger.critical("Query failed, reason: %s", str(ex))
            self._state_object.database_health = ComponentDegradationLevel.FULLY_DEGRADED
            self._state_object.database_health_state_str = \
                "is_valid_custom_test_case_field fatal SQL failure"
            return None

        # Returns True if the custom test case field exists, False otherwise
        return rows[0][0] > 0

    def tc_custom_field_system_name_exists(self, system_name: str) \
            -> typing.Optional[bool]:
        """
        Check if a system name exists in the TC_CUSTOM_FIELDS table.

        Case-insensitive match.

        Parameters:
            system_name (str): The system name to check.

        Returns:
            bool: True if exists, False otherwise.
        """
        sql: str = (f"SELECT 1 FROM {cms_tables.TC_CUSTOM_FIELDS} "
                    "WHERE LOWER(system_name) = LOWER(?) "
                    "LIMIT 1")

        try:
            rows: dict = self.query_with_values(sql, (system_name,))

        except SqliteInterfaceException as ex:
            self._logger.critical("Query failed, reason: %s", str(ex))
            self._state_object.database_health = ComponentDegradationLevel.FULLY_DEGRADED
            self._state_object.database_health_state_str = \
                "tc_custom_field_system_name_exists fatal SQL failure"
            return None

        return bool(rows)
## 279