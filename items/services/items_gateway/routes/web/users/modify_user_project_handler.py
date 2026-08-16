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


class ModifyUserProjectHandler(BaseApiRoute):
    """Handles PATCH /users/<user_id>/projects/<project_id> — set role.

    No CMS existence check here, unlike ``AddUserProjectHandler`` - the
    project referenced by the URL is already an existing membership (it
    was validated against CMS when the membership was created), and this
    endpoint only ever changes the *role* on it, never the project.
    Proxies to the identity service.
    """

    def __init__(self,
                 logger: logging.Logger,
                 configuration: GatewayConfiguration,
                 rest_client: RestClient) -> None:
        self._logger = logger.getChild(type(self).__name__)
        self._configuration = configuration
        self._rest_client = rest_client

    async def modify_user_project(self, user_id: str,
                                  project_id: int) -> Response:
        """Change (or clear) the role on an existing membership.

        Args:
            user_id: The user's UUID (from the URL).
            project_id: The project's id (from the URL).

        Returns:
            200 on success.
            400 if the request body is missing or not valid JSON, or a
            supplied ``role_id`` doesn't exist.
            404 if no user exists with that UUID, or the user is not a
            member of this project.
            500 if the identity service is unreachable.
        """
        body = await request.get_json(force=True, silent=True)
        if body is None:
            return Response(
                json.dumps({"error": "Invalid JSON body"}),
                status=HTTPStatus.BAD_REQUEST,
                content_type="application/json")

        url: str = (f"{self._configuration.apis_identity_svc}"
                    f"users/{user_id}/projects/{project_id}")
        response: ApiResponse = await self._rest_client.patch(url,
                                                               json_data=body)

        if response.exception_msg is not None:
            self._logger.error("Connection to identity service failed: %s",
                               response.exception_msg)
            return Response(
                json.dumps({"error": "Identity service unavailable"}),
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
                content_type="application/json")

        return Response(json.dumps(response.body),
                        status=response.status_code,
                        content_type="application/json")
