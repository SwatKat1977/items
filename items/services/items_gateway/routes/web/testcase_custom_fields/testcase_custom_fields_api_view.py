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
from weaver_framework.microservice.base_api_route import BaseApiRoute
from weaver_framework.microservice.rest_client import RestClient
from items.services.items_gateway.gateway_configuration import GatewayConfiguration
from items.services.items_gateway.route_injections import RouteInjections


class GetAllCustomFieldsHandler(BaseApiRoute):

    def __init__(self, injections: RouteInjections) -> None:
        self._logger: logging.Logger = injections.logger.getChild(
            type(self).__name__)
        self._config: GatewayConfiguration = injections.configuration
        self._rest_client: RestClient = injections.rest_client

    async def get_all_custom_fields(self):
        cms_svc: str = self._config.apis_cms_svc
        url: str = f"{cms_svc}admin/testcase_custom_fields/" \
                   f"testcase_custom_fields"

        api_response = await self._call_api_get(url)

        return Response(json.dumps(api_response.body),
                        status=HTTPStatus.OK,
                        content_type="application/json")
