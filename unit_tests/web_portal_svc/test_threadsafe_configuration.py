import unittest
from unittest.mock import patch
from configuration_layout import ConfigurationConstants as consts
from configuration.configuration_manager import ConfigurationManager
from threadsafe_configuration import ThreadSafeConfiguration


class TestThreadSafeSingleton(unittest.TestCase):
    @patch.object(ConfigurationManager, 'get_entry')
    def test_general_api_signing_secret(self, mock_get_entry):
        """Test general_api_signing_secret property"""
        # Set up mock return value for the get_entry method
        mock_get_entry.return_value = "SigningSecret"

        # Instantiate ThreadSafeConfiguration
        config = ThreadSafeConfiguration()

        # Call the apis_accounts_svc property
        api: str = config.general_api_signing_secret

        # Assert that get_entry was called with the expected parameters
        mock_get_entry.assert_called_once_with(
            consts.SECTION_GENERAL, consts.GENERAL_API_SIGNING_SECRET
        )
