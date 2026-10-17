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
from items.services.items_web_portal.configuration import Configuration
from items.services.items_web_portal.configuration_layout import (
    ConfigurationConstants)


class TestConfiguration(unittest.TestCase):

    def setUp(self):
        with patch.object(Configuration, "__init__", return_value=None):
            self.config = Configuration()
        self.config.get_entry = MagicMock()

    def test_logging_log_level(self):
        self.config.get_entry.return_value = "INFO"
        result = self.config.logging_log_level
        self.config.get_entry.assert_called_once_with(
            ConfigurationConstants.SECTION_LOGGING,
            ConfigurationConstants.LOGGING_LOG_LEVEL)
        self.assertEqual(result, "INFO")

    def test_general_api_signing_secret(self):
        self.config.get_entry.return_value = "secret"
        result = self.config.general_api_signing_secret
        self.config.get_entry.assert_called_once_with(
            ConfigurationConstants.SECTION_GENERAL,
            ConfigurationConstants.GENERAL_API_SIGNING_SECRET)
        self.assertEqual(result, "secret")

    def test_apis_gateway_svc(self):
        self.config.get_entry.return_value = "http://localhost:7050/"
        result = self.config.apis_gateway_svc
        self.config.get_entry.assert_called_once_with(
            ConfigurationConstants.SECTION_APIS,
            ConfigurationConstants.APIS_GATEWAY_SVC)
        self.assertEqual(result, "http://localhost:7050/")

    def test_tls_cert_file(self):
        self.config.get_entry.return_value = "/certs/cert.pem"
        result = self.config.tls_cert_file
        self.config.get_entry.assert_called_once_with(
            ConfigurationConstants.SECTION_TLS,
            ConfigurationConstants.TLS_CERT_FILE)
        self.assertEqual(result, "/certs/cert.pem")

    def test_tls_key_file(self):
        self.config.get_entry.return_value = "/certs/key.pem"
        result = self.config.tls_key_file
        self.config.get_entry.assert_called_once_with(
            ConfigurationConstants.SECTION_TLS,
            ConfigurationConstants.TLS_KEY_FILE)
        self.assertEqual(result, "/certs/key.pem")

    def test_tls_enabled_when_both_set(self):
        self.config.get_entry.return_value = "/certs/file.pem"
        self.assertTrue(self.config.tls_enabled)

    def test_tls_disabled_when_neither_set(self):
        self.config.get_entry.return_value = ""
        self.assertFalse(self.config.tls_enabled)

    def test_tls_disabled_when_only_cert_set(self):
        self.config.get_entry.side_effect = ["/certs/cert.pem", ""]
        self.assertFalse(self.config.tls_enabled)

    def test_tls_secure_cookies(self):
        self.config.get_entry.return_value = True
        result = self.config.tls_secure_cookies
        self.config.get_entry.assert_called_once_with(
            ConfigurationConstants.SECTION_TLS,
            ConfigurationConstants.TLS_SECURE_COOKIES)
        self.assertTrue(result)

    def test_use_secure_cookies_when_tls_enabled(self):
        self.config.get_entry.side_effect = ["c", "k"]
        self.assertTrue(self.config.use_secure_cookies)

    def test_use_secure_cookies_when_flag_set(self):
        self.config.get_entry.side_effect = ["", True]
        self.assertTrue(self.config.use_secure_cookies)

    def test_use_secure_cookies_false_by_default(self):
        self.config.get_entry.side_effect = ["", False]
        self.assertFalse(self.config.use_secure_cookies)


if __name__ == "__main__":
    unittest.main()
