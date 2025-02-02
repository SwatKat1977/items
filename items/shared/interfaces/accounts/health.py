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

SCHEMA_HEALTH_RESPONSE: dict = {
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "status": {
      "type": "string",
      "enum": ["healthy", "degraded", "down"]
    },
    "issues": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "component": { "type": "string" },
          "status": { "type": "string" },
          "details": { "type": "string" }
        },
        "required": ["component", "status", "details"]
      },
      "minItems": 1
    },
    "dependencies": {
      "type": "object",
      "properties": {
        "database": {
          "enum": ["none", "partial", "fully_degraded"]},
        "service": {
          "enum": ["none", "partial", "fully_degraded"]}
      },
      "required": ["database", "service"]
    },
    "uptime_seconds": {"type": "integer", "minimum": 0},
    "version": {"type": "string", "pattern": "^\\d+\\.\\d+\\.\\d+$"}
  },
  "required": ["status", "degradation_level", "dependencies", "uptime_seconds", "version"],
  "additionalProperties": False,
  "allOf": [
    {
      "if": {
        "properties": {"status": {"const": "healthy"}}
      },
      "then": {
        "properties": {
          "issues": {"type": "null"}
        }
      }
    },
    {
      "if": {
        "properties": {"status": { "enum": ["degraded", "down"]}}
      },
      "then": {
        "required": ["issues"]
      }
    }
  ]
}
