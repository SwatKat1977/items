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
from weaver_framework.configuration_system.configuration_setup import (
    ConfigItemDataType, ConfigurationSetup, ConfigurationSetupItem)
# pylint: disable=too-few-public-methods


class ConfigurationConstants:
    """ Constants for the microservice configuration. """

    SECTION_LOGGING: str = "logging"
    SECTION_GENERAL: str = "general"
    SECTION_APIS: str = "apis"

    LOGGING_LOG_LEVEL: str = "log_level"
    LOGGING_LOG_LEVEL_DEBUG: str = "DEBUG"
    LOGGING_LOG_LEVEL_INFO: str = "INFO"

    GENERAL_METADATA_CONFIG_FILE: str = "metadata_config_file"
    GENERAL_METADATA_CONFIG_FILE_DEFAULT: str = "metadata.config"
    GENERAL_API_SIGNING_SECRET: str = "api_signing_secret"

    APIS_IDENTITY_SVC: str = "identity_svc"
    APIS_CMS_SVC: str = "cms_svc"
    APIS_WEB_PORTAL_SVC: str = "web_portal_svc"
    APIS_IDENTITY_SVC_DEFAULT: str = "http://localhost:5050/"
    APIS_CMS_SVC_DEFAULT: str = "http://localhost:6050/"
    APIS_WEB_PORTAL_SVC_DEFAULT: str = "http://localhost:8080/"

    SECTION_SMTP: str = "smtp"
    SMTP_HOST: str = "host"
    SMTP_PORT: str = "port"
    SMTP_USERNAME: str = "username"
    SMTP_PASSWORD: str = "password"
    SMTP_FROM_ADDRESS: str = "from_address"
    SMTP_USE_TLS: str = "use_tls"
    SMTP_HOST_DEFAULT: str = "localhost"
    SMTP_PORT_DEFAULT: int = 1025
    SMTP_USE_TLS_DEFAULT: bool = False


CONFIGURATION_LAYOUT = ConfigurationSetup(
    {
        ConfigurationConstants.SECTION_LOGGING: [
            ConfigurationSetupItem(
                ConfigurationConstants.LOGGING_LOG_LEVEL,
                ConfigItemDataType.STRING,
                valid_values=[ConfigurationConstants.LOGGING_LOG_LEVEL_DEBUG,
                              ConfigurationConstants.LOGGING_LOG_LEVEL_INFO],
                default_value=ConfigurationConstants.LOGGING_LOG_LEVEL_INFO)
        ],

        ConfigurationConstants.SECTION_GENERAL: [
            ConfigurationSetupItem(
                ConfigurationConstants.GENERAL_METADATA_CONFIG_FILE,
                ConfigItemDataType.STRING,
                default_value=
                ConfigurationConstants.GENERAL_METADATA_CONFIG_FILE_DEFAULT),
            ConfigurationSetupItem(
                ConfigurationConstants.GENERAL_API_SIGNING_SECRET,
                ConfigItemDataType.STRING,
                is_required=True),
        ],

        ConfigurationConstants.SECTION_APIS: [
            ConfigurationSetupItem(
                ConfigurationConstants.APIS_IDENTITY_SVC,
                ConfigItemDataType.STRING,
                default_value=
                ConfigurationConstants.APIS_IDENTITY_SVC_DEFAULT),
            ConfigurationSetupItem(
                ConfigurationConstants.APIS_CMS_SVC,
                ConfigItemDataType.STRING,
                default_value=
                ConfigurationConstants.APIS_CMS_SVC_DEFAULT),
            ConfigurationSetupItem(
                ConfigurationConstants.APIS_WEB_PORTAL_SVC,
                ConfigItemDataType.STRING,
                default_value=
                ConfigurationConstants.APIS_WEB_PORTAL_SVC_DEFAULT)
        ],

        ConfigurationConstants.SECTION_SMTP: [
            ConfigurationSetupItem(
                ConfigurationConstants.SMTP_HOST,
                ConfigItemDataType.STRING,
                default_value=ConfigurationConstants.SMTP_HOST_DEFAULT),
            ConfigurationSetupItem(
                ConfigurationConstants.SMTP_PORT,
                ConfigItemDataType.INTEGER,
                default_value=ConfigurationConstants.SMTP_PORT_DEFAULT),
            ConfigurationSetupItem(
                ConfigurationConstants.SMTP_USERNAME,
                ConfigItemDataType.STRING,
                is_required=False),
            ConfigurationSetupItem(
                ConfigurationConstants.SMTP_PASSWORD,
                ConfigItemDataType.STRING,
                is_required=False),
            ConfigurationSetupItem(
                ConfigurationConstants.SMTP_FROM_ADDRESS,
                ConfigItemDataType.STRING,
                is_required=False),
            ConfigurationSetupItem(
                ConfigurationConstants.SMTP_USE_TLS,
                ConfigItemDataType.BOOLEAN,
                default_value=ConfigurationConstants.SMTP_USE_TLS_DEFAULT),
        ]
    }
)
