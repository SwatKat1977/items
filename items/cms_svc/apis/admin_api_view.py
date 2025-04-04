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
from base_view import BaseView
from sqlite_interface import CustomFieldMoveDirection, SqliteInterface

class AdminApiView(BaseView):
    __slots__ = ['_logger']

    def __init__(self, logger: logging.Logger, db: SqliteInterface) -> None:
        self._logger = logger.getChild(__name__)
        self._db: SqliteInterface = db

    async def add_testcase_custom_field(self):
        ...

    async def move_testcase_custom_field(self, field_id: int):

        self._db.move_test_case_custom_field(10, CustomFieldMoveDirection.UP)

''''
        return await view.add_testcase_custom_field()

    logger.info("=> admin/move_testcase_custom_field_position [POST]")

    @blueprint.route('/admin/move_testcase_custom_field_position',
                     methods=['POST'])
    async def move_testcase_custom_field_position_request():
        return await move_testcase_custom_field_position_field()

'''