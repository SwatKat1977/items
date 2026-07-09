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
from items.services.items_gateway.configuration_layout import \
    ConfigurationConstants


class GatewayConfiguration(ConfigurationManager):
    """Provides typed access to gateway configuration settings."""

    @property
    def logging_log_level(self) -> str:
        """ Configuration property : Logging | log level """
        return self.get_entry(ConfigurationConstants.SECTION_LOGGING,
                              ConfigurationConstants.LOGGING_LOG_LEVEL)

    @property
    def general_metadata_config_file(self) -> str:
        """ Configuration property : General | metadata config file """

        return self.get_entry(ConfigurationConstants.SECTION_GENERAL,
                              ConfigurationConstants.GENERAL_METADATA_CONFIG_FILE)

    @property
    def general_api_signing_secret(self) -> str:
        """ Configuration property : General | API signing secret """
        return self.get_entry(ConfigurationConstants.SECTION_GENERAL,
                              ConfigurationConstants.GENERAL_API_SIGNING_SECRET)

    @property
    def apis_identity_svc(self) -> str:
        """ Configuration property : APIs | Identity Service base path """
        return self.get_entry(ConfigurationConstants.SECTION_APIS,
                              ConfigurationConstants.APIS_IDENTITY_SVC)

    @property
    def apis_cms_svc(self) -> str:
        """ Configuration property : APIs | CMS Service base path """
        return self.get_entry(ConfigurationConstants.SECTION_APIS,
                              ConfigurationConstants.APIS_CMS_SVC)

    @property
    def apis_web_portal_svc(self) -> str:
        """ Configuration property : APIs | Web Portal Service base path """
        return self.get_entry(ConfigurationConstants.SECTION_APIS,
                              ConfigurationConstants.APIS_WEB_PORTAL_SVC)
