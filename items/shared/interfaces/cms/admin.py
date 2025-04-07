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

SCHEMA_ADD_TEST_CASE_CUSTOM_FIELD_REQUEST: dict = {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "TestCaseCustomFieldConfiguration",
  "type": "object",
  "properties": {
    "setup": {
      "type": "object",
      "properties": {
        "field_name": {
          "type": "string",
          "minLength": 1,
          "description": "Name of the custom field"
        },
        "description": {
          "type": "string",
          "default": "",
          "description": "Description of the custom field"
        },
        "system_name": {
          "type": "string",
          "minLength": 1,
          "description": "System name used internally"
        },
        "field_type": {
          "type": "string",
          "enum": [
            "Checkbox",
            "Date",
            "Dropdown",
            "Integer",
            "String",
            "Text",
            "Url (Link)",
            "User"
          ],
          "description": "Type of the field"
        },
        "enabled": {
          "type": "boolean",
          "description": "True if the field is enabled"
        }
      },
      "required": [
        "field_name",
        "description",
        "system_name",
        "field_type",
        "enabled"
      ],
      "additionalProperties": False
    },
    "field_options": {
      "type": "array",
      "description": "Optional list of options for a field",
      "items": {
        "type": "object",
        "properties": {
          "name": {
            "type": "string",
            "description": "Display name of the option"
          },
          "value": {
            "type": "string",
            "description": "Value used internally"
          }
        },
        "required": ["name", "value"],
        "additionalProperties": False
      }
    }
  },
  "required": ["setup"],
  "additionalProperties": False
}
