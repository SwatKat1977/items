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
# pylint: disable=R0801

SCHEMA_ACCOUNTS_SVC_HEALTH_RESPONSE: dict = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "$defs": {
        "component_status": {
            "type": "string",
            "enum": ["none", "partial", "fully_degraded"]
        }
    },
    "properties": {
        "status": {
            "type": "string",
            "enum": ["healthy", "degraded", "critical"]
        },
        "issues": {
            "oneOf": [
                {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "component": {"type": "string"},
                            "status": {"$ref": "#/$defs/component_status"},
                            "details": {"type": "string"}
                        },
                        "required": ["component", "status", "details"]
                    },
                    "minItems": 1
                },
                {"type": "null"}
            ]
        },
        "dependencies": {
            "type": "object",
            "properties": {
                "database": {"$ref": "#/$defs/component_status"},
                "service": {"$ref": "#/$defs/component_status"}
            },
            "required": ["database", "service"]
        },
        "uptime_seconds": {
            "type": "integer",
            "minimum": 0
        },
        "version": {
            "type": "string",
            "pattern": "^V\\d+\\.\\d+\\.\\d+(?:-[A-Za-z0-9 #._-]+)?$"
        }
    },
    "required": ["status", "dependencies", "uptime_seconds", "version"],
    "additionalProperties": False,
    "allOf": [
        {
            "if": {"properties": {"status": {"const": "healthy"}}},
            "then": {"properties": {"issues": {"type": "null"}}}
        },
        {
            "if": {"properties": {"status": {"enum": ["degraded",
                                                      "critical"]}}},
            "then": {
                "properties": {
                    "issues": {
                        "type": "array",
                        "minItems": 1
                    }
                }
            }
        }
    ]
}
