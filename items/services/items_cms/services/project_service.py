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
from typing import Any, NamedTuple, Optional
from weaver_framework.database.sqlite_interface import SqliteInterfaceException
from items.shared.service_state import ServiceState
from items.services.items_cms.repositories.project_repository import ProjectRepository


class ProjectResult(NamedTuple):
    """
    Outcome of a project service operation.

    Attributes:
        success:     True if the operation completed without error.
        data:        Operation payload on success (project dict, list, or
                     new project ID depending on the operation).
        error_msg:   Human-readable error description when success is False.
        is_internal: True when the failure is a server-side fault (maps to
                     HTTP 500); False when it is a client-side fault (HTTP 400).
    """
    success: bool
    data: Optional[Any] = None
    error_msg: str = ""
    is_internal: bool = False


class ProjectService:
    """
    Business logic for the projects domain.

    Mediates between route handlers and the project repository. All
    database exceptions are caught here; callers receive a ProjectResult
    describing success or failure without needing to know about the
    underlying storage layer.
    """

    def __init__(self,
                 logger: logging.Logger,
                 state: ServiceState,
                 repository: ProjectRepository) -> None:
        self._logger = logger.getChild(__name__)
        self._state = state
        self._repository = repository

    # ------------------------------------------------------------------
    # Read operations
    # ------------------------------------------------------------------

    def get_project(self, project_id: int) -> ProjectResult:
        """Retrieve full details for a single project.

        Args:
            project_id: ID of the project to retrieve.

        Returns:
            ProjectResult with data set to the project dict on success,
            or an appropriate error result if not found or a DB failure
            occurs.
        """
        if not self._state.is_available():
            return ProjectResult(success=False,
                                 error_msg="Service unavailable",
                                 is_internal=True)

        try:
            details = self._repository.get_project_details(project_id)
        except SqliteInterfaceException as ex:
            self._logger.exception(
                "Database failure retrieving project %d: %s", project_id, ex)
            self._state.mark_database_failed()
            return ProjectResult(success=False,
                                 error_msg="Internal error in CMS",
                                 is_internal=True)

        if details is None:
            return ProjectResult(success=False, error_msg="Project not found")

        return ProjectResult(success=True, data=details)

    def list_projects(self,
                      value_fields: list[str],
                      count_milestones: bool,
                      count_test_runs: bool) -> ProjectResult:
        """Retrieve all active projects with optional metric counts.

        Args:
            value_fields:      Validated column names to include in each
                               project entry (e.g. ["name"]). The id column
                               is always included by the repository.
            count_milestones:  When True, include a no_of_milestones count
                               for each project.
            count_test_runs:   When True, include a no_of_test_runs count
                               for each project.

        Returns:
            ProjectResult with data set to a list of project dicts on
            success, or an error result on DB failure.
        """
        if not self._state.is_available():
            return ProjectResult(success=False,
                                 error_msg="Service unavailable",
                                 is_internal=True)

        try:
            rows = self._repository.get_projects(value_fields)
        except SqliteInterfaceException as ex:
            self._logger.exception(
                "Database failure listing projects: %s", ex)
            self._state.mark_database_failed()
            return ProjectResult(success=False,
                                 error_msg="Internal error in CMS",
                                 is_internal=True)

        all_fields = ["id"] + value_fields
        projects = []

        for row in rows:
            project = dict(zip(all_fields, row))

            if count_milestones:
                project["no_of_milestones"] = (
                    self._repository.get_no_of_milestones_for_project(
                        project["id"]))

            if count_test_runs:
                project["no_of_test_runs"] = (
                    self._repository.get_no_of_testruns_for_project(
                        project["id"]))

            projects.append(project)

        return ProjectResult(success=True, data=projects)

    # ------------------------------------------------------------------
    # Write operations
    # ------------------------------------------------------------------

    def create_project(self,
                       name: str,
                       announcement: str,
                       announcement_on_overview: bool) -> ProjectResult:
        """Create a new project.

        Rejects the request if a project with the same name already exists.

        Args:
            name:                     Project name (must be unique).
            announcement:             Announcement text (may be empty).
            announcement_on_overview: Whether to display the announcement
                                      on the project overview page.

        Returns:
            ProjectResult with data set to the new project ID on success,
            a conflict error if the name is taken, or an internal error on
            DB failure.
        """
        if not self._state.is_available():
            return ProjectResult(success=False,
                                 error_msg="Service unavailable",
                                 is_internal=True)

        try:
            exists = self._repository.project_name_exists(name)
        except SqliteInterfaceException as ex:
            self._logger.exception(
                "Database failure checking project name: %s", ex)
            self._state.mark_database_failed()
            return ProjectResult(success=False,
                                 error_msg="Internal error in CMS",
                                 is_internal=True)

        if exists:
            return ProjectResult(success=False,
                                 error_msg="Project name already exists")

        try:
            new_id = self._repository.add_project(
                name, announcement, announcement_on_overview)
        except SqliteInterfaceException as ex:
            self._logger.exception(
                "Database failure creating project: %s", ex)
            self._state.mark_database_failed()
            return ProjectResult(success=False,
                                 error_msg="Internal SQL error in CMS",
                                 is_internal=True)

        return ProjectResult(success=True, data=new_id)

    def modify_project(self,
                       project_id: int,
                       name: str,
                       announcement: str,
                       announcement_on_overview: bool) -> ProjectResult:
        """Update the details of an existing project.

        If the name has changed, checks that the new name is not already
        taken by another project before applying the update.

        Args:
            project_id:               ID of the project to update.
            name:                     New project name.
            announcement:             Updated announcement text.
            announcement_on_overview: Whether to display the announcement
                                      on the project overview page.

        Returns:
            ProjectResult indicating success, a client error (invalid ID
            or name conflict), or an internal error on DB failure.
        """
        if not self._state.is_available():
            return ProjectResult(success=False,
                                 error_msg="Service unavailable",
                                 is_internal=True)

        try:
            existing = self._repository.get_project_details(project_id)
        except SqliteInterfaceException as ex:
            self._logger.exception(
                "Database failure retrieving project %d for update: %s",
                project_id, ex)
            self._state.mark_database_failed()
            return ProjectResult(success=False,
                                 error_msg="Internal error: Cannot get project details",
                                 is_internal=True)

        if existing is None:
            return ProjectResult(success=False, error_msg="Invalid project ID")

        new_name: Optional[str] = None
        if name != existing["name"]:
            try:
                name_taken = self._repository.project_name_exists(name)
            except SqliteInterfaceException as ex:
                self._logger.exception(
                    "Database failure checking project name: %s", ex)
                self._state.mark_database_failed()
                return ProjectResult(success=False,
                                     error_msg="Internal error: Cannot check project name",
                                     is_internal=True)

            if name_taken:
                return ProjectResult(success=False,
                                     error_msg="New project name already exists")

            new_name = name

        try:
            self._repository.modify_project(
                project_id, announcement, announcement_on_overview, new_name)
        except SqliteInterfaceException as ex:
            self._logger.exception(
                "Database failure modifying project %d: %s", project_id, ex)
            self._state.mark_database_failed()
            return ProjectResult(success=False,
                                 error_msg="Internal error modifying project",
                                 is_internal=True)

        return ProjectResult(success=True)

    def delete_project(self,
                       project_id: int,
                       hard_delete: bool) -> ProjectResult:
        """Delete or soft-delete a project.

        A soft delete marks the project as awaiting purge; a hard delete
        permanently removes it from the database.

        Args:
            project_id:  ID of the project to delete.
            hard_delete: When True, permanently delete the project.
                         When False, mark it as awaiting purge.

        Returns:
            ProjectResult indicating success, a client error (invalid ID),
            or an internal error on DB failure.
        """
        if not self._state.is_available():
            return ProjectResult(success=False,
                                 error_msg="Service unavailable",
                                 is_internal=True)

        try:
            exists = self._repository.is_valid_project_id(project_id)
        except SqliteInterfaceException as ex:
            self._logger.exception(
                "Database failure checking project ID %d: %s", project_id, ex)
            self._state.mark_database_failed()
            return ProjectResult(success=False,
                                 error_msg="Internal error in CMS",
                                 is_internal=True)

        if not exists:
            return ProjectResult(success=False,
                                 error_msg="Project id is invalid")

        try:
            if hard_delete:
                self._logger.info("Hard-deleting project %d", project_id)
                self._repository.hard_delete_project(project_id)
            else:
                self._logger.info(
                    "Marking project %d as awaiting purge", project_id)
                self._repository.mark_project_for_purge(project_id)

        except SqliteInterfaceException as ex:
            self._logger.exception(
                "Database failure deleting project %d: %s", project_id, ex)
            self._state.mark_database_failed()
            return ProjectResult(success=False,
                                 error_msg="Internal error in CMS",
                                 is_internal=True)

        return ProjectResult(success=True)
