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

# Field types in tuple (id, name)
STATIC_VALUES_FIELD_TYPES: list = [
    (1, "Checkbox"),
    (2, "Date"),
    (3, "Dropdown"),
    (4, "Integer"),
    (5, "String"),
    (6, "Text"),
    (7, "Url (Link)"),
    (8, "User")
]

'''
Future fields:
    Milestone
    Multi-select
    Steps
    Scenarios
'''

# (id, field_type_id, option_name)
STATIC_VALUES_FIELD_TYPE_OPTIONS: list = [
    # Checkbox field type options
    (1, 1, "Default Value"),

    # Dropdown field type options
    (2, 3, "Items"),
    (3, 3, "Default Value"),
    (4, 3, "Field Required"),

    # Integer field type options
    (5, 4, "Default Value"),
    (6, 4, "Field Required"),

    # String field type options
    (7, 5, "Default Value"),
    (8, 5, "Field Required"),

    # Text field type options
    (9,  6, "Text Format"),  # Markdown or Plain
    (10, 6, "Rows"),
    (11, 6, "Default Value"),
    (12, 6, "Field Required"),

    # Url (Link) field type options
    (13, 7, "Default Value"),
    (14, 7, "Field Required"),

    # Url (Link) field type options
    (15, 8, "Default Value"),
    (16, 8, "Field Required"),
]

# (id, field_mame, system_name, field_type_id, entry_type, enabled, position)
STATIC_VALUES_SYSTEM_FIELDS: list = [
    # Reference - String field (5)
    (1, "References", "references", 5, "system", True, 1),

    # Status - The status of the test case. E.g. draft, review, approved
    (2, "Status", "status", 3, "system", True, 2),

    # Estimate - Estimate of the time it will time to execute the test case
    #            as a free-form string.
    (3, "Estimate", "estimate", 5, "system", True, 3)
]
