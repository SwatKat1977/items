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
import items.services.items_cms.cms_db_tables as cms_tables


class FolderRepository:
    """
    Persistence operations for testcase folder data.

    Encapsulates all database access for the folders domain. Raises
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

    async def get_folder(self, folder_id: int) -> Optional[dict]:
        """Retrieve full details for a single folder.

        Args:
            folder_id: Primary key of the folder.

        Returns:
            A dict with ``id``, ``project_id``, ``parent_id``, and ``name``
            if found, or None if no row matches.

        Raises:
            SqliteInterfaceException: If the database query fails.
        """
        query = (
            f"SELECT id, project_id, parent_id, name "
            f"FROM {cms_tables.TC_FOLDERS} WHERE id = ?"
        )
        row = await self._db.run_query(query, (folder_id,), fetch_one=True)

        if not row:
            return None

        folder_id, project_id, parent_id, name = row
        return {
            'id': folder_id,
            'project_id': project_id,
            'parent_id': parent_id,
            'name': name
        }

    async def get_folders(self, project_id: int) -> list[dict]:
        """Retrieve every folder belonging to a project, as a flat list.

        Args:
            project_id: ID of the project to query.

        Returns:
            A list of ``{id, parent_id, name}`` dicts, ordered by parent
            then id.

        Raises:
            SqliteInterfaceException: If the database query fails.
        """
        query = (
            f"SELECT id, parent_id, name FROM {cms_tables.TC_FOLDERS} "
            "WHERE project_id = ? ORDER BY parent_id, id"
        )
        rows = await self._db.run_query(query, (project_id,))

        return [
            {'id': folder_id, 'parent_id': parent_id, 'name': name}
            for folder_id, parent_id, name in (rows or [])
        ]

    async def folder_name_exists(self,
                                 project_id: int,
                                 parent_id: Optional[int],
                                 name: str,
                                 exclude_id: Optional[int] = None) -> bool:
        """Return True if a sibling folder with the given name already exists.

        Case-sensitive match against folders sharing the same project and
        parent. SQL ``NULL`` never equals ``NULL``, so root-level folders
        (``parent_id IS NULL``) are compared with an explicit ``IS NULL``
        clause rather than ``= ?``.

        Args:
            project_id:  Project the folder belongs to.
            parent_id:   Parent folder ID, or None for a root-level folder.
            name:        Folder name to check.
            exclude_id:  ID of the folder being updated (excluded from the
                         check), or None when creating a new folder.

        Returns:
            True if the name is already taken by a sibling folder.

        Raises:
            SqliteInterfaceException: If the database query fails.
        """
        parent_clause = "parent_id IS NULL" if parent_id is None \
            else "parent_id = ?"
        params: list = [project_id]
        if parent_id is not None:
            params.append(parent_id)
        params.append(name)

        query = (
            f"SELECT 1 FROM {cms_tables.TC_FOLDERS} "
            f"WHERE project_id = ? AND {parent_clause} AND name = ?"
        )

        if exclude_id is not None:
            query += " AND id != ?"
            params.append(exclude_id)

        query += " LIMIT 1"

        row = await self._db.run_query(query, tuple(params), fetch_one=True)
        return bool(row)

    async def add_folder(self,
                         project_id: int,
                         parent_id: Optional[int],
                         name: str) -> int:
        """Insert a new folder and return its ID.

        Args:
            project_id: Project the folder belongs to.
            parent_id:  Parent folder ID, or None for a root-level folder.
            name:       Folder name.

        Returns:
            The ID of the newly inserted folder row.

        Raises:
            SqliteInterfaceException: If the database insert fails.
        """
        query = (
            f"INSERT INTO {cms_tables.TC_FOLDERS} "
            "(project_id, parent_id, name) VALUES (?, ?, ?)"
        )
        return await self._db.insert_query(
            query, (project_id, parent_id, name))

    async def update_folder_name(self, folder_id: int, name: str) -> None:
        """Rename an existing folder.

        Args:
            folder_id: ID of the folder to rename.
            name:      New folder name.

        Raises:
            SqliteInterfaceException: If the database update fails.
        """
        query = f"UPDATE {cms_tables.TC_FOLDERS} SET name = ? WHERE id = ?"
        await self._db.run_query(query, (name, folder_id), commit=True)

    async def update_folder_parent(self,
                                   folder_id: int,
                                   parent_id: Optional[int]) -> None:
        """Move a folder under another folder, or to the top level.

        Args:
            folder_id: ID of the folder to move.
            parent_id: ID of the new parent folder, or None to make the
                       folder a root-level folder.

        Raises:
            SqliteInterfaceException: If the database update fails.
        """
        query = (
            f"UPDATE {cms_tables.TC_FOLDERS} SET parent_id = ? WHERE id = ?"
        )
        await self._db.run_query(query, (parent_id, folder_id), commit=True)

    async def is_in_subtree(self, root_id: int, folder_id: int) -> bool:
        """Return True if a folder is the root of a subtree, or inside it.

        Used to refuse moving a folder into itself or into one of its own
        descendants, which would cut the subtree off from the rest of the
        tree.

        Args:
            root_id:   ID of the folder at the top of the subtree.
            folder_id: ID of the folder to look for.

        Returns:
            True if ``folder_id`` is ``root_id`` itself or any folder
            beneath it, however deeply nested.

        Raises:
            SqliteInterfaceException: If the database query fails.
        """
        query = (
            "WITH RECURSIVE subtree(id) AS ("
            f"SELECT id FROM {cms_tables.TC_FOLDERS} WHERE id = ? "
            "UNION ALL "
            f"SELECT f.id FROM {cms_tables.TC_FOLDERS} f "
            "JOIN subtree s ON f.parent_id = s.id) "
            "SELECT 1 FROM subtree WHERE id = ? LIMIT 1")
        row = await self._db.run_query(
            query, (root_id, folder_id), fetch_one=True)
        return bool(row)

    async def count_testcases_in_subtree(self, folder_id: int) -> int:
        """Count the test cases in a folder and all of its descendants.

        Args:
            folder_id: ID of the folder at the top of the subtree.

        Returns:
            The number of test cases in the folder itself and in every
            folder beneath it, however deeply nested.

        Raises:
            SqliteInterfaceException: If the database query fails.
        """
        query = (
            "WITH RECURSIVE subtree(id) AS ("
            f"SELECT id FROM {cms_tables.TC_FOLDERS} WHERE id = ? "
            "UNION ALL "
            f"SELECT f.id FROM {cms_tables.TC_FOLDERS} f "
            "JOIN subtree s ON f.parent_id = s.id) "
            f"SELECT COUNT(*) FROM {cms_tables.TC_TEST_CASES} "
            "WHERE folder_id IN (SELECT id FROM subtree)")
        row = await self._db.run_query(query, (folder_id,), fetch_one=True)
        return int(row[0]) if row else 0

    async def delete_folder(self, folder_id: int,
                            cascade: bool = False) -> int:
        """Delete a folder, refusing if it would also destroy test cases.

        Child folders are always removed with it (``ON DELETE CASCADE``). The
        test cases in the folder and its descendants are removed the same
        way, which is why this refuses by default: unless ``cascade`` is
        true, nothing is deleted if any test case sits anywhere in the
        subtree.

        The refusal is part of the delete itself, not a count followed by a
        delete: the delete runs as one transaction (``BEGIN IMMEDIATE``)
        guarded on there being no test cases in the subtree, so a test case
        added after the count cannot be wiped out by a delete that was
        approved without it. If the guarded delete does nothing, the folder
        is still there and the caller is told how many test cases blocked it.

        ``folder_id`` is coerced with ``int()`` before being formatted into
        the script (executescript takes no bound parameters).

        Args:
            folder_id: ID of the folder to delete.
            cascade:   True to delete the subtree's test cases as well.

        Returns:
            0 if the folder was deleted, otherwise the number of test cases
            in its subtree that stopped the delete (always above zero).

        Raises:
            SqliteInterfaceException: If any database operation fails.
        """
        if cascade:
            query = f"DELETE FROM {cms_tables.TC_FOLDERS} WHERE id = ?"
            await self._db.run_query(query, (folder_id,), commit=True)
            return 0

        blocking = await self.count_testcases_in_subtree(folder_id)
        if blocking:
            return blocking

        folder_id = int(folder_id)
        folders = cms_tables.TC_FOLDERS
        await self._db.run_script(
            "BEGIN IMMEDIATE;"
            f"DELETE FROM {folders} WHERE id = {folder_id} "
            f"AND NOT EXISTS (SELECT 1 FROM {cms_tables.TC_TEST_CASES} "
            "WHERE folder_id IN (WITH RECURSIVE subtree(id) AS ("
            f"SELECT id FROM {folders} WHERE id = {folder_id} "
            "UNION ALL "
            f"SELECT f.id FROM {folders} f "
            "JOIN subtree s ON f.parent_id = s.id) "
            "SELECT id FROM subtree));"
            "COMMIT;")

        still_there = await self._db.run_query(
            f"SELECT 1 FROM {folders} WHERE id = ?",
            (folder_id,), fetch_one=True)
        if still_there:
            # A test case arrived after the count, and the guard held. There
            # is at least one now.
            return max(await self.count_testcases_in_subtree(folder_id), 1)

        return 0
