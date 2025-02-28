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
import typing
from base_application import BaseApplication
from base_sqlite_interface import SqliteInterfaceException
from configuration_layout import CONFIGURATION_LAYOUT
from logging_consts import LOGGING_DATETIME_FORMAT_STRING, \
                           LOGGING_DEFAULT_LOG_LEVEL, \
                           LOGGING_LOG_FORMAT_STRING
from sqlite_interface import SqliteInterface
from threadsafe_configuration import ThreadSafeConfiguration as Configuration
from version import BUILD_TAG, BUILD_VERSION, RELEASE_VERSION, \
                    SERVICE_COPYRIGHT_TEXT, LICENSE_TEXT
from apis import health_api
from apis import project_api
from apis import testcases_api
from state_object import StateObject


class Application(BaseApplication):
    """ ITEMS Accounts Service """

    def __init__(self, quart_instance):
        super().__init__()
        self._quart_instance = quart_instance
        self._db: typing.Optional[SqliteInterface] = None
        self._state_object: StateObject = StateObject()

        self._logger = logging.getLogger(__name__)
        log_format= logging.Formatter(LOGGING_LOG_FORMAT_STRING,
                                      LOGGING_DATETIME_FORMAT_STRING)
        console_stream = logging.StreamHandler()
        console_stream.setFormatter(log_format)
        self._logger.setLevel(LOGGING_DEFAULT_LOG_LEVEL)
        self._logger.addHandler(console_stream)

    def _initialise(self) -> bool:

        build = f"V{RELEASE_VERSION}-{BUILD_VERSION}{BUILD_TAG}"

        self._logger.info('ITEMS CMS Microservice %s', build)
        self._logger.info(SERVICE_COPYRIGHT_TEXT)
        self._logger.info(LICENSE_TEXT)

        # Set the version string on state object.
        self._state_object.version = build

        if not self._manage_configuration():
            return False

        self._logger.info('Setting logging level to %s',
                          Configuration().logging_log_level)
        self._logger.setLevel(Configuration().logging_log_level)

        # Open databases.
        if not self._open_database():
            return False

        health_blueprint = health_api.create_blueprint(self._logger,
                                                       self._state_object)
        self._quart_instance.register_blueprint(health_blueprint)

        project_blueprint = project_api.create_blueprint(self._logger,
                                                       self._db)
        self._quart_instance.register_blueprint(project_blueprint)

        testcases_blueprint = testcases_api.create_blueprint(self._logger,
                                                             self._db)
        self._quart_instance.register_blueprint(testcases_blueprint)

        return True

    async def _main_loop(self) -> None:
        """ Abstract method for main application. """
        await asyncio.sleep(0.1)

    def _shutdown(self):
        """ Abstract method for application shutdown. """

    def _manage_configuration(self) -> bool:
        """
        Manage the service configuration.
        """

        config_file = os.getenv("ITEMS_CMS_SVC_CONFIG_FILE", None)

        config_file_required_str: str = os.getenv(
            "ITEMS_CMS_SVC_CONFIG_FILE_REQUIRED", None)

        config_file_required: bool = False
        if config_file_required_str is not None and config_file_required_str == "1":
            config_file_required = True

        self._logger.info("Configuration file required? %s",
                          "True" if config_file_required else "False")

        if not config_file and config_file_required:
            self._logger.critical("Configuration file missing!")
            return False

        if config_file_required:
            self._logger.info("Configuration file : %s", config_file)

        Configuration().configure(CONFIGURATION_LAYOUT, config_file,
                                  config_file_required)

        try:
            Configuration().process_config()

        except ValueError as ex:
            self._logger.critical("Configuration error : %s", str(ex))
            return False

        self._logger.info("Configuration")
        self._logger.info("=============")

        self._logger.info("[logging]")
        self._logger.info("=> Logging log level : %s",
                          Configuration().logging_log_level)

        self._logger.info("[Backend]")
        self._logger.info("=> Database filename : %s",
                          Configuration().backend_db_filename)

        return True

    def _open_database(self) -> bool:
        self._logger.info("Opening internal database...")

        status: bool = False

        filename: str = Configuration().backend_db_filename

        self._db = SqliteInterface(self._logger, filename, self._state_object)

        try:
            self._db.open()

        except SqliteInterfaceException as ex:
            self._logger.critical("Unable to open '%s', reason: %s",
                                  filename, str(ex))

        else:
            self._logger.info("Database '%s' opened successful", filename)
            status = True

        return status
