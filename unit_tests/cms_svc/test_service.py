import os
import unittest
from unittest.mock import MagicMock, patch
import asyncio
from service import Service
from configuration_layout import CONFIGURATION_LAYOUT


class TestApplication(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        """Set up the Application instance and mock dependencies."""
        self.mock_quart_instance = MagicMock()
        self.application = Service(self.mock_quart_instance)

        # Mock the logger
        self.mock_logger_instance = MagicMock()
        self.application._logger = self.mock_logger_instance

        # Mock Configuration
        self.mock_config_instance = MagicMock()
        patch("application.Configuration", return_value=self.mock_config_instance).start()
        self.addCleanup(patch.stopall)

    @patch("application.Configuration")
    @patch("application.RELEASE_VERSION", "1.0.0")
    @patch("application.BUILD_VERSION", "123")
    @patch("application.BUILD_TAG", "-alpha")
    def test_initialise_success(self, mock_configuration_class):
        """Test _initialise when configuration management succeeds."""

        # Mock config instance and its properties
        mock_config = MagicMock()
        mock_config.logging_log_level = "DEBUG"
        mock_config.backend_db_filename = "mock_db.sqlite"
        mock_configuration_class.return_value = mock_config

        # Patch deeply nested calls if needed
        self.application._manage_configuration = MagicMock(return_value=True)
        self.application._open_database = MagicMock(return_value=True)

        # Patch blueprint creation if they involve side effects
        with patch("application.create_api_routes") as mock_create_routes:
            mock_create_routes.return_value = MagicMock()  # Simulate a valid blueprint

            # Run the method under test
            result = self.application._initialise()

        self.assertTrue(result, "Initialization should succeed")
        self.mock_logger_instance.info.assert_any_call(
            'ITEMS CMS Microservice %s', "V1.0.0-123-alpha"
        )

    def test_initialise_failure_configuration(self):
        """Test _initialise when configuration management fails."""
        # Mock configuration management failure
        self.application._manage_configuration = MagicMock(return_value=False)

        # Call _initialise
        result = self.application._initialise()

        # Assertions
        self.assertFalse(result, "Initialization should fail")
        self.application._manage_configuration.assert_called_once()
        self.mock_logger_instance.info.assert_called()  # Logger should still log build info

    @patch.dict(os.environ, {"ITEMS_CMS_SVC_CONFIG_FILE_REQUIRED": "1"})
    def test_manage_configuration_missing_config_file_required(self):
        """Test _manage_configuration when config file is required but missing."""
        # Make sure to simulate a missing config file correctly

        # Call the method being tested
        result = self.application._manage_configuration()

        # Check that the method returns False due to the missing config file
        self.assertFalse(result, "Configuration should fail if the required config file is missing")

        # Ensure that the error log is called
        self.mock_logger_instance.critical.assert_called_with("Configuration file missing!")

    @patch.dict(os.environ, {"ITEMS_CMS_SVC_CONFIG_FILE": "config_file_path"})
    @patch.dict(os.environ, {"ITEMS_CMS_SVC_CONFIG_FILE_REQUIRED": "1"})
    def test_manage_configuration_success(self):
        """Test _manage_configuration when configuration is successful."""
        self.mock_config_instance.configure = MagicMock()
        self.mock_config_instance.process_config = MagicMock()
        self.mock_config_instance.logging_log_level = "DEBUG"
        self.mock_config_instance.backend_db_filename = "db_filename"

        result = self.application._manage_configuration()

        self.assertTrue(result, "Configuration should succeed when the config file exists and is processed")
        self.mock_config_instance.configure.assert_called_once_with(CONFIGURATION_LAYOUT, "config_file_path", True)
        self.mock_config_instance.process_config.assert_called_once()
        self.mock_logger_instance.info.assert_any_call("[logging]")
        self.mock_logger_instance.info.assert_any_call("=> Logging log level : %s", "DEBUG")
        self.mock_logger_instance.info.assert_any_call("[Backend]")
        self.mock_logger_instance.info.assert_any_call("=> Database filename : %s", "db_filename")

    @patch.dict(os.environ, {"ITEMS_CMS_SVC_CONFIG_FILE": "config_file_path"})
    @patch.dict(os.environ, {"ITEMS_CMS_SVC_CONFIG_FILE_REQUIRED": "1"})
    def test_manage_configuration_process_config_exception(self):
        """Test _manage_configuration when Configuration.process_config throws ValueError."""
        self.mock_config_instance.configure = MagicMock()
        self.mock_config_instance.process_config = MagicMock(side_effect=ValueError("Test config error"))

        result = self.application._manage_configuration()

        self.assertFalse(result, "Configuration should fail if process_config raises an exception")
        self.mock_config_instance.configure.assert_called_once_with(CONFIGURATION_LAYOUT, "config_file_path", True)
        self.mock_config_instance.process_config.assert_called_once()
        self.mock_logger_instance.critical.assert_called_with("Configuration error : %s", "Test config error")

    async def test_main_loop_execution(self):
        """Test that _main_loop executes properly with asyncio.sleep."""
        # We'll use an event loop to run the async method and check if it completes
        loop = asyncio.get_event_loop()
        try:
            await asyncio.wait_for(self.application._main_loop(), timeout=1.0)
        except asyncio.TimeoutError:
            self.fail("_main_loop did not complete within the expected time frame.")

