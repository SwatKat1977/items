"""
Copyright 2025-2026 Integrated Test Management Suite Development Team
Copyright 2017-2025 INTMAC Development Team [Defunct]

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
import uuid
from quart import Response
from weaver_framework.microservice.api_response import ApiResponse
from weaver_framework.microservice.base_api_route import BaseApiRoute
from weaver_framework.microservice.microservice_decorators import validate_json
from weaver_framework.microservice.rest_client import RestClient
from items.shared.account_logon_type import AccountLogonType
from items.services.items_gateway.sessions import Sessions
from items.services.items_gateway.gateway_configuration import (
    GatewayConfiguration)

SCHEMA_NEW_SESSION_PASSWORD_REQUEST: dict = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "SessionCreateRequest",
    "type": "object",
    "properties": {
        "email_address": {"type": "string", "minLength": 3},
        "password": {"type": "string", "minLength": 8}
    },
    "required": ["email_address", "password"],
    "additionalProperties": False
}


class NewSessionPasswordHandler(BaseApiRoute):
    """API handler for creating password-authenticated user sessions."""

    def __init__(self,
                 logger: logging.Logger,
                 sessions: Sessions,
                 configuration: GatewayConfiguration,
                 rest_client: RestClient) -> None:
        """Initialise the password session creation handler.

        Args:
            logger: Logger instance used for diagnostic logging.
            sessions: Session manager used to create and track user sessions.
            configuration: Gateway configuration containing service endpoint
                information.
            rest_client: REST client used to communicate with the identity
                service.
        """
        self._logger = logger.getChild(type(self).__name__)
        self._sessions: Sessions = sessions
        self._configuration: GatewayConfiguration = configuration
        self._rest_client: RestClient = rest_client

    @validate_json(SCHEMA_NEW_SESSION_PASSWORD_REQUEST)
    async def create_new_session(self, request_msg: ApiResponse) -> Response:
        """Create a new authenticated user session.

        The supplied credentials are validated against the identity service.
        If authentication succeeds, a new session token is generated and
        stored before being returned to the client.

        Args:
            request_msg: Incoming API request containing the validated JSON
                request body.

        Returns:
            Response: HTTP response containing the newly created session token
            on success, or an appropriate error response if authentication or
            session creation fails.
        """
        email_address: str = request_msg.body["email_address"]
        password:  str = request_msg.body["password"]

        auth_url: str = f"{self._configuration.apis_identity_svc}auth/login"
        auth_request: dict = {
            "email_address": email_address,
            "password": password
        }

        response: ApiResponse = await self._rest_client.post(
            auth_url, json_data=auth_request
        )

        if response.exception_msg:
            self._logger.error("Connection to identity service failed: %s",
                               response.exception_msg)
            return Response(
                json.dumps({"status": 0, "error": "Internal error!"}),
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
                content_type="application/json"
            )

        if response.status_code != HTTPStatus.OK:
            if response.status_code == HTTPStatus.UNAUTHORIZED:
                self._logger.warning(
                    "User '%s' login failed (email/password mismatch)",
                    email_address)
                return Response(status=HTTPStatus.UNAUTHORIZED,
                                content_type="application/json")

            self._logger.critical(
                "Identity service request failed with status %s",
                response.status_code)
            return Response(
                json.dumps({"status": 0, "error": "Internal error!"}),
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
                content_type="application/json")

        token: str = uuid.uuid4().hex

        if await self._sessions.has_session(email_address):
            self._logger.info("User '%s' is being re-logged in",
                              email_address)
        else:
            self._logger.info("User '%s' logged in",
                              email_address)

        # Fetch the user profile so we can store is_administrator and the
        # user's id against the session and return it on every subsequent
        # validate call.
        is_administrator: bool = False
        user_id: str = ""
        profile_url: str = (f"{self._configuration.apis_identity_svc}"
                            f"users/profile")
        profile_response: ApiResponse = await self._rest_client.post(
            profile_url, json_data={"email_address": email_address})

        if profile_response.status_code == HTTPStatus.OK and profile_response.body:
            is_administrator = bool(
                profile_response.body.get("is_administrator", False))
            user_id = profile_response.body.get("id", "")
        else:
            self._logger.warning(
                "Could not retrieve profile for '%s' (status %s); "
                "is_administrator will default to False",
                email_address, profile_response.status_code)

        # Snapshot the user's project memberships too, so read routes can
        # enforce access without a per-request identity lookup. Same
        # cached-at-login tradeoff as is_administrator above - see
        # SessionEntry's docstring.
        project_ids: frozenset[int] = await self._fetch_member_project_ids(
            user_id)

        await self._sessions.add_session(email_address,
                                         token,
                                         AccountLogonType.BASIC,
                                         is_administrator=is_administrator,
                                         user_id=user_id,
                                         project_ids=project_ids)

        return Response(
            json.dumps({"status": 1, "token": token}),
            status=HTTPStatus.OK,
            content_type="application/json")

    async def _fetch_member_project_ids(self, user_id: str) -> frozenset[int]:
        """Fetch the set of project ids the user is a member of.

        A failure here is non-fatal to login: the session is simply
        cached with no memberships (the safe default - no membership
        already means no access anywhere else in this system), rather
        than failing the login entirely over a read that isn't essential
        to authenticating the user.

        Args:
            user_id: The user's identity-service UUID. Empty if it could
                not be resolved from their profile.

        Returns:
            A frozenset of project ids, or an empty frozenset on any
            failure (including no user_id being available at all).
        """
        if not user_id:
            return frozenset()

        url = (f"{self._configuration.apis_identity_svc}"
              f"users/{user_id}/projects")
        try:
            response: ApiResponse = await self._rest_client.get(url)
        except Exception:  # pylint: disable=broad-except
            self._logger.warning(
                "Unable to fetch project memberships for user '%s'", user_id)
            return frozenset()

        if response.status_code != HTTPStatus.OK or not response.body:
            self._logger.warning(
                "Unable to fetch project memberships for user '%s' "
                "(status %s)", user_id, response.status_code)
            return frozenset()

        memberships = response.body.get("memberships", [])
        return frozenset(
            m["project_id"] for m in memberships
            if m.get("project_id") is not None)
