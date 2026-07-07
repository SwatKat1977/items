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
import asyncio
import logging
import aiohttp
from weaver_framework.microservice.rest_client import RestClient
from weaver_framework.microservice.api_response import ApiResponse
from items.services.items_gateway.gateway_configuration import (
    GatewayConfiguration)
from items.shared.api_signature import generate_api_signature
from items.services.items_gateway.metadata_handler import MetadataHandler


class WebPortalClient:
    """
    Client for outbound HTTP communication with the Web Portal service.

    Handles signing and sending metadata update requests to the Web Portal
    webhook endpoint, with configurable retry behaviour.

    Attributes:
        INFINITE_UPDATE_RETRIES (int): Sentinel value (-1) indicating that
                                       update attempts should retry indefinitely.
    """
    # pylint: disable=too-few-public-methods

    INFINITE_UPDATE_RETRIES: int = -1

    def __init__(self,
                 logger: logging.Logger,
                 metadata_handler: MetadataHandler,
                 config: GatewayConfiguration,
                 http_session: aiohttp.ClientSession) -> None:
        """
        Initialises the WebPortalClient.

        Args:
            logger (logging.Logger): Parent logger; a child logger scoped to
                                     this module is created automatically.
            metadata_handler (MetadataHandler): Source of metadata configuration
                                                used to build webhook payloads.
            config (GatewayConfiguration): Service configuration providing API
                                           endpoints and signing secrets.
            http_session (aiohttp.ClientSession): Shared aiohttp session used
                                                  for all outbound HTTP requests.
        """
        self._logger: logging.Logger = logger.getChild(type(self).__name__)
        self._metadata_handler: MetadataHandler = metadata_handler
        self._config: GatewayConfiguration = config
        self._rest_client: RestClient = RestClient(http_session)

    async def update_web_portal_webhook(self, retries: int = 0) -> bool:
        """
        Sends an update request to the Web Portal webhook with metadata configuration.

        Args:
            retries (int): Number of retry attempts. Use INFINITE_UPDATE_RETRIES (-1)
                           to retry indefinitely, or 0 for a single attempt.

        Returns:
            bool: True if the update is successful, False otherwise.
        """
        perform_update: int = 1 if retries in (0, self.INFINITE_UPDATE_RETRIES) \
                                else retries

        metadata_items: dict = self._metadata_handler.build_metadata_dictionary()

        secret: bytes = self._config.general_api_signing_secret.encode()
        signature: str = generate_api_signature(secret, metadata_items)
        headers = {
            "Content-Type": "application/json",
            "X-Signature": signature
        }

        url: str = f"{self._config.apis_web_portal_svc}webhook/update_metadata"

        while perform_update != 0:
            response: ApiResponse = await self._rest_client.post(
                url, json_data=metadata_items, headers=headers, timeout=1)

            if response.success:
                self._logger.info("Updated Web Portal with metadata "
                                  "configuration items")
                return True

            if response.exception_msg:
                self._logger.error(
                    "Connection to web portal service failed: %s",
                    response.exception_msg
                )
            else:
                self._logger.warning(
                    "Web Portal returned status %s", response.status_code
                )

            if retries != self.INFINITE_UPDATE_RETRIES:
                perform_update -= 1

            await asyncio.sleep(3)

        self._logger.critical("Failed to update Web Portal with metadata "
                              "configuration items")
        return False
