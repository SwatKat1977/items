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
from items.services.items_cms.repositories.testcase_repository import TestcaseRepository


@dataclass(slots=True)
class TestcaseResult(ServiceResult):
    """Outcome of a testcase service operation.

    Extends ServiceResult with an ``is_conflict`` flag to distinguish
    resource-conflict failures (HTTP 409, e.g. a duplicate sibling name)
    from generic client errors (HTTP 400).
    """
    is_conflict: bool = field(default=False)


class TestcaseService:
    """
    Business logic for the testcases domain.

    Mediates between route handlers and the testcase repository. All
    database exceptions are caught here; callers receive a TestcaseResult
    describing success or failure without needing to know about the
    underlying storage layer.
    """

    def __init__(self,
                 logger: logging.Logger,
                 state: ServiceState,
                 repository: TestcaseRepository) -> None:
        self._logger = logger.getChild(__name__)
        self._state = state
        self._repository = repository

    async def list_testcases(self, project_id: int) -> TestcaseResult:
        """Retrieve the folder hierarchy and test case stubs for a project.

        Args:
            project_id: ID of the project to list test cases for.

        Returns:
            TestcaseResult with data set to a dict containing ``folders``
            and ``test_cases`` lists on success, or an error result on
            DB failure.
        """
        if not self._state.is_available():
            return TestcaseResult(success=False,
                                  error_msg="Service unavailable",
                                  is_internal=True)

        try:
            exists = await self._repository.is_valid_project_id(project_id)
        except SqliteInterfaceException as ex:
            self._logger.exception(
                "Database failure validating project %d: %s", project_id, ex)
            self._state.mark_database_failed()
            return TestcaseResult(success=False,
                                  error_msg="Internal error in CMS",
                                  is_internal=True)

        if not exists:
            return TestcaseResult(success=False,
                                  error_msg="Project id is invalid",
                                  not_found=True)

        try:
            data = await self._repository.get_testcases(project_id)
        except SqliteInterfaceException as ex:
            self._logger.exception(
                "Database failure listing testcases for project %d: %s",
                project_id, ex)
            self._state.mark_database_failed()
            return TestcaseResult(success=False,
                                  error_msg="Internal error in CMS",
                                  is_internal=True)

        return TestcaseResult(success=True, data=data)

    async def get_testcase(self, case_id: int) -> TestcaseResult:
        """Retrieve full details for a single test case.

        Args:
            case_id: ID of the test case to retrieve.

        Returns:
            TestcaseResult with data set to the test case dict on success,
            or an appropriate error result if not found or a DB failure
            occurs.
        """
        if not self._state.is_available():
            return TestcaseResult(success=False,
                                  error_msg="Service unavailable",
                                  is_internal=True)

        try:
            testcase = await self._repository.get_testcase(case_id)
        except SqliteInterfaceException as ex:
            self._logger.exception(
                "Database failure retrieving testcase %d: %s", case_id, ex)
            self._state.mark_database_failed()
            return TestcaseResult(success=False,
                                  error_msg="Internal error in CMS",
                                  is_internal=True)

        if testcase is None:
            return TestcaseResult(success=False,
                                  error_msg="Test case not found",
                                  not_found=True)

        return TestcaseResult(success=True, data=testcase)

    # ------------------------------------------------------------------
    # Write operations
    # ------------------------------------------------------------------

    async def create_testcase(self,
                              project_id: int,
                              folder_id: Optional[int],
                              name: str,
                              description: str) -> TestcaseResult:
        """Create a new test case.

        Args:
            project_id:  Project the test case belongs to.
            folder_id:   Folder ID, or None for a root-level test case.
            name:        Test case name. Must be unique among siblings.
            description: Test case description.

        Returns:
            TestcaseResult with data set to the new test case ID on
            success, a not-found error if the project or folder doesn't
            exist, a conflict error if the name is taken, or an internal
            error on DB failure.
        """
        # pylint: disable=too-many-return-statements

        if not self._state.is_available():
            return TestcaseResult(success=False,
                                  error_msg="Service unavailable",
                                  is_internal=True)

        try:
            project_exists = await self._repository.is_valid_project_id(
                project_id)
        except SqliteInterfaceException as ex:
            self._logger.exception(
                "Database failure validating project %d: %s", project_id, ex)
            self._state.mark_database_failed()
            return TestcaseResult(success=False,
                                  error_msg="Internal error in CMS",
                                  is_internal=True)

        if not project_exists:
            return TestcaseResult(success=False,
                                  error_msg="Project id is invalid",
                                  not_found=True)

        if folder_id is not None:
            try:
                folder_project_id = \
                    await self._repository.get_folder_project_id(folder_id)
            except SqliteInterfaceException as ex:
                self._logger.exception(
                    "Database failure validating folder %d: %s",
                    folder_id, ex)
                self._state.mark_database_failed()
                return TestcaseResult(success=False,
                                      error_msg="Internal error in CMS",
                                      is_internal=True)

            if folder_project_id is None:
                return TestcaseResult(success=False,
                                      error_msg="Folder id is invalid",
                                      not_found=True)

            if folder_project_id != project_id:
                return TestcaseResult(
                    success=False,
                    error_msg="Folder does not belong to the specified "
                             "project")

        try:
            name_taken = await self._repository.testcase_name_exists(
                project_id, folder_id, name)
        except SqliteInterfaceException as ex:
            self._logger.exception(
                "Database failure checking testcase name: %s", ex)
            self._state.mark_database_failed()
            return TestcaseResult(success=False,
                                  error_msg="Internal error in CMS",
                                  is_internal=True)

        if name_taken:
            return TestcaseResult(success=False,
                                  error_msg="Test case name already exists",
                                  is_conflict=True)

        try:
            new_id = await self._repository.add_testcase(
                project_id, folder_id, name, description)
        except SqliteInterfaceException as ex:
            self._logger.exception(
                "Database failure creating testcase: %s", ex)
            self._state.mark_database_failed()
            return TestcaseResult(success=False,
                                  error_msg="Internal SQL error in CMS",
                                  is_internal=True)

        return TestcaseResult(success=True, data=new_id)

    async def update_testcase(self,
                              case_id: int,
                              name: str,
                              description: str) -> TestcaseResult:
        """Rename and/or update the description of an existing test case.

        Args:
            case_id:     ID of the test case to update.
            name:        New test case name. Must be unique among siblings.
            description: New test case description.

        Returns:
            TestcaseResult indicating success, a not-found error if the
            test case doesn't exist, a conflict error if the name is
            taken by a sibling, or an internal error on DB failure.
        """
        # pylint: disable=too-many-return-statements

        if not self._state.is_available():
            return TestcaseResult(success=False,
                                  error_msg="Service unavailable",
                                  is_internal=True)

        try:
            existing = await self._repository.get_testcase(case_id)
        except SqliteInterfaceException as ex:
            self._logger.exception(
                "Database failure retrieving testcase %d for update: %s",
                case_id, ex)
            self._state.mark_database_failed()
            return TestcaseResult(success=False,
                                  error_msg="Internal error in CMS",
                                  is_internal=True)

        if existing is None:
            return TestcaseResult(success=False,
                                  error_msg="Test case not found",
                                  not_found=True)

        if name != existing["name"]:
            try:
                name_taken = await self._repository.testcase_name_exists(
                    existing["project_id"], existing["folder_id"], name,
                    exclude_id=case_id)
            except SqliteInterfaceException as ex:
                self._logger.exception(
                    "Database failure checking testcase name: %s", ex)
                self._state.mark_database_failed()
                return TestcaseResult(success=False,
                                      error_msg="Internal error in CMS",
                                      is_internal=True)

            if name_taken:
                return TestcaseResult(
                    success=False,
                    error_msg="Test case name already exists",
                    is_conflict=True)

        try:
            await self._repository.update_testcase(
                case_id, name, description)
        except SqliteInterfaceException as ex:
            self._logger.exception(
                "Database failure updating testcase %d: %s", case_id, ex)
            self._state.mark_database_failed()
            return TestcaseResult(success=False,
                                  error_msg="Internal error modifying "
                                           "testcase",
                                  is_internal=True)

        return TestcaseResult(success=True)

    async def delete_testcase(self, case_id: int) -> TestcaseResult:
        """Delete a test case.

        Args:
            case_id: ID of the test case to delete.

        Returns:
            TestcaseResult indicating success, a not-found error if the
            test case doesn't exist, or an internal error on DB failure.
        """
        if not self._state.is_available():
            return TestcaseResult(success=False,
                                  error_msg="Service unavailable",
                                  is_internal=True)

        try:
            exists = await self._repository.get_testcase(case_id)
        except SqliteInterfaceException as ex:
            self._logger.exception(
                "Database failure checking testcase %d: %s", case_id, ex)
            self._state.mark_database_failed()
            return TestcaseResult(success=False,
                                  error_msg="Internal error in CMS",
                                  is_internal=True)

        if exists is None:
            return TestcaseResult(success=False,
                                  error_msg="Test case not found",
                                  not_found=True)

        try:
            await self._repository.delete_testcase(case_id)
        except SqliteInterfaceException as ex:
            self._logger.exception(
                "Database failure deleting testcase %d: %s", case_id, ex)
            self._state.mark_database_failed()
            return TestcaseResult(success=False,
                                  error_msg="Internal error in CMS",
                                  is_internal=True)

        return TestcaseResult(success=True)
