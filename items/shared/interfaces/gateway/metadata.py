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

SCHEMA_UPDATE_METADATA_REQUEST: dict  = {
    "type": "object",
    "properties": {
        "default_time_zone": {"type": "string"},
        "using_server_default_time_zone": {"type": "boolean"},
        "instance_name": {"type": "string"}
    },
    "required": ["default_time_zone", "using_server_default_time_zone", "instance_name"],
    "additionalProperties": False
}
