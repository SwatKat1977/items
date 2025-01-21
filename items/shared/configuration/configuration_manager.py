'''
Copyright 2025 Integrated Test Management Suite Development Team

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
'''
import configparser
import os
from configuration import configuration_setup

class ConfigurationManager():
    """
    Class that wraps the functionality of configparser to support additional
    features such as trying multiple sources for the configuration item.
    """

    def __init__(self):
        """ Constructor for the configuration manager class. """

        self._parser = configparser.ConfigParser()

        self._config_file : str = ''
        self._has_config_file = False
        self._config_file_required = False
        self._layout : configuration_setup.ConfigurationSetup = None
        self._config_items = {}

    def configure(self, layout : configuration_setup.ConfigurationSetup,
                 config_file : str = None, file_required : bool = False):
        """
        Constructor for the configuration base class, it take in a layout
        class to validate the file.

        Example of layout:
        {
            "logging": [
                configuration_setup.ConfigurationSetupItem(
                    "log_level", configuration_setup.DataType.STRING,
                    valid_values=['DEBUG', 'INFO'],
                    default_value="INFO")
            ]
        }

        parameters:
            layout : Dictionary defining the configuration file
            config_file : Config file to read (optional, default = None)
            file_required : Is the file required (optional, default = False)
            required_files : Dict of required item (optional, default = None)
        """
        self._config_file = config_file
        self._config_file_required = file_required
        self._layout = layout

    def process_config(self):
        """
        Process the configuration
        """

        files_read = []

        if self._config_file:
            try:
                files_read = self._parser.read(self._config_file)

            except configparser.ParsingError as ex:
                raise ValueError(
                    f"Failed to read required config file, reason: {ex}") from ex

            if not files_read and self._config_file_required:
                raise ValueError(
                    f"Failed to open required config file '{self._config_file}'")

            self._has_config_file = True

        self._read_configuration()

    def get_entry(self, section : str, item : str) -> object:
        """
        Get a configuration entry item value from a seciotn.

        parameters:
            section (str) : Name of section
            item (str) : Name of configuration item to retrieve

        returns:
            Value of entry, the type depends on the items type - e.g.
            string (str) or integer (int).
        """

        if section not in self._config_items:
            raise ValueError(f"Invalid section '{section}'")

        if item not in self._config_items[section]:
            raise ValueError(f"Invalid config item {section}::{item}'")

        return self._config_items[section][item]

    def _read_configuration(self):

        sections = self._layout.get_sections()

        for section_name in sections:
            section_items = self._layout.get_section(section_name)

            for section_item in section_items:

                if section_item.item_type == configuration_setup.ConfigItemDataType.INTEGER:
                    item_value : int = self._read_int(section_name, section_item)

                    if section_name not in self._config_items:
                        self._config_items[section_name] = {}

                    self._config_items[section_name][section_item.item_name] = item_value

                elif section_item.item_type == configuration_setup.ConfigItemDataType.STRING:
                    item_value : str = self._read_str(section_name,
                                                     section_item.item_name,
                                                     section_item)

                    if section_name not in self._config_items:
                        self._config_items[section_name] = {}

                    self._config_items[section_name][section_item.item_name] = item_value

    def _read_str(self, section : str, option : str,
                 fmt : configuration_setup.ConfigurationSetupItem) -> str:
        """
        Read a configuration option of type string, firstly it will check for
        an environment variable (format is section_option), otherise try the
        configuration file (if it exists). An ValueError exception is thrown
        it's missing and marked as is_required.

        parameters:
            section : Configuration section
            option : Configuration option to read
            default : Default value (if not a required variable)
            is_required : Is a required env variable flag (default is False)

        returns:
            A str or None if it's not a required field.
        """
        env_variable : str = f"{section}_{option}".upper()
        value = os.getenv(env_variable)

        # If no environment variable is found, check config file (if exits)
        if not value and self._has_config_file:
            try:
                value = self._parser.get(section, option)

            except configparser.NoOptionError:
                value = None

            except configparser.NoSectionError:
                value = None

        value = value if value else fmt.default_value

        if not value and fmt.is_required:
            raise ValueError("Missing required config option "
                             f"'{section}::{fmt.item_name}'")

        if fmt.valid_values and value not in fmt.valid_values:
            raise ValueError(f"Value of '{value}' for {fmt.item_name} is invalid")

        return value

    def _read_int(self, section : str,
                  fmt : configuration_setup.ConfigurationSetupItem) -> int:
        """
        Read a configuration option of type int, firstly it will check for
        an enviroment variable (format is section_option), otherise try the
        configuration file (if it exists). An ValueError exception is thrown
        it's missing and marked as is_required or is not an int.

        parameters:
            section : Configuration section
            option : Configuration option to read
            default : Default value (if not a required variable)
            is_required : Is a required env variable flag (default is False)

        returns:
            An int or None if it's not a required field.
        """
        env_variable : str = f"{section}_{fmt.item_name}".upper()
        value = os.getenv(env_variable)

        # If no environment variable is found, check config file (if exits)
        if not value and self._has_config_file:
            try:
                value = self._parser.getint(section, fmt.item_name)

            except configparser.NoOptionError:
                value = None

            except configparser.NoSectionError:
                value = None

            except ValueError as ex:
                raise ValueError((f"Config file option '{fmt.item_name}'"
                                   " is not a valid int.")) from ex

        value = value if value else fmt.default_value

        if not value and fmt.is_required:
            raise ValueError("Missing required config option "
                             f"'{section}::{fmt.item_name}'")

        try:
            value = int(value)

        except ValueError as ex:
            raise ValueError((f"Configuration option '{fmt.item_name}' with"
                              f" a value of '{value}' is not an int.")) from ex

        return value
