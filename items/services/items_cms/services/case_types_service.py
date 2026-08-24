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
from weaver_framework.database.sqlite_interface import SqliteInterfaceException
from items.services.items_cms.services.service_result import ServiceResult
from items.shared.service_state import ServiceState
from items.services.items_cms.repositories.case_types_repository import (
    CaseTypesRepository,
)


@dataclass(slots=True)
class CaseTypeResult(ServiceResult):
    """Outcome of a case type service operation.

    Extends ServiceResult with an ``is_conflict`` flag to distinguish
    resource-conflict failures (HTTP 409) from generic client errors
    (HTTP 400) - same shape as TestcaseCustomFieldResult.
    """
    is_conflict: bool = field(default=False)


class CaseTypesService:
    """
    Business logic for the case types domain.

    Mediates between route handlers and the case types repository. All
    database exceptions are caught here; callers receive a
    CaseTypeResult describing success or failure without needing to know
    about the underlying storage layer.
    """

    def __init__(self,
                 logger: logging.Logger,
                 state: ServiceState,
                 repository: CaseTypesRepository) -> None:
        self._logger = logger.getChild(__name__)
        self._state = state
        self._repository = repository

    # ------------------------------------------------------------------
    # Read operations
    # ------------------------------------------------------------------

    async def get_case_type(self, type_id: int) -> CaseTypeResult:
        """Retrieve a single case type.

        Args:
            type_id: ID of the case type to retrieve.

        Returns:
            CaseTypeResult with data set to the type row on success, a
            not_found result if no type has that ID, or an internal
            error result on DB failure.
        """
        if not self._state.is_available():
            return CaseTypeResult(success=False,
                                  error_msg="Service unavailable",
                                  is_internal=True)

        try:
            row = await self._repository.get_case_type(type_id)
        except SqliteInterfaceException as ex:
            self._logger.exception(
                "Database failure retrieving case type %d: %s", type_id, ex)
            self._state.mark_database_failed()
            return CaseTypeResult(success=False,
                                  error_msg="Internal error in CMS",
                                  is_internal=True)

        if row is None:
            return CaseTypeResult(success=False,
                                  error_msg="Case type not found",
                                  not_found=True)

        return CaseTypeResult(success=True, data=row)

    async def get_all_case_types(self) -> CaseTypeResult:
        """Retrieve every case type.

        Returns:
            CaseTypeResult with data set to a list of type rows on
            success, or an internal error result on DB failure.
        """
        if not self._state.is_available():
            return CaseTypeResult(success=False,
                                  error_msg="Service unavailable",
                                  is_internal=True)

        try:
            rows = await self._repository.get_all_case_types()
        except SqliteInterfaceException as ex:
            self._logger.exception(
                "Database failure retrieving case types: %s", ex)
            self._state.mark_database_failed()
            return CaseTypeResult(success=False,
                                  error_msg="Internal error in CMS",
                                  is_internal=True)

        return CaseTypeResult(success=True, data=rows)

    # ------------------------------------------------------------------
    # Write operations
    # ------------------------------------------------------------------

    async def add_case_type(self, name: str,
                            description: str) -> CaseTypeResult:
        """Create a new case type.

        Validates name uniqueness before inserting. Always created as
        non-default.

        Args:
            name:        Display name (must be unique, case-insensitive).
            description: Human-readable description (may be empty).

        Returns:
            CaseTypeResult with data set to the new type's ID on success,
            a conflict result if the name is taken, or an internal error
            result on DB failure.
        """
        if not self._state.is_available():
            return CaseTypeResult(success=False,
                                  error_msg="Service unavailable",
                                  is_internal=True)

        error = await self._check_name_available(name)
        if error is not None:
            return error

        try:
            type_id = await self._repository.add_case_type(name, description)
        except SqliteInterfaceException as ex:
            self._logger.exception(
                "Database failure adding case type '%s': %s", name, ex)
            self._state.mark_database_failed()
            return CaseTypeResult(success=False,
                                  error_msg="Internal error in CMS",
                                  is_internal=True)

        return CaseTypeResult(success=True, data=type_id)

    async def update_case_type(self,
                               type_id: int,
                               name: str,
                               description: str) -> CaseTypeResult:
        """Update a case type's name and description.

        Args:
            type_id:     ID of the case type to update.
            name:        New display name (must be unique, excluding this
                        type's own current name).
            description: New description (may be empty).

        Returns:
            CaseTypeResult indicating success, not_found if no type has
            that ID, a conflict result if the name is taken by another
            type, or an internal error result on DB failure.
        """
        if not self._state.is_available():
            return CaseTypeResult(success=False,
                                  error_msg="Service unavailable",
                                  is_internal=True)

        error = await self._check_name_available(name, exclude_id=type_id)
        if error is not None:
            return error

        try:
            updated = await self._repository.update_case_type(
                type_id, name, description)
        except SqliteInterfaceException as ex:
            self._logger.exception(
                "Database failure updating case type %d: %s", type_id, ex)
            self._state.mark_database_failed()
            return CaseTypeResult(success=False,
                                  error_msg="Internal error in CMS",
                                  is_internal=True)

        if not updated:
            return CaseTypeResult(success=False,
                                  error_msg="Case type not found",
                                  not_found=True)

        return CaseTypeResult(success=True)

    async def set_default_case_type(self, type_id: int) -> CaseTypeResult:
        """Make a case type the default, un-defaulting whichever held it.

        Args:
            type_id: ID of the case type to make the default.

        Returns:
            CaseTypeResult indicating success (including if the type was
            already the default), not_found if no type has that ID, or
            an internal error result on DB failure.
        """
        if not self._state.is_available():
            return CaseTypeResult(success=False,
                                  error_msg="Service unavailable",
                                  is_internal=True)

        try:
            updated = await self._repository.set_default_case_type(type_id)
        except SqliteInterfaceException as ex:
            self._logger.exception(
                "Database failure setting case type %d as default: %s",
                type_id, ex)
            self._state.mark_database_failed()
            return CaseTypeResult(success=False,
                                  error_msg="Internal error in CMS",
                                  is_internal=True)

        if not updated:
            return CaseTypeResult(success=False,
                                  error_msg="Case type not found",
                                  not_found=True)

        return CaseTypeResult(success=True)

    async def _check_name_available(
            self, name: str,
            exclude_id: int | None = None) -> CaseTypeResult | None:
        """Check a case type name isn't already taken.

        Args:
            name:       Display name to check.
            exclude_id: ID of the type being updated, if any (excluded
                       from the check).

        Returns:
            None if the name is available. Otherwise a CaseTypeResult
            describing the conflict or internal error to return
            immediately.
        """
        try:
            name_taken = await self._repository.case_type_name_exists(
                name, exclude_id=exclude_id)
        except SqliteInterfaceException as ex:
            self._logger.exception(
                "Database failure checking case type name uniqueness: %s", ex)
            self._state.mark_database_failed()
            return CaseTypeResult(success=False,
                                  error_msg="Internal error in CMS",
                                  is_internal=True)

        if name_taken:
            return CaseTypeResult(
                success=False,
                error_msg=f"Case type name '{name}' already exists",
                is_conflict=True)

        return None
