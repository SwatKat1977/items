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


SCHEMA_SESSION_VALIDATE_REQUEST = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "properties": {
        "email_address": {
            "type": "string",
            "format": "email"
        },
        "token": {
            "type": "string",
            "pattern": "^[a-f0-9]{32}$"
        }
    },
    "required": ["email_address", "token"],
    "additionalProperties": False
}

SCHEMA_SESSION_VALIDATE_RESPONSE = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "properties": {
        "status": {
            "type": "string",
            "enum": ["VALID", "INVALID"]
        }
    },
    "required": ["status"],
    "additionalProperties": False
}
