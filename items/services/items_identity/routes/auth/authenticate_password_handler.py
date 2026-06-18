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
from http import HTTPStatus
import json
import logging
from quart import Response
from weaver_framework.microservice.api_response import ApiResponse
from weaver_framework.microservice.base_api_route import BaseApiRoute
from weaver_framework.microservice.microservice_decorators import validate_json
from items.services.items_identity.data_access.authentication_service import (
    AuthenticationService)
from items.services.items_identity.identity_configuration import IdentityConfiguration
from items.services.items_identity.data_access.user_repository import UserRepository
from items.services.items_identity.routes.auth.schemas import (
    SCHEMA_AUTHENTICATE_REQUEST)
from items.shared.service_state import ServiceState


class AuthenticatePasswordHandler(BaseApiRoute):
    """
    Provides API endpoints related to user authentication for the service.

    This class handles authentication logic including validating credentials
    for different authentication mechanisms such as basic authentication.
    It uses the provided logger for logging and an instance of SqliteInterface
    to interact with the underlying SQLite database.

    Attributes:
        _logger (logging.Logger): Logger instance for recording operational details.
    """

    def __init__(self,
                 logger: logging.Logger,
                 service_state: ServiceState,
                 configuration: IdentityConfiguration) -> None:
        self._logger = logger.getChild(__name__)
        self._service_state: ServiceState = service_state

        user_repository: UserRepository = UserRepository(self._logger,
                                                         configuration)
        self._auth_service: AuthenticationService = AuthenticationService(
            self._logger, self._service_state, user_repository)

    @validate_json(SCHEMA_AUTHENTICATE_REQUEST)
    async def authenticate_password(self, request_msg: ApiResponse) -> Response:
        """
        Handles password authentication requests.
        """
        print(request_msg.body)
        success, message = await self._auth_service.authenticate_password(
            email=request_msg.body['email_address'],
            password=request_msg.body['password'])

        response_json = {
            "success": success,
            "message": message
        }

        status_code = HTTPStatus.OK if success else HTTPStatus.UNAUTHORIZED

        return Response(
            json.dumps(response_json),
            status=status_code,
            content_type="application/json"
        )
