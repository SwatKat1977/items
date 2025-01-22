import unittest
from unittest.mock import patch, MagicMock
from configuration_layout import ConfigurationConstants as consts
from configuration.configuration_manager import ConfigurationManager
#from thread_safe_singleton import ThreadSafeSingleton
from threadsafe_configuration import ThreadSafeConfiguration


class TestThreadafeConfiguration(unittest.TestCase):
    @patch.object(ConfigurationManager, 'get_entry')
    def test_logging_log_level(self, mock_get_entry):
        """Test logging_log_level property"""
        # Set up mock return value for the get_entry method
        mock_get_entry.return_value = "DEBUG"

        # Instantiate ThreadafeConfiguration
        config = ThreadSafeConfiguration()

        # Call the logging_log_level property
        log_level = config.logging_log_level

        # Assert that get_entry was called with the expected parameters
        mock_get_entry.assert_called_once_with(
            consts.SECTION_LOGGING, consts.ITEM_LOGGING_LOG_LEVEL
        )

        # Assert that the logging_log_level property returns the correct value
        self.assertEqual(log_level, "DEBUG")

    @patch.object(ConfigurationManager, 'get_entry')
    def test_backend_db_filename(self, mock_get_entry):
        """Test backend_db_filename property"""
        # Set up mock return value for the get_entry method
        mock_get_entry.return_value = "/path/to/database.db"

        # Instantiate ThreadafeConfiguration
        config = ThreadSafeConfiguration()

        # Call the backend_db_filename property
        db_filename = config.backend_db_filename

        # Assert that get_entry was called with the expected parameters
        mock_get_entry.assert_called_once_with(
            consts.SECTION_BACKEND, consts.ITEM_BACKEND_DB_FILENAME
        )

        # Assert that the backend_db_filename property returns the correct value
        self.assertEqual(db_filename, "/path/to/database.db")

    @patch.object(ConfigurationManager, 'get_entry')
    def test_logging_log_level_default(self, mock_get_entry):
        """Test logging_log_level property when default value is returned"""
        # Set up mock return value for the get_entry method (no value provided)
        mock_get_entry.return_value = "INFO"

        # Instantiate ThreadSafeConfiguration
        config = ThreadSafeConfiguration()

        # Call the logging_log_level property
        log_level = config.logging_log_level

        # Assert that get_entry was called with the expected parameters
        mock_get_entry.assert_called_once_with(
            consts.SECTION_LOGGING, consts.ITEM_LOGGING_LOG_LEVEL
        )

        # Assert that the logging_log_level property returns the correct value
        self.assertEqual(log_level, "INFO")

    @patch.object(ConfigurationManager, 'get_entry')
    def test_backend_db_filename_default(self, mock_get_entry):
        """Test backend_db_filename property when default value is returned"""
        # Set up mock return value for the get_entry method (no value provided)
        mock_get_entry.return_value = "/default/path/to/database.db"

        # Instantiate ThreadafeConfiguration
        config = ThreadSafeConfiguration()

        # Call the backend_db_filename property
        db_filename = config.backend_db_filename

        # Assert that get_entry was called with the expected parameters
        mock_get_entry.assert_called_once_with(
            consts.SECTION_BACKEND, consts.ITEM_BACKEND_DB_FILENAME
        )

        # Assert that the backend_db_filename property returns the correct value
        self.assertEqual(db_filename, "/default/path/to/database.db")
