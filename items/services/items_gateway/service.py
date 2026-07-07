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
import http
import typing
import jsonschema
import aiohttp
from quart import Quart
from weaver_framework.configuration_system.configuration_manager import (
    ConfigurationError)
from weaver_framework.microservice.base_microservice import BaseMicroservice
from weaver_framework.microservice.api_response import ApiResponse
from weaver_framework.microservice.rest_client import RestClient

from items.services.items_gateway.routes import create_routes
from items.shared import LICENSE_TEXT, SERVICE_COPYRIGHT_TEXT, __version__
from items.shared.service_state import ServiceState
from items.shared.interfaces.identity.health import (
    SCHEMA_IDENTITY_SVC_HEALTH_RESPONSE)
from items.shared.interfaces.cms.health import SCHEMA_CMS_SVC_HEALTH_RESPONSE
from items.shared.service_health_enums import ServiceDegradationStatus
from items.services.items_gateway.configuration_layout import \
    CONFIGURATION_LAYOUT
from items.services.items_gateway.gateway_configuration import \
    GatewayConfiguration
from items.services.items_gateway.metadata_handler import MetadataHandler
from items.services.items_gateway.web_portal_client import WebPortalClient
from items.services.items_gateway.sessions import Sessions
from items.services.items_gateway.route_injections import RouteInjections


class Service(BaseMicroservice):
    """ ITEMS Gateway Microservice """
    # pylint: disable=too-many-instance-attributes

    SERVICE_NAME: str = "Gateway"
    CONFIG_FILE_ENV: str = "ITEMS_GATEWAY_CONFIG_FILE"
    CONFIG_REQUIRED_ENV: str = "ITEMS_GATEWAY_CONFIG_FILE_REQUIRED"

    def __init__(self, quart_instance: Quart):
        super().__init__()
        self._quart_instance = quart_instance
        self._service_state: ServiceState = ServiceState()
        self._config: GatewayConfiguration = GatewayConfiguration()
        self._http_session: aiohttp.ClientSession | None = None
        self._metadata_handler: MetadataHandler | None = None
        self._web_portal_client: WebPortalClient | None = None
        self._rest_client: RestClient | None = None
        self._sessions: Sessions = Sessions()

        self._service_state.database_enabled = True

    async def _initialise(self) -> bool:
        self.logger.info('ITEMS Gateway Microservice %s', __version__)
        self.logger.info(SERVICE_COPYRIGHT_TEXT)
        self.logger.info(LICENSE_TEXT)

        self._service_state.version = __version__

        if not self._manage_configuration():
            return False

        self.logger.info("Setting logging level to %s",
                         self._config.logging_log_level)
        self.logger.setLevel(self._config.logging_log_level)

        self._http_session = aiohttp.ClientSession()
        self._metadata_handler = MetadataHandler(self.logger, self._config)
        self._web_portal_client = WebPortalClient(
            self.logger,
            self._metadata_handler,
            self._config,
            self._http_session)
        self._rest_client: RestClient = RestClient(self._http_session)

        if not self._metadata_handler.read_metadata_file():
            return False

        if not await self._check_identity_svc_status():
            return False

        if not await self._check_cms_svc_status():
            return False

        route_injections: RouteInjections = RouteInjections(
            logger=self.logger,
            sessions=self._sessions,
            configuration=self._config,
            rest_client=self._rest_client)

        self._quart_instance.register_blueprint(
            create_routes(route_injections))

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
        self.logger.info("[general]")
        self.logger.info("=> Metadata config file : %s",
                         self._config.general_metadata_config_file)
        self.logger.info("[routes]")
        self.logger.info("=> Identity Service API : %s",
                         self._config.apis_identity_svc)
        self.logger.info("=> CMS Service API : %s",
                         self._config.apis_cms_svc)
        self.logger.info("=> Web Portal Service API : %s",
                         self._config.apis_web_portal_svc)

        return True

    async def _shutdown_wait_task(self) -> None:
        await self.shutdown_event.wait()

    async def _check_identity_svc_status(self) -> bool:
        perform_check: bool = True

        while perform_check:
            try:
                data = await self._identity_svc_health_check()

                if data:
                    self.logger.info("[Identity Service]")
                    self.logger.info("=> Status: %s", data["status"])
                    self.logger.info("=> Version: %s", data["version"])
                    perform_check = False

                else:
                    await asyncio.sleep(3)

            except RuntimeError as ex:
                self._logger.critical(str(ex))
                return False

        return True

    async def _identity_svc_health_check(self) -> typing.Optional[dict]:
        url: str = f"{self._config.apis_identity_svc}system/health"

        response: ApiResponse = await self._rest_client.get(url, timeout=5)

        if response.status_code != http.HTTPStatus.OK:
            self.logger.warning(
                "Connection to identity service returned status %s",
                response.status_code)
            return None

        try:
            jsonschema.validate(instance=response.body,
                                schema=SCHEMA_IDENTITY_SVC_HEALTH_RESPONSE)

        except jsonschema.exceptions.ValidationError as ex:
            raise RuntimeError(
                "Schema for accounts service health check invalid!") from ex

        if response.body["version"] != __version__:
            self.logger.warning(
                "Identity Service version (%s) does not match gateway (%s),"
                ", unforeseen issues may occur!", response.body["version"],
                __version__)

        if response.body["status"] == ServiceDegradationStatus.CRITICAL.value:
            self.logger.warning("Identity service critically degraded, "
                                "retrying...")
            return None

        if response.body["status"] == ServiceDegradationStatus.DEGRADED.value:
            self.logger.warning("Identity service degraded, can continue, but"
                                " retries/slow-down may occur..")

        return response.body

    async def _check_cms_svc_status(self) -> bool:
        perform_check: bool = True

        while perform_check:
            try:
                data = await self._cms_svc_health_check()

                if data:
                    self.logger.info("[CMS Service]")
                    self.logger.info("=> Status: %s", data["status"])
                    self.logger.info("=> Version: %s", data["version"])
                    perform_check = False

                else:
                    await asyncio.sleep(3)

            except RuntimeError as ex:
                self._logger.critical(str(ex))
                return False

        return True

    async def _cms_svc_health_check(self) -> typing.Optional[dict]:
        url: str = f"{self._config.apis_cms_svc}system/health"

        response: ApiResponse = await self._rest_client.get(url, timeout=5)

        if response.status_code != http.HTTPStatus.OK:
            self.logger.warning(
                "Connection to CMS service returned status %s",
                response.status_code)
            return None

        try:
            jsonschema.validate(instance=response.body,
                                schema=SCHEMA_CMS_SVC_HEALTH_RESPONSE)

        except jsonschema.exceptions.ValidationError as ex:
            raise RuntimeError(
                "Schema for cms service health check invalid!") from ex

        if response.body["version"] != __version__:
            self._logger.warning(
                "CMS Service version (%s) does not match gateway (%s),"
                ", unforeseen issues may occur!", response.body["version"],
                __version__)

        if response.body["status"] == ServiceDegradationStatus.CRITICAL.value:
            self._logger.warning("CMS service critically degraded, "
                                 "retrying...")
            return None

        if response.body["status"] == ServiceDegradationStatus.DEGRADED.value:
            self._logger.warning("CMS service degraded, can continue, but"
                                 " retries/slow-down may occur..")

        return response.body
