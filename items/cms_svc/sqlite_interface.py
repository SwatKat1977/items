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

    def get_project_details(self, project_id: int) -> typing.Optional[dict]:
        """
        Retrieve project details from the database using the provided project
        ID.

        Args:
            project_id (int): The ID of the project to retrieve.

        Returns:
            dict | None: A dictionary containing project details if the project
                         exists and is not marked for purge, or `None` if:
            - The project does not exist.
            - The project is flagged for purge (`awaiting_purge`).
            - A database error occurs.

        The returned dictionary contains the following keys:
            - "id" (int): Project ID.
            - "name" (str): Project name.
            - "announcement" (str | None): Project announcement message.
            - "show_announcement_on_overview" (bool): Indicates if the
              announcement should be displayed.

        Logs:
            - Critical error if the SQL query fails.
        """
        sql: str = ("SELECT id, name, awaiting_purge, announcement, "
                    "show_announcement_on_overview FROM projects "
                    f"WHERE id={project_id}")

        try:
            rows: dict = self.query_with_values(sql)

        except SqliteInterfaceException as ex:
            self._logger.critical(
                "'get_project_details' Query failed, reason: %s",
                str(ex))
            self._state_object.database_health = \
                ComponentDegradationLevel.FULLY_DEGRADED
            self._state_object.database_health_state_str = \
                "get_project_details fatal SQL failure"
            return None

        # No project found, return None to represent that
        if not rows:
            return None

        entry = rows[0]

        # If 'awaiting_purge' flag is set then treat it the project the same as
        # if it didn't exist.
        if entry[2] == 1:
            return None

        project_details: dict = {
            "id": entry[0],
            "name": entry[1],
            "announcement": entry[3],
            "show_announcement_on_overview": entry[4]
        }

        return project_details

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

    def project_name_exists(self, project_name: str) -> typing.Optional[bool]:
        """
        Check if a project with the given name exists in the database.
        Updates the database health status to `FULLY_DEGRADED` in case of
        failure.

        Args:
            project_name (str): The name of the project to check.

        Returns:
            Optional[bool]:
                - True if the project exists.
                - False if the project does not exist.
                - None if a database query error occurs.

        Logs:
            - Critical log entry if the query fails, along with the exception
              message.
        """

        query: str = "SELECT COUNT(*) FROM projects WHERE name = ?"

        try:
            rows: dict = self.query_with_values(query, (project_name,))

        except SqliteInterfaceException as ex:
            self._logger.critical("Query failed, reason: %s", str(ex))
            self._state_object.database_health = ComponentDegradationLevel.FULLY_DEGRADED
            self._state_object.database_health_state_str = \
                "project_name_exists fatal SQL failure"
            return None

        # Returns True if the project exists, False otherwise
        return rows[0][0] > 0

    def project_id_exists(self, project_id: int) -> typing.Optional[bool]:
        """
        Check if a project with the given id exists in the database.
        Updates the database health status to `FULLY_DEGRADED` in case of
        failure.

        Args:
            project_id (int): The id of the project to check.

        Returns:
            Optional[bool]:
                - True if the project exists.
                - False if the project does not exist.
                - None if a database query error occurs.

        Logs:
            - Critical log entry if the query fails, along with the exception
              message.
        """

        query: str = "SELECT COUNT(*) FROM projects WHERE id = ?"

        try:
            rows: dict = self.query_with_values(query, (project_id,))

        except SqliteInterfaceException as ex:
            self._logger.critical("Query failed, reason: %s", str(ex))
            self._state_object.database_health = ComponentDegradationLevel.FULLY_DEGRADED
            self._state_object.database_health_state_str = \
                "project_id_exists fatal SQL failure"
            return None

        # Returns True if the project exists, False otherwise
        return rows[0][0] > 0

    def add_project(self, details: dict) -> typing.Optional[int]:
        """
        Insert a new project into the database.
        Updates the database health status to `FULLY_DEGRADED` upon failure.

        Args:
            details (dict): Project details.

        Returns:
            Optional[int]:
                - The ID of the newly inserted project if successful.
                - None if a database query error occurs.

        Logs:
            - Logs a critical error if the database query fails.
        """
        name: str = details["project_name"]
        announcement: str = details["announcement"]
        announcement_on_overview: str = details["announcement_on_overview"]
        sql: str = ("INSERT INTO projects(name, announcement, "
                    "show_announcement_on_overview) VALUES(?,?,?)")

        try:
            return self.insert_query(sql, (name,
                                           announcement,
                                           announcement_on_overview))

        except SqliteInterfaceException as ex:
            self._logger.critical("Query failed, reason: %s", str(ex))
            self._state_object.database_health = ComponentDegradationLevel.FULLY_DEGRADED
            self._state_object.database_health_state_str = \
                "add_project fatal SQL failure"
            return None

    def modify_project(self, project_id: int, details: dict) \
            -> typing.Optional[bool]:

        announcement: str = details["announcement"]
        announcement_on_overview: str = details["announcement_on_overview"]

        if "project_name" not in details:
            sql: str = ("UPDATE projects SET announcement=?,"
                        "show_announcement_on_overview=? WHERE id=?")
            sql_values: tuple = (announcement,
                                 announcement_on_overview,
                                 project_id)

        else:
            sql: str = ("UPDATE projects SET name=?, announcement=?,"
                        "show_announcement_on_overview=?  WHERE id=?")
            name: str = details["project_name"]
            sql_values: tuple = (name,
                                 announcement,
                                 announcement_on_overview,
                                 project_id)

        try:
            self.query(sql, sql_values, commit=True)

        except SqliteInterfaceException as ex:
            self._logger.critical(
                "modify_project %d query failed, reason: %s",
                project_id, str(ex))
            self._state_object.database_health = \
                ComponentDegradationLevel.FULLY_DEGRADED
            self._state_object.database_health_state_str = \
                "modify_project fatal SQL failure"
            return False

        return True

    def mark_project_for_awaiting_purge(self, project_id: int) -> bool:
        """
        Marks a project as awaiting purge in the database.

        This method updates the `awaiting_purge` flag for the specified project
        in the `projects` table. If the update fails due to a database error,
        it logs the failure, updates the database health status, and returns
        `False`. Otherwise, it returns `True` upon successful update.

        Args:
            project_id (int): The unique identifier of the project to update.

        Returns:
            bool: `True` if the project was successfully marked, `False` on
                  error.
        """
        sql: str = "UPDATE projects SET awaiting_purge = 1 WHERE id = ?"

        try:
            self.query(sql, (project_id,), commit=True)

        except SqliteInterfaceException as ex:
            self._logger.critical("Query failed, reason: %s", str(ex))
            self._state_object.database_health = ComponentDegradationLevel.FULLY_DEGRADED
            self._state_object.database_health_state_str = \
                "mark_project_for_awaiting_purge fatal SQL failure"
            return False

        return True

    def hard_delete_project(self, project_id: int) -> bool:
        """
        Permanently deletes a project from the database.

        This method attempts to delete a project from the `projects` table
        based on the given project ID. If the deletion fails due to a database
        error, it logs the critical failure, updates the database health
        status, and returns `False`. Otherwise, it returns `True` upon
        successful deletion.

        Args:
            project_id (int): The unique identifier of the project to be
                              deleted.

        Returns:
            bool: `True` if the project was successfully deleted, `False` if an
                  error occurred.
        """

        sql: str = "DELETE FROM projects WHERE id = ?"

        try:
            self.delete_query(sql, (project_id,))

        except SqliteInterfaceException as ex:
            self._logger.critical("Query failed, reason: %s", str(ex))
            self._state_object.database_health = ComponentDegradationLevel.FULLY_DEGRADED
            self._state_object.database_health_state_str = \
                "hard_delete_project fatal SQL failure"
            return False

        return True
