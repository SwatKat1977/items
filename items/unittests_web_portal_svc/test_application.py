import http
import os
import unittest
from unittest.mock import MagicMock, patch
import asyncio
import requests
from application import Application, GET_METADATA_INFINITE_RETRIES
from configuration_layout import CONFIGURATION_LAYOUT


class TestApplication(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        """Set up the Application instance and mock dependencies."""
        self.mock_quart_instance = MagicMock()
        self.application = Application(self.mock_quart_instance)

        # Mock the logger
        self.mock_logger_instance = MagicMock()
        self.application._logger = self.mock_logger_instance
        self.application._metadata_settings = MagicMock()

    def test_initialise_success(self):
        """Test _initialise when configuration management succeeds."""
        # Mock constants
        patch("application.RELEASE_VERSION", "1.0.0").start()
        patch("application.BUILD_VERSION", "123").start()
        patch("application.BUILD_TAG", "-alpha").start()

        self.application._manage_configuration = MagicMock(return_value=True)

        with patch.object(self.application, "get_metadata", return_value=True) as mock_get_metadata:
            print("DEBUG: Calling _initialise()")
            result = self.application._initialise()
            print(f"DEBUG: get_metadata() called? {mock_get_metadata.called}")
            self.assertTrue(result, "Initialization should succeed")

        return

        # Call _initialise
        result = self.application._initialise()

        # Assertions
        self.assertTrue(result, "Initialization should succeed")
        self.mock_logger_instance.info.assert_any_call(
            'ITEMS Web Portal Microservice %s', "V1.0.0-123-alpha"
        )

    async def test_main_loop_execution(self):
        """Test that _main_loop executes properly with asyncio.sleep."""
        # We'll use an event loop to run the async method and check if it completes
        loop = asyncio.get_event_loop()
        try:
            await asyncio.wait_for(self.application._main_loop(), timeout=1.0)
        except asyncio.TimeoutError:
            self.fail("_main_loop did not complete within the expected time frame.")

    def test_initialise_configuration_failure(self):
        """Test _initialise when configuration management fails."""
        # Mock configuration management failure
        self.application._manage_configuration = MagicMock(return_value=False)

        # Call _initialise
        result = self.application._initialise()

        # Assertions
        self.assertFalse(result, "Initialization should fail")
        self.application._manage_configuration.assert_called_once()
        self.mock_logger_instance.info.assert_called()  # Logger should still log build info

    def test_initialise_get_metadata_failure(self):
        """Test _initialise when configuration management succeeds."""
        # Mock constants
        patch("application.RELEASE_VERSION", "1.0.0").start()
        patch("application.BUILD_VERSION", "123").start()
        patch("application.BUILD_TAG", "-alpha").start()

        self.application.get_metadata = MagicMock(return_value=False)

        # Call _initialise
        result = self.application._initialise()

        # Assertions
        self.assertFalse(result, "Initialization should fail")
        self.mock_logger_instance.info.assert_any_call(
            'ITEMS Web Portal Microservice %s', "V1.0.0-123-alpha"
        )

    @patch.dict(os.environ, {"ITEMS_WEB_PORTAL_SVC_CONFIG_FILE_REQUIRED": "1"})
    def test_manage_configuration_missing_config_file_required(self):
        """Test _manage_configuration when config file is required but missing."""
        # Make sure to simulate a missing config file correctly

        # Call the method being tested
        result = self.application._manage_configuration()

        # Check that the method returns False due to the missing config file
        self.assertFalse(result, "Configuration should fail if the required config file is missing")

        # Ensure that the error log is called
        self.mock_logger_instance.critical.assert_called_with("Configuration file missing!")

    @patch.dict(os.environ, {"ITEMS_WEB_PORTAL_SVC_CONFIG_FILE": "config_file_path"})
    @patch.dict(os.environ, {"ITEMS_WEB_PORTAL_SVC_CONFIG_FILE_REQUIRED": "1"})
    @patch("application.Configuration")  # Correctly patch Configuration where it's used
    def test_manage_configuration_success(self, mock_configuration):
        """Test _manage_configuration when configuration is successful."""

        # Setup Configuration mock
        mock_config_instance = mock_configuration.return_value
        mock_config_instance.configure = MagicMock()
        mock_config_instance.process_config = MagicMock()
        mock_config_instance.logging_log_level = "DEBUG"
        mock_config_instance.apis_gateway_svc = "http://localhost:3000/"

        result = self.application._manage_configuration()

        # Assertions
        self.assertTrue(result, "Configuration should succeed when the config file exists and is processed")
        mock_config_instance.configure.assert_called_once_with(CONFIGURATION_LAYOUT,
                                                               "config_file_path", True)
        mock_config_instance.process_config.assert_called_once()

        # Check logger calls
        expected_logs = [
            ("[logging]",),
            ("=> Logging log level : %s", "DEBUG"),
            ("[apis]",),
            ("=> Gateway Service API : %s", "http://localhost:3000/")
        ]

        # Print logs for debugging if assertion fails
        logged_calls = self.mock_logger_instance.info.call_args_list

        # Assert that each expected log message was called
        for log_args in expected_logs:
            self.mock_logger_instance.info.assert_any_call(*log_args)

    @patch.dict(os.environ, {"ITEMS_WEB_PORTAL_SVC_CONFIG_FILE": "config_file_path"})
    @patch.dict(os.environ, {"ITEMS_WEB_PORTAL_SVC_CONFIG_FILE_REQUIRED": "1"})
    def test_manage_configuration_process_config_exception(self):
        # Mock Configuration
        mock_config_instance = MagicMock()
        patch("application.Configuration", return_value=mock_config_instance).start()
        self.addCleanup(patch.stopall)

        """Test _manage_configuration when Configuration.process_config throws ValueError."""
        mock_config_instance.configure = MagicMock()
        mock_config_instance.process_config = MagicMock(side_effect=ValueError("Test config error"))

        result = self.application._manage_configuration()

        self.assertFalse(result, "Configuration should fail if process_config raises an exception")
        mock_config_instance.configure.assert_called_once_with(CONFIGURATION_LAYOUT, "config_file_path", True)
        mock_config_instance.process_config.assert_called_once()
        self.mock_logger_instance.critical.assert_called_with("Configuration error : %s", "Test config error")

    @patch("requests.get")
    @patch("application.Configuration")
    @patch("base_view.BaseView.generate_api_signature")
    @patch("uuid.uuid4")
    @patch("time.sleep")
    def test_get_metadata_success(self,
                                  mock_sleep,
                                  mock_uuid,
                                  mock_generate_api_signature,
                                  mock_config,
                                  mock_requests_get):
        mock_uuid.return_value = "test-nonce"
        mock_generate_api_signature.return_value = "test-signature"
        mock_config().general_api_signing_secret = "test-secret"
        mock_config().apis_gateway_svc = "http://test-url/"

        mock_response = MagicMock()
        mock_response.status_code = http.HTTPStatus.OK
        mock_response.json.return_value = {
            "default_time_zone": "UTC",
            "using_server_default_time_zone": True,
            "instance_name": "Test Instance"
        }
        mock_requests_get.return_value = mock_response

        result = self.application.get_metadata()

        self.assertTrue(result)
        self.application._metadata_settings.default_time_zone = "UTC"
        self.application._metadata_settings.using_server_default_time_zone = True
        self.application._metadata_settings.instance_name = "Test Instance"
        self.application._logger.info.assert_called()

    @patch("requests.get", side_effect=requests.exceptions.ConnectionError("Test error"))
    @patch("time.sleep")
    @patch("application.Configuration")
    def test_get_metadata_connection_error(self,
                                           mock_configuration,
                                           mock_sleep,
                                           mock_requests_get):
        mock_config_instance = mock_configuration.return_value
        mock_config_instance.general_api_signing_secret = "UnitTest"

        result = self.application.get_metadata(retries=1)

        self.assertFalse(result)
        self.application._logger.error.assert_called()
        self.application._logger.critical.assert_called()

    @patch("requests.get")
    @patch("time.sleep")
    @patch("application.Configuration")
    def test_get_metadata_non_200_response(self,
                                           mock_configuration,
                                           mock_sleep,
                                           mock_requests_get):
        mock_config_instance = mock_configuration.return_value
        mock_config_instance.general_api_signing_secret = "UnitTest"

        mock_response = MagicMock()
        mock_response.status_code = http.HTTPStatus.BAD_REQUEST
        mock_requests_get.return_value = mock_response

        result = self.application.get_metadata(retries=1)

        self.assertFalse(result)
        self.application._logger.warning.assert_called()
        self.application._logger.critical.assert_called()

    @patch("requests.get", side_effect=requests.exceptions.ConnectionError("Test error"))
    @patch("time.sleep")
    @patch("application.Configuration")
    def test_get_metadata_infinite_retries(self, mock_configuration, mock_sleep, mock_requests_get):
        mock_config_instance = mock_configuration.return_value
        mock_config_instance.general_api_signing_secret = "UnitTest"

        mock_response = MagicMock()
        mock_response.status_code = http.HTTPStatus.OK
        mock_requests_get.return_value = mock_response

        with patch("time.sleep", side_effect=StopIteration()):
            with self.assertRaises(StopIteration):
                self.application.get_metadata(retries=GET_METADATA_INFINITE_RETRIES)

        self.application._logger.error.assert_called()
        self.application._logger.critical.assert_not_called()

    @patch("requests.get")
    @patch("time.sleep")
    @patch("application.Configuration")
    def test_get_metadata_retries_exhausted(self,
                                            mock_configuration,
                                            mock_sleep,
                                            mock_requests_get):
        mock_config_instance = mock_configuration.return_value
        mock_config_instance.general_api_signing_secret = "UnitTest"

        mock_response = MagicMock()
        mock_response.status_code = http.HTTPStatus.BAD_REQUEST
        mock_requests_get.return_value = mock_response

        result = self.application.get_metadata(retries=2)

        self.assertFalse(result)
        self.assertEqual(mock_requests_get.call_count, 2)
        self.application._logger.critical.assert_called()
