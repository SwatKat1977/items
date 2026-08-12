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


class GetTestcaseHandler(BaseApiRoute):
    """Handle requests for retrieving a single testcase.

    This handler acts as a proxy between the web application and the CMS
    service, requesting testcase details from the CMS API and translating the
    response into an appropriate HTTP response for the client.
    """

    def __init__(self,
                 logger: logging.Logger,
                 configuration: GatewayConfiguration,
                 rest_client: RestClient) -> None:
        """Initialise the handler.

        Args:
            logger: Application logger used for diagnostic and error logging.
            configuration: Gateway configuration containing service endpoint
                information.
            rest_client: REST client used to communicate with the CMS service.
        """
        self._logger = logger.getChild(type(self).__name__)
        self._config = configuration
        self._rest_client: RestClient = rest_client

    async def get_testcase(self, case_id: int) -> Response:
        """Retrieve the details of a single testcase.

        Requires a ``project_id`` query parameter - unlike CMS's own route,
        which treats it as optional, the gateway needs it to authorise the
        request (see ``user_roles_design.md`` §9.2) and has no other source
        for it, so it can't be inferred or skipped here. The request is
        forwarded to CMS, which enforces that the testcase actually belongs
        to the stated project.

        Args:
            case_id: Unique identifier of the testcase to retrieve.

        Returns:
            Response: A JSON response containing the testcase details or an
            error message.

            400 if ``project_id`` is missing or not a valid integer.
            404 if the testcase doesn't exist, or exists under a different
            project than the one supplied.
            500 on an unexpected CMS error.
        """
        raw_project_id = request.args.get("project_id")
        if raw_project_id is None:
            response_json = {"error": "project_id query parameter is required"}
            return Response(json.dumps(response_json),
                            status=HTTPStatus.BAD_REQUEST,
                            content_type="application/json")

        try:
            project_id = int(raw_project_id)
        except ValueError:
            response_json = {"error": "project_id must be an integer"}
            return Response(json.dumps(response_json),
                            status=HTTPStatus.BAD_REQUEST,
                            content_type="application/json")

        cms_svc: str = self._config.apis_cms_svc

        details_url: str = (
            f"{cms_svc}testcases/{case_id}?project_id={project_id}")

        api_response: ApiResponse = await self._rest_client.get(details_url)

        if api_response.status_code == HTTPStatus.NOT_FOUND:
            response_json = {
                "status": 0,
                'error': api_response.body.get("error", "unknown error")
            }
            return Response(json.dumps(response_json),
                            status=HTTPStatus.NOT_FOUND,
                            content_type="application/json")

        if api_response.status_code != HTTPStatus.OK:
            self._logger.critical("CMS GET /testcases/<id> request invalid"
                                  " - Reason: %s", api_response.exception_msg)
            response_json = {
                "status": 0,
                'error': 'Internal error!'
            }
            return Response(json.dumps(response_json),
                            status=HTTPStatus.INTERNAL_SERVER_ERROR,
                            content_type="application/json")

        return Response(json.dumps(api_response.body),
                        status=HTTPStatus.OK,
                        content_type="application/json")
