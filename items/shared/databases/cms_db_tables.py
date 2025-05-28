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

# ###############
# All tables related to Test Cases will be prefixed with 'tc'
# ###############

# Represents folders used to organize test cases hierarchically within a
# project.
TC_FOLDERS: str = "tc_folders"

# Test case definitions.
TC_TEST_CASES: str = "tc_test_cases"

# Type of field - e.g. 'string', 'text', 'int'.
TC_CUSTOM_FIELD_TYPES: str = "tc_custom_field_types"

# Custom fields Test Case field definitions.
TC_CUSTOM_FIELDS: str = "tc_custom_fields"

# Table defines the option kinds (e.g. text_format).
TC_CUSTOM_FIELD_OPTION_KINDS: str = "tc_custom_field_option_kinds"

# If a test case custom field option has specific values, e.g. priority level
# of 'low', 'medium' or 'high'.
TC_CUSTOM_FIELD_OPTION_KIND_VALUES: str = "tc_custom_field_option_kind_values"

# Links a field to an option kind and assigns it a specific value.
TC_CUSTOM_FIELD_TYPE_OPTIONS: str = "tc_custom_field_type_options"

# Link table between test case custom fields and projects.
TC_CUSTOM_FIELD_PROJECTS: str = "tc_custom_field_projects"

# Values for a Test Case field option.
TC_CUSTOM_FIELD_TYPE_OPTION_VALUES: str = "tc_custom_field_type_option_values"

# Values for a Test Case field option.
TC_CUSTOM_FIELD_OPTION_VALUES: str = "tc_custom_field_option_values"
