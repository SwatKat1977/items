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
import http
import logging
import os
import time
import uuid
import requests
from base_application import BaseApplication
from logging_consts import LOGGING_DATETIME_FORMAT_STRING, \
                           LOGGING_DEFAULT_LOG_LEVEL, \
                           LOGGING_LOG_FORMAT_STRING
from version import BUILD_TAG, BUILD_VERSION, RELEASE_VERSION, \
                    SERVICE_COPYRIGHT_TEXT, LICENSE_TEXT
from configuration_layout import CONFIGURATION_LAYOUT
from threadsafe_configuration import ThreadSafeConfiguration as Configuration
from apis import auth_api
from apis import dashboard_api
from apis import test_cases_api
from apis import webhook_api
from base_view import BaseView
from metadata_settings import MetadataSettings

GET_METADATA_INFINITE_RETRIES: int = -1


class Application(BaseApplication):
    """ ITEMS Accounts Service """

    def __init__(self, quart_instance):
        super().__init__()
        self._quart_instance = quart_instance
        self._metadata_settings: MetadataSettings = MetadataSettings()

        self._logger = logging.getLogger(__name__)
        log_format = logging.Formatter(LOGGING_LOG_FORMAT_STRING,
                                       LOGGING_DATETIME_FORMAT_STRING)
        console_stream = logging.StreamHandler()
        console_stream.setFormatter(log_format)
        self._logger.setLevel(LOGGING_DEFAULT_LOG_LEVEL)
        self._logger.addHandler(console_stream)

    def _initialise(self) -> bool:

        build = f"V{RELEASE_VERSION}-{BUILD_VERSION}{BUILD_TAG}"

        self._logger.info('ITEMS Web Portal Microservice %s', build)
        self._logger.info(SERVICE_COPYRIGHT_TEXT)
        self._logger.info(LICENSE_TEXT)

        if not self._manage_configuration():
            return False

        self._logger.info('Setting logging level to %s',
                          Configuration().logging_log_level)
        self._logger.setLevel(Configuration().logging_log_level)

        if not self.get_metadata(GET_METADATA_INFINITE_RETRIES):
            return False

        auth_blueprint = auth_api.create_blueprint(
            self._logger, self._metadata_settings)
        self._quart_instance.register_blueprint(auth_blueprint)

        dashboard_blueprint = dashboard_api.create_blueprint(
            self._logger, self._metadata_settings)
        self._quart_instance.register_blueprint(dashboard_blueprint)

        test_cases_blueprint = test_cases_api.create_blueprint(
            self._logger, self._metadata_settings)
        self._quart_instance.register_blueprint(test_cases_blueprint)

        webhook_blueprint = webhook_api.create_blueprint(
            self._logger, self._metadata_settings)
        self._quart_instance.register_blueprint(webhook_blueprint)

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

        config_file = os.getenv("ITEMS_WEB_PORTAL_SVC_CONFIG_FILE", None)

        config_file_required_str: str = os.getenv(
            "ITEMS_WEB_PORTAL_SVC_CONFIG_FILE_REQUIRED", None)

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

        self._logger.info("[apis]")
        self._logger.info("=> Gateway Service API : %s",
                          Configuration().apis_gateway_svc)

        return True

    def get_metadata(self, retries: int = 0) -> bool:
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
        perform_update: int = 1 if retries in (0,
                                               GET_METADATA_INFINITE_RETRIES) \
                                else retries

        # Generate number used once (NONCE)
        nonce = str(uuid.uuid4())

        string_to_sign: str = f"/webhook/get_metadata:{nonce}"
        secret: bytes = Configuration().general_api_signing_secret.encode()
        signature: str = BaseView.generate_api_signature(secret, string_to_sign)
        headers = {
            "Content-Type": "application/json",
            "X-Signature": signature
        }

        base_path: str = Configuration().apis_gateway_svc
        url: str = f"{base_path}webhook/get_metadata?nonce={nonce}"

        while perform_update != 0:
            try:
                response = requests.get(url, timeout=1, headers=headers)

                if response.status_code == http.HTTPStatus.OK:
                    data: dict = response.json()
                    self._metadata_settings.default_time_zone = \
                        data["default_time_zone"]
                    self._metadata_settings.using_server_default_time_zone = \
                        data["using_server_default_time_zone"]
                    self._metadata_settings.instance_name = \
                        data["instance_name"]

                    self._logger.info("Successfully updated Web Portal with "
                                      "metadata configuration items")
                    return True

            except requests.exceptions.ConnectionError as ex:
                self._logger.error(("Connection to web portal service timed "
                                    "out whilst getting metadata: %s"),
                                   str(ex))

            self._logger.warning("Unable to update Web Portal with metadata "
                                 "configuration items")

            if retries != GET_METADATA_INFINITE_RETRIES:
                perform_update -= 1

            time.sleep(3)

        self._logger.critical("Failed to update Web Portal with metadata "
                              "configuration items")
        return False
