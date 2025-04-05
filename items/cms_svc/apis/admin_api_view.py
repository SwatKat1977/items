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
import typing

import quart
from base_view import BaseView
from sqlite_interface import CustomFieldMoveDirection, SqliteInterface

class AdminApiView(BaseView):
    __slots__ = ['_logger']

    def __init__(self, logger: logging.Logger, db: SqliteInterface) -> None:
        self._logger = logger.getChild(__name__)
        self._db: SqliteInterface = db

    async def add_testcase_custom_field(self):
        ...

    async def move_testcase_custom_field(self,
                                         field_id: int,
                                         direction: str):
        """
        Moves a custom field for a test case in the specified direction (up or
        down).

        Args:
            field_id (int): The ID of the custom field to be moved.
            direction (str): The direction in which to move the custom field.
                             Must be either 'up' or 'down'.

        Returns:
            quart.Response: A JSON response indicating the status of the
                            operation. The response will include a status of 1
                            for success or 0 for failure, along with an error
                            message if applicable.
                            The HTTP status code will reflect the outcome:
                            - 400 Bad Request for invalid direction.
                            - 500 Internal Server Error for unexpected issues.
                            - 200 OK for a successful or failed move operation.
        """
        if direction not in ('up', 'down'):
            body: dict = {
                "status": 0,
                "error": "Invalid direction. Must be 'up' or 'down'."
            }
            return quart.Response(json.dumps(body),
                                  status=http.HTTPStatus.BAD_REQUEST,
                                  content_type="application/json")

        direction_enum: CustomFieldMoveDirection = \
            CustomFieldMoveDirection.UP if direction == "up" \
            else CustomFieldMoveDirection.DOWN
        result = self._db.move_test_case_custom_field(field_id, direction_enum)

        if result is None:
            body: dict = {
                "status": 0,
                "error": "Internal error"
            }
            return quart.Response(json.dumps(body),
                                  status=http.HTTPStatus.INTERNAL_SERVER_ERROR,
                                  content_type="application/json")

        if result:
            body: dict = {
                "status": 1
            }
            return quart.Response(json.dumps(body),
                                  status=http.HTTPStatus.OK,
                                  content_type="application/json")

        body: dict = {
            "status": 0,
            "error": "Invalid field or move operation"
        }
        return quart.Response(json.dumps(body),
                              status=http.HTTPStatus.OK,
                              content_type="application/json")

''''
        return await view.add_testcase_custom_field()

    logger.info("=> admin/move_testcase_custom_field_position [POST]")

    @blueprint.route('/admin/move_testcase_custom_field_position',
                     methods=['POST'])
    async def move_testcase_custom_field_position_request():
        return await move_testcase_custom_field_position_field()

'''