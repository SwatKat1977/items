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
import databases.cms_db_tables as cms_tables

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
        folders_query: str = f"""
            WITH RECURSIVE folder_hierarchy AS (
                SELECT id, parent_id, name, project_id
                FROM {cms_tables.TC_FOLDERS}
                WHERE parent_id IS NULL AND project_id = ?

                UNION ALL

                SELECT f.id, f.parent_id, f.name, f.project_id
                FROM {cms_tables.TC_FOLDERS} f
                JOIN folder_hierarchy h ON f.parent_id = h.id
            )
            SELECT
                id AS folder_id,
                parent_id AS parent_folder_id,
                name AS folder_name
            FROM folder_hierarchy
            ORDER BY parent_id, id;
        """

        cases_query: str = f"""
            SELECT id, folder_id, name
            FROM {cms_tables.TC_TEST_CASES} WHERE project_id =?
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
                      f"FROM {cms_tables.TC_TEST_CASES} WHERE id=? "
                      "AND project_id=?")

        try:
            rows: typing.Optional[dict] = self.query_with_values(
                query, (case_id, project_id))

        except SqliteInterfaceException as ex:
            self._logger.critical("Query failed, reason: %s", str(ex))
            self._state_object.database_health = ComponentDegradationLevel.FULLY_DEGRADED
            self._state_object.database_health_state_str = "Fatal SQL failure"
            return None

        return rows

    def get_project_id_by_name(self, project_name: str) -> typing.Optional[int]:
        """
        Retrieve the project ID for a given project name.

        This function queries the PRJ_PROJECTS table to find the ID of a project
        matching the provided project_name. If the project is not found, it returns
        0. If a database error occurs, it logs the error, updates internal state,
        and returns None.

        Args:
            project_name (str): The name of the project to search for.

        Returns:
            Optional[int]: The project ID if found, 0 if not found, or None on
            database error.
        """

        query: str = f"SELECT ID FROM {cms_tables.PRJ_PROJECTS} WHERE name = ?"

        try:
            rows: dict = self.query_with_values(query, (project_name,))

        except SqliteInterfaceException as ex:
            self._logger.critical("Query failed, reason: %s", str(ex))
            self._state_object.database_health = ComponentDegradationLevel.FULLY_DEGRADED
            self._state_object.database_health_state_str = \
                "get_project_id_by_name fatal SQL failure"
            return None

        # Returns True if the project exists, False otherwise
        if not rows:
            return 0

        return int(rows[0][0])

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

    def assign_projects_to_custom_tc_field(self, tc_field_id: int,
                                           projects: list) -> typing.Optional[bool]:
        print(f"Assigning tc custom fields to {tc_field_id} : {projects}")

        project_ids: typing.List[int] = []

        for name in projects:
            project_id: int = self.get_project_id_by_name(name)
            if not project_id:
                return False

            project_ids.append(project_id)

        print(f"[DEBUG] Project IDs :  {project_ids}")

        return False

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
