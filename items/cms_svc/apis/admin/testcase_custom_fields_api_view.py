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
import interfaces.cms.admin as json_schemas
from base_view import BaseView, validate_json, ApiResponse
from sql.sql_tc_custom_fields import CustomFieldMoveDirection
from sql.sql_interface import SqlInterface
from state_object import StateObject


class TestcaseCustomFieldsApiView(BaseView):
    """
    API view for managing custom fields associated with test cases.

    This class provides methods to handle API operations related to custom
    fields used in test case definitions or execution metadata.
    """
    __slots__ = ['_logger']

    def __init__(self, logger: logging.Logger,
                 state_object: StateObject) -> None:
        """
        Initialize the TestcaseCustomFieldsApiView.

        Args:
            logger (logging.Logger): The application-wide logger instance.
            state_object (StateObject): The state or configuration object used
                to initialize the database interface and other stateful components.

        Attributes:
            _logger (logging.Logger): Logger scoped to this class/module.
            _db (SqlInterface): Interface for interacting with the database.
        """
        self._logger = logger.getChild(__name__)
        self._db: SqlInterface = SqlInterface(logger, state_object)

    @validate_json(json_schemas.SCHEMA_ADD_TEST_CASE_CUSTOM_FIELD_REQUEST)
    async def add_custom_field(self, request_msg: ApiResponse):
        """
        Add a new custom field to the test case system.

        This endpoint validates the uniqueness of both the field name and
        system name, checks for duplicate project assignments, and adds the
        custom field to the database. If project assignments are specified,
        it associates the new custom field with those projects.

        Args:
            request_msg (ApiResponse): The API request containing the custom
            field details in the JSON body.

        Returns:
            quart.Response: A JSON response with a status flag indicating
            success or error, along with a message if applicable.
        """

        # Check to see if the field name is already in use, None means an
        # internal error and True means it already exists/
        field_name_exists = self._db.tc_custom_fields.custom_field_name_exists(
            request_msg.body.field_name)
        if field_name_exists is None:
            response_json = {
                'status': 0,
                'error': "Internal error"}
            return quart.Response(json.dumps(response_json),
                                  status=http.HTTPStatus.INTERNAL_SERVER_ERROR,
                                  content_type="application/json")

        if field_name_exists:
            response_json = {
                'status': 0,
                'error': "Duplicate field_name"}
            return quart.Response(json.dumps(response_json),
                                  status=http.HTTPStatus.OK,
                                  content_type="application/json")

        # Check to see if the system name is already in use, None means an
        # internal error and True means it already exists/
        system_name_exists = self._db.tc_custom_fields.system_name_exists(
            request_msg.body.system_name)
        if system_name_exists is None:
            response_json = {
                'status': 0,
                'error': "Internal error"}
            return quart.Response(json.dumps(response_json),
                                  status=http.HTTPStatus.INTERNAL_SERVER_ERROR,
                                  content_type="application/json")

        if system_name_exists:
            response_json = {
                'status': 0,
                'error': "Duplicate system_name"}
            return quart.Response(json.dumps(response_json),
                                  status=http.HTTPStatus.OK,
                                  content_type="application/json")
        if isinstance(request_msg.body.projects, list):
            if len(request_msg.body.projects) \
                    != len(set(request_msg.body.projects)):
                response_json = {
                    'status': 0,
                    'error': "Duplicate projects"}
                return quart.Response(json.dumps(response_json),
                                      status=http.HTTPStatus.BAD_REQUEST,
                                      content_type="application/json")

        custom_field_id: int = self._db.tc_custom_fields.add_custom_field(
            request_msg.body.field_name, request_msg.body.description,
            request_msg.body.system_name, request_msg.body.field_type,
            request_msg.body.enabled, request_msg.body.is_required,
            request_msg.body.default_value,
            request_msg.body.applies_to_all_projects)

        if not custom_field_id:
            response_json = {
                'status': 0,
                'error': "Internal error"}
            return quart.Response(json.dumps(response_json),
                                  status=http.HTTPStatus.INTERNAL_SERVER_ERROR,
                                  content_type="application/json")

        # ===========================================
        # TO BE DONE: Upon failing to add projects (if there are any) we should
        #             perform some form of roll-back on custom field add.
        # ===========================================

        if request_msg.body.projects and len(request_msg.body.projects):
            status = self._db.tc_custom_fields.assign_custom_field_to_project(
                custom_field_id, request_msg.body.projects)

        response_json = {
            'status': 1
        }
        return quart.Response(json.dumps(response_json),
                              status=http.HTTPStatus.OK,
                              content_type="application/json")

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
        result = self._db.tc_custom_fields.move_custom_field(field_id,
                                                             direction_enum)

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
