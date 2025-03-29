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
# pylint: disable=duplicate-code

SCHEMA_ADD_PROJECT_REQUEST: dict = {
    "$schema": "http://json-schema.org/draft-07/schema#",

    "type": "object",
    "additionalProperties": False,

    "properties":
        {
            "name":
                {
                    "type": "string"
                },
            "announcement":
                {
                    "type": "string"
                },
            "announcement_on_overview":
                {
                    "type": "boolean"
                }
        },
    "required": ["name", "announcement", "announcement_on_overview"]
}


SCHEMA_MODIFY_PROJECT_REQUEST: dict = {
    "$schema": "http://json-schema.org/draft-07/schema#",

    "type": "object",
    "additionalProperties": False,

    "properties":
        {
            "name":
                {
                    "type": "string"
                },
            "announcement":
                {
                    "type": "string"
                },
            "announcement_on_overview":
                {
                    "type": "boolean"
                }
        },
    "required": ["name", "announcement", "announcement_on_overview"]
}
