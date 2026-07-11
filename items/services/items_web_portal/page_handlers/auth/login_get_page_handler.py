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
import logging
from quart import make_response
from weaver_framework.microservice.rest_client import RestClient
from items.shared.base_items_exception import BaseItemsException
from items.services.items_web_portal.configuration import Configuration
import items.services.items_web_portal.page_locations as pages
from items.services.items_web_portal.portal_page_handler import (
    PortalPageHandler)


class LoginGetPageHandler(PortalPageHandler):

    def __init__(self,
                 logger: logging.Logger,
                 config: Configuration,
                 rest_client: RestClient):
        super().__init__(logger, config, rest_client)

    async def login_get(self):
        try:
            if await self._has_auth_cookies() and await self._validate_cookies():
                redirect = self._generate_redirect('')
                response = await make_response(redirect)
                return response

        except BaseItemsException as ex:
            self._logger.error('Internal Error: %s', ex)
            return await self._render_page(pages.TEMPLATE_INTERNAL_ERROR_PAGE)

        return await self._render_page(pages.TEMPLATE_LOGIN_PAGE)
