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
import logging
import quart
from sessions import Sessions
from base_view import ApiResponse, BaseView, validate_json
#import interfaces.gateway.testcase as json_schemas


class TestCaseApiView(BaseView):
    __slots__ = ['_logger']

    def __init__(self, logger: logging.Logger, sessions: Sessions) -> None:
        self._logger = logger.getChild(__name__)
        self._sessions: Sessions = sessions

    #@validate_json(json_schemas.SCHEMA_TESTCASES_DETAILS_REQUEST)
    async def testcase_details(self, request_msg: ApiResponse,
                               project_id: int) -> quart.Response:
        ...

    async def get_testcase(self, request_msg: ApiResponse,
                           project_id: int,
                           case_id: int) -> quart.Response:
        ...
