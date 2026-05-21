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
from pathlib import Path
from quart import Quart
from weaver_framework.microservice.base_microservice import BaseMicroservice
from items.shared import LICENSE_TEXT, SERVICE_COPYRIGHT_TEXT, __version__
from items.shared.service_state import ServiceState
from items.services.items_identity.identity_configuration import \
    IdentityConfiguration
from items.services.items_identity.apis import create_routes
from items.services.items_identity.configuration_layout import \
    CONFIGURATION_LAYOUT
from items.services.items_identity.repositories.user_repository import \
    UserRepository
from items.services.items_identity.data_access.authentication_service import \
    AuthenticationService


class Service(BaseMicroservice):
    """ ITEMS Identity Microservice """

    CONFIG_FILE_ENV: str = "ITEMS_IDENTITY_CONFIG_FILE"
    CONFIG_REQUIRED_ENV: str = "ITEMS_IDENTITY_CONFIG_FILE_REQUIRED"

    def __init__(self, quart_instance: Quart):
        super().__init__()
        self._quart_instance = quart_instance
        self._service_state: ServiceState = ServiceState()
        self._config: IdentityConfiguration = IdentityConfiguration()
        self._user_repository: UserRepository | None = None
        self._authentication_service: AuthenticationService | None = None

        self._service_state.database_enabled = True

    async def _initialise(self) -> bool:
        self.logger.info('ITEMS Identity Microservice %s', __version__)
        self.logger.info(SERVICE_COPYRIGHT_TEXT)
        self.logger.info(LICENSE_TEXT)

        if not self._manage_configuration():
            return False

        self.logger.info('Setting logging level to %s',
                         self._config.logging_log_level)
        self.logger.setLevel(self._config.logging_log_level)

        self._user_repository = UserRepository(self.logger,
                                               self._config)
        self._authentication_service = AuthenticationService(
            self.logger,
            self._service_state,
            self._user_repository)

        db_filename: Path = Path(self._config.backend_db_filename)
        if not db_filename.is_file():
            self._logger.critical("Backend database file '%s' is missing!",
                                  db_filename)
            return False

        self._quart_instance.register_blueprint(
            create_routes(self._logger, self._service_state))

        return True

    async def _create_tasks(self) -> list[asyncio.Task]:
        """ Create and return the service's background tasks. """
        return [asyncio.create_task(self._dummy_task())]

    async def _shutdown(self):
        """ Abstract method for application shutdown. """

    def _manage_configuration(self) -> bool:
        """
        Manage the service configuration.
        """
        error_status, required, config_file = self._check_for_configuration(
            self.CONFIG_FILE_ENV,self.CONFIG_REQUIRED_ENV)
        if error_status:
            self._logger.critical(error_status)
            return False

        self._config.configure(CONFIGURATION_LAYOUT, config_file, required)

        try:
            self._config.process_config()

        except ValueError as ex:
            self._logger.critical("Configuration error : %s", str(ex))
            return False

        self._logger.info("Configuration")
        self._logger.info("=============")

        self._logger.info("Configuration file required: %s",
                          "True" if required else "False")
        self._logger.info("Configuration file : %s",
                          "None"if not required else config_file)
        self._logger.info("[logging]")
        self._logger.info("=> Logging log level : %s",
                          self._config.logging_log_level)
        self._logger.info("[Backend]")
        self._logger.info("=> Database filename : %s",
                          self._config.backend_db_filename)

        return True

    async def _dummy_task(self) -> None:
        await self.shutdown_event.wait()
