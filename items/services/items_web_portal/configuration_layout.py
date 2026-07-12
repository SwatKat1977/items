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

# ___pylint___: disable=too-few-public-methods

APIS_GATEWAY_SVC_DEFAULT = "http://localhost:7050/"


class ConfigurationConstants:
    """ Constants for the microservice configuration. """
    # pylint: disable=too-few-public-methods

    SECTION_LOGGING: str = 'logging'
    SECTION_APIS: str = 'routes'
    SECTION_GENERAL: str = 'general'

    LOGGING_LOG_LEVEL: str = 'log_level'
    LOG_LEVEL_DEBUG: str = 'DEBUG'
    LOG_LEVEL_INFO: str = 'INFO'

    GENERAL_API_SIGNING_SECRET: str = "api_signing_secret"

    APIS_GATEWAY_SVC: str = "gateway_svc"


CONFIGURATION_LAYOUT = ConfigurationSetup(
    {
        ConfigurationConstants.SECTION_LOGGING: [
            ConfigurationSetupItem(
                ConfigurationConstants.LOGGING_LOG_LEVEL,
                ConfigItemDataType.STRING,
                valid_values=[ConfigurationConstants.LOG_LEVEL_DEBUG,
                              ConfigurationConstants.LOG_LEVEL_INFO],
                default_value=ConfigurationConstants.LOG_LEVEL_INFO)
        ],
        ConfigurationConstants.SECTION_GENERAL: [
            ConfigurationSetupItem(
                ConfigurationConstants.GENERAL_API_SIGNING_SECRET,
                ConfigItemDataType.STRING,
                is_required=True),
        ],
        ConfigurationConstants.SECTION_APIS: [
            ConfigurationSetupItem(
                ConfigurationConstants.APIS_GATEWAY_SVC,
                ConfigItemDataType.STRING,
                default_value=APIS_GATEWAY_SVC_DEFAULT)
        ]
    }
)
