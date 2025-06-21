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
from __future__ import annotations
import logging
import typing
from sql.extended_sql_interface import ExtendedSqlInterface
from state_object import StateObject
import databases.cms_db_tables as cms_tables


class SqlProjects(ExtendedSqlInterface):
    def __init__(self, logger: logging.Logger,
                 state_object: StateObject,
                 parent: SqlInterface) -> None:
        super().__init__(logger, state_object)
        self._parent = parent

    def is_valid_project_id(self, project_id: int) -> typing.Optional[bool]:
        """
        Check to see if a project id is valid.

        parameters:
            project_id - Project ID to verify

        returns:
            boolean status
        """

        query: str = f"SELECT id FROM {cms_tables.PRJ_PROJECTS} WHERE id = ?"

        row = self.safe_query(query,
                              (project_id,),
                              "Query failed during project ID check",
                              fetch_one=True)
        return None if row is None else bool(row)

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
        sql: str = ("SELECT name, awaiting_purge, announcement, "
                    f"show_announcement_on_overview FROM {cms_tables.PRJ_PROJECTS} "
                    f"WHERE id=?")

        row = self.safe_query(sql,
                              (project_id,),
                              "Query failed getting project details",
                              fetch_one=True)
        if row is None:
            return None

        if row == ():
            return {}

        name, awaiting_purge, announcement, show_announcement_on_overview = row

        # If 'awaiting_purge' flag is set then treat it the project the same as
        # if it didn't exist.
        if awaiting_purge == 1:
            return {}

        project_details: dict = {
            "id": project_id,
            "name": name,
            "announcement": announcement,
            "show_announcement_on_overview": show_announcement_on_overview
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
        sql = f"SELECT {fields} FROM {cms_tables.PRJ_PROJECTS}"
        rows = self.safe_query(sql,
                               (),
                               "Query failed getting projects details")
        if rows is None:
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

        sql: str = (f"SELECT COUNT(*) FROM {cms_tables.PRJ_PROJECTS} "
                    "WHERE name = ?")

        rows = self.safe_query(sql,
                               (project_name,),
                               "Query failed checking project name exists",
                               fetch_one=True)
        if rows is None:
            return None

        # Returns True if the project exists, False otherwise
        return False if not rows[0] else True

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
        sql_values = (name, announcement, announcement_on_overview)

        return self.safe_insert_query(sql,
                                      sql_values,
                                      "Query failed adding a new project")

    def modify_project(self, project_id: int, details: dict) -> bool:
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
            bool:
                - `True` if the project details were successfully updated.
                - `False` if the update failed due to a database error.

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

        row_count = self.safe_query(sql,
                                    sql_values,
                                    "Query failed modifying a project",
                                    commit=True)
        if row_count is None:
            return False

        return True if row_count else False

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
        row_count = self.safe_query(
            sql, (project_id,),
            "Query failed marking project awaiting purge", commit=True)
        if row_count is None:
            return False

        return True if row_count else False

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
        row_count = self.safe_query(
            sql, (project_id,),
            "Query failed hard deleting a project", commit=True)
        if row_count is None:
            return False

        return True if row_count else False

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
        sql: str = f"SELECT ID FROM {cms_tables.PRJ_PROJECTS} WHERE name = ?"

        row = self.safe_query(sql, (project_name,),
                              "get_project_id_by_name fatal SQL failure",
                              fetch_one=True)
        if row is None:
            return None

        if not row:
            return 0

        # Returns True if the project exists, False otherwise
        return 0 if not row else int(row[0])
