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
from items.services.items_cms.repositories.testcase_custom_fields_repository import (
    TestcaseCustomFieldsRepository,
    CustomFieldMoveDirection,
)


@dataclass(slots=True)
class TestcaseCustomFieldResult(ServiceResult):
    """Outcome of a testcase custom field service operation.

    Extends ServiceResult with an ``is_conflict`` flag to distinguish
    resource-conflict failures (HTTP 409) from generic client errors
    (HTTP 400).
    """
    is_conflict: bool = field(default=False)


class TestcaseCustomFieldsService:
    """
    Business logic for the testcase custom fields domain.

    Mediates between route handlers and the testcase custom fields
    repository. All database exceptions are caught here; callers receive a
    TestcaseCustomFieldResult describing success or failure without needing
    to know about the underlying storage layer.
    """

    def __init__(self,
                 logger: logging.Logger,
                 state: ServiceState,
                 repository: TestcaseCustomFieldsRepository) -> None:
        self._logger = logger.getChild(__name__)
        self._state = state
        self._repository = repository

    # ------------------------------------------------------------------
    # Read operations
    # ------------------------------------------------------------------

    async def get_custom_field(self, field_id: int) -> TestcaseCustomFieldResult:
        """Retrieve full details for a single custom field.

        Args:
            field_id: ID of the custom field to retrieve.

        Returns:
            TestcaseCustomFieldResult with data set to the field row on
            success, a not_found result if no field has that ID, or an
            internal error result on DB failure.
        """
        if not self._state.is_available():
            return TestcaseCustomFieldResult(success=False,
                                             error_msg="Service unavailable",
                                             is_internal=True)

        try:
            row = await self._repository.get_custom_field(field_id)
        except SqliteInterfaceException as ex:
            self._logger.exception(
                "Database failure retrieving custom field %d: %s", field_id, ex)
            self._state.mark_database_failed()
            return TestcaseCustomFieldResult(success=False,
                                             error_msg="Internal error in CMS",
                                             is_internal=True)

        if row is None:
            return TestcaseCustomFieldResult(success=False,
                                             error_msg="Custom field not found",
                                             not_found=True)

        return TestcaseCustomFieldResult(success=True, data=row)

    async def get_custom_fields(
            self,
            project_id: Optional[int] = None) -> TestcaseCustomFieldResult:
        """Retrieve custom field definitions, optionally filtered by project.

        Args:
            project_id: If provided, return only fields applicable to this
                        project. If None, return all fields.

        Returns:
            TestcaseCustomFieldResult with data set to a list of field rows
            on success, or an error result on DB failure.
        """
        if not self._state.is_available():
            return TestcaseCustomFieldResult(success=False,
                                             error_msg="Service unavailable",
                                             is_internal=True)

        if project_id is not None:
            try:
                exists = await self._repository.is_valid_project_id(project_id)
            except SqliteInterfaceException as ex:
                self._logger.exception(
                    "Database failure validating project %d: %s", project_id, ex)
                self._state.mark_database_failed()
                return TestcaseCustomFieldResult(success=False,
                                                 error_msg="Internal error in CMS",
                                                 is_internal=True)

            if not exists:
                return TestcaseCustomFieldResult(success=False,
                                                 error_msg="Project id is invalid",
                                                 not_found=True)

        try:
            if project_id is not None:
                rows = await self._repository.get_fields_for_project(project_id)
            else:
                rows = await self._repository.get_all_fields()
        except SqliteInterfaceException as ex:
            self._logger.exception(
                "Database failure retrieving custom fields: %s", ex)
            self._state.mark_database_failed()
            return TestcaseCustomFieldResult(success=False,
                                             error_msg="Internal error in CMS",
                                             is_internal=True)

        return TestcaseCustomFieldResult(success=True, data=rows)

    # ------------------------------------------------------------------
    # Write operations
    # ------------------------------------------------------------------

    async def add_custom_field(self,
                               field_name: str,
                               description: str,
                               system_name: str,
                               field_type: str,
                               enabled: bool,
                               is_required: bool,
                               default_value: str,
                               applies_to_all_projects: bool,
                               projects: Optional[list[str]] = None
                               ) -> TestcaseCustomFieldResult:
        """Create a new testcase custom field.

        Validates uniqueness of ``field_name`` and ``system_name`` before
        inserting. When ``applies_to_all_projects`` is False, links the new
        field to the specified project names.

        Args:
            field_name:              Display name (must be unique).
            description:             Human-readable description.
            system_name:             Internal identifier (must be unique).
            field_type:              Type name; must exist in the DB types table.
            enabled:                 Whether the field is active.
            is_required:             Whether the field must be filled in.
            default_value:           Default value string (may be empty).
            applies_to_all_projects: If True, no project list is needed.
            projects:                Project names to link (required when
                                     ``applies_to_all_projects`` is False).

        Returns:
            TestcaseCustomFieldResult with data set to the new field ID on
            success, or an appropriate error result on failure.
        """
        # pylint: disable=too-many-arguments, too-many-positional-arguments

        if not self._state.is_available():
            return TestcaseCustomFieldResult(success=False,
                                             error_msg="Service unavailable",
                                             is_internal=True)

        error, project_ids = await self._validate_add_request(
            field_name, system_name, applies_to_all_projects, projects)
        if error is not None:
            return error

        try:
            field_id = await self._repository.add_custom_field(
                field_name=field_name,
                description=description,
                system_name=system_name,
                field_type=field_type,
                enabled=enabled,
                is_required=is_required,
                default_value=default_value,
                applies_to_all_projects=applies_to_all_projects)
        except SqliteInterfaceException as ex:
            self._logger.exception(
                "Database failure adding custom field '%s': %s", field_name, ex)
            self._state.mark_database_failed()
            return TestcaseCustomFieldResult(success=False,
                                             error_msg="Internal error in CMS",
                                             is_internal=True)

        if field_id is None:
            return TestcaseCustomFieldResult(
                success=False,
                error_msg=f"Unknown field type '{field_type}'")

        if project_ids:
            try:
                await self._repository.assign_custom_field_to_projects(
                    field_id, project_ids)
            except SqliteInterfaceException as ex:
                self._logger.exception(
                    "Database failure assigning field %d to projects: %s",
                    field_id, ex)
                self._state.mark_database_failed()
                return TestcaseCustomFieldResult(success=False,
                                                 error_msg="Internal error in CMS",
                                                 is_internal=True)

        return TestcaseCustomFieldResult(success=True, data=field_id)

    async def _validate_add_request(
            self,
            field_name: str,
            system_name: str,
            applies_to_all_projects: bool,
            projects: Optional[list[str]]
    ) -> tuple[Optional[TestcaseCustomFieldResult], list[int]]:
        """Validate a custom field creation request before any writes.

        Checks name uniqueness, system name uniqueness, and resolves project
        names to IDs. All checks are read-only — no data is written.

        Args:
            field_name:              Display name to check for uniqueness.
            system_name:             System name to check for uniqueness.
            applies_to_all_projects: If True, project list is not checked.
            projects:                Project names to resolve (when not global).

        Returns:
            A tuple of ``(error_result, project_ids)``. On success,
            ``error_result`` is None and ``project_ids`` contains the resolved
            IDs (empty list when ``applies_to_all_projects`` is True). On
            failure, ``error_result`` is set and ``project_ids`` is empty.
        """
        # pylint: disable=too-many-return-statements

        empty: list[int] = []

        try:
            name_taken = await self._repository.custom_field_name_exists(
                field_name)
        except SqliteInterfaceException as ex:
            self._logger.exception(
                "Database failure checking field name uniqueness: %s", ex)
            self._state.mark_database_failed()
            return (TestcaseCustomFieldResult(success=False,
                                              error_msg="Internal error in CMS",
                                              is_internal=True), empty)

        if name_taken:
            return (TestcaseCustomFieldResult(
                success=False,
                error_msg=f"Custom field name '{field_name}' already exists",
                is_conflict=True), empty)

        try:
            system_name_taken = await self._repository.system_name_exists(
                system_name)
        except SqliteInterfaceException as ex:
            self._logger.exception(
                "Database failure checking system name uniqueness: %s", ex)
            self._state.mark_database_failed()
            return (TestcaseCustomFieldResult(success=False,
                                              error_msg="Internal error in CMS",
                                              is_internal=True), empty)

        if system_name_taken:
            return (TestcaseCustomFieldResult(
                success=False,
                error_msg=f"System name '{system_name}' already exists",
                is_conflict=True), empty)

        if applies_to_all_projects:
            return (None, empty)

        if not projects:
            return (TestcaseCustomFieldResult(
                success=False,
                error_msg="projects is required when applies_to_all_projects "
                          "is false"), empty)

        if len(projects) != len(set(projects)):
            return (TestcaseCustomFieldResult(
                success=False,
                error_msg="Duplicate project names in the request"), empty)

        try:
            resolved = await self._repository.resolve_project_names(projects)
        except SqliteInterfaceException as ex:
            self._logger.exception(
                "Database failure resolving project names: %s", ex)
            self._state.mark_database_failed()
            return (TestcaseCustomFieldResult(success=False,
                                              error_msg="Internal error in CMS",
                                              is_internal=True), empty)

        if resolved is None:
            return (TestcaseCustomFieldResult(
                success=False,
                error_msg="One or more project names are invalid"), empty)

        return (None, resolved)

    async def update_custom_field(self,
                                   field_id: int,
                                   field_name: str,
                                   description: str,
                                   system_name: str,
                                   field_type: str,
                                   enabled: bool,
                                   is_required: bool,
                                   default_value: str,
                                   applies_to_all_projects: bool,
                                   projects: Optional[list[str]] = None
                                   ) -> TestcaseCustomFieldResult:
        """Update an existing testcase custom field.

        Validates uniqueness of ``field_name`` and ``system_name`` against
        other fields (excluding the field being updated). Replaces project
        associations when ``applies_to_all_projects`` is False.

        Args:
            field_id:                ID of the field to update.
            field_name:              New display name (must be unique).
            description:             New human-readable description.
            system_name:             New internal identifier (must be unique).
            field_type:              New type name; must exist in types table.
            enabled:                 Whether the field should be active.
            is_required:             Whether the field must be filled in.
            default_value:           New default value (may be empty string).
            applies_to_all_projects: If True, removes per-project links.
            projects:                Project names to link when not global.

        Returns:
            TestcaseCustomFieldResult indicating success, not_found if no
            field has that ID, conflict if name/system_name is taken, or an
            appropriate error result on failure.
        """
        # pylint: disable=too-many-arguments, too-many-positional-arguments

        if not self._state.is_available():
            return TestcaseCustomFieldResult(success=False,
                                             error_msg="Service unavailable",
                                             is_internal=True)

        if not self._repository.is_valid_custom_field_id(field_id):
            return TestcaseCustomFieldResult(success=False,
                                             error_msg="Custom field not found",
                                             not_found=True)

        error, project_ids = await self._validate_update_request(
            field_id, field_name, system_name, applies_to_all_projects,
            projects)
        if error is not None:
            return error

        try:
            updated = await self._repository.update_custom_field(
                field_id=field_id,
                field_name=field_name,
                description=description,
                system_name=system_name,
                field_type=field_type,
                enabled=enabled,
                is_required=is_required,
                default_value=default_value,
                applies_to_all_projects=applies_to_all_projects,
                project_ids=project_ids)
        except SqliteInterfaceException as ex:
            self._logger.exception(
                "Database failure updating custom field %d: %s", field_id, ex)
            self._state.mark_database_failed()
            return TestcaseCustomFieldResult(success=False,
                                             error_msg="Internal error in CMS",
                                             is_internal=True)

        if updated is False:
            return TestcaseCustomFieldResult(success=False,
                                             error_msg="Custom field not found",
                                             not_found=True)

        if updated is None:
            return TestcaseCustomFieldResult(
                success=False,
                error_msg="System custom fields cannot be modified")

        return TestcaseCustomFieldResult(success=True)

    async def _validate_update_request(
            self,
            field_id: int,
            field_name: str,
            system_name: str,
            applies_to_all_projects: bool,
            projects: Optional[list[str]]
    ) -> tuple[Optional[TestcaseCustomFieldResult], list[int]]:
        """Validate a custom field update request before any writes.

        Checks name and system name uniqueness against other fields, then
        resolves project names to IDs. All checks are read-only.

        Args:
            field_id:                ID of the field being updated.
            field_name:              New display name to check for uniqueness.
            system_name:             New system name to check for uniqueness.
            applies_to_all_projects: If True, project list is not checked.
            projects:                Project names to resolve (when not global).

        Returns:
            A tuple of ``(error_result, project_ids)``. On success,
            ``error_result`` is None. On failure, ``error_result`` is set
            and ``project_ids`` is empty.
        """
        # pylint: disable=too-many-arguments, too-many-positional-arguments
        # pylint: disable=too-many-return-statements

        empty: list[int] = []

        try:
            name_taken = await self._repository.custom_field_name_exists(
                field_name, exclude_id=field_id)
        except SqliteInterfaceException as ex:
            self._logger.exception(
                "Database failure checking field name uniqueness: %s", ex)
            self._state.mark_database_failed()
            return (TestcaseCustomFieldResult(success=False,
                                              error_msg="Internal error in CMS",
                                              is_internal=True), empty)

        if name_taken:
            return (TestcaseCustomFieldResult(
                success=False,
                error_msg=f"Custom field name '{field_name}' already exists",
                is_conflict=True), empty)

        try:
            system_name_taken = await self._repository.system_name_exists(
                system_name, exclude_id=field_id)
        except SqliteInterfaceException as ex:
            self._logger.exception(
                "Database failure checking system name uniqueness: %s", ex)
            self._state.mark_database_failed()
            return (TestcaseCustomFieldResult(success=False,
                                              error_msg="Internal error in CMS",
                                              is_internal=True), empty)

        if system_name_taken:
            return (TestcaseCustomFieldResult(
                success=False,
                error_msg=f"System name '{system_name}' already exists",
                is_conflict=True), empty)

        if applies_to_all_projects:
            return (None, empty)

        if not projects:
            return (TestcaseCustomFieldResult(
                success=False,
                error_msg="projects is required when applies_to_all_projects "
                          "is false"), empty)

        if len(projects) != len(set(projects)):
            return (TestcaseCustomFieldResult(
                success=False,
                error_msg="Duplicate project names in the request"), empty)

        try:
            resolved = await self._repository.resolve_project_names(projects)
        except SqliteInterfaceException as ex:
            self._logger.exception(
                "Database failure resolving project names: %s", ex)
            self._state.mark_database_failed()
            return (TestcaseCustomFieldResult(success=False,
                                              error_msg="Internal error in CMS",
                                              is_internal=True), empty)

        if resolved is None:
            return (TestcaseCustomFieldResult(
                success=False,
                error_msg="One or more project names are invalid"), empty)

        return (None, resolved)

    async def delete_custom_field(self, field_id: int) -> TestcaseCustomFieldResult:
        """Permanently remove a custom field and all its dependent data.

        Args:
            field_id: ID of the custom field to delete.

        Returns:
            TestcaseCustomFieldResult indicating success, not_found if no
            field has that ID, or an internal error result on DB failure.
        """
        if not self._state.is_available():
            return TestcaseCustomFieldResult(success=False,
                                             error_msg="Service unavailable",
                                             is_internal=True)

        try:
            deleted = await self._repository.delete_custom_field(field_id)
        except SqliteInterfaceException as ex:
            self._logger.exception(
                "Database failure deleting custom field %d: %s", field_id, ex)
            self._state.mark_database_failed()
            return TestcaseCustomFieldResult(success=False,
                                             error_msg="Internal error in CMS",
                                             is_internal=True)

        if deleted is False:
            return TestcaseCustomFieldResult(success=False,
                                             error_msg="Custom field not found",
                                             not_found=True)

        if deleted is None:
            return TestcaseCustomFieldResult(
                success=False,
                error_msg="System custom fields cannot be deleted")

        return TestcaseCustomFieldResult(success=True)

    async def move_custom_field(self,
                                field_id: int,
                                direction: str) -> TestcaseCustomFieldResult:
        """Change the display order of a custom field.

        Args:
            field_id:  ID of the field to move.
            direction: ``"up"`` to decrease the position, ``"down"`` to
                       increase it.

        Returns:
            TestcaseCustomFieldResult indicating success, not_found if the
            field does not exist or is already at the boundary, or an
            internal error on DB failure.
        """
        if not self._state.is_available():
            return TestcaseCustomFieldResult(success=False,
                                             error_msg="Service unavailable",
                                             is_internal=True)

        move_direction = (CustomFieldMoveDirection.UP
                          if direction == "up"
                          else CustomFieldMoveDirection.DOWN)

        try:
            moved = await self._repository.move_custom_field(
                field_id, move_direction)
        except SqliteInterfaceException as ex:
            self._logger.exception(
                "Database failure moving custom field %d: %s", field_id, ex)
            self._state.mark_database_failed()
            return TestcaseCustomFieldResult(success=False,
                                             error_msg="Internal error in CMS",
                                             is_internal=True)

        if moved is False:
            return TestcaseCustomFieldResult(
                success=False,
                error_msg="Custom field not found",
                not_found=True)

        if moved is None:
            return TestcaseCustomFieldResult(
                success=False,
                error_msg="Custom field is already at the boundary")

        return TestcaseCustomFieldResult(success=True)
