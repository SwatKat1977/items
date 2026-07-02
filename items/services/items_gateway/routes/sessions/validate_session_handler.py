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
from items.services.items_gateway.sessions import Sessions

SCHEMA_SESSION_VALIDATE_REQUEST = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "properties": {
        "email_address": {
            "type": "string",
            "format": "email"
        },
        "token": {
            "type": "string",
            "pattern": "^[a-f0-9]{32}$"
        }
    },
    "required": ["email_address", "token"],
    "additionalProperties": False
}


class ValidateSessionHandler(BaseApiRoute):
    """API handler for validating user sessions."""

    def __init__(self, logger: logging.Logger, sessions: Sessions) -> None:
        """Initialise the session validation handler.

        Args:
            logger: Logger instance used for diagnostic logging.
            sessions: Session manager used to validate active sessions.
        """
        self._logger = logger.getChild(__name__)
        self._sessions = sessions

    @validate_json(SCHEMA_SESSION_VALIDATE_REQUEST)
    async def validate_session(self, request_msg: ApiResponse):
        """Validate whether a user's session token is currently valid.

        The request body must contain an email address and session token.
        A JSON response is returned indicating whether the session is
        valid.

        Args:
            request_msg: Incoming API request containing the validated JSON
                request body.

        Returns:
            Response: HTTP response containing a JSON object with a
            ``status`` field set to either ``"VALID"`` or ``"INVALID"``.
        """
        email_address: str = request_msg.body["email_address"]
        token: str = request_msg.body["token"]

        valid = await self._sessions.is_valid_session(email_address, token)

        response_json = {"status": "VALID" if valid else "INVALID"}
        response_status = HTTPStatus.OK

        return Response(json.dumps(response_json), response_status,
                        content_type="application/json")
