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

SCHEMA_CREATE_USER_REQUEST: dict = {
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
        "full_name":
        {
            "type": "string",
            "minLength": 1,
            "maxLength": 200
        },
        "display_name":
        {
            "type": "string",
            "minLength": 1,
            "maxLength": 100
        },
        "password":
        {
            "type": "string",
            "minLength": 8,
            "maxLength": 1000
        },
        "is_administrator":
        {
            "type": "boolean"
        }
    },
    "required": ["email_address", "full_name", "display_name"]
}

SCHEMA_MODIFY_USER_REQUEST: dict = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",

    "type": "object",
    "additionalProperties": False,
    "minProperties": 1,

    "properties":
    {
        "full_name":
        {
            "type": "string",
            "minLength": 1,
            "maxLength": 200
        },
        "display_name":
        {
            "type": "string",
            "minLength": 1,
            "maxLength": 100
        },
        "account_status":
        {
            "type": "integer",
            "enum": [0, 1]
        },
        "is_administrator":
        {
            "type": "boolean"
        },
    },
    "required": []
}

SCHEMA_RESET_PASSWORD_REQUEST: dict = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",

    "type": "object",
    "additionalProperties": False,

    "properties":
    {
        "new_password":
        {
            "type": "string",
            "minLength": 8,
            "maxLength": 1000
        }
    },
    "required": ["new_password"]
}

SCHEMA_ADD_USER_PROJECT_REQUEST: dict = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",

    "type": "object",
    "additionalProperties": False,

    "properties":
    {
        "project_id":
        {
            "type": "integer"
        },
        "role_id":
        {
            # Omitting role_id entirely also means "no role yet" - this
            # lets a caller be explicit about it instead if they prefer.
            "type": ["integer", "null"]
        }
    },
    "required": ["project_id"]
}

SCHEMA_MODIFY_USER_PROJECT_REQUEST: dict = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",

    "type": "object",
    "additionalProperties": False,

    "properties":
    {
        "role_id":
        {
            # null clears the role back to "member, no role assigned"
            # (§4.3 of user_roles_design.md) rather than being omittable -
            # this endpoint's only job is changing the role, so leaving
            # role_id out of the body would be ambiguous about intent.
            "type": ["integer", "null"]
        }
    },
    "required": ["role_id"]
}

SCHEMA_CHANGE_PASSWORD_REQUEST: dict = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",

    "type": "object",
    "additionalProperties": False,

    "properties":
    {
        "user_id":
        {
            "type": "string",
            "format": "uuid"
        },
        "current_password":
        {
            "type": "string",
            "minLength": 1,
            "maxLength": 1000
        },
        "new_password":
        {
            "type": "string",
            "minLength": 8,
            "maxLength": 1000
        }
    },
    "required": ["user_id", "current_password", "new_password"]
}
