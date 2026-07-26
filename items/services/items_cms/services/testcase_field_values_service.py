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
from dataclasses import dataclass
from typing import Optional
from weaver_framework.database.sqlite_interface import SqliteInterfaceException
from items.services.items_cms.services.service_result import ServiceResult
from items.services.items_cms.services.testcase_field_value_validation import (
    validate_value,
)
from items.shared.service_state import ServiceState
from items.services.items_cms.repositories.testcase_field_values_repository import (
    TestcaseFieldValuesRepository,
)


@dataclass(slots=True)
class TestcaseFieldValuesResult(ServiceResult):
    """Outcome of a testcase field values service operation.

    Extends ServiceResult to represent the outcome of operations within
    the testcase field values domain.
    """


class TestcaseFieldValuesService:
    """
    Business logic for the per-test-case custom field values domain.

    Mediates between route handlers and the field values repository. All
    database exceptions are caught here; callers receive a
    TestcaseFieldValuesResult describing success or failure without needing
    to know about the underlying storage layer.
    """

    def __init__(self,
                 logger: logging.Logger,
                 state: ServiceState,
                 repository: TestcaseFieldValuesRepository) -> None:
        self._logger = logger.getChild(__name__)
        self._state = state
        self._repository = repository

    async def get_field_values(self, case_id: int) -> TestcaseFieldValuesResult:
        """Retrieve every applicable custom field and its value for a test case.

        Fields with no stored value fall back to their configured default
        value. Results are ordered by each field's display position.

        Args:
            case_id: ID of the test case to retrieve values for.

        Returns:
            TestcaseFieldValuesResult with data set to a list of
            ``{field_id, field_name, field_type, position, is_required,
            value}`` dicts on success, a not-found error if the test case
            doesn't exist, or an internal error on DB failure.
        """
        if not self._state.is_available():
            return TestcaseFieldValuesResult(success=False,
                                             error_msg="Service unavailable",
                                             is_internal=True)

        project_id = await self._get_testcase_project_id(case_id)
        if isinstance(project_id, TestcaseFieldValuesResult):
            return project_id

        try:
            fields = await self._repository.get_applicable_fields(project_id)
        except SqliteInterfaceException as ex:
            self._logger.exception(
                "Database failure retrieving fields for project %d: %s",
                project_id, ex)
            self._state.mark_database_failed()
            return TestcaseFieldValuesResult(success=False,
                                             error_msg="Internal error in CMS",
                                             is_internal=True)

        try:
            stored = await self._repository.get_field_values(case_id)
        except SqliteInterfaceException as ex:
            self._logger.exception(
                "Database failure retrieving field values for testcase "
                "%d: %s", case_id, ex)
            self._state.mark_database_failed()
            return TestcaseFieldValuesResult(success=False,
                                             error_msg="Internal error in CMS",
                                             is_internal=True)

        data = [
            {
                "field_id": field["id"],
                "field_name": field["field_name"],
                "field_type": field["field_type"],
                "position": field["position"],
                "is_required": field["is_required"],
                "value": stored.get(field["id"], field["default_value"]),
            }
            for field in fields
        ]

        return TestcaseFieldValuesResult(success=True, data=data)

    async def set_field_values(
            self,
            case_id: int,
            values: dict[int, str]) -> TestcaseFieldValuesResult:
        """Set one or more custom field values for a test case.

        Only the fields present in ``values`` are affected — omitted fields
        keep whatever value (or default) they already had. Each field must
        be applicable to the test case's project; values are checked
        against the field's ``is_required`` flag and, where the field type
        has a well-defined format (Integer, Checkbox, Date, Url (Link)),
        against that format too. All values are validated before any
        writes happen.

        Args:
            case_id: ID of the test case to update.
            values:  Mapping of field_id to the new value string.

        Returns:
            TestcaseFieldValuesResult indicating success, a not-found error
            if the test case doesn't exist, a bad-request error if any
            field is inapplicable or fails validation, or an internal
            error on DB failure.
        """
        if not self._state.is_available():
            return TestcaseFieldValuesResult(success=False,
                                             error_msg="Service unavailable",
                                             is_internal=True)

        project_id = await self._get_testcase_project_id(case_id)
        if isinstance(project_id, TestcaseFieldValuesResult):
            return project_id

        try:
            fields = await self._repository.get_applicable_fields(project_id)
        except SqliteInterfaceException as ex:
            self._logger.exception(
                "Database failure retrieving fields for project %d: %s",
                project_id, ex)
            self._state.mark_database_failed()
            return TestcaseFieldValuesResult(success=False,
                                             error_msg="Internal error in CMS",
                                             is_internal=True)

        fields_by_id = {field["id"]: field for field in fields}

        validation_error = self._validate_values(fields_by_id, values)
        if validation_error is not None:
            return TestcaseFieldValuesResult(success=False,
                                             error_msg=validation_error)

        try:
            for field_id, value in values.items():
                exists = await self._repository.value_row_exists(
                    case_id, field_id)
                if exists:
                    await self._repository.update_field_value(
                        case_id, field_id, value)
                else:
                    await self._repository.insert_field_value(
                        case_id, field_id, value)
        except SqliteInterfaceException as ex:
            self._logger.exception(
                "Database failure writing field values for testcase %d: %s",
                case_id, ex)
            self._state.mark_database_failed()
            return TestcaseFieldValuesResult(success=False,
                                             error_msg="Internal error in CMS",
                                             is_internal=True)

        return TestcaseFieldValuesResult(success=True)

    @staticmethod
    def _validate_values(fields_by_id: dict[int, dict],
                         values: dict[int, str]) -> Optional[str]:
        """Validate every field_id/value pair before any writes happen.

        Args:
            fields_by_id: Field definitions applicable to the test case's
                          project, keyed by field_id.
            values:       Mapping of field_id to the new value string.

        Returns:
            A human-readable error message for the first invalid entry
            found, or None if every entry is valid.
        """
        for field_id, value in values.items():
            field = fields_by_id.get(field_id)
            if field is None:
                return (f"Field {field_id} does not apply to this test "
                        "case's project")

            if field["is_required"] and not value.strip():
                return f"{field['field_name']} is required"

            if value.strip():
                error = validate_value(field["field_type"], value)
                if error is not None:
                    return f"{field['field_name']}: {error}"

        return None

    async def _get_testcase_project_id(self, case_id: int):
        """Look up a test case's project ID, wrapping failures as a result.

        Args:
            case_id: ID of the test case to look up.

        Returns:
            The project ID (int) on success, or a TestcaseFieldValuesResult
            describing the failure (not-found or internal error).
        """
        try:
            project_id = await self._repository.get_testcase_project_id(
                case_id)
        except SqliteInterfaceException as ex:
            self._logger.exception(
                "Database failure retrieving testcase %d: %s", case_id, ex)
            self._state.mark_database_failed()
            return TestcaseFieldValuesResult(success=False,
                                             error_msg="Internal error in CMS",
                                             is_internal=True)

        if project_id is None:
            return TestcaseFieldValuesResult(success=False,
                                             error_msg="Test case not found",
                                             not_found=True)

        return project_id
