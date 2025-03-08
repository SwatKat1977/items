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
import time
import typing
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
from interfaces.accounts.health import SCHEMA_ACCOUNTS_SVC_HEALTH_RESPONSE
from interfaces.cms.health import SCHEMA_CMS_SVC_HEALTH_RESPONSE
from apis import handshake_api
from apis import project_api
from apis import testcase_api
import service_health_enums as health_enums
from sessions import Sessions
from metadata_handler import MetadataHandler


class Application(BaseApplication):
    """ ITEMS Accounts Service """

    def __init__(self, quart_instance):
        super().__init__()
        self._quart_instance = quart_instance
        self._sessions: Sessions = Sessions()

        self._logger = logging.getLogger(__name__)
        log_format = logging.Formatter(LOGGING_LOG_FORMAT_STRING,
                                       LOGGING_DATETIME_FORMAT_STRING)
        console_stream = logging.StreamHandler()
        console_stream.setFormatter(log_format)
        self._logger.setLevel(LOGGING_DEFAULT_LOG_LEVEL)
        self._logger.addHandler(console_stream)

        self._metadata_handler: MetadataHandler = MetadataHandler(self._logger)

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

        if not self._metadata_handler.read_metadata_file():
            return False

        if not self._metadata_handler.update_web_portal_webhook(-1):
            return False

        if not self._check_accounts_svc_api_status(version_info):
            return False

        if not self._check_cms_svc_api_status(version_info):
            return False

        handshake_blueprint = handshake_api.create_blueprint(
            self._logger, self._sessions)
        self._quart_instance.register_blueprint(handshake_blueprint)

        project_blueprint = project_api.create_blueprint(self._logger)
        self._quart_instance.register_blueprint(project_blueprint)

        testcase_blueprint = testcase_api.create_blueprint(
            self._logger, self._sessions)
        self._quart_instance.register_blueprint(testcase_blueprint)

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

        self._logger.info("[general]")
        self._logger.info("=> Metadata config file : %s",
                          Configuration().general_metadata_config_file)

        self._logger.info("[apis]")
        self._logger.info("=> Accounts Service API : %s",
                          Configuration().apis_accounts_svc)
        self._logger.info("=> CMS Service API : %s",
                          Configuration().apis_cms_svc)
        self._logger.info("=> Web Portal Service API : %s",
                          Configuration().apis_web_portal_svc)

        return True

    def _check_accounts_svc_api_status(self, version_info: str) -> bool:
        perform_check: bool = True

        while perform_check:
            try:
                data = self._accounts_svc_api_health_check(version_info)

                if data:
                    self._logger.info("[Accounts API]")
                    self._logger.info("=> Status: %s", data["status"])
                    self._logger.info("=> Version: %s", data["version"])
                    perform_check = False

                else:
                    time.sleep(3)

            except RuntimeError as ex:
                self._logger.critical(str(ex))
                return False

        return True

    def _accounts_svc_api_health_check(self, version_info: str) \
            -> typing.Optional[dict]:
        url: str = f"{Configuration().apis_accounts_svc}health/status"

        try:
            response = requests.get(url, timeout=1)

        except requests.exceptions.ConnectionError as ex:
            self._logger.error("Connection to accounts service timed out: %s",
                               str(ex))
            return None

        if response is None:
            raise RuntimeError(
                "Missing/invalid JSON accounts svc health call JSON body")

        try:
            json_data = json.loads(response.text)

        except (TypeError, json.JSONDecodeError) as ex:
            raise RuntimeError(
                "Invalid JSON body type for accounts svc health call") from ex

        try:
            jsonschema.validate(instance=json_data,
                                schema=SCHEMA_ACCOUNTS_SVC_HEALTH_RESPONSE)

        except jsonschema.exceptions.ValidationError as ex:
            raise RuntimeError(
                "Schema for accounts service health check invalid!") from ex

        if json_data["version"] != version_info:
            self._logger.warning(
                "Accounts Service version (%s) does not match gateway (%s),"
                ", unforeseen issues may occur!", json_data["version"],
                version_info)

        if json_data["status"] == health_enums.STATUS_CRITICAL:
            msg: str = "Accounts service critically degraded, access to "\
                       "accounts service discontinued until it is fixed"
            raise RuntimeError(msg)

        if json_data["status"] == health_enums.STATUS_DEGRADED:
            self._logger.warning("Accounts service degraded, can continue, but"
                                 " retries/slow-down may occur..")

        return json_data

    def _check_cms_svc_api_status(self, version_info: str) -> bool:
        perform_check: bool = True

        while perform_check:
            try:
                data = self._cms_svc_api_health_check(version_info)

                if data:
                    self._logger.info("[CMS API]")
                    self._logger.info("=> Status: %s", data["status"])
                    self._logger.info("=> Version: %s", data["version"])
                    perform_check = False

                else:
                    time.sleep(3)

            except RuntimeError as ex:
                self._logger.critical(str(ex))
                return False

        return True

    def _cms_svc_api_health_check(self, version_info: str) \
            -> typing.Optional[dict]:
        url: str = f"{Configuration().apis_cms_svc}health/status"

        try:
            response = requests.get(url, timeout=1)

        except requests.exceptions.ConnectionError as ex:
            self._logger.error("Connection to cms service timed out: %s",
                               str(ex))
            return None

        if response is None:
            raise RuntimeError(
                "Missing/invalid JSON cms svc health call JSON body")

        try:
            json_data = json.loads(response.text)

        except (TypeError, json.JSONDecodeError) as ex:
            raise RuntimeError(
                "Invalid JSON body type for cms svc health call") from ex

        try:
            jsonschema.validate(instance=json_data,
                                schema=SCHEMA_CMS_SVC_HEALTH_RESPONSE)

        except jsonschema.exceptions.ValidationError as ex:
            raise RuntimeError(
                "Schema for cms service health check invalid!") from ex

        if json_data["version"] != version_info:
            self._logger.warning(
                "CMS Service version (%s) does not match gateway (%s),"
                ", unforeseen issues may occur!", json_data["version"],
                version_info)

        if json_data["status"] == health_enums.STATUS_CRITICAL:
            msg: str = "CMS service critically degraded, access to "\
                       "cms service discontinued until it is fixed"
            raise RuntimeError(msg)

        if json_data["status"] == health_enums.STATUS_DEGRADED:
            self._logger.warning("CMS service degraded, can continue, but"
                                 " retries/slow-down may occur..")

        return json_data
