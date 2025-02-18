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
from base_view import BaseView, validate_json
import interfaces.cms.testcases as json_schemas

class TestCasesApiView(BaseView):
    __slots__ = ['_logger']

    def __init__(self, logger: logging.Logger) -> None:
        self._logger = logger.getChild(__name__)

    @validate_json(json_schemas.SCHEMA_TESTCASES_DETAILS_REQUEST)
    async def testcase_details(self):
        ...