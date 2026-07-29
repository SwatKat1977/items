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
from items.services.items_identity.data_access.user_repository import (
    UserRepository)
from items.services.items_identity.identity_configuration import (
    IdentityConfiguration)
from items.services.items_identity.routes.users.schemas import (
    SCHEMA_GET_USER_PROFILE_REQUEST)
from items.services.items_identity.services.user_profile_service import (
    UserProfileResult, UserProfileService)
from items.shared.service_state import ServiceState


class GetUserProfileHandler(BaseApiRoute):
    """Handles requests for a user's profile details.

    Returns the profile fields a caller needs in order to know who a user is
    and what they may do - notably ``is_administrator``, which the gateway
    stores against the session so the web portal can gate the administration
    pages.
    """

    def __init__(self,
                 logger: logging.Logger,
                 service_state: ServiceState,
                 configuration: IdentityConfiguration) -> None:
        """Initialise the user profile handler.

        Args:
            logger:        Logger used for diagnostic messages.
            service_state: Shared service state used to determine
                availability.
            configuration: Identity service configuration.
        """
        self._logger = logger.getChild(__name__)
        self._service_state: ServiceState = service_state

        user_repository: UserRepository = UserRepository(self._logger,
                                                         configuration)
        self._profile_service: UserProfileService = UserProfileService(
            self._logger, self._service_state, user_repository)

    @validate_json(SCHEMA_GET_USER_PROFILE_REQUEST)
    async def get_user_profile(self, request_msg: ApiResponse) -> Response:
        """Retrieve a user's profile by email address.

        The email address is supplied in the request body rather than the URL.
        This matches the existing session and authentication endpoints, and
        keeps the address out of URLs and access logs.

        Args:
            request_msg: Validated request containing ``email_address``.

        Returns:
            200 with the user's profile on success.
            404 if no user exists with that email address.
            503 if the service is unavailable or the database failed.
        """
        email_address: str = request_msg.body["email_address"]

        result: UserProfileResult = \
            await self._profile_service.get_profile_by_email(email_address)

        if not result.available:
            return Response(
                json.dumps({"error": "Service unavailable"}),
                status=HTTPStatus.SERVICE_UNAVAILABLE,
                content_type="application/json")

        if not result.found:
            return Response(
                json.dumps({"error": "User not found"}),
                status=HTTPStatus.NOT_FOUND,
                content_type="application/json")

        return Response(
            json.dumps(result.profile),
            status=HTTPStatus.OK,
            content_type="application/json")
