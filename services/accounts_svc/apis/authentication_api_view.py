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
import json
import logging
from quart import Response
import interfaces.accounts.basic_authentication as basic_auth
from base_view import ApiResponse, BaseView, validate_json
from services.authentication_service import AuthenticationService
from data_access.user_data_access_layer import UserDataAccessLayer
from items_common.service_state import ServiceState


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

    def __init__(self,
                 logger: logging.Logger,
                 service_state: ServiceState) -> None:
        self._logger = logger.getChild(__name__)
        user_dal = UserDataAccessLayer(service_state, logger)
        self._auth_service = AuthenticationService(self._logger, user_dal)

    @validate_json(basic_auth.SCHEMA_BASIC_AUTHENTICATE_REQUEST)
    async def authenticate_basic(self, request_msg: ApiResponse):
        """
        Handles basic authentication requests (HTTP layer).
        """
        status_code, response_json = self._auth_service.authenticate_basic(
            email=request_msg.body.email_address,
            password=request_msg.body.password
        )
        return Response(
            json.dumps(response_json),
            status=status_code,
            content_type="application/json"
        )
