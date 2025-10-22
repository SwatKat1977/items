import os
import unittest
from unittest.mock import MagicMock, patch
import asyncio
from application import Application
from configuration_layout import CONFIGURATION_LAYOUT
from threadsafe_configuration import ThreadSafeConfiguration


class TestApplication(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        """Set up the Application instance and mock dependencies."""
        self.mock_quart_instance = MagicMock()

        # Mock the logger
        self.mock_logger_instance = MagicMock()

        # Patch configuration
        patcher = patch.object(
            ThreadSafeConfiguration,
            'get_entry',
            return_value=":memory:"
        )
        self.mock_get_entry = patcher.start()
        self.addCleanup(patcher.stop)

    @patch("application.Configuration")
    @patch('application.os.path.isfile', return_value=True)
    def test_initialise_success(self, mock_isfile, mock_configuration_class):
        """Test _initialise when configuration management succeeds."""
        # Mock constants
        patch("application.RELEASE_VERSION", "1.0.0").start()
        patch("application.BUILD_VERSION", "123").start()
        patch("application.BUILD_TAG", "-alpha").start()

        # Mock config instance and its properties
        mock_config = MagicMock()
        mock_config.logging_log_level = "DEBUG"
        mock_config.backend_db_filename = "mock_db.sqlite"
        mock_configuration_class.return_value = mock_config

        application = Application(self.mock_quart_instance)
        application._logger = self.mock_logger_instance

        # Mock configuration management success
        application._manage_configuration = MagicMock(return_value=True)

        # Call _initialise
        result = application._initialise()

        # Assertions
        self.assertTrue(result, "Initialization should succeed")
        self.mock_logger_instance.info.assert_any_call(
            'ITEMS Accounts Microservice %s', "V1.0.0-123-alpha"
        )
        self.mock_logger_instance.info.assert_any_call("Setting logging level to %s", "DEBUG")
        self.mock_logger_instance.setLevel.assert_called_once_with("DEBUG")
        application._manage_configuration.assert_called_once()

    def test_initialise_failure_configuration(self):
        """Test _initialise when configuration management fails."""
        # Mock configuration management failure
        application = Application(self.mock_quart_instance)
        application._logger = self.mock_logger_instance

        application._manage_configuration = MagicMock(return_value=False)

        # Call _initialise
        result = application._initialise()

        # Assertions
        self.assertFalse(result, "Initialization should fail")
        application._manage_configuration.assert_called_once()
        self.mock_logger_instance.info.assert_called()  # Logger should still log build info

    @patch('application.os.path.isfile', return_value=False)
    def test_initialise_failure_database_missing(self, mock_isfile):
        """Test _initialise when configuration management fails."""
        application = Application(self.mock_quart_instance)
        application._logger = self.mock_logger_instance

        # Mock configuration management failure
        application._manage_configuration = MagicMock(return_value=True)

        # Call _initialise
        result = application._initialise()

        # Assertions
        self.assertFalse(result, "Initialization should fail")
        application._manage_configuration.assert_called_once()
        mock_isfile.assert_called_once_with(':memory:')
        self.mock_logger_instance.info.assert_called()  # Logger should still log build info

    @patch.dict(os.environ, {"ITEMS_ACCOUNTS_SVC_CONFIG_FILE_REQUIRED": "1"})
    def test_manage_configuration_missing_config_file_required(self):
        """Test _manage_configuration when config file is required but missing."""
        application = Application(self.mock_quart_instance)
        application._logger = self.mock_logger_instance

        # Call the method being tested
        result = application._manage_configuration()

        # Check that the method returns False due to the missing config file
        self.assertFalse(result, "Configuration should fail if the required config file is missing")

        # Ensure that the error log is called
        self.mock_logger_instance.critical.assert_called_with("Configuration file is not defined")

    @patch("application.Configuration")
    @patch('application.os.path.isfile', return_value=True)
    def test_initialise_success(self, mock_isfile, mock_configuration_class):
        # Mock constants
        patch("application.RELEASE_VERSION", "1.0.0").start()
        patch("application.BUILD_VERSION", "123").start()
        patch("application.BUILD_TAG", "-alpha").start()

        application = Application(self.mock_quart_instance)
        application._logger = self.mock_logger_instance

        # Mock config instance and its properties
        mock_config = MagicMock()
        mock_config.logging_log_level = "DEBUG"
        mock_config.backend_db_filename = "mock_db.sqlite"
        mock_configuration_class.return_value = mock_config

        # Mock configuration management failure
        application._manage_configuration = MagicMock(return_value=True)

        # Call _initialise
        result = application._initialise()

        # Assertions
        self.assertTrue(result, "Initialization should succeed")
        self.mock_logger_instance.info.assert_any_call(
            'ITEMS Accounts Microservice %s', "V1.0.0-123-alpha"
        )
        self.mock_logger_instance.info.assert_any_call("Setting logging level to %s", "DEBUG")
        self.mock_logger_instance.setLevel.assert_called_once_with("DEBUG")
        application._manage_configuration.assert_called_once()

    @patch.dict(os.environ, {"ITEMS_ACCOUNTS_SVC_CONFIG_FILE": "config_file_path"})
    @patch.dict(os.environ, {"ITEMS_ACCOUNTS_SVC_CONFIG_FILE_REQUIRED": "1"})
    @patch("application.Configuration")
    @patch('application.os.path.isfile', return_value=True)
    def test_manage_configuration_success(self, mock_isfile, mock_configuration_class):
        """Test _manage_configuration when configuration is successful."""
        application = Application(self.mock_quart_instance)
        application._logger = self.mock_logger_instance

        # Mock config instance and its properties
        mock_config = MagicMock()
        mock_config.logging_log_level = "DEBUG"
        mock_config.backend_db_filename = "mock_db.sqlite"
        mock_configuration_class.return_value = mock_config

        result = application._manage_configuration()

        self.assertTrue(result, "Configuration should succeed when the config file exists and is processed")
        mock_config.configure.assert_called_once_with(CONFIGURATION_LAYOUT, "config_file_path", True)
        mock_config.process_config.assert_called_once()
        self.mock_logger_instance.info.assert_any_call("[logging]")
        self.mock_logger_instance.info.assert_any_call("=> Logging log level : %s", "DEBUG")
        self.mock_logger_instance.info.assert_any_call("[Backend]")
        self.mock_logger_instance.info.assert_any_call("=> Database filename : %s", "mock_db.sqlite")

    @patch.dict(os.environ, {"ITEMS_ACCOUNTS_SVC_CONFIG_FILE": "config_file_path"})
    @patch.dict(os.environ, {"ITEMS_ACCOUNTS_SVC_CONFIG_FILE_REQUIRED": "1"})
    @patch("application.Configuration")
    def test_manage_configuration_process_config_exception(self, mock_configuration_class):
        """Test _manage_configuration when Configuration.process_config throws ValueError."""

        # Mock config instance and its properties
        mock_config = MagicMock()
        mock_config.logging_log_level = "DEBUG"
        mock_config.backend_db_filename = "mock_db.sqlite"
        mock_config.process_config = MagicMock(side_effect=ValueError("Test config error"))
        mock_configuration_class.return_value = mock_config

        application = Application(self.mock_quart_instance)
        application._logger = self.mock_logger_instance

        result = application._manage_configuration()

        self.assertFalse(result, "Configuration should fail if process_config raises an exception")
        self.mock_logger_instance.critical.assert_called_with("Configuration error : %s", "Test config error")

    async def test_main_loop_execution(self):
        """Test that _main_loop executes properly with asyncio.sleep."""
        application = Application(self.mock_quart_instance)
        application._logger = self.mock_logger_instance

        # We'll use an event loop to run the async method and check if it completes
        loop = asyncio.get_event_loop()
        try:
            await asyncio.wait_for(application._main_loop(), timeout=1.0)
        except asyncio.TimeoutError:
            self.fail("_main_loop did not complete within the expected time frame.")
