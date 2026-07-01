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

    def __init__(self,
                 logger: logging.Logger,
                 sessions: Sessions,
                 configuration: GatewayConfiguration,
                 rest_client: RestClient) -> None:
        self._logger = logger.getChild(type(self).__name__)
        self._sessions: Sessions = sessions
        self._configuration: GatewayConfiguration = configuration
        self._rest_client: RestClient = rest_client

    @validate_json(SCHEMA_NEW_SESSION_PASSWORD_REQUEST)
    async def create_new_session(self, request_msg: ApiResponse) -> Response:
        """
        Handler for creating a new user session.

        Validates the request body, authenticates the user against the identity
        service, and creates a session token on success.

        Args:
            request_msg (ApiResponse): Validated request body passed by the
                                       @validate_json decorator.

        Returns:
            Response: Quart Response with session token on success, or an error
                      response on failure.
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
            else:
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

        await self._sessions.add_session(email_address,
                                         token,
                                         AccountLogonType.BASIC)

        return Response(
            json.dumps({"status": 1, "token": token}),
            status=HTTPStatus.OK,
            content_type="application/json")
