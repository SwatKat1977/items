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
import quart
from quart import Response
from weaver_framework.microservice.base_api_route import BaseApiRoute
from weaver_framework.microservice.rest_client import RestClient
from items.services.items_gateway.gateway_configuration import GatewayConfiguration


class GetAllCustomFieldsHandler(BaseApiRoute):
    """Handles GET /testcase_custom_fields requests."""

    def __init__(self,
                 logger: logging.Logger,
                 configuration: GatewayConfiguration,
                 rest_client: RestClient) -> None:
        """Initialise the handler.

        Args:
            logger:        Parent logger instance.
            configuration: Gateway configuration containing service endpoint
                           information.
            rest_client:   REST client used to communicate with the CMS service.
        """
        self._logger = logger.getChild(type(self).__name__)
        self._configuration = configuration
        self._rest_client = rest_client

    async def get_all_custom_fields(self) -> Response:
        """Retrieve testcase custom field definitions from the CMS service.

        Query parameters:
            project_id (int, optional): If provided, return only fields
                                        applicable to that project.

        Returns:
            200 with the list of custom field definitions on success.
            400 if ``project_id`` is present but not a valid integer.
            500 if the CMS service is unreachable or returns an error.
        """
        params: dict | None = None
        project_id_param = quart.request.args.get("project_id")

        if project_id_param is not None:
            try:
                project_id = int(project_id_param)
                if project_id <= 0:
                    raise ValueError
            except ValueError:
                return Response(
                    json.dumps({"error": "project_id must be an integer"}),
                    status=HTTPStatus.BAD_REQUEST,
                    content_type="application/json")
            params = {"project_id": project_id}

        url: str = f"{self._configuration.apis_cms_svc}testcase_custom_fields"

        response = await self._rest_client.get(url, params=params)

        if response.exception_msg is not None:
            self._logger.error("Connection to CMS service failed: %s",
                               response.exception_msg)
            return Response(
                json.dumps({"error": "Internal error!"}),
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
                content_type="application/json")

        if response.status_code != HTTPStatus.OK:
            self._logger.error("CMS service returned status %s",
                               response.status_code)
            return Response(
                json.dumps(response.body),
                status=response.status_code,
                content_type="application/json")

        return Response(
            json.dumps(response.body),
            status=HTTPStatus.OK,
            content_type="application/json")
