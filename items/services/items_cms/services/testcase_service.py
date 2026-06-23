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
from items.services.items_cms.repositories.testcase_repository import TestcaseRepository


class TestcaseResult(NamedTuple):
    """
    Outcome of a testcase service operation.

    Attributes:
        success:     True if the operation completed without error.
        data:        Operation payload on success.
        error_msg:   Human-readable error description when success is False.
        is_internal: True when the failure is a server-side fault (maps to
                     HTTP 500); False when it is a client-side fault.
        not_found:   True when the requested resource does not exist (maps
                     to HTTP 404). Only meaningful when success is False and
                     is_internal is False.
    """
    success: bool
    data: Optional[Any] = None
    error_msg: str = ""
    is_internal: bool = False
    not_found: bool = False


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

    def list_testcases(self, project_id: int) -> TestcaseResult:
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
            data = self._repository.get_testcases(project_id)
        except SqliteInterfaceException as ex:
            self._logger.exception(
                "Database failure listing testcases for project %d: %s",
                project_id, ex)
            self._state.mark_database_failed()
            return TestcaseResult(success=False,
                                  error_msg="Internal error in CMS",
                                  is_internal=True)

        return TestcaseResult(success=True, data=data)

    def get_testcase(self, case_id: int) -> TestcaseResult:
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
            testcase = self._repository.get_testcase(case_id)
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
