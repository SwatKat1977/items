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
    """
    Enum representing the direction in which a custom field can be moved.

    Attributes:
        UP (int): Indicates the custom field should be moved up (0).
        DOWN (int): Indicates the custom field should be moved down (1).
    """
    UP = 0
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
        sql: str = (f"SELECT id FROM {cms_tables.TC_CUSTOM_FIELDS} "
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
        # pylint: disable=too-many-return-statements

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

    def add_custom_test_case_custom_field(self,
                                          field_name: str,
                                          description: str,
                                          system_name: str,
                                          field_type: str,
                                          enabled: bool,
                                          is_required: bool,
                                          default_value: str,
                                          applies_to_all_projects: bool) \
            -> int:
        """
        Adds a custom test case field to the database.

        Parameters:
            field_name (str): The name of the custom field.
            description (str): A description of the custom field.
            system_name (str): Internal system name (lowercase with underscores).
            field_type (str): The type of the field (e.g., 'String').
            enabled (bool): Whether the field is enabled.
            is_required (bool): Whether the field is required for test cases.
            default_value (str): The default value for the field.
            applies_to_all_projects (bool): If True, applies to all projects.

        Returns:
            int: value > 1 if the field was added successfully, 0 otherwise.
        """
        # pylint: disable=too-many-arguments, too-many-positional-arguments
        # pylint: disable=too-many-locals

        max_position = self.__get_test_case_custom_field_max_position()
        if max_position is None:
            return 0

        max_position += 1

        sql: str = (f"INSERT INTO {cms_tables.TC_CUSTOM_FIELDS}("
                    "field_name, description, system_name, field_type_id,"
                    "entry_type, enabled, position, is_required,"
                    "default_value) VALUES(?,?,?,?,?,?,?,?,?)")

        field_type_info = self.__get_tc_custom_field_type_info(field_type)
        if field_type_info is None:
            return 0

        # field_type_info = id, supports_default_value, supports_is_required
        type_id, supports_default_value, supports_is_required = field_type_info
        print((f"type_id: {type_id} ~ supports_default_value: {supports_default_value}, "
               f"supports_is_required: {supports_is_required}"))
        sql_values = (field_name, description, system_name, type_id,
                      'user', enabled, is_required, default_value,
                      applies_to_all_projects)

        try:
            custom_field_id: int = self.insert_query(sql, sql_values)

        except SqliteInterfaceException as ex:
            self._logger.critical("Query failed, reason: %s", str(ex))
            self._state_object.database_health = ComponentDegradationLevel.FULLY_DEGRADED
            self._state_object.database_health_state_str = \
                "Insert of custom tc field SQL failed"
            return 0

        return custom_field_id

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

    def __get_test_case_custom_field_max_position(self) -> typing.Optional[int]:
        """
        Returns the highest value of 'position' in the 'tc_custom_fields' table.
        If the table is empty, returns None.
        """
        query = f"SELECT MAX(position) FROM {cms_tables.TC_CUSTOM_FIELDS}"

        try:
            rows: dict = self.query_with_values(query, fetch_one=True)

        except SqliteInterfaceException as ex:
            self._logger.critical("Query failed, reason: %s", str(ex))
            self._state_object.database_health = ComponentDegradationLevel.FULLY_DEGRADED
            self._state_object.database_health_state_str = \
                "__get_test_case_custom_field_max_position fatal SQL failure"
            return None

        return int(rows[0])

    def __get_tc_custom_field_type_info(self, field_type: str) \
            -> typing.Optional[tuple[int, bool, bool]]:
        """
        Retrieves the ID, supports_default_value, and supports_is_required for
        the given field type name.
        Raises ValueError if the field type is not found.
        """
        query = f"""
            SELECT id, supports_default_value, supports_is_required
            FROM {cms_tables.TC_CUSTOM_FIELD_TYPES}
            WHERE name = ?
        """

        try:
            rows: dict = self.query_with_values(query, (field_type,))

        except SqliteInterfaceException as ex:
            self._logger.critical("Query failed, reason: %s", str(ex))
            self._state_object.database_health = ComponentDegradationLevel.FULLY_DEGRADED
            self._state_object.database_health_state_str = \
                "__get_tc_custom_field_type_info fatal SQL failure"
            return None

        if not rows:
            self._logger.warning("Invalid field type name '%s'", field_type)
            return None

        # Returns the number of  custom test case fields
        return_tuple: tuple[int, bool, bool] = (int(rows[0][0]),
                                                bool(rows[0][1]),
                                                bool(rows[0][1]))
        return return_tuple

    def tc_custom_field_name_exists(self, field_name: str) \
            -> typing.Optional[bool]:
        """
        Check if a field name exists in the TC_CUSTOM_FIELDS table.

        Case-insensitive match.

        Parameters:
            field_name (str): The name to check.

        Returns:
            bool: True if exists, False otherwise.
        """
        sql: str = (f"SELECT 1 FROM {cms_tables.TC_CUSTOM_FIELDS} "
                    "WHERE LOWER(field_name) = LOWER(?) "
                    "LIMIT 1")

        try:
            rows: dict = self.query_with_values(sql, (field_name,))

        except SqliteInterfaceException as ex:
            self._logger.critical("Query failed, reason: %s", str(ex))
            self._state_object.database_health = ComponentDegradationLevel.FULLY_DEGRADED
            self._state_object.database_health_state_str = \
                "tc_custom_field_name_exists fatal SQL failure"
            return None

        return bool(rows)

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
