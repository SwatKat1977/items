import unittest
from unittest.mock import patch
from configuration_layout import ConfigurationConstants as consts
from configuration.configuration_manager import ConfigurationManager
from threadsafe_configuration import ThreadSafeConfiguration


class TestThreadSafeConfiguration(unittest.TestCase):
    @patch.object(ConfigurationManager, 'get_entry')
    def test_logging_log_level(self, mock_get_entry):
        """Test logging_log_level property"""
        # Set up mock return value for the get_entry method
        mock_get_entry.return_value = "DEBUG"

        # Instantiate ThreadsafeConfiguration
        config = ThreadSafeConfiguration()

        # Call the logging_log_level property
        log_level = config.logging_log_level

        # Assert that get_entry was called with the expected parameters
        mock_get_entry.assert_called_once_with(
            consts.SECTION_LOGGING, consts.LOGGING_LOG_LEVEL
        )

        # Assert that the logging_log_level property returns the correct value
        self.assertEqual(log_level, "DEBUG")

    @patch.object(ConfigurationManager, 'get_entry')
    def test_apis_accounts_svc(self, mock_get_entry):
        """Test apis_accounts_svc property"""
        # Set up mock return value for the get_entry method
        mock_get_entry.return_value = "http://unittests:9001"

        # Instantiate ThreadSafeConfiguration
        config = ThreadSafeConfiguration()

        # Call the apis_accounts_svc property
        api: str = config.apis_accounts_svc

        # Assert that get_entry was called with the expected parameters
        mock_get_entry.assert_called_once_with(
            consts.SECTION_APIS, consts.APIS_ACCOUNTS_SVC
        )

        # Assert that the apis_accounts_svc property returns the correct value
        self.assertEqual(api, "http://unittests:9001")

    @patch.object(ConfigurationManager, 'get_entry')
    def test_apis_cms_svc(self, mock_get_entry):
        """Test apis_cms_svc property"""
        # Set up mock return value for the get_entry method
        mock_get_entry.return_value = "http://unittests:9002"

        # Instantiate ThreadSafeConfiguration
        config = ThreadSafeConfiguration()

        # Call the apis_cms_svc property
        api: str = config.apis_cms_svc

        # Assert that get_entry was called with the expected parameters
        mock_get_entry.assert_called_once_with(
            consts.SECTION_APIS, consts.APIS_CMS_SVC
        )

        # Assert that the apis_cms_svc property returns the correct value
        self.assertEqual(api, "http://unittests:9002")

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
            consts.SECTION_LOGGING, consts.LOGGING_LOG_LEVEL
        )

        # Assert that the logging_log_level property returns the correct value
        self.assertEqual(log_level, "INFO")
