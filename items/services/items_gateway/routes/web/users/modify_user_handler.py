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
from quart import request, Response
from weaver_framework.microservice.api_response import ApiResponse
from weaver_framework.microservice.base_api_route import BaseApiRoute
from weaver_framework.microservice.rest_client import RestClient
from items.services.items_gateway.gateway_configuration import GatewayConfiguration
from items.services.items_gateway.sessions import Sessions


class ModifyUserHandler(BaseApiRoute):
    """Handles PATCH /users/<user_id> — update a user's profile fields.

    Patch-style: only fields present in the body are updated; omitted
    fields retain their current values. Proxies to the identity service.
    """

    def __init__(self,
                 logger: logging.Logger,
                 configuration: GatewayConfiguration,
                 rest_client: RestClient,
                 sessions: Sessions) -> None:
        self._logger = logger.getChild(type(self).__name__)
        self._configuration = configuration
        self._rest_client = rest_client
        self._sessions = sessions

    async def modify_user(self, user_id: str) -> Response:
        """Update a user's profile fields.

        On a successful update, keeps the user's already-open session (if
        any) in sync with what changed:
          - ``is_administrator``, when present in the body, is live-patched
            into the session immediately - see
            ``Sessions.set_is_administrator_for_user``.
          - ``account_status`` set to ``0`` (deactivation) deletes the
            session outright, forcing a re-login (which will then
            correctly fail) - see ``Sessions.delete_session_for_user``.

        Args:
            user_id: The user's UUID (from the URL).

        Returns:
            200 on success.
            400 if the request body is missing or not valid JSON.
            403 if the update would leave no active administrator.
            404 if no user exists with that ID.
            500 if the identity service is unreachable.
        """
        body = await request.get_json(force=True, silent=True)
        if body is None:
            return Response(
                json.dumps({"error": "Invalid JSON body"}),
                status=HTTPStatus.BAD_REQUEST,
                content_type="application/json")

        url: str = f"{self._configuration.apis_identity_svc}users/{user_id}"
        response: ApiResponse = await self._rest_client.patch(url,
                                                               json_data=body)

        if response.exception_msg is not None:
            self._logger.error("Connection to identity service failed: %s",
                               response.exception_msg)
            return Response(
                json.dumps({"error": "Identity service unavailable"}),
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
                content_type="application/json")

        if response.status_code == HTTPStatus.OK:
            if body.get("account_status") == 0:
                await self._sessions.delete_session_for_user(user_id)
            elif "is_administrator" in body:
                await self._sessions.set_is_administrator_for_user(
                    user_id, bool(body["is_administrator"]))

        return Response(json.dumps(response.body),
                        status=response.status_code,
                        content_type="application/json")
