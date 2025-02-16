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

    def is_valid_project_id(self, project_id : int) -> typing.Optional[bool]:
        """
        Check to see if a project id is valid.

        parameters:
            project_id - Project ID to verify

        returns:
            boolean status
        """

        query: str = "SELECT id FROM project WHERE id = ?"

        try:
            rows: typing.Optional[dict] = self.query_with_values(
                query, (project_id,))

        except SqliteInterfaceException as ex:
            self._logger.critical("Query failed, reason: %s", str(ex))
            self._state_object.database_health = ComponentDegradationLevel.FULLY_DEGRADED
            self._state_object.database_health_state_str = "Fatal SQL failure"
            return None

        return bool(rows)

    def get_testcase_overviews(self, project_id: int) -> typing.Optional[dict]:
        """
        Retrieve an overview of test cases organized by folder hierarchy within
        a project.

        This method queries the database using a recursive common table
        expression (CTE) to construct the folder hierarchy for the given
        project. It then retrieves test case IDs associated with each folder.

        Args:
            project_id (int): The ID of the project for which to retrieve test
                              case overviews.

        Returns:
            Optional[dict]: A dictionary containing query results, where
                            folders are mapped to their corresponding test
                            cases. Returns None if the query fails.

        Raises:
            SqliteInterfaceException: If there is a failure while executing the
                                      SQL query.

        Notes:
            - The function uses a recursive CTE (`folder_hierarchy`) to
              determine folder relationships within the project.
            - Test cases are joined with their respective folders.
            - The results are ordered by folder level, folder ID, and test case
              ID.
            - If a fatal SQL error occurs, the database health state is updated
              accordingly.
        """

        query: str = '''
        WITH RECURSIVE folder_hierarchy AS (
            -- Base case: Get root folders in the project
            SELECT id, parent_id, 0 AS level
            FROM folders
            WHERE project_id = ? AND parent_id IS NULL

            UNION ALL

            -- Recursive case: Get subfolders
            SELECT f.id, f.parent_id, fh.level + 1
            FROM folders f
            JOIN folder_hierarchy fh ON f.parent_id = fh.id
        )
        SELECT
            fh.level,
            fh.id AS folder_id,
            tc.id AS test_case_id
        FROM folder_hierarchy fh
        LEFT JOIN test_cases tc ON fh.id = tc.folder_id
        ORDER BY fh.level, fh.id, tc.id;
        '''

        try:
            rows: typing.Optional[dict] = self.query_with_values(
                query, (project_id,))

        except SqliteInterfaceException as ex:
            self._logger.critical("Query failed, reason: %s", str(ex))
            self._state_object.database_health = ComponentDegradationLevel.FULLY_DEGRADED
            self._state_object.database_health_state_str = "Fatal SQL failure"
            return None

        return rows
