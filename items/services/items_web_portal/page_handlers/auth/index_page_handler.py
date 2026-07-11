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
import logging
from quart import make_response
from weaver_framework.microservice.rest_client import RestClient
from items.shared.base_items_exception import BaseItemsException
from items.services.items_web_portal.configuration import Configuration
from items.services.items_web_portal.metadata_settings import MetadataSettings
import items.services.items_web_portal.page_locations as pages
from items.services.items_web_portal.portal_page_handler import (
    PortalPageHandler)


'''
from http import HTTPStatus

from base_web_view import PortalPageHandler
from base_view import ApiResponse
from quart import make_response, request, Response
from base_items_exception import BaseItemsException
import page_locations as pages
from threadsafe_configuration import ThreadSafeConfiguration
from metadata_settings import MetadataSettings
'''


class IndexPageHandler(PortalPageHandler):

    def __init__(self,
                 logger: logging.Logger,
                 config: Configuration,
                 rest_client: RestClient,
                 metadata: MetadataSettings):
        super().__init__(logger, config, rest_client)
        self._metadata_settings = metadata

    async def index(self):
        try:
            if not self._has_auth_cookies() or not self._validate_cookies():
                redirect = self._generate_redirect('login')
                return await make_response(redirect)

        except BaseItemsException as ex:
            self._logger.error('Internal Error: %s', ex)
            return await self._render_page(pages.TEMPLATE_INTERNAL_ERROR_PAGE)

        base_url: str = self._config.apis_gateway_svc
        url = f"{base_url}/web/projects?value_fields=name&" + \
              "count_fields=no_of_test_runs,no_of_milestones"
        response: ApiResponse = await self._call_api_get(url)

        if response.status_code != HTTPStatus.OK:
            self._logger.critical("Gateway svc request invalid - Reason: %s",
                                  response.exception_msg)
            return await self._render_page(pages.TEMPLATE_INTERNAL_ERROR_PAGE)

        page: str = "dashboard"
        projects = response.body["projects"]

        return await self._render_page(
            pages.TEMPLATE_DASHBOARD_PAGE,
            active_page=page,
            projects=projects,
            instance_name=self._metadata_settings.instance_name)
