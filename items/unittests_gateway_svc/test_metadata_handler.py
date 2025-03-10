import json
import logging
import unittest
from unittest.mock import MagicMock, mock_open, patch
from configuration.configuration_manager import ConfigurationManager
from metadata_handler import MetadataHandler, SECTION_SERVER_SETTINGS, \
        SERVER_SETTINGS_INSTANCE_NAME, SERVER_SETTINGS_DEFAULT_TIME_ZONE, \
        DEFAULT_TIME_ZONE_DEFAULT


class TestMetadataHandler(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        """Set up a MetadataHandler instance with a mock logger."""
        self.mock_logger = MagicMock(spec=logging.Logger)
        self.mock_logger.getChild.return_value = self.mock_logger  # getChild should return itself

        self.metadata_handler = MetadataHandler(self.mock_logger)

    @patch("os.path.exists", return_value=False)
    @patch.object(ConfigurationManager, 'get_entry')
    def test_read_metadata_file_missing(self,
                                        mock_get_entry,
                                        mock_exists):
        """Test when the metadata file does not exist."""

        mock_get_entry.return_value = "metadata.cfg"
        self.assertFalse(self.metadata_handler.read_metadata_file())

    @patch("os.path.exists", return_value=True)
    @patch("builtins.open", new_callable=mock_open, read_data="not a json")
    @patch.object(ConfigurationManager, 'get_entry')
    def test_read_metadata_file_invalid_json(self,
                                             mock_get_entry,
                                             _mock_file_open,
                                             _mock_exists):
        """Test when the metadata file contains invalid JSON."""

        mock_get_entry.return_value = "metadata.cfg"
        self.assertFalse(self.metadata_handler.read_metadata_file())

        with patch.object(self.mock_logger, "critical") as mock_log:
            self.assertFalse(self.metadata_handler.read_metadata_file())
            mock_log.assert_any_call("The JSON file is not properly formatted.")

    @patch("os.path.exists", return_value=True)
    @patch("builtins.open", new_callable=mock_open, read_data='{"invalid": "data"}')
    @patch.object(ConfigurationManager, 'get_entry')
    def test_read_metadata_file_schema_validation_fails(self,
                                                        mock_get_entry,
                                                        mock_file_open,
                                                        mock_exists):
        """Test when the metadata file does not conform to the expected schema."""

        mock_get_entry.return_value = "metadata.cfg"
        with patch.object(self.mock_logger, "critical") as mock_log, \
             patch("json.load", return_value={"invalid": "data"}):
            self.assertFalse(self.metadata_handler.read_metadata_file())
            mock_log.assert_called_with("Metadata config file failed JSON schema validation")

    @patch("os.path.exists", return_value=True)
    @patch("builtins.open", new_callable=mock_open, read_data=json.dumps({
        "server_settings": {
            "instance_name": "TestInstance",
            "default_time_zone": "UTC"
        }
    }))
    @patch.object(ConfigurationManager, 'get_entry')
    def test_read_metadata_file_success(self, mock_get_entry, mock_file_open, mock_exists):
        """Test when the metadata file is successfully read and validated."""

        mock_get_entry.return_value = "metadata.cfg"
        with patch("json.load", return_value={
            "server_settings": {
                "instance_name": "TestInstance",
                "default_time_zone": "UTC"
            }
        }):
            self.assertTrue(self.metadata_handler.read_metadata_file())

    @patch("os.path.exists", return_value=True)
    @patch("builtins.open", side_effect=IOError("File error"))
    @patch.object(ConfigurationManager, 'get_entry')
    def test_read_metadata_file_io_error(self, mock_get_entry, mock_file_open, mock_exists):
        """Test when the metadata file has an IO error."""

        mock_get_entry.return_value = "metadata.cfg"
        with patch.object(self.mock_logger, "critical") as mock_log:
            self.assertFalse(self.metadata_handler.read_metadata_file())
            mock_log.assert_called_with("An IO error occurred: %s", "File error")

    @patch("tzlocal.get_localzone_name", return_value="Europe/London")  # Simulate a valid timezone
    @patch("os.path.exists", return_value=True)
    @patch("builtins.open", new_callable=mock_open, read_data=json.dumps({
        SECTION_SERVER_SETTINGS: {
            SERVER_SETTINGS_INSTANCE_NAME: "TestInstance",
            SERVER_SETTINGS_DEFAULT_TIME_ZONE: DEFAULT_TIME_ZONE_DEFAULT  # Trigger the branch
        }
    }))
    @patch.object(ConfigurationManager, 'get_entry')
    def test_read_metadata_file_default_time_zone_valid(self,
                                                        mock_get_entry,
                                                        _mock_file_open,
                                                        _mock_exists,
                                                        mock_get_tz):
        """Test when the metadata file has DEFAULT_TIME_ZONE_DEFAULT and a valid system timezone."""

        mock_get_entry.return_value = "metadata.cfg"

        with patch.object(self.metadata_handler._logger, "info") as mock_log:
            self.assertTrue(self.metadata_handler.read_metadata_file())

            # Check that the valid timezone was used
            self.assertEqual(self.metadata_handler.metadata_settings.default_time_zone, "Europe/London")
            self.assertTrue(self.metadata_handler.metadata_settings.using_server_default_time_zone)

            mock_log.assert_any_call("Default server time zone: (Server): %s", "Europe/London")

    @patch("tzlocal.get_localzone_name", return_value="Invalid/TimeZone")  # Simulate an invalid timezone
    @patch("os.path.exists", return_value=True)
    @patch("builtins.open", new_callable=mock_open, read_data=json.dumps({
        SECTION_SERVER_SETTINGS: {
            SERVER_SETTINGS_INSTANCE_NAME: "TestInstance",
            SERVER_SETTINGS_DEFAULT_TIME_ZONE: DEFAULT_TIME_ZONE_DEFAULT  # Trigger the branch
        }
    }))
    @patch.object(ConfigurationManager, 'get_entry')
    def test_read_metadata_file_default_time_zone_invalid(self,
                                                           mock_get_entry,
                                                           _mock_file_open,
                                                           _mock_exists,
                                                           mock_get_tz):
        """Test when the metadata file has DEFAULT_TIME_ZONE_DEFAULT but the system timezone is invalid."""

        mock_get_entry.return_value = "metadata.cfg"

        with patch.object(self.metadata_handler._logger, "critical") as mock_log:
            self.assertFalse(self.metadata_handler.read_metadata_file())

            # Ensure it logged the failure
            mock_log.assert_any_call("Unable to get server timezone, aborting...")

    @patch("os.path.exists", return_value=True)
    @patch("builtins.open", new_callable=mock_open, read_data=json.dumps({
        SECTION_SERVER_SETTINGS: {
            SERVER_SETTINGS_INSTANCE_NAME: "TestInstance",
            SERVER_SETTINGS_DEFAULT_TIME_ZONE: "INVALID_TZ"  # Invalid time zone
        }
    }))
    @patch.object(ConfigurationManager, 'get_entry')
    def test_read_metadata_file_invalid_time_zone(self,
                                                  mock_get_entry,
                                                  _mock_file_open,
                                                  _mock_exists):
        """Test when the metadata file has an invalid default time zone."""

        mock_get_entry.return_value = "metadata.cfg"

        with patch.object(self.metadata_handler._logger, "critical") as mock_log:
            self.assertFalse(self.metadata_handler.read_metadata_file())

            mock_log.assert_any_call(
                ("Default server time zone (%s) in metadata configuration "
                 "is not a valid time zone!"), "INVALID_TZ"
            )
