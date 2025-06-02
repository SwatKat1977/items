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
from sql.extended_sql_interface import ExtendedSqlInterface
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


class SqlTCCustomFields(ExtendedSqlInterface):
    def __init__(self, logger: logging.Logger,
                 state_object: StateObject) -> None:
        super().__init__(logger, state_object)

    def move_custom_field(self,
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

        sql: str = (f"SELECT position FROM {cms_tables.TC_CUSTOM_FIELDS} "
                    "WHERE id = ?")
        row = self.safe_query(sql, (field_id,),
                              "Query failed getting TC custom field position",
                              logging.CRITICAL,
                              fetch_one=True)
        if row is None:
            return None

        # If the field id is not found then return False to represent that.
        if not row:
            return False

        total_fields: int = self.__count_custom_fields()
        if total_fields == -1:
            return None

        current_position: int = int(row[0])
        target_position = current_position - 1 \
            if direction == CustomFieldMoveDirection.UP \
            else current_position + 1

        # Clamp the position, so it doesn't go out of range.
        if target_position < 1 or target_position > total_fields:
            return False

        target_field_id = self.__get_id_for_custom_field_in_position(
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

        update_status = self.safe_query(
            update_sql, update_parameters,
            "move_test_case_custom_field fatal SQL failure",
            logging.CRITICAL,
            commit=True)
        return None if update_status is None else True

    def __get_id_for_custom_field_in_position(self, position: int) -> int:
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
        row = self.safe_query(
            sql, (position,),
            "Query failed get_id_for_test_case_custom_field_in_position",
            logging.CRITICAL, fetch_one=True)
        if row is None:
            return -1

        # If the field id is not found then return False to represent that else
        # return the id of the custom test case field.
        return 0 if not row else int(row[0])

    def __count_custom_fields(self) -> int:
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
        sql: str = f"SELECT COUNT(*) FROM {cms_tables.TC_CUSTOM_FIELDS}"
        row = self.safe_query(sql,
                              (),
                              "Query failed counting tc custom fields",
                              logging.CRITICAL,
                              fetch_one=True)

        # Returns True if the project exists, False otherwise
        return -1 if row is None else row[0]
