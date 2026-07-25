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
from dataclasses import dataclass, field
from typing import Optional
from weaver_framework.database.sqlite_interface import SqliteInterfaceException
from items.services.items_cms.services.service_result import ServiceResult
from items.shared.service_state import ServiceState
from items.services.items_cms.repositories.folder_repository import (
    FolderRepository)


@dataclass(slots=True)
class FolderResult(ServiceResult):
    """Outcome of a folder service operation.

    Extends ServiceResult with an ``is_conflict`` flag to distinguish
    resource-conflict failures (HTTP 409, e.g. a duplicate sibling name)
    from generic client errors (HTTP 400).
    """
    is_conflict: bool = field(default=False)


class FolderService:
    """
    Business logic for the testcase folders domain.

    Mediates between route handlers and the folder repository. All
    database exceptions are caught here; callers receive a FolderResult
    describing success or failure without needing to know about the
    underlying storage layer.
    """

    def __init__(self,
                 logger: logging.Logger,
                 state: ServiceState,
                 repository: FolderRepository) -> None:
        self._logger = logger.getChild(__name__)
        self._state = state
        self._repository = repository

    # ------------------------------------------------------------------
    # Read operations
    # ------------------------------------------------------------------

    async def get_folder(self, folder_id: int) -> FolderResult:
        """Retrieve full details for a single folder.

        Args:
            folder_id: ID of the folder to retrieve.

        Returns:
            FolderResult with data set to the folder dict on success,
            or an appropriate error result if not found or a DB failure
            occurs.
        """
        if not self._state.is_available():
            return FolderResult(success=False,
                                error_msg="Service unavailable",
                                is_internal=True)

        try:
            folder = await self._repository.get_folder(folder_id)
        except SqliteInterfaceException as ex:
            self._logger.exception(
                "Database failure retrieving folder %d: %s", folder_id, ex)
            self._state.mark_database_failed()
            return FolderResult(success=False,
                                error_msg="Internal error in CMS",
                                is_internal=True)

        if folder is None:
            return FolderResult(success=False,
                                error_msg="Folder not found",
                                not_found=True)

        return FolderResult(success=True, data=folder)

    async def list_folders(self, project_id: int) -> FolderResult:
        """Retrieve every folder belonging to a project.

        Args:
            project_id: ID of the project to query.

        Returns:
            FolderResult with data set to a list of folder dicts on
            success, a not-found error if the project doesn't exist, or
            an internal error on DB failure.
        """
        if not self._state.is_available():
            return FolderResult(success=False,
                                error_msg="Service unavailable",
                                is_internal=True)

        try:
            exists = await self._repository.is_valid_project_id(project_id)
        except SqliteInterfaceException as ex:
            self._logger.exception(
                "Database failure validating project %d: %s", project_id, ex)
            self._state.mark_database_failed()
            return FolderResult(success=False,
                                error_msg="Internal error in CMS",
                                is_internal=True)

        if not exists:
            return FolderResult(success=False,
                                error_msg="Project id is invalid",
                                not_found=True)

        try:
            folders = await self._repository.get_folders(project_id)
        except SqliteInterfaceException as ex:
            self._logger.exception(
                "Database failure listing folders for project %d: %s",
                project_id, ex)
            self._state.mark_database_failed()
            return FolderResult(success=False,
                                error_msg="Internal error in CMS",
                                is_internal=True)

        return FolderResult(success=True, data=folders)

    # ------------------------------------------------------------------
    # Write operations
    # ------------------------------------------------------------------

    async def create_folder(self,
                            project_id: int,
                            parent_id: Optional[int],
                            name: str) -> FolderResult:
        """Create a new folder.

        Args:
            project_id: Project the folder belongs to.
            parent_id:  Parent folder ID, or None for a root-level folder.
            name:       Folder name. Must be unique among siblings.

        Returns:
            FolderResult with data set to the new folder ID on success, a
            not-found error if the project or parent folder doesn't
            exist, a conflict error if the name is taken, or an internal
            error on DB failure.
        """
        # pylint: disable=too-many-return-statements

        if not self._state.is_available():
            return FolderResult(success=False,
                                error_msg="Service unavailable",
                                is_internal=True)

        try:
            project_exists = await self._repository.is_valid_project_id(
                project_id)
        except SqliteInterfaceException as ex:
            self._logger.exception(
                "Database failure validating project %d: %s", project_id, ex)
            self._state.mark_database_failed()
            return FolderResult(success=False,
                                error_msg="Internal error in CMS",
                                is_internal=True)

        if not project_exists:
            return FolderResult(success=False,
                                error_msg="Project id is invalid",
                                not_found=True)

        if parent_id is not None:
            try:
                parent = await self._repository.get_folder(parent_id)
            except SqliteInterfaceException as ex:
                self._logger.exception(
                    "Database failure validating parent folder %d: %s",
                    parent_id, ex)
                self._state.mark_database_failed()
                return FolderResult(success=False,
                                    error_msg="Internal error in CMS",
                                    is_internal=True)

            if parent is None:
                return FolderResult(success=False,
                                    error_msg="Parent folder id is invalid",
                                    not_found=True)

            if parent["project_id"] != project_id:
                return FolderResult(
                    success=False,
                    error_msg="Parent folder does not belong to the "
                             "specified project")

        try:
            name_taken = await self._repository.folder_name_exists(
                project_id, parent_id, name)
        except SqliteInterfaceException as ex:
            self._logger.exception(
                "Database failure checking folder name: %s", ex)
            self._state.mark_database_failed()
            return FolderResult(success=False,
                                error_msg="Internal error in CMS",
                                is_internal=True)

        if name_taken:
            return FolderResult(success=False,
                                error_msg="Folder name already exists",
                                is_conflict=True)

        try:
            new_id = await self._repository.add_folder(
                project_id, parent_id, name)
        except SqliteInterfaceException as ex:
            self._logger.exception(
                "Database failure creating folder: %s", ex)
            self._state.mark_database_failed()
            return FolderResult(success=False,
                                error_msg="Internal SQL error in CMS",
                                is_internal=True)

        return FolderResult(success=True, data=new_id)

    async def update_folder(self, folder_id: int, name: str) -> FolderResult:
        """Rename an existing folder.

        Args:
            folder_id: ID of the folder to rename.
            name:      New folder name. Must be unique among siblings.

        Returns:
            FolderResult indicating success, a not-found error if the
            folder doesn't exist, a conflict error if the name is taken
            by a sibling, or an internal error on DB failure.
        """
        # pylint: disable=too-many-return-statements

        if not self._state.is_available():
            return FolderResult(success=False,
                                error_msg="Service unavailable",
                                is_internal=True)

        try:
            existing = await self._repository.get_folder(folder_id)
        except SqliteInterfaceException as ex:
            self._logger.exception(
                "Database failure retrieving folder %d for update: %s",
                folder_id, ex)
            self._state.mark_database_failed()
            return FolderResult(success=False,
                                error_msg="Internal error in CMS",
                                is_internal=True)

        if existing is None:
            return FolderResult(success=False,
                                error_msg="Folder not found",
                                not_found=True)

        if name != existing["name"]:
            try:
                name_taken = await self._repository.folder_name_exists(
                    existing["project_id"], existing["parent_id"], name,
                    exclude_id=folder_id)
            except SqliteInterfaceException as ex:
                self._logger.exception(
                    "Database failure checking folder name: %s", ex)
                self._state.mark_database_failed()
                return FolderResult(success=False,
                                    error_msg="Internal error in CMS",
                                    is_internal=True)

            if name_taken:
                return FolderResult(success=False,
                                    error_msg="Folder name already exists",
                                    is_conflict=True)

        try:
            await self._repository.update_folder_name(folder_id, name)
        except SqliteInterfaceException as ex:
            self._logger.exception(
                "Database failure renaming folder %d: %s", folder_id, ex)
            self._state.mark_database_failed()
            return FolderResult(success=False,
                                error_msg="Internal error modifying folder",
                                is_internal=True)

        return FolderResult(success=True)

    async def delete_folder(self, folder_id: int) -> FolderResult:
        """Delete a folder.

        Child folders and their test cases are removed automatically via
        the database's ``ON DELETE CASCADE`` constraints.

        Args:
            folder_id: ID of the folder to delete.

        Returns:
            FolderResult indicating success, a not-found error if the
            folder doesn't exist, or an internal error on DB failure.
        """
        if not self._state.is_available():
            return FolderResult(success=False,
                                error_msg="Service unavailable",
                                is_internal=True)

        try:
            exists = await self._repository.get_folder(folder_id)
        except SqliteInterfaceException as ex:
            self._logger.exception(
                "Database failure checking folder %d: %s", folder_id, ex)
            self._state.mark_database_failed()
            return FolderResult(success=False,
                                error_msg="Internal error in CMS",
                                is_internal=True)

        if exists is None:
            return FolderResult(success=False,
                                error_msg="Folder not found",
                                not_found=True)

        try:
            await self._repository.delete_folder(folder_id)
        except SqliteInterfaceException as ex:
            self._logger.exception(
                "Database failure deleting folder %d: %s", folder_id, ex)
            self._state.mark_database_failed()
            return FolderResult(success=False,
                                error_msg="Internal error in CMS",
                                is_internal=True)

        return FolderResult(success=True)
