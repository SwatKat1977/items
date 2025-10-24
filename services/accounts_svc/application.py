"""
Copyright 2025 Integrated Test Management Suite Development Team

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
import os
from items_common.base_microservice import BaseMicroservice
from configuration_layout import CONFIGURATION_LAYOUT
from logging_consts import LOGGING_DATETIME_FORMAT_STRING, \
                           LOGGING_DEFAULT_LOG_LEVEL, \
                           LOGGING_LOG_FORMAT_STRING
from threadsafe_configuration import ThreadSafeConfiguration as Configuration
from version import BUILD_TAG, BUILD_VERSION, RELEASE_VERSION, \
                    SERVICE_COPYRIGHT_TEXT, LICENSE_TEXT
from apis import create_routes

#class Application(BaseApplication):
class Service(BaseMicroservice):
    """ ITEMS Accounts Service """

    CONFIG_FILE_ENV: str = "ITEMS_ACCOUNTS_SVC_CONFIG_FILE"
    CONFIG_REQUIRED_ENV: str = "ITEMS_ACCOUNTS_SVC_CONFIG_FILE_REQUIRED"

    def __init__(self, quart_instance):
        super().__init__()
        self._quart_instance = quart_instance

        self._logger = logging.getLogger(__name__)
        log_format = logging.Formatter(LOGGING_LOG_FORMAT_STRING,
                                       LOGGING_DATETIME_FORMAT_STRING)
        console_stream = logging.StreamHandler()
        console_stream.setFormatter(log_format)
        self._logger.setLevel(LOGGING_DEFAULT_LOG_LEVEL)
        self._logger.addHandler(console_stream)

    async def _initialise(self) -> bool:

        build = f"V{RELEASE_VERSION}-{BUILD_VERSION}{BUILD_TAG}"

        self._logger.info('ITEMS Accounts Microservice %s', build)
        self._logger.info(SERVICE_COPYRIGHT_TEXT)
        self._logger.info(LICENSE_TEXT)

        if not self._manage_configuration():
            return False

        self._logger.info('Setting logging level to %s',
                          Configuration().logging_log_level)
        self._logger.setLevel(Configuration().logging_log_level)

        if not os.path.isfile(Configuration().backend_db_filename):
            self._logger.critical("Backend database file '%s' is missing!",
                                  Configuration().backend_db_filename)
            return False

        self._quart_instance.register_blueprint(
            create_routes(self._logger, self._service_state))

        return True

    async def _main_loop(self) -> None:
        """ Abstract method for main application. """
        await asyncio.sleep(0.1)

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

        Configuration().configure(CONFIGURATION_LAYOUT, config_file, required)

        try:
            Configuration().process_config()

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
                          Configuration().logging_log_level)
        self._logger.info("[Backend]")
        self._logger.info("=> Database filename : %s",
                          Configuration().backend_db_filename)

        return True
