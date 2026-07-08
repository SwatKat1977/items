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


class GetAllProjectsHandler(BaseApiRoute):
    """API route handler for listing projects.

    This handler processes requests to retrieve the collection of projects
    accessible to the client. Optional query parameters are forwarded to the
    CMS service to control which value and count fields are included in the
    response.
    """

    def __init__(self,
                 logger: logging.Logger,
                 config: GatewayConfiguration,
                 rest_client: RestClient) -> None:
        """Initialise the project listing handler.

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

    async def list_all_projects(self):
        """Retrieve the list of accessible projects.

        Forwards the request to the CMS service. If present, the
        ``value_fields`` and ``count_fields`` query parameters are passed
        through to control the fields included in the response.

        Returns:
            A Quart ``Response`` containing the list of projects if the
            request succeeds, or an error response describing why the request
            failed.
        """
        # Get fields from query parameters
        value_fields = request.args.get("value_fields")
        count_fields = request.args.get("count_fields")
        value_fields_str = f"value_fields={value_fields}" if value_fields \
            else ""
        count_fields_str = f"count_fields={count_fields}" if count_fields \
            else ""
        joiner_str = "&" if value_fields and count_fields else ""
        cms_svc: str = self._config.apis_cms_svc
        url: str = f"{cms_svc}projects?{value_fields_str}" + \
                   f"{joiner_str}{count_fields_str}"

        response: ApiResponse = await self._rest_client.get(url)

        if response.status_code == HTTPStatus.BAD_REQUEST:
            error_msg: str = response.body.get("error", "")
            self._logger.warning(
                "[WEB Get Projects] Failed to get projects, reason: %s",
                error_msg)
            response_json: dict = {"status": 0, "error": error_msg}
            return Response(json.dumps(response_json),
                            status=HTTPStatus.BAD_REQUEST,
                            content_type="application/json")

        if response.status_code != HTTPStatus.OK:
            self._logger.critical(
                "[WEB Get Projects] Get projects returned HTTP status %s",
                response.status_code)
            return Response(
                json.dumps({"status": 0, "error": "Internal error!"}),
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
                content_type="application/json")

        return Response(json.dumps(response.body),
                        status=HTTPStatus.OK,
                        content_type="application/json")
