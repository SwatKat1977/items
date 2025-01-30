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

CONFIGURATION_LAYOUT = configuration_setup.ConfigurationSetup(
    {
        "logging": [
            configuration_setup.ConfigurationSetupItem(
                "log_level", configuration_setup.ConfigItemDataType.STRING,
                valid_values=['DEBUG', 'INFO'], default_value="INFO")
        ],
        "apis": [
            configuration_setup.ConfigurationSetupItem(
                "accounts_svc", configuration_setup.ConfigItemDataType.STRING,
                default_value="http://localhost:3000/"),
            configuration_setup.ConfigurationSetupItem(
                "cms_svc", configuration_setup.ConfigItemDataType.STRING,
                default_value="http://localhost:4000/")
        ]
    }
)
