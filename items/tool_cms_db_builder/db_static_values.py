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

# Field types in tuple (id, name, supports_default_value, supports_is_required)
STATIC_VALUES_FIELD_TYPES: list = [
    (1, "Checkbox", 1, 0),
    (2, "Date", 0, 1),
    (3, "Dropdown", 1 , 1),
    (4, "Integer", 1, 1),
    (5, "String", 1 , 1),
    (6, "Text", 1, 1),
    (7, "Url (Link)", 1, 1),
    (8, "User", 1, 1)
]

'''
Future fields:
    Milestone
    Multi-select
    Steps
    Scenarios
'''

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

#  Define the option kind (id, option_mame)
STATIC_VALUES_TEST_CASE_CUSTOM_FIELD_OPTION_KINDS: list = [
    (1, 'dropdown_items'),
    (2, 'text_text_format'),
    (3, 'text_rows')
]

# Add allowed values for this kind (id, kind_id, value)
STATIC_VALUES_TEST_CASE_CUSTOM_FIELD_OPTION_VALUES: list = [
    (1, 2, 'Plain Text'),
    (2, 2, 'Markdown'),
    (3, 3, '1'),
    (4, 3, '2'),
    (5, 3, '3'),
    (6, 3, '4'),
    (7, 3, '5'),
    (8, 3, '6'),
    (9, 3, '7'),
    (10, 3, '8'),
    (11, 3, '9'),
    (12, 3, '10')
]
