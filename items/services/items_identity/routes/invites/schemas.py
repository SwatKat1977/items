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

_EMAIL_FIELD: dict = {
    "type": "string",
    "format": "email",
    "minLength": 3,
    "maxLength": 320
}

SCHEMA_CREATE_INVITE_REQUEST: dict = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "email_address": _EMAIL_FIELD
    },
    "required": ["email_address"]
}

SCHEMA_RESEND_INVITE_REQUEST: dict = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "email_address": _EMAIL_FIELD
    },
    "required": ["email_address"]
}

SCHEMA_UNINVITE_REQUEST: dict = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "email_address": _EMAIL_FIELD
    },
    "required": ["email_address"]
}
