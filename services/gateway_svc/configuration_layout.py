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
from configuration import configuration_setup

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

    APIS_ACCOUNTS_SVC: str = "accounts_svc"
    APIS_CMS_SVC: str = "cms_svc"
    APIS_WEB_PORTAL_SVC: str = "web_portal_svc"
    APIS_ACCOUNTS_SVC_DEFAULT: str = "http://localhost:4000/"
    APIS_CMS_SVC_DEFAULT: str = "http://localhost:5000/"
    APIS_WEB_PORTAL_SVC_DEFAULT: str = "http://localhost:8080/"


CONFIGURATION_LAYOUT = configuration_setup.ConfigurationSetup(
    {
        ConfigurationConstants.SECTION_LOGGING: [
            configuration_setup.ConfigurationSetupItem(
                ConfigurationConstants.LOGGING_LOG_LEVEL,
                configuration_setup.ConfigItemDataType.STRING,
                valid_values=[ConfigurationConstants.LOGGING_LOG_LEVEL_DEBUG,
                              ConfigurationConstants.LOGGING_LOG_LEVEL_INFO],
                default_value=ConfigurationConstants.LOGGING_LOG_LEVEL_INFO)
        ],

        ConfigurationConstants.SECTION_GENERAL: [
            configuration_setup.ConfigurationSetupItem(
                ConfigurationConstants.GENERAL_METADATA_CONFIG_FILE,
                configuration_setup.ConfigItemDataType.STRING,
                default_value=
                ConfigurationConstants.GENERAL_METADATA_CONFIG_FILE_DEFAULT),
            configuration_setup.ConfigurationSetupItem(
                ConfigurationConstants.GENERAL_API_SIGNING_SECRET,
                configuration_setup.ConfigItemDataType.STRING,
                is_required=True),
        ],

        ConfigurationConstants.SECTION_APIS: [
            configuration_setup.ConfigurationSetupItem(
                ConfigurationConstants.APIS_ACCOUNTS_SVC,
                configuration_setup.ConfigItemDataType.STRING,
                default_value=
                ConfigurationConstants.APIS_ACCOUNTS_SVC_DEFAULT),
            configuration_setup.ConfigurationSetupItem(
                ConfigurationConstants.APIS_CMS_SVC,
                configuration_setup.ConfigItemDataType.STRING,
                default_value=
                ConfigurationConstants.APIS_CMS_SVC_DEFAULT),
            configuration_setup.ConfigurationSetupItem(
                ConfigurationConstants.APIS_WEB_PORTAL_SVC,
                configuration_setup.ConfigItemDataType.STRING,
                default_value=
                ConfigurationConstants.APIS_WEB_PORTAL_SVC_DEFAULT)
        ]
    }
)
