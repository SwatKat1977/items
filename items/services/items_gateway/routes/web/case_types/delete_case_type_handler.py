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


class DeleteCaseTypeHandler(BaseApiRoute):
    """Handles DELETE /case_types/<type_id> - delete a test case type.

    Proxies the request to the CMS service and propagates the response. The
    CMS moves any test cases using the type to the current default type in
    the same transaction as the delete, and refuses to delete the default.
    """

    def __init__(self,
                 logger: logging.Logger,
                 configuration: GatewayConfiguration,
                 rest_client: RestClient) -> None:
        self._logger = logger.getChild(type(self).__name__)
        self._configuration = configuration
        self._rest_client = rest_client

    async def delete_case_type(self, type_id: int) -> Response:
        """Delete a case type.

        Args:
            type_id: The case type's id (from the URL).

        Returns:
            200 on success.
            404 if no case type exists with that id.
            409 if the case type is the default, which is never deleted.
            500 if the CMS service is unreachable or reports an internal
            error.
        """
        url: str = f"{self._configuration.apis_cms_svc}case_types/{type_id}"
        response: ApiResponse = await self._rest_client.delete(url)

        if response.exception_msg is not None:
            self._logger.error("Connection to CMS service failed: %s",
                               response.exception_msg)
            return Response(
                json.dumps({"error": "CMS service unavailable"}),
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
                content_type="application/json")

        return Response(json.dumps(response.body),
                        status=response.status_code,
                        content_type="application/json")
