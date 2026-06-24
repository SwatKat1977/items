"""
Copyright 2025-2026 Integrated Test Management Suite Development Team

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
from typing import Optional
from weaver_framework.database.sqlite_interface import SqliteInterface
from items.services.items_cms.cms_configuration import CMSConfiguration
import items.shared.databases.cms_db_tables as cms_tables


class ProjectRepository:
    """
    Persistence operations for project data.

    Encapsulates all database access for the projects domain. Raises
    SqliteInterfaceException on database failures; callers are responsible
    for handling those exceptions and updating service state accordingly.
    """

    def __init__(self,
                 logger: logging.Logger,
                 config: CMSConfiguration) -> None:
        self._logger = logger.getChild(__name__)
        self._db = SqliteInterface(self._logger, config.backend_db_filename)

    async def is_valid_project_id(self, project_id: int) -> bool:
        """Return True if the project ID exists in the database.

        Args:
            project_id: ID of the project to check.

        Returns:
            True if the project exists, False otherwise.

        Raises:
            SqliteInterfaceException: If the database query fails.
        """
        query = f"SELECT id FROM {cms_tables.PRJ_PROJECTS} WHERE id = ?"
        row = await self._db.run_query(query, (project_id,), fetch_one=True)
        return bool(row)

    async def get_project_details(self, project_id: int) -> Optional[dict]:
        """Retrieve full details for a project by ID.

        Projects marked as awaiting purge are treated as non-existent.

        Args:
            project_id: ID of the project to retrieve.

        Returns:
            A dict with project fields if found, or None if the project
            does not exist or is awaiting purge.

        Raises:
            SqliteInterfaceException: If the database query fails.
        """
        query = (
            f"SELECT name, awaiting_purge, announcement, "
            f"show_announcement_on_overview "
            f"FROM {cms_tables.PRJ_PROJECTS} WHERE id = ?"
        )
        row = await self._db.run_query(query, (project_id,), fetch_one=True)

        if not row:
            return None

        name, awaiting_purge, announcement, show_announcement_on_overview = row

        if awaiting_purge:
            return None

        return {
            "id": project_id,
            "name": name,
            "announcement": announcement,
            "show_announcement_on_overview": show_announcement_on_overview,
        }

    async def get_projects(self, value_fields: list[str]) -> list[tuple]:
        """Retrieve all active projects with the specified fields.

        The id column is always included as the first field. Projects
        awaiting purge are excluded.

        Args:
            value_fields: Additional column names to select (validated
                against a whitelist by the caller).

        Returns:
            A list of row tuples in (id, *value_fields) order.

        Raises:
            SqliteInterfaceException: If the database query fails.
        """
        all_fields = ["id"] + value_fields
        query = (
            f"SELECT {','.join(all_fields)} FROM {cms_tables.PRJ_PROJECTS} "
            "WHERE awaiting_purge = 0"
        )
        rows = await self._db.run_query(query, ())
        return rows or []

    async def get_no_of_milestones_for_project(self, _project_id: int) -> int:
        """Return the number of milestones for a project.

        Not yet implemented — always returns 0.
        """
        return 0

    async def get_no_of_testruns_for_project(self, _project_id: int) -> int:
        """Return the number of test runs for a project.

        Not yet implemented — always returns 0.
        """
        return 0

    async def project_name_exists(self, project_name: str) -> bool:
        """Return True if a project with the given name already exists.

        Args:
            project_name: Name to check for uniqueness.

        Returns:
            True if the name is taken, False otherwise.

        Raises:
            SqliteInterfaceException: If the database query fails.
        """
        query = f"SELECT COUNT(*) FROM {cms_tables.PRJ_PROJECTS} WHERE name = ?"
        row = await self._db.run_query(query, (project_name,), fetch_one=True)
        return bool(row[0])

    async def add_project(self,
                          name: str,
                          announcement: str,
                          announcement_on_overview: bool) -> int:
        """Insert a new project and return its ID.

        Args:
            name: Project name.
            announcement: Announcement text (may be empty).
            announcement_on_overview: Whether to show the announcement
                on the project overview page.

        Returns:
            The ID of the newly inserted project row.

        Raises:
            SqliteInterfaceException: If the database insert fails.
        """
        query = (
            f"INSERT INTO {cms_tables.PRJ_PROJECTS}"
            "(name, announcement, show_announcement_on_overview) VALUES(?,?,?)"
        )
        return await self._db.insert_query(
            query, (name, announcement, announcement_on_overview))

    async def modify_project(self,
                             project_id: int,
                             announcement: str,
                             announcement_on_overview: bool,
                             name: Optional[str] = None) -> None:
        """Update project details.

        Args:
            project_id: ID of the project to update.
            announcement: Updated announcement text.
            announcement_on_overview: Whether to show the announcement
                on the project overview page.
            name: New project name, or None to leave the name unchanged.

        Raises:
            SqliteInterfaceException: If the database update fails.
        """
        if name is None:
            query = (
                f"UPDATE {cms_tables.PRJ_PROJECTS} "
                "SET announcement = ?, show_announcement_on_overview = ? "
                "WHERE id = ?"
            )
            await self._db.run_query(
                query,
                (announcement, announcement_on_overview, project_id),
                commit=True)
        else:
            query = (
                f"UPDATE {cms_tables.PRJ_PROJECTS} "
                "SET name = ?, announcement = ?, show_announcement_on_overview = ? "
                "WHERE id = ?"
            )
            await self._db.run_query(
                query,
                (name, announcement, announcement_on_overview, project_id),
                commit=True)

    async def mark_project_for_purge(self, project_id: int) -> None:
        """Soft-delete a project by marking it as awaiting purge.

        Args:
            project_id: ID of the project to mark.

        Raises:
            SqliteInterfaceException: If the database update fails.
        """
        query = (
            f"UPDATE {cms_tables.PRJ_PROJECTS} "
            "SET awaiting_purge = 1 WHERE id = ?"
        )
        await self._db.run_query(query, (project_id,), commit=True)

    async def hard_delete_project(self, project_id: int) -> None:
        """Permanently delete a project from the database.

        Args:
            project_id: ID of the project to delete.

        Raises:
            SqliteInterfaceException: If the database delete fails.
        """
        query = f"DELETE FROM {cms_tables.PRJ_PROJECTS} WHERE id = ?"
        await self._db.run_query(query, (project_id,), commit=True)

    async def get_project_id_by_name(self, project_name: str) -> Optional[int]:
        """Return the project ID for a given name.

        Args:
            project_name: Name to look up.

        Returns:
            The project ID if found, or None if no project has that name.

        Raises:
            SqliteInterfaceException: If the database query fails.
        """
        query = f"SELECT id FROM {cms_tables.PRJ_PROJECTS} WHERE name = ?"
        row = await self._db.run_query(query, (project_name,), fetch_one=True)
        return int(row[0]) if row else None
