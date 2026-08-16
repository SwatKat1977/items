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
from weaver_framework.microservice.rest_client import RestClient
from items.services.items_gateway.gateway_configuration import GatewayConfiguration


class DeleteRoleHandler(BaseApiRoute):
    """Handles DELETE /roles/<role_id> — delete a role.

    Proxies the request to the identity service and propagates the response.
    Any project membership holding this role has its role assignment
    cleared, not deleted - identity's concern, not the gateway's.
    """

    def __init__(self,
                 logger: logging.Logger,
                 configuration: GatewayConfiguration,
                 rest_client: RestClient) -> None:
        self._logger = logger.getChild(type(self).__name__)
        self._configuration = configuration
        self._rest_client = rest_client

    async def delete_role(self, role_id: int) -> Response:
        """Delete a role.

        Args:
            role_id: The role's id (from the URL).

        Returns:
            200 on success.
            404 if no role exists with that id.
            500 if the identity service is unreachable.
        """
        url: str = f"{self._configuration.apis_identity_svc}roles/{role_id}"
        response: ApiResponse = await self._rest_client.delete(url)

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
