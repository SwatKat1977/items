import logging
import unittest
from unittest.mock import MagicMock, mock_open, patch
from configuration.configuration_manager import ConfigurationManager
from metadata_handler import MetadataHandler

# 265-331, 335-360, 363-
# 272-331, 335-360, 363-411
# 278-279, 285-287, 293-336, 340-365, 368-416


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


