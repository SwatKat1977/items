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
    "title": "Custom Field Definition",
    "type": "object",
    "properties": {
        "field_name": {
            "type": "string",
            "minLength": 1,
            "description": "The display name of the custom field."
        },
        "description": {
            "type": "string",
            "description": "A human-readable description of the field."
        },
        "system_name": {
            "type": "string",
            "pattern": "^[a-z][a-z_]*$",
            "description": "Internal system identifier (lowercase letters and underscores only)."
        },
        "field_type": {
            "type": "string",
            "description": "The data type of the field.",
            "enum": [
                "Checkbox",
                "Date",
                "Dropdown",
                "Integer",
                "String",
                "Text",
                "Url (Link)",
                "User"
            ]
        },
        "enabled": {
            "type": "boolean",
            "description": "Whether the field is active."
        },
        "is_required": {
            "type": "boolean",
            "description": "Whether the field must be filled in for test cases."
        },
        "default_value": {
            "type": "string",
            "description": "Optional default value for the field."
        },
        "applies_to_all_projects": {
            "type": "boolean",
            "description": "If true, the field applies to all projects."
        },
        "projects": {
            "type": "array",
            "description": "List of project identifiers (if not global).",
            "items": {
                "type": "string"
            }
        }
    },
    "required": [
        "field_name",
        "description",
        "system_name",
        "field_type",
        "enabled",
        "is_required",
        "default_value",
        "applies_to_all_projects"
    ],
    "additionalProperties": False,

    "allOf": [
    {
      "if": {
        "properties": {
            "applies_to_all_projects": {
                "const": True
            }
        }
      },
      "then": {
        "not": {
          "required": ["projects"]
        }
      },
      "else": {
        "required": ["projects"]
      }
    }
  ]
}
