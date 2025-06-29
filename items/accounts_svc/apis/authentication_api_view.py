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
from http import HTTPStatus
import json
import logging
from quart import Response
from account_logon_type import AccountLogonType
import interfaces.accounts.basic_authentication as basic_auth
from base_view import ApiResponse, BaseView, validate_json
from state_object import StateObject
from sql.sqlite_interface import SqliteInterface


class AuthenticationApiView(BaseView):
    """
    Provides API endpoints related to user authentication for the service.

    This class handles authentication logic including validating credentials
    for different authentication mechanisms such as basic authentication.
    It uses the provided logger for logging and an instance of SqliteInterface
    to interact with the underlying SQLite database.

    Attributes:
        _logger (logging.Logger): Logger instance for recording operational details.
        _db (SqliteInterface): Interface to handle database interactions.
    """

    def __init__(self, logger: logging.Logger,
                 state_object: StateObject) -> None:
        self._logger = logger.getChild(__name__)
        self._db: SqliteInterface = SqliteInterface(logger, state_object)

    @validate_json(basic_auth.SCHEMA_BASIC_AUTHENTICATE_REQUEST)
    async def authenticate_basic(self, request_msg: ApiResponse):
        """
        Handles authentication requests for basic authentication.

        This method validates the JSON request body against a predefined schema,
        checks the user's logon type, and attempts to authenticate the user.
        It returns an appropriate JSON response based on the success or failure
        of the authentication process.

        Workflow:
        1. Validates the request body against `SCHEMA_BASIC_AUTHENTICATE_REQUEST`.
        2. Checks if the user is valid for logon using the provided email and logon type.
        3. Authenticates the user by verifying their credentials.
        4. Returns a JSON response indicating the authentication status.

        Returns:
            Response: A Flask `Response` object with:
                - `status`: 1 if authentication is successful, otherwise 0.
                - `error`: An error message if authentication fails, otherwise an empty string.
                - HTTP status codes:
                    - `200 OK` for successful responses.
                    - `500 Internal Server Error` for validation or query failures.

        Exceptions:
            - Returns a 500 response if the JSON validation or SQL query encounters errors.

        Example Response (Successful Authentication):
            {
                "status": 1,
                "error": ""
            }

        Example Response (Failure):
            {
                "status": 0,
                "error": "Invalid credentials"
            }

        Example Usage:
            ```
            response = await authenticate()
            print(response.get_data(as_text=True))  # Access JSON response as a string
            ```

        Note:
            - The method uses `self._sql_interface` for database interactions.
            - Relies on `basic_auth.SCHEMA_BASIC_AUTHENTICATE_REQUEST` for request validation.
        """
        query_result = self._db.valid_user_to_logon(
            request_msg.body.email_address, AccountLogonType.BASIC.value)
        user_id, err_str = query_result

        if user_id is None:
            response_json = {
                'status': 0,
                'error': "Internal server error"
            }
            return Response(json.dumps(response_json),
                            status=HTTPStatus.INTERNAL_SERVER_ERROR,
                            content_type="application/json")

        if user_id:
            status, err_str = self._db.basic_user_authenticate(
                user_id, request_msg.body.password)

            response_json = {
                'status':  1 if status else 0,
                'error': '' if status else err_str
            }
            return Response(json.dumps(response_json), status=HTTPStatus.OK,
                            content_type="application/json")

        response_json = {
            'status': 0,
            'error': err_str
        }
        return Response(json.dumps(response_json), status=HTTPStatus.OK,
                        content_type="application/json")
