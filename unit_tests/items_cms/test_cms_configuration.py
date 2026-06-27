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
from items.services.items_cms.cms_configuration import CMSConfiguration
from items.services.items_cms.configuration_layout import ConfigurationConstants


class TestCMSConfiguration(unittest.TestCase):

    def setUp(self):
        with patch.object(CMSConfiguration, "__init__", return_value=None):
            self.config = CMSConfiguration()
        self.config.get_entry = MagicMock()

    def test_logging_log_level_calls_get_entry_with_correct_keys(self):
        self.config.get_entry.return_value = "INFO"
        result = self.config.logging_log_level
        self.config.get_entry.assert_called_once_with(
            ConfigurationConstants.SECTION_LOGGING,
            ConfigurationConstants.LOGGING_LOG_LEVEL)
        self.assertEqual(result, "INFO")

    def test_backend_db_filename_calls_get_entry_with_correct_keys(self):
        self.config.get_entry.return_value = "items_cms.db"
        result = self.config.backend_db_filename
        self.config.get_entry.assert_called_once_with(
            ConfigurationConstants.SECTION_BACKEND,
            ConfigurationConstants.BACKEND_DB_FILENAME)
        self.assertEqual(result, "items_cms.db")


if __name__ == "__main__":
    unittest.main()
