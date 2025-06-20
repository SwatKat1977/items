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
    __slots__ = ['_logger']

    def __init__(self, logger: logging.Logger,
                 state_object: StateObject) -> None:
        self._logger = logger.getChild(__name__)
        self._db: SqlInterface = SqlInterface(logger, state_object)

    @validate_json(json_schemas.SCHEMA_TESTCASES_DETAILS_REQUEST)
    async def testcase_details(self, request_msg: ApiResponse):
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
        project_id: int = request_msg.body.project_id

        case_details: dict = self._db.testcases.get_testcase(case_id, project_id)

        if not case_details:
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
