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


class ModifyRoleHandler(BaseApiRoute):
    """Handles PATCH /roles/<role_id> — update a role's name and/or grid.

    Patch-style: only fields present in the body are updated; ``permissions``,
    when present, replaces the role's entire grid (identity's own rule, not
    re-enforced here). Proxies to the identity service.
    """

    def __init__(self,
                 logger: logging.Logger,
                 configuration: GatewayConfiguration,
                 rest_client: RestClient) -> None:
        self._logger = logger.getChild(type(self).__name__)
        self._configuration = configuration
        self._rest_client = rest_client

    async def modify_role(self, role_id: int) -> Response:
        """Update a role's name and/or replace its permission grid.

        Args:
            role_id: The role's id (from the URL).

        Returns:
            200 on success.
            400 if the request body is missing or not valid JSON, or the
            supplied permission grid is invalid.
            404 if no role exists with that id.
            409 if renaming to a name already in use by another role.
            500 if the identity service is unreachable.
        """
        body = await request.get_json(force=True, silent=True)
        if body is None:
            return Response(
                json.dumps({"error": "Invalid JSON body"}),
                status=HTTPStatus.BAD_REQUEST,
                content_type="application/json")

        url: str = f"{self._configuration.apis_identity_svc}roles/{role_id}"
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
