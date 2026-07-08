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
from quart import request, Response
from weaver_framework.microservice.api_response import ApiResponse
from weaver_framework.microservice.base_api_route import BaseApiRoute
from weaver_framework.microservice.rest_client import RestClient
from items.services.items_gateway.gateway_configuration import GatewayConfiguration


class DeleteProjectHandler(BaseApiRoute):
    """API route handler for deleting projects.

    This handler processes project deletion requests received by the gateway.
    It validates the optional ``hard_delete`` query parameter, forwards the
    request to the CMS service, and returns the appropriate HTTP response to
    the client.

    A soft delete is performed by default when the ``hard_delete`` parameter
    is omitted.
    """

    def __init__(self,
                 logger: logging.Logger,
                 config: GatewayConfiguration,
                 rest_client: RestClient) -> None:
        """Initialise the project deletion handler.

        Args:
            logger: Parent logger instance used to create a child logger for
                this handler.
            config: Gateway configuration containing service endpoint
                information.
            rest_client: REST client used to communicate with backend
                services.
        """
        self._logger = logger.getChild(type(self).__name__)
        self._config: GatewayConfiguration = config
        self._rest_client: RestClient = rest_client

    async def delete_project(self, project_id: int):
        """Delete a project.

        Reads the optional ``hard_delete`` query parameter from the incoming
        request and validates its value. If omitted, the request defaults to a
        soft delete. The request is then forwarded to the CMS service.

        Args:
            project_id: Unique identifier of the project to delete.

        Returns:
            A Quart ``Response`` containing the result of the deletion
            operation or an appropriate error response if validation fails or
            the CMS service returns an error.
        """
        cms_svc: str = self._config.apis_cms_svc
        hard_delete = request.args.get("hard_delete")
        if not hard_delete:
            url: str = f"{cms_svc}projects/{project_id}?hard_delete=false"
        else:
            hard_delete = hard_delete.strip().lower()

            if hard_delete not in ("true", "false"):
                response_json = {
                    "status": 0,
                    "error": f"Invalid value for hard_delete: '{hard_delete}'. "
                    "Expected 'true' or 'false'."
                }
                return Response(json.dumps(response_json),
                                status=HTTPStatus.INTERNAL_SERVER_ERROR,
                                content_type="application/json")

            is_hard_delete: bool = hard_delete == "true"
            url: str = f"{cms_svc}projects/{project_id}?hard_delete={is_hard_delete}"

        response: ApiResponse = await self._rest_client.delete(url)

        status = response.status_code
        if status != HTTPStatus.OK:
            if status == HTTPStatus.NOT_FOUND:
                err_msg = response.body.get("error", "")
                return Response(json.dumps(err_msg),
                                status,
                                content_type="application/json")

            response_json = {
                "status": 0,
                "error": response.exception_msg
            }
            return Response(json.dumps(response_json),
                            status=HTTPStatus.INTERNAL_SERVER_ERROR,
                            content_type="application/json")

        return Response(json.dumps(response.body),
                        status=HTTPStatus.OK,
                        content_type="application/json")
