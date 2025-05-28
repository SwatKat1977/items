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


class CustomFieldMoveDirection(enum.Enum):
    UP = 0,
    DOWN = 1


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

        query: str = f"SELECT id FROM {cms_tables.PRJ_PROJECTS} WHERE id = ?"

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
                    f"show_announcement_on_overview FROM {cms_tables.PRJ_PROJECTS} "
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
            return {}

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

        query = f"SELECT {fields} FROM {cms_tables.PRJ_PROJECTS}"

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

        query: str = f"SELECT COUNT(*) FROM {cms_tables.PRJ_PROJECTS} WHERE name = ?"

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

        query: str = f"SELECT COUNT(*) FROM {cms_tables.PRJ_PROJECTS} WHERE id = ?"

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
        sql: str = (f"INSERT INTO {cms_tables.PRJ_PROJECTS}(name, announcement, "
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
        """
        Update the details of a project in the database.

        Args:
            project_id (int): The ID of the project to be updated.
            details (dict): A dictionary containing the project details to be
                            updated.
                - `announcement` (str): The project announcement message.
                - `announcement_on_overview` (str): Indicates if the
                                                    announcement should be
                                                    displayed on the overview.
                - `project_name` (str, optional): The new name of the project,
                                                  if it is being changed.

        Returns:
            Optional[bool]:
                - `True` if the project details were successfully updated.
                - `False` if the update failed due to a database error.
                - `None` if no update was performed (this case is not
                         explicitly handled,
                  but a return value of `None` could indicate no data or
                  unexpected behavior).

        Behavior:
            - If `project_name` is provided, it updates the project name along
              with the announcement details.
            - If `project_name` is not provided, only the announcement details
              are updated.
            - Executes an SQL `UPDATE` statement using safe parameter
              substitution to prevent SQL injection.
            - If the query fails, logs the error, updates the database health
              state to `FULLY_DEGRADED`, and returns `False`.

        Errors:
            - Logs a critical error and degrades the database state if a
              `SqliteInterfaceException` occurs.

        Example:
            ```python
            result = modify_project(101, {
                "announcement": "New product launch soon!",
                "announcement_on_overview": "true",
                "project_name": "Updated Project Name"
            })
            if result:
                print("Project updated successfully.")
            else:
                print("Failed to update project.")
            ```
        """
        announcement: str = details["announcement"]
        announcement_on_overview: str = details["announcement_on_overview"]

        if "project_name" not in details:
            sql: str = (f"UPDATE {cms_tables.PRJ_PROJECTS} SET announcement=?,"
                        "show_announcement_on_overview=? WHERE id=?")
            sql_values: tuple = (announcement,
                                 announcement_on_overview,
                                 project_id)

        else:
            sql: str = (f"UPDATE {cms_tables.PRJ_PROJECTS} SET name=?, announcement=?,"
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
        sql: str = (f"UPDATE {cms_tables.PRJ_PROJECTS} "
                    "SET awaiting_purge = 1 WHERE id = ?")

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

        sql: str = f"DELETE FROM {cms_tables.PRJ_PROJECTS} WHERE id = ?"

        try:
            self.delete_query(sql, (project_id,))

        except SqliteInterfaceException as ex:
            self._logger.critical("Query failed, reason: %s", str(ex))
            self._state_object.database_health = ComponentDegradationLevel.FULLY_DEGRADED
            self._state_object.database_health_state_str = \
                "hard_delete_project fatal SQL failure"
            return False

        return True

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

    def count_test_case_fields(self) -> int:
        """
        Count the number of custom test case fields in the database.

        This method queries the `test_case_custom_fields` table to retrieve the
        total count of defined custom test case fields. If the query fails due
        to a database error, it logs the critical error, updates the database
        health status, and returns -1  to indicate the failure.

        Returns:
            int:
                - The number of custom test case fields if the query succeeds.
                - `-1` if a database error occurs.
        """
        query: str = f"SELECT COUNT(*) FROM {cms_tables.TC_CUSTOM_FIELDS}"

        try:
            rows: dict = self.query_with_values(query)

        except SqliteInterfaceException as ex:
            self._logger.critical("Query failed, reason: %s", str(ex))
            self._state_object.database_health = ComponentDegradationLevel.FULLY_DEGRADED
            self._state_object.database_health_state_str = \
                "count_test_case_fields fatal SQL failure"
            return -1

        # Returns the number of  custom test case fields
        return int(rows[0][0])

    def get_id_for_test_case_custom_field_in_position(self, position: int) \
            -> int:
        """
        Retrieve the ID of the custom test case field at a given position.

        This method queries the `test_case_custom_fields` table to find the
        ID of the field at the specified `position`. If the query fails due
        to a database error, it logs the error, updates the database health
        status, and returns `-1`. If no field is found at the position, it
        returns `0`.

        Args:
            position (int): The position of the custom test case field.

        Returns:
            int:
                - The ID of the custom test case field if found.
                - `0` if no field exists at the given position.
                - `-1` if a database error occurs.
        """
        sql: str = (f"SELECT id FROM {{cms_tables.TC_CUSTOM_FIELDS}} "
                    "WHERE position = ?")

        try:
            rows: dict = self.query_with_values(sql,
                                                (position,),
                                                fetch_one=True)

        except SqliteInterfaceException as ex:
            self._logger.critical("Query failed, reason: %s", str(ex))
            self._state_object.database_health = ComponentDegradationLevel.FULLY_DEGRADED
            self._state_object.database_health_state_str = \
                "get_id_for_test_case_custom_field_in_position fatal SQL failure"
            return -1

        # If the field id is not found then return False to represent that.
        if not rows:
            return 0

        # Return the id of the custom test case field
        return int(rows[0])

    def move_test_case_custom_field(self,
                                    field_id: int,
                                    direction: CustomFieldMoveDirection) \
            -> typing.Optional[bool]:
        """
        Moves a test case custom field up or down in its positional ordering.

        Retrieves the current position of the custom field specified by `field_id`,
        calculates the target position based on the `direction` parameter, and
        attempts to swap positions with the field currently occupying the target
        position.

        If successful, the fields are swapped and True is returned. If the field
        does not exist or the move would go out of range, False is returned. If a
        database error occurs, logs the error, updates the internal database
        health state, and returns None.

        Parameters:
            field_id (int): The ID of the custom field to move.
            direction (CustomFieldMoveDirection): Direction to move the field,
                either up or down.

        Returns:
            Optional[bool]: True if the move was successful, False if invalid
                conditions were encountered (e.g., field not found or out-of-range
                move), or None if a fatal database error occurred.
        """

        query: str = (f"SELECT position FROM {cms_tables.TC_CUSTOM_FIELDS} "
                      "WHERE id = ?")

        try:
            rows: dict = self.query_with_values(query, (field_id,),
                                                fetch_one=True)

        except SqliteInterfaceException as ex:
            self._logger.critical(
                "move_test_case_custom_field query failed, reason: %s",
                str(ex))
            self._state_object.database_health = ComponentDegradationLevel.FULLY_DEGRADED
            self._state_object.database_health_state_str = \
                "move_test_case_custom_field fatal SQL failure"
            return None

        # If the field id is not found then return False to represent that.
        if not rows:
            return False

        total_fields: int = self.count_test_case_fields()

        if total_fields == -1:
            self._logger.critical(
                "move_test_case_custom_field failed to count fields")
            self._state_object.database_health = \
                ComponentDegradationLevel.FULLY_DEGRADED
            self._state_object.database_health_state_str = \
                "move_test_case_custom_field failed to count fields"
            return None

        current_position = rows[0]
        target_position = current_position - 1 \
            if direction == CustomFieldMoveDirection.UP \
            else current_position + 1

        # Clamp the position so it doesn't go out of range.
        if target_position < 1 or target_position > total_fields:
            return False

        target_field_id = self.get_id_for_test_case_custom_field_in_position(
            target_position)

        # If target field is None then an exception has been raised
        if target_field_id == -1:
            return None

        # If target field is -1 then the target field was notfound
        if not target_field_id:
            return False

        # Swap the positions SQL
        update_sql: str = f"""
            UPDATE {cms_tables.TC_CUSTOM_FIELDS}
            SET position = CASE
                WHEN id = ? THEN ?
                WHEN id = ? THEN ?
            END
            WHERE id IN (?, ?)
        """

        update_parameters: tuple = \
            (field_id, target_position, target_field_id, current_position,
             field_id, target_field_id)

        try:
            rows: dict = self.query(update_sql,
                                    update_parameters,
                                    commit=True)

        except SqliteInterfaceException as ex:
            self._logger.critical(
                "move_test_case_custom_field query failed, reason: %s",
                str(ex))
            self._state_object.database_health = ComponentDegradationLevel.FULLY_DEGRADED
            self._state_object.database_health_state_str = \
                "move_test_case_custom_field fatal SQL failure"
            return None

        return True
