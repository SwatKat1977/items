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
import json
import logging
import os
import types
import jsonschema
import requests
from logging_consts import LOGGING_DATETIME_FORMAT_STRING, \
                           LOGGING_DEFAULT_LOG_LEVEL, \
                           LOGGING_LOG_FORMAT_STRING
from version import BUILD_TAG, BUILD_VERSION, RELEASE_VERSION, \
                    SERVICE_COPYRIGHT_TEXT, LICENSE_TEXT
from base_application import BaseApplication
from configuration_layout import CONFIGURATION_LAYOUT
from threadsafe_configuration import ThreadSafeConfiguration as Configuration
from interfaces.accounts.health import SCHEMA_HEALTH_RESPONSE
import service_health_enums as health_enums

class Application(BaseApplication):
    """ ITEMS Accounts Service """

    def __init__(self, quart_instance):
        super().__init__()
        self._quart_instance = quart_instance

        self._logger = logging.getLogger(__name__)
        log_format= logging.Formatter(LOGGING_LOG_FORMAT_STRING,
                                      LOGGING_DATETIME_FORMAT_STRING)
        console_stream = logging.StreamHandler()
        console_stream.setFormatter(log_format)
        self._logger.setLevel(LOGGING_DEFAULT_LOG_LEVEL)
        self._logger.addHandler(console_stream)

    def _initialise(self) -> bool:

        version_info: str = f"V{RELEASE_VERSION}-{BUILD_VERSION}{BUILD_TAG}"

        self._logger.info('ITEMS Gateway Microservice %s', version_info)
        self._logger.info(SERVICE_COPYRIGHT_TEXT)
        self._logger.info(LICENSE_TEXT)

        if not self._manage_configuration():
            return False

        self._logger.info('Setting logging level to %s',
                          Configuration().logging_log_level)
        self._logger.setLevel(Configuration().logging_log_level)

        return self._perform_accounts_health_check(version_info)

        return True

    async def _main_loop(self) -> None:
        """ Main application loop """
        await asyncio.sleep(0.1)

    def _shutdown(self):
        """ Application shutdown. """

    def _manage_configuration(self) -> bool:
        """
        Manage the service configuration.
        """

        config_file = os.getenv("ITEMS_GATEWAY_SVC_CONFIG_FILE", None)

        config_file_required_str: str = os.getenv(
            "ITEMS_GATEWAY_SVC_CONFIG_FILE_REQUIRED", None)

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
        self._logger.info("=> Accounts Service API : %s",
                          Configuration().apis_accounts_svc)
        self._logger.info("=> CMS Service API : %s",
                          Configuration().apis_cms_svc)

        return True

    def _perform_accounts_health_check(self, version_info: str) -> bool:
        url: str = f"{Configuration().apis_accounts_svc}health/status"

        perform_check: bool = True

        while perform_check:
            try:
                response = requests.get(url)

            except requests.exceptions.ConnectionError as ex:
                self._logger.error("Connection to accounts service timed out: %s",
                                   str(ex))
                return False

            if response is None:
                self._logger.error(
                    "Missing/invalid JSON body for accounts svc health call")
                return False

            try:
                json_data = json.loads(response.text)

            except (TypeError, json.JSONDecodeError):
                self._logger.error(
                    "Invalid JSON body type for accounts svc health call")
                return False

            try:
                jsonschema.validate(instance=json_data,
                                    schema=SCHEMA_HEALTH_RESPONSE)

            except jsonschema.exceptions.ValidationError:
                self._logger.critical(
                    "Schema for accounts service health check invalid!")
                return False

            if json_data["status"] == health_enums.STATUS_CRITICAL:
                self._logger.critical("Accounts service critically degraded, "
                                      "access to accounts service discontinued "
                                      "until it is fixed")
                return False

            elif json_data["status"] == health_enums.STATUS_DEGRADED:
                self._logger.warning("Accounts service degraded, can continue, but"
                                     " retries/slow-down may occur..")

            if json_data["version"] != version_info:
                self._logger.warning(
                    "Accounts Service version (%s) does not match gateway (%s),"
                    ", unforeseen issues may occur!", json_data["version"],
                    version_info)

            self._logger.info("[Accounts API]")
            self._logger.info("=> Status: %s", json_data["status"])
            self._logger.info("=> Version: %s", json_data["version"])
            perform_check = False

        return True

    def _perform_accounts_health_check2(self, version_info: str) -> bool:
        url: str = f"{Configuration().apis_accounts_svc}health/status"

        try:
            response = requests.get(url)

        except requests.exceptions.ConnectionError as ex:
            self._logger.error("Connection to accounts service timed out: %s",
                               str(ex))
            return False

        if response is None:
            self._logger.error(
                "Missing/invalid JSON body for accounts svc health call")
            return False

        try:
            json_data = json.loads(response.text)

        except (TypeError, json.JSONDecodeError):
            self._logger.error(
                "Invalid JSON body type for accounts svc health call")
            return False

        print(json_data)

        try:
            jsonschema.validate(instance=json_data,
                                schema=SCHEMA_HEALTH_RESPONSE)

        except jsonschema.exceptions.ValidationError as ex:
            self._logger.critical(
                "Schema for accounts service health check invalid!")
            return False

        if json_data["version"] == version_info:
            self._logger.warning(
                "Accounts Service version (%s) does not match gateway (%s),"
                ", unforeseen issues may occur!", json_data["version"],
                version_info)

        if json_data["status"] == "healthy":
            self._logger.critical("Accounts service critically degraded, "
                                  "access to accounts service discontinued "
                                  "until it is fixed")
        else:
            self._logger.warning("Accounts service degraded, can continue, but"
                                 "retries/slow-down may occur..")

        return False
