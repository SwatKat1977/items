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

SCHEMA_GET_USER_PROFILE_REQUEST: dict = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",

    "type": "object",
    "additionalProperties": False,

    "properties":
    {
        "email_address":
        {
            "type": "string",
            "format": "email",
            "minLength": 3,
            "maxLength": 320
        },
    },
    "required": ["email_address"]
}

# Shared field definitions, so create and update cannot drift apart.
_EMAIL_ADDRESS: dict = {
    "type": "string",
    "format": "email",
    "minLength": 3,
    "maxLength": 320
}

_NAME: dict = {
    "type": "string",
    "minLength": 1,
    "maxLength": 255
}

_PASSWORD: dict = {
    "type": "string",
    "minLength": 8,
    "maxLength": 4096
}

SCHEMA_CREATE_USER_REQUEST: dict = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",

    "type": "object",
    "additionalProperties": False,

    "properties":
    {
        "email_address": _EMAIL_ADDRESS,
        "full_name": _NAME,
        "display_name": _NAME,
        "is_administrator": {"type": "boolean"},
        "enabled": {"type": "boolean"},
        # Omit to have a password generated and returned once in the response.
        "password": _PASSWORD,
    },
    "required": ["email_address", "full_name", "display_name"]
}

SCHEMA_UPDATE_USER_REQUEST: dict = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",

    "type": "object",
    "additionalProperties": False,

    # Every field is optional - only what is supplied gets changed. At least
    # one must be present, otherwise the request is a no-op.
    "minProperties": 1,

    "properties":
    {
        "email_address": _EMAIL_ADDRESS,
        "full_name": _NAME,
        "display_name": _NAME,
        "is_administrator": {"type": "boolean"},
        "enabled": {"type": "boolean"},
    }
}

SCHEMA_SET_PASSWORD_REQUEST: dict = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",

    "type": "object",
    "additionalProperties": False,

    "properties":
    {
        # Omit to have a password generated and returned once in the response.
        "password": _PASSWORD,
    }
}
