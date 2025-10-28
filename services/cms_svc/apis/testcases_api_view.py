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
import http
import json
import logging
import quart
from base_view import ApiResponse, BaseView, validate_json
import interfaces.cms.testcases as json_schemas
from sql.sql_interface import SqlInterface
from state_object import StateObject


class TestCasesApiView(BaseView):
    """
    API view for handling test case-related requests.

    Provides endpoints to retrieve test case overviews and details
    for a specific project. All requests are validated against predefined
    JSON schemas before processing.
    """
    __slots__ = ['_logger']

    def __init__(self, logger: logging.Logger,
                 state_object: StateObject) -> None:
        """
        Initialize the TestCasesApiView.

        Args:
            logger (logging.Logger): The application logger instance.
            state_object (StateObject): Shared application state containing
                                        configuration or runtime data.
        """
        self._logger = logger.getChild(__name__)
        self._db: SqlInterface = SqlInterface(logger, state_object)

    @validate_json(json_schemas.SCHEMA_TESTCASES_DETAILS_REQUEST)
    async def testcase_details(self, request_msg: ApiResponse):
        """
        Retrieve test case overviews for a given project.

        Args:
            request_msg (ApiResponse): The incoming request object, expected
                                       to contain a valid `project_id` in the
                                       body.

        Returns:
            quart.Response: A JSON response containing a list of test case
                            overviews, or an error message if the project ID is
                            invalid.
        """
        project_id: int = request_msg.body.project_id

        if not self._db.projects.is_valid_project_id(project_id):
            response_json = {
                'status': 0,
                'error': "Invalid project id"
            }
            return quart.Response(json.dumps(response_json),
                                  status=http.HTTPStatus.INTERNAL_SERVER_ERROR,
                                  content_type="application/json")

        test_suites: list = self._db.testcases.get_testcase_overviews(project_id)

        test_suites = [] if not test_suites else test_suites
        return quart.Response(json.dumps(test_suites),
                              status=http.HTTPStatus.OK,
                              content_type="application/json")

    @validate_json(json_schemas.SCHEMA_TESTCASES_CASE_REQUEST)
    async def testcase_get_case(self, request_msg: ApiResponse, case_id: int):
        """
        Retrieve the full details of a specific test case.

        Args:
            request_msg (ApiResponse): The incoming request object, containing
            `                          project_id` in the body.
            case_id (int): The unique ID of the test case to retrieve.

        Returns:
            quart.Response: A JSON response containing the test case details,
                            or an error message if the case is not found or an
                            internal error occurs.
        """
        project_id: int = request_msg.body.project_id

        case_details: dict = self._db.testcases.get_testcase(case_id, project_id)

        if case_details is None:
            response_json = {
                'status': 0,
                'error': "Internal error"
            }
            return quart.Response(json.dumps(response_json),
                                  status=http.HTTPStatus.INTERNAL_SERVER_ERROR,
                                  content_type="application/json")

        return quart.Response(json.dumps(case_details),
                              status=http.HTTPStatus.OK,
                              content_type="application/json")
