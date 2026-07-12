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
from weaver_framework.configuration_system.configuration_manager import (
    ConfigurationManager)
from items.services.items_web_portal.configuration_layout import \
    ConfigurationConstants


class Configuration(ConfigurationManager):
    """Provides strongly typed access to application configuration settings.

    This class extends :class:`ConfigurationManager` by exposing commonly used
    configuration values as typed properties. Each property retrieves its value
    from the underlying configuration store using the appropriate section and
    key.
    """

    @property
    def logging_log_level(self) -> str:
        """Gets the configured logging level.

        Returns:
            The logging level configured for the application (for example,
            ``"DEBUG"``, ``"INFO"``, ``"WARNING"``, or ``"ERROR"``).
        """
        return self.get_entry(ConfigurationConstants.SECTION_LOGGING,
                              ConfigurationConstants.LOGGING_LOG_LEVEL)

    @property
    def general_api_signing_secret(self) -> str:
        """Gets the API signing secret.

        Returns:
            The secret used to sign and verify API requests.
        """
        return self.get_entry(
            ConfigurationConstants.SECTION_GENERAL,
            ConfigurationConstants.GENERAL_API_SIGNING_SECRET)

    @property
    def apis_gateway_svc(self) -> str:
        """Gets the gateway service base URL.

        Returns:
            The base URL used to communicate with the gateway service.
        """
        return self.get_entry(ConfigurationConstants.SECTION_APIS,
                              ConfigurationConstants.APIS_GATEWAY_SVC)
