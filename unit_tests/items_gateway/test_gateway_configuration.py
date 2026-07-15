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
import unittest
from unittest.mock import MagicMock, patch
from items.services.items_gateway.gateway_configuration import (
    GatewayConfiguration)
from items.services.items_gateway.configuration_layout import (
    ConfigurationConstants)


class TestGatewayConfiguration(unittest.TestCase):

    def setUp(self):
        with patch.object(GatewayConfiguration, "__init__", return_value=None):
            self.config = GatewayConfiguration()
        self.config.get_entry = MagicMock()

    def test_logging_log_level(self):
        self.config.get_entry.return_value = "INFO"
        result = self.config.logging_log_level
        self.config.get_entry.assert_called_once_with(
            ConfigurationConstants.SECTION_LOGGING,
            ConfigurationConstants.LOGGING_LOG_LEVEL)
        self.assertEqual(result, "INFO")

    def test_general_metadata_config_file(self):
        self.config.get_entry.return_value = "metadata.config"
        result = self.config.general_metadata_config_file
        self.config.get_entry.assert_called_once_with(
            ConfigurationConstants.SECTION_GENERAL,
            ConfigurationConstants.GENERAL_METADATA_CONFIG_FILE)
        self.assertEqual(result, "metadata.config")

    def test_general_api_signing_secret(self):
        self.config.get_entry.return_value = "secret"
        result = self.config.general_api_signing_secret
        self.config.get_entry.assert_called_once_with(
            ConfigurationConstants.SECTION_GENERAL,
            ConfigurationConstants.GENERAL_API_SIGNING_SECRET)
        self.assertEqual(result, "secret")

    def test_apis_identity_svc(self):
        self.config.get_entry.return_value = "http://localhost:5050/"
        result = self.config.apis_identity_svc
        self.config.get_entry.assert_called_once_with(
            ConfigurationConstants.SECTION_APIS,
            ConfigurationConstants.APIS_IDENTITY_SVC)
        self.assertEqual(result, "http://localhost:5050/")

    def test_apis_cms_svc(self):
        self.config.get_entry.return_value = "http://localhost:6050/"
        result = self.config.apis_cms_svc
        self.config.get_entry.assert_called_once_with(
            ConfigurationConstants.SECTION_APIS,
            ConfigurationConstants.APIS_CMS_SVC)
        self.assertEqual(result, "http://localhost:6050/")

    def test_apis_web_portal_svc(self):
        self.config.get_entry.return_value = "http://localhost:8080/"
        result = self.config.apis_web_portal_svc
        self.config.get_entry.assert_called_once_with(
            ConfigurationConstants.SECTION_APIS,
            ConfigurationConstants.APIS_WEB_PORTAL_SVC)
        self.assertEqual(result, "http://localhost:8080/")


if __name__ == "__main__":
    unittest.main()
