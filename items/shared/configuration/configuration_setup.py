"""
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
"""
import enum
import typing
from dataclasses import dataclass

class ConfigItemDataType(enum.Enum):
    """ Enumeration for configuration item data type """
    INTEGER = enum.auto()
    STRING = enum.auto()

@dataclass(frozen=True)
class ConfigurationSetupItem:
    """ Configuration layout class """

    item_name : str
    valid_values : typing.Optional[list]
    is_required : bool
    item_type : ConfigItemDataType
    default_value : typing.Optional[object]

    def __init__(self, item_name : str, item_type : ConfigItemDataType,
                 valid_values : typing.Optional[list] = None,
                 is_required : bool = False,
                 default_value : typing.Optional[object] = None) -> None:
        # pylint: disable=too-many-arguments
        object.__setattr__(self, "item_name", item_name)
        object.__setattr__(self, "item_type", item_type)
        object.__setattr__(self, "valid_values",
                           valid_values if valid_values else [])
        object.__setattr__(self, "is_required", is_required)
        object.__setattr__(self, "default_value",
                  default_value if default_value else [])

class ConfigurationSetup:
    """ Class that defines the configuaration Format """

    def __init__(self, setup_items : dict) -> None:
        self._items = setup_items

    def get_sections(self) -> list:
        """
        Get a list of sections available.

        returns:
            List of strings that represent the sections available.
        """
        return list(self._items.keys())

    def get_section(self, name : str):
        """
        Get a list of items within a given sections.

        returns:
            List of list of configuration items.
        """
        if name not in self._items:
            return None

        return self._items[name]
