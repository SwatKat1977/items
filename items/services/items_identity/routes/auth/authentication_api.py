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
import logging
from quart import Blueprint
from weaver_framework.microservice.api_response import ApiResponse
from weaver_framework.microservice.base_api_route import BaseApiRoute
from weaver_framework.microservice.microservice_decorators import validate_json
from items.services.items_identity.data_access.user_data_access_layer import (
    UserDataAccessLayer)
from items.services.items_identity.routes.auth.schemas import (
    SCHEMA_AUTHENTICATE_REQUEST)
from items.shared.service_state import ServiceState


def create_blueprint(logger: logging.Logger,
                     service_state: ServiceState) -> Blueprint:
    """
    Creates and registers a Quart Blueprint for handling authentication.

    This function initializes a `View` object with the provided logger, and
    then defines an API endpoints for authentication.

    Args:
        logger (logging.Logger): A logger instance for logging messages.

    Returns:
        Blueprint: A Flask `Blueprint` object containing the registered route.
    """
    view = AuthenticationApiView(logger, service_state)

    blueprint = Blueprint('auth_api', __name__)

    logger.debug("Registering Authentication API routes:")

    logger.debug("=> /authentication/basic [POST]")

    # pylint: disable=no-value-for-parameter
    @blueprint.route('/basic', methods=['POST'])
    async def authenticate_basic_request():
        return await view.authenticate_basic()

    return blueprint


class AuthenticationApiView(BaseApiRoute):
    """
    Provides API endpoints related to user authentication for the service.

    This class handles authentication logic including validating credentials
    for different authentication mechanisms such as basic authentication.
    It uses the provided logger for logging and an instance of SqliteInterface
    to interact with the underlying SQLite database.

    Attributes:
        _logger (logging.Logger): Logger instance for recording operational details.
    """

    def __init__(self, logger: logging.Logger, service_state: ServiceState) -> None:
        self._logger = logger.getChild(__name__)
        self._service_state = service_state
        user_dal = UserDataAccessLayer(service_state, logger)
        self._auth_service = AuthenticationService(self._logger, user_dal)

    @validate_json(SCHEMA_AUTHENTICATE_REQUEST)
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
