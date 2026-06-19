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
from weaver_framework.configuration_system.configuration_setup import (
    ConfigItemDataType, ConfigurationSetup, ConfigurationSetupItem)
# pylint: disable=too-few-public-methods


class ConfigurationConstants:
    """ Constants for the microservice configuration. """

    SECTION_LOGGING: str = 'logging'
    SECTION_BACKEND: str = 'backend'

    ITEM_LOGGING_LOG_LEVEL: str = 'log_level'
    LOG_LEVEL_DEBUG: str = 'DEBUG'
    LOG_LEVEL_INFO: str = 'INFO'

    ITEM_BACKEND_DB_FILENAME: str = 'db_filename'


CONFIGURATION_LAYOUT = ConfigurationSetup(
    {
        ConfigurationConstants.SECTION_LOGGING: [
            ConfigurationSetupItem(
                ConfigurationConstants.ITEM_LOGGING_LOG_LEVEL,
                ConfigItemDataType.STRING,
                valid_values=[ConfigurationConstants.LOG_LEVEL_DEBUG,
                              ConfigurationConstants.LOG_LEVEL_INFO],
                default_value=ConfigurationConstants.LOG_LEVEL_INFO)
        ],
        ConfigurationConstants.SECTION_BACKEND: [
            ConfigurationSetupItem(
                ConfigurationConstants.ITEM_BACKEND_DB_FILENAME,
                ConfigItemDataType.STRING,
                default_value="items_accounts_svc.db")
        ]
    }
)
