"""
Copyright 2025-2026 Integrated Test Management Suite Development Team

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
from items.shared.permission_area import PermissionArea

_AREA_VALUES: list[str] = [area.value for area in PermissionArea]

_PERMISSION_ITEM_SCHEMA: dict = {
    "type": "object",
    "additionalProperties": False,

    "properties":
    {
        "area":
        {
            "type": "string",
            "enum": _AREA_VALUES
        },
        "can_read":
        {
            "type": "boolean"
        },
        "can_add_modify":
        {
            "type": "boolean"
        },
        "can_delete":
        {
            "type": "boolean"
        }
    },
    "required": ["area", "can_read", "can_add_modify", "can_delete"]
}

SCHEMA_CREATE_ROLE_REQUEST: dict = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",

    "type": "object",
    "additionalProperties": False,

    "properties":
    {
        "name":
        {
            "type": "string",
            "minLength": 1,
            "maxLength": 100
        },
        "permissions":
        {
            "type": "array",
            "items": _PERMISSION_ITEM_SCHEMA
        }
    },
    "required": ["name"]
}

SCHEMA_MODIFY_ROLE_REQUEST: dict = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",

    "type": "object",
    "additionalProperties": False,
    "minProperties": 1,

    "properties":
    {
        "name":
        {
            "type": "string",
            "minLength": 1,
            "maxLength": 100
        },
        "permissions":
        {
            "type": "array",
            "items": _PERMISSION_ITEM_SCHEMA
        }
    },
    "required": []
}
