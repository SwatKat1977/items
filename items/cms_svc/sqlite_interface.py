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

        query: str = "SELECT id FROM projects WHERE id = ?"

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

        # Query for folders with levels
        folders_query: str = """
            WITH RECURSIVE folder_hierarchy AS (
                SELECT id, parent_id, name, project_id
                FROM test_case_folders
                WHERE parent_id IS NULL AND project_id = ?

                UNION ALL

                SELECT f.id, f.parent_id, f.name, f.project_id
                FROM test_case_folders f
                JOIN folder_hierarchy h ON f.parent_id = h.id
            )
            SELECT
                id AS folder_id,
                parent_id AS parent_folder_id,
                name AS folder_name
            FROM folder_hierarchy
            ORDER BY parent_id, id;
        """

        cases_query: str = """
            SELECT id, folder_id, name
            FROM test_cases WHERE project_id =?
            ORDER BY folder_id, id;
        """

        try:
            folders_rows: typing.Optional[dict] = self.query_with_values(
                folders_query, (project_id,))

        except SqliteInterfaceException as ex:
            self._logger.critical("Test cases folder query failed, reason: %s",
                                  str(ex))
            self._state_object.database_health = ComponentDegradationLevel.FULLY_DEGRADED
            self._state_object.database_health_state_str = "Fatal SQL failure"
            return None

        try:
            cases_rows: typing.Optional[dict] = self.query_with_values(
                cases_query, (project_id,))

        except SqliteInterfaceException as ex:
            self._logger.critical("Test cases query failed, reason: %s",
                                  str(ex))
            self._state_object.database_health = ComponentDegradationLevel.FULLY_DEGRADED
            self._state_object.database_health_state_str = "Fatal SQL failure"
            return None

        # Build the data structure
        data = {
            'folders': [
                {'id': folder_id,
                 'name': name,
                 'parent_id': parent_id}
                for folder_id, parent_id, name in folders_rows],
            'test_cases': [
                {'folder_id': folder_id,
                 'id': test_id,
                 'name': name} for test_id, folder_id, name in cases_rows]
        }

        return data

    def get_testcase(self,
                     case_id: int,
                     project_id: int) -> typing.Optional[dict]:
        """
        Retrieve a test case by its ID from the database.

        Parameters:
            case_id (int): The ID of the test case to retrieve.
            project_id (int): The ID of the project case is part of.

        Returns:
            dict | None: A dictionary containing the test case details
                         (id, folder_id, name, description) if found,
                         otherwise None.

        Handles:
            - Logs a critical error and updates the database health state
              if an SqliteInterfaceException occurs.
        """
        query: str = ("SELECT id, folder_id, name, description "
                      "FROM test_cases WHERE id=? AND project_id=?")

        try:
            rows: typing.Optional[dict] = self.query_with_values(
                query, (case_id, project_id))

        except SqliteInterfaceException as ex:
            self._logger.critical("Query failed, reason: %s", str(ex))
            self._state_object.database_health = ComponentDegradationLevel.FULLY_DEGRADED
            self._state_object.database_health_state_str = "Fatal SQL failure"
            return None

        return rows

    def get_projects_details(self, fields: str):
        """
        Retrieve project details from the database.

        This method constructs and executes a SQL query to fetch the specified
        fields from the `projects` table. If the query fails, it logs the error
        and updates the database health status accordingly.

        Args:
            fields (str): A comma-separated string specifying the columns to
                          retrieve from the `projects` table.

        Returns:
            dict | None: A dictionary containing the query results if successful,
                         otherwise `None` if an error occurs.
        """

        query = f"SELECT {fields} FROM projects"

        try:
            rows: dict = self.query_with_values(query)

        except SqliteInterfaceException as ex:
            self._logger.critical("Query failed, reason: %s", str(ex))
            self._state_object.database_health = ComponentDegradationLevel.FULLY_DEGRADED
            self._state_object.database_health_state_str = \
                "get_projects_details fatal SQL failure"
            return None

        return rows

    def get_no_of_milestones_for_project(self, _project_id: int) -> int:
        """
        NOTE: Currently not implemented, so will always return 0
        """

        return 0

    def get_no_of_testruns_for_project(self, _project_id: int) -> int:
        """
        NOTE: Currently not implemented, so will always return 0
        """

        return 0

    def project_name_exists(self, _project_name: str) -> typing.Optional[bool]:
        """
        Check if a project with the given name exists in the database.

        Args:
            _project_name (str): The name of the project to check.

        Returns:
            Optional[bool]:
                - True if the project exists.
                - False if the project does not exist.
                - None if a database query error occurs.

        Logs:
            - Critical log entry if the query fails, along with the exception message.
            - Updates the database health status to `FULLY_DEGRADED` in case of failure.
        """

        query: str = "SELECT COUNT(*) FROM projects WHERE name = ?"

        try:
            rows: dict = self.query_with_values(query, (_project_name,))

        except SqliteInterfaceException as ex:
            self._logger.critical("Query failed, reason: %s", str(ex))
            self._state_object.database_health = ComponentDegradationLevel.FULLY_DEGRADED
            self._state_object.database_health_state_str = \
                "get_projects_details fatal SQL failure"
            return None

        # Returns True if the project exists, False otherwise
        return rows[0][0] > 0

    def add_project(self, name: str) -> typing.Optional[int]:
        """
        Insert a new project into the database.
        Updates the database health status to `FULLY_DEGRADED` upon failure.

        Args:
            name (str): The name of the project to be added.

        Returns:
            Optional[int]:
                - The ID of the newly inserted project if successful.
                - None if a database query error occurs.

        Logs:
            - Logs a critical error if the database query fails.
        """
        sql: str = "INSERT INTO projects(name) VALUES(?)"

        try:
            return self.insert_query(sql, (name,))

        except SqliteInterfaceException as ex:
            self._logger.critical("Query failed, reason: %s", str(ex))
            self._state_object.database_health = ComponentDegradationLevel.FULLY_DEGRADED
            self._state_object.database_health_state_str = \
                "add_project fatal SQL failure"
            return None
