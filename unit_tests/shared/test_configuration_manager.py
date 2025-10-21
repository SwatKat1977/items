import unittest
from unittest.mock import patch, MagicMock, mock_open
import os
from configuration import configuration_setup
from configuration.configuration_setup import (
    ConfigurationSetup, ConfigurationSetupItem, ConfigItemDataType
)
from configuration.configuration_manager import ConfigurationManager
import configparser

class TestConfigurationManager(unittest.TestCase):

    def setUp(self):
        self.layout = ConfigurationSetup({
            "logging": [
                ConfigurationSetupItem(
                    item_name="log_level",
                    item_type=ConfigItemDataType.STRING,
                    valid_values=["DEBUG", "INFO", "WARNING", "ERROR"],
                    is_required=True
                )
            ],
            "database": [
                ConfigurationSetupItem(
                    item_name="max_connections",
                    item_type=ConfigItemDataType.INTEGER,
                    default_value=10,
                    is_required=False
                )
            ]
        })
        self.config_manager = ConfigurationManager()

    @patch("os.getenv")
    def test_read_configuration_from_environment(self, mock_getenv):
        mock_getenv.side_effect = lambda key: {
            "LOGGING_LOG_LEVEL": "DEBUG",
            "DATABASE_MAX_CONNECTIONS": "20"
        }.get(key)

        self.config_manager.configure(self.layout)
        self.config_manager.process_config()

        log_level = self.config_manager.get_entry("logging", "log_level")
        max_connections = self.config_manager.get_entry("database", "max_connections")

        self.assertEqual(log_level, "DEBUG")
        self.assertEqual(max_connections, 20)


    @patch("builtins.open", new_callable=mock_open, read_data="[logging]\nlog_level=ERROR\n")
    @patch("os.getenv", return_value=None)
    def test_read_configuration_from_file(self, mock_getenv, mock_file):
        self.config_manager.configure(self.layout, config_file="test_config.ini")
        self.config_manager.process_config()

        log_level = self.config_manager.get_entry("logging", "log_level")
        self.assertEqual(log_level, "ERROR")

    @patch("os.getenv", return_value=None)
    def test_missing_required_configuration(self, mock_getenv):
        with self.assertRaises(ValueError) as context:
            self.config_manager.configure(self.layout)
            self.config_manager.process_config()
        self.assertIn("Missing required config option 'logging::log_level'", str(context.exception))

    @patch("os.getenv", return_value=None)
    @patch("builtins.open", new_callable=mock_open, read_data="[logging]\nlog_level=INVALID\n")
    def test_invalid_value_in_configuration_file(self, mock_file, mock_getenv):
        self.config_manager.configure(self.layout, config_file="test_config.ini")
        with self.assertRaises(ValueError) as context:
            self.config_manager.process_config()
        self.assertIn("Value of 'INVALID' for log_level is invalid", str(context.exception))

    def test_get_entry_invalid_section(self):
        self.config_manager.configure(self.layout)
        with self.assertRaises(ValueError) as context:
            self.config_manager.get_entry("invalid_section", "log_level")
        self.assertIn("Invalid section 'invalid_section'", str(context.exception))

    @patch("builtins.open", new_callable=mock_open, read_data="[logging]\nlog_level=ERROR\n")
    @patch("os.getenv", return_value=None)
    def test_get_entry_invalid_item(self, mock_getenv, mock_file):
        self.config_manager.configure(self.layout, config_file="test_config.ini")
        self.config_manager.process_config()

        with self.assertRaises(ValueError) as context:
            self.config_manager.get_entry("logging", "invalid_item")
        self.assertIn("Invalid config item logging::invalid_item'", str(context.exception))

    @patch("os.getenv", return_value=None)
    @patch("builtins.open", new_callable=mock_open, read_data="[logging]\nlog_level=ERROR\n[database]\nmax_connections=abc\n")
    def test_invalid_integer_value_in_config(self, mock_file, mock_getenv):
        self.config_manager.configure(self.layout, config_file="test_config.ini")
        with self.assertRaises(ValueError) as context:
            self.config_manager.process_config()
        self.assertIn("Config file option 'max_connections' is not a valid int", str(context.exception))

    @patch("os.getenv")
    def test_integer_environment_variable(self, mock_getenv):
        mock_getenv.side_effect = ["ERROR", "30", "90"]
        self.config_manager.configure(self.layout)
        self.config_manager.process_config()
        max_connections = self.config_manager.get_entry("database", "max_connections")
        self.assertEqual(max_connections, 30)

    @patch("os.getenv")
    def test_default_value_usage(self, mock_getenv):
        mock_getenv.side_effect = ["INFO", None]
        self.config_manager.configure(self.layout)
        self.config_manager.process_config()
        max_connections = self.config_manager.get_entry("database", "max_connections")
        self.assertEqual(max_connections, 10)

    @patch("os.getenv")
    def test_no_config_file_required(self, mock_getenv):
        mock_getenv.side_effect = ["INFO", "30", "90"]
        self.config_manager.configure(self.layout, file_required=False)
        self.config_manager.process_config()
        log_level = self.config_manager.get_entry("logging", "log_level")
        self.assertEqual(log_level, "INFO")

    @patch("os.getenv", return_value=None)
    def test_required_config_file_not_found(self, mock_getenv):
        self.config_manager.configure(self.layout, config_file="non_existent.ini", file_required=True)
        with self.assertRaises(ValueError) as context:
            self.config_manager.process_config()
        self.assertIn("Failed to open required config file", str(context.exception))

    @patch("builtins.open", new_callable=mock_open, read_data="[logging]\ninvalid item\n")
    @patch("os.getenv", return_value=None)
    def test_config_file_parse_error(self, mock_getenv, mock_file):
        with self.assertRaises(ValueError) as context:
            self.config_manager.configure(self.layout, config_file="test_config.ini")
            self.config_manager.process_config()
        self.assertIn("Failed to read required config file, reason: Source contains parsing errors", str(context.exception))

    @patch("os.getenv", return_value=None)
    def test_no_option_error_str(self, mock_getenv):
        # Simulate a NoOptionError being raised by _parser.get
        self.config_manager._has_config_file = True
        self.config_manager._parser = MagicMock()
        self.config_manager._parser.get.side_effect = configparser.NoOptionError("section", "option")

        fmt = MagicMock(default_value=None, is_required=False, valid_values=None, item_name="option")

        # Call the _read_str method
        result = self.config_manager._read_str("section", "option", fmt)

        # Verify that the result is None (default value for missing option)
        self.assertIsNone(result)

    @patch("os.getenv", return_value=None)
    def test_no_section_error_handling_str(self, mock_getenv):
        # Ensure _has_config_file is True so the function checks the config file
        self.config_manager._has_config_file = True

        # Mock _parser.get to raise NoSectionError
        self.config_manager._parser = MagicMock()
        self.config_manager._parser.get.side_effect = configparser.NoSectionError("section")

        # Create a mock ConfigurationSetupItem with default values
        fmt = MagicMock(default_value="default_value", is_required=False, valid_values=None, item_name="option")

        # Call the _read_str method
        result = self.config_manager._read_str("section", "option", fmt)

        # Assert that the function falls back to the default value
        self.assertEqual(result, "default_value")

    @patch("os.getenv", return_value=None)
    def test_no_option_error_handling_int(self, mock_getenv):
        # Ensure _has_config_file is True so the function checks the config file
        self.config_manager._has_config_file = True

        # Mock _parser.getint to raise NoOptionError
        self.config_manager._parser = MagicMock()
        self.config_manager._parser.getint.side_effect = configparser.NoOptionError("section", "option")

        # Create a mock ConfigurationSetupItem with default values
        fmt = MagicMock(default_value=42, is_required=False, valid_values=None, item_name="option")

        # Call the _read_int method
        result = self.config_manager._read_int("section", fmt)

        # Assert that the function falls back to the default value
        self.assertEqual(result, 42)

    @patch("os.getenv", return_value=None)
    def test_no_section_error_handling_int(self, mock_getenv):
        # Ensure _has_config_file is True so the function checks the config file
        self.config_manager._has_config_file = True

        # Mock _parser.getint to raise NoSectionError
        self.config_manager._parser = MagicMock()
        self.config_manager._parser.getint.side_effect = configparser.NoSectionError("section")

        # Create a mock ConfigurationSetupItem with default values
        fmt = MagicMock(default_value=42, is_required=False, valid_values=None, item_name="option")

        # Call the _read_int method
        result = self.config_manager._read_int("section", fmt)

        # Assert that the function falls back to the default value
        self.assertEqual(result, 42)

    @patch("os.getenv", return_value=None)
    def test_missing_required_config_option_int(self, mock_getenv):
        # Ensure _has_config_file is True so the function checks the config file
        self.config_manager._has_config_file = True

        # Mock _parser.getint to return None (simulating no option found)
        self.config_manager._parser = MagicMock()
        self.config_manager._parser.getint.side_effect = configparser.NoOptionError("section", "option")

        # Create a mock ConfigurationSetupItem with no default value and required flag set to True
        fmt = MagicMock(default_value=None, is_required=True, valid_values=None, item_name="option")

        # Assert that a ValueError is raised with the expected message
        with self.assertRaises(ValueError) as context:
            self.config_manager._read_int("section", fmt)

        self.assertEqual(str(context.exception), "Missing required config option 'section::option'")

    @patch("os.getenv", return_value="non_integer_value")
    def test_value_error_when_value_is_not_int(self, mock_getenv):
        # Ensure _has_config_file is False (no fallback to config file)
        self.config_manager._has_config_file = False

        # Create a mock ConfigurationSetupItem with a required field
        fmt = MagicMock(default_value=None, is_required=True, valid_values=None, item_name="option")

        # Call the _read_int method, which should raise a ValueError
        with self.assertRaises(ValueError) as context:
            self.config_manager._read_int("section", fmt)

        # Assert that the error message contains the expected content
        self.assertEqual(str(context.exception), "Configuration option 'option' with a value of 'non_integer_value' is not an int.")

    def test_get_section_with_non_existent_section(self):
        # Create some mock ConfigurationSetupItem objects
        item1 = ConfigurationSetupItem(item_name="item1", item_type=ConfigItemDataType.STRING)

        # Create a mock setup_items dictionary with a section
        setup_items = {
            "section1": [item1]
        }

        # Initialize ConfigurationSetup with the mock data
        config_setup = ConfigurationSetup(setup_items)

        # Call get_section for a non-existent section
        result = config_setup.get_section("non_existent_section")

        # Assert that the result is None, as the section doesn't exist
        self.assertIsNone(result)
