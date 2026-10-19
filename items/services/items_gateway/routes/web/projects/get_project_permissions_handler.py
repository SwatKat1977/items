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
from weaver_framework.microservice.base_api_route import BaseApiRoute
from weaver_framework.microservice.rest_client import RestClient
from items.services.items_gateway.auth_decorators import (
    fetch_user_permissions)
from items.services.items_gateway.gateway_configuration import (
    GatewayConfiguration)
from items.services.items_gateway.sessions import SessionEntry


class GetProjectPermissionsHandler(BaseApiRoute):
    """API route handler telling the caller what they may do in a project.

    The Portal uses this to decide which controls to show (design doc
    section 9.5), so it can hide an Add or Delete button the person's role
    does not allow. It is a convenience for the user interface, not a
    security measure: every write route enforces the same permissions
    itself, whatever the Portal shows.

    It only ever answers about the **caller**. The user is taken from the
    session, never from the request, so nobody can use it to look up what
    someone else may do.
    """

    def __init__(self,
                 logger: logging.Logger,
                 config: GatewayConfiguration,
                 rest_client: RestClient) -> None:
        """Initialise the project permissions handler.

        Args:
            logger: Parent logger instance used to create a child logger for
                this handler.
            config: Gateway configuration containing the Identity service
                address.
            rest_client: REST client used to ask the Identity service.
        """
        self._logger = logger.getChild(type(self).__name__)
        self._config: GatewayConfiguration = config
        self._rest_client: RestClient = rest_client

    async def get_project_permissions(self, project_id: int,
                                      session_entry: SessionEntry) -> Response:
        """Return the caller's effective permissions in a project.

        Args:
            project_id: The project to answer about (from the URL).
            session_entry: The caller's resolved session; supplies the user.

        Returns:
            200 with ``{"project_id": n, "areas": {<area>: {"read",
            "add_modify", "delete"}}}`` exactly as the Identity service
            returns it. Not being a member, having no role, and being
            disabled are all a 200 with every flag false: having no access
            is an answer, not an error.
            403 if the session has no user id, or Identity does not know the
            user.
            500 if Identity cannot be reached or answers unexpectedly.
        """
        if not session_entry.user_id:
            # The user's id could not be resolved at login, so there is
            # nobody to ask Identity about.
            return Response(json.dumps({"error": "Forbidden"}),
                            status=HTTPStatus.FORBIDDEN,
                            content_type="application/json")

        body, failure = await fetch_user_permissions(
            self._logger, self._config, self._rest_client,
            session_entry.user_id, project_id)
        if failure is not None:
            return failure

        return Response(json.dumps(body),
                        status=HTTPStatus.OK,
                        content_type="application/json")
