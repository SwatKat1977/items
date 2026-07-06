import unittest
from unittest.mock import patch
from items.services.items_identity.configuration_layout import ConfigurationConstants as consts
from items.services.items_identity.identity_configuration import IdentityConfiguration


class TestIdentityConfiguration(unittest.TestCase):

    @patch.object(IdentityConfiguration, 'get_entry')
    def test_logging_log_level(self, mock_get_entry):
        mock_get_entry.return_value = "DEBUG"
        config = IdentityConfiguration()
        log_level = config.logging_log_level
        mock_get_entry.assert_called_once_with(
            consts.SECTION_LOGGING, consts.ITEM_LOGGING_LOG_LEVEL)
        self.assertEqual(log_level, "DEBUG")

    @patch.object(IdentityConfiguration, 'get_entry')
    def test_backend_db_filename(self, mock_get_entry):
        mock_get_entry.return_value = "/path/to/database.db"
        config = IdentityConfiguration()
        db_filename = config.backend_db_filename
        mock_get_entry.assert_called_once_with(
            consts.SECTION_BACKEND, consts.ITEM_BACKEND_DB_FILENAME)
        self.assertEqual(db_filename, "/path/to/database.db")

    @patch.object(IdentityConfiguration, 'get_entry')
    def test_logging_log_level_default(self, mock_get_entry):
        mock_get_entry.return_value = "INFO"
        config = IdentityConfiguration()
        log_level = config.logging_log_level
        mock_get_entry.assert_called_once_with(
            consts.SECTION_LOGGING, consts.ITEM_LOGGING_LOG_LEVEL)
        self.assertEqual(log_level, "INFO")

    @patch.object(IdentityConfiguration, 'get_entry')
    def test_backend_db_filename_default(self, mock_get_entry):
        mock_get_entry.return_value = "/default/path/to/database.db"
        config = IdentityConfiguration()
        db_filename = config.backend_db_filename
        mock_get_entry.assert_called_once_with(
            consts.SECTION_BACKEND, consts.ITEM_BACKEND_DB_FILENAME)
        self.assertEqual(db_filename, "/default/path/to/database.db")
