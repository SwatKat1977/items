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
from quart import Response
from weaver_framework.microservice.api_response import ApiResponse
from weaver_framework.microservice.base_api_route import BaseApiRoute
from weaver_framework.microservice.rest_client import RestClient
from items.services.items_gateway.gateway_configuration import GatewayConfiguration


class GetTestcaseHandler(BaseApiRoute):

    def __init__(self,
                 logger: logging.Logger,
                 configuration: GatewayConfiguration,
                 rest_client: RestClient) -> None:
        self._logger = logger.getChild(type(self).__name__)
        self._config = configuration
        self._rest_client: RestClient = rest_client

    async def get_testcase(self, project_id: int, case_id: int) -> Response:
        cms_svc: str = self._config.apis_cms_svc

        details_url: str = f"{cms_svc}web/testcases/{case_id}"

        api_response: ApiResponse = await self._rest_client.get(details_url)

        try:

            if api_response.status_code != HTTPStatus.OK:
                print(api_response.body)
                self._logger.critical("CMS svc /testcases/get_case request invalid"
                                      " - Reason: %s",api_response.exception_msg)
                response_json = {
                    "status": 0,
                    'error': 'Internal error!'
                }
                return Response(json.dumps(response_json),
                                status=HTTPStatus.INTERNAL_SERVER_ERROR,
                                content_type="application/json")

        except requests.exceptions.ConnectionError as ex:
            except_str = f"Internal error: {ex}"
            self._logger.error(except_str)

            response_json = {
                "status":  0,
                "error": str(ex)
            }
            return Response(json.dumps(response_json),
                                  status=HTTPStatus.INTERNAL_SERVER_ERROR,
                                  content_type="application/json")

        return Response(json.dumps(api_response.body),
                              status=HTTPStatus.OK,
                              content_type="application/json")
