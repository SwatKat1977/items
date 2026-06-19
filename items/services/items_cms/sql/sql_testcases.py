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
from items_common.service_state import ServiceState
import databases.cms_db_tables as cms_tables


class SqlTestcases(ExtendedSqlInterface):
    def __init__(self, logger: logging.Logger,
                 state_object: ServiceState,
                 parent: SqlInterface) -> None:
        super().__init__(logger, state_object)
        self._parent = parent

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

        folders_rows = self.safe_query(
            folders_query,
            (project_id,),
            "Query failed getting tc folder hierarchy")
        if folders_rows is None:
            return None

        cases_rows = self.safe_query(
            cases_query,
            (project_id,),
            "Query failed getting test cases")
        if cases_rows is None:
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

        rows = self.safe_query(query, (case_id, project_id),
                               "Query failed getting test case details")
        if rows is None:
            return None

        return rows
