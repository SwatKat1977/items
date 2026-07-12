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
import asyncio
from http import HTTPStatus
import uuid
import aiohttp
from quart import Quart
from weaver_framework.microservice.api_response import ApiResponse
from weaver_framework.microservice.base_microservice import BaseMicroservice
from weaver_framework.configuration_system.configuration_manager import (
    ConfigurationError)
from weaver_framework.microservice.rest_client import RestClient
from items.services.items_web_portal.metadata_settings import MetadataSettings
from items.services.items_web_portal.page_handlers import create_page_handlers
from items.shared import LICENSE_TEXT, SERVICE_COPYRIGHT_TEXT, __version__
from items.services.items_web_portal.configuration_layout import CONFIGURATION_LAYOUT
from items.services.items_web_portal.configuration import Configuration
from items.shared.api_signature import generate_api_signature
from items.services.items_web_portal.page_handler_injections import (
    PageHandlerInjections)


class Service(BaseMicroservice):
    """ ITEMS Gateway Microservice """
    # pylint: disable=too-many-instance-attributes

    SERVICE_NAME: str = "Web Portal"
    CONFIG_FILE_ENV: str = "ITEMS_WEB_PORTAL_CONFIG_FILE"
    CONFIG_REQUIRED_ENV: str = "ITEMS_WEB_PORTAL_CONFIG_FILE_REQUIRED"

    GET_METADATA_INFINITE_RETRIES: int = -1

    def __init__(self, quart_instance: Quart):
        super().__init__()
        self._quart_instance = quart_instance
        self._config: Configuration = Configuration()
        self._http_session: aiohttp.ClientSession | None = None
        self._metadata_settings: MetadataSettings = MetadataSettings()
        self._rest_client: RestClient | None = None

    async def _initialise(self) -> bool:
        self.logger.info('ITEMS Web Portal Microservice %s', __version__)
        self.logger.info(SERVICE_COPYRIGHT_TEXT)
        self.logger.info(LICENSE_TEXT)

        if not self._manage_configuration():
            return False

        self.logger.info("Setting logging level to %s",
                         self._config.logging_log_level)
        self.logger.setLevel(self._config.logging_log_level)

        self._http_session = aiohttp.ClientSession()
        self._metadata_settings: MetadataSettings = MetadataSettings()
        self._rest_client: RestClient = RestClient(self._http_session)

        injections: PageHandlerInjections = PageHandlerInjections(
            self._config,
            self.logger,
            self._metadata_settings,
            self._rest_client)

        # TEMPORARY DISABLE
        # if not await self._get_metadata(self.GET_METADATA_INFINITE_RETRIES):
        #     return False

        self._quart_instance.register_blueprint(create_page_handlers(
            injections))

        return True

    async def _create_tasks(self) -> list[asyncio.Task]:
        """ Create and return the service's background tasks. """
        return [asyncio.create_task(self._shutdown_wait_task())]

    async def _shutdown(self):
        """ Abstract method for application shutdown. """
        if self._http_session:
            await self._http_session.close()

    def _manage_configuration(self) -> bool:
        """
        Manage the service configuration.
        """
        error_status, required, config_file = self._check_for_configuration(
            self.CONFIG_FILE_ENV,self.CONFIG_REQUIRED_ENV)
        if error_status:
            self.logger.critical(error_status)
            return False

        self._config.configure(CONFIGURATION_LAYOUT, config_file, required)

        try:
            self._config.process_config()

        except ConfigurationError as ex:
            self.logger.critical("Configuration error : %s", str(ex))
            return False

        except ValueError as ex:
            self.logger.critical("Configuration error : %s", str(ex))
            return False

        self.logger.info("Configuration")
        self.logger.info("=============")

        self.logger.info("Configuration file required: %s",
                         "True" if required else "False")
        self.logger.info("Configuration file : %s",
                         "None"if not required else config_file)
        self.logger.info("[logging]")
        self.logger.info("=> Logging log level : %s",
                         self._config.logging_log_level)
        self._logger.info("[routes]")
        self._logger.info("=> Gateway Service API : %s",
                          self._config.apis_gateway_svc)

        return True

    async def _shutdown_wait_task(self) -> None:
        await self.shutdown_event.wait()

    async def _get_metadata(self, retries: int = 0) -> bool:
        """
        Fetches metadata from the web portal service and updates internal
        settings.

        This method retrieves metadata configuration items such as the default
        time zone, whether the server's default time zone is used, and the
        instance name. It attempts the request up to a specified number of
        retries.

        Args:
            retries (int, optional): The number of times to retry fetching
                                     metadata. If set to
                                     `GET_METADATA_INFINITE_RETRIES`, it
                                     retries indefinitely. Defaults to 0.

        Returns:
            bool: True if metadata was successfully retrieved and updated,
                  False otherwise.

        Logs:
            - INFO: If metadata retrieval is successful.
            - WARNING: If a request fails but retries are remaining.
            - ERROR: If a connection error occurs.
            - CRITICAL: If all retries are exhausted without success.

        Raises:
            requests.exceptions.ConnectionError: If a connection to the web
            portal fails.

        Notes:
            - The request is signed using an API signature for authentication.
            - Uses a UUID as a nonce for security.
            - Sleeps for 3 seconds between failed attempts before retrying.
        """
        perform_update: int = 1 if (retries in
                                    (0, self.GET_METADATA_INFINITE_RETRIES)) \
                                else retries

        # Generate number used once (NONCE)
        nonce = str(uuid.uuid4())

        string_to_sign: str = f"/web/webhook/get_metadata:{nonce}"
        secret: bytes = self._config.general_api_signing_secret.encode()
        signature: str = generate_api_signature(secret, string_to_sign)
        headers = {
            "Content-Type": "application/json",
            "X-Signature": signature
        }

        base_path: str = self._config.apis_gateway_svc
        url: str = f"{base_path}web/webhook/get_metadata?nonce={nonce}"

        while perform_update != 0:
            response: ApiResponse = await self._rest_client.get(url,
                                                                headers=headers,
                                                                timeout=5)

            if response.status_code == HTTPStatus.UNAUTHORIZED:
                self.logger.critical("API secret key mismatch, not "
                                     "authorised")
                return False

            if response.status_code == HTTPStatus.OK:
                data: dict = response.body
                self._metadata_settings.default_time_zone = \
                    data.get("default_time_zone")
                self._metadata_settings.using_server_default_time_zone = \
                    data.get("using_server_default_time_zone")
                self._metadata_settings.instance_name = \
                    data.get("instance_name")

                self._logger.info("Successfully updated Web Portal with "
                                  "metadata configuration items")
                return True

            self._logger.warning("Unable to update Web Portal with metadata "
                                 "configuration items")

            if retries != self.GET_METADATA_INFINITE_RETRIES:
                perform_update -= 1

            await asyncio.sleep(3)

        self._logger.critical("Failed to update Web Portal with metadata "
                              "configuration items")
        return False
