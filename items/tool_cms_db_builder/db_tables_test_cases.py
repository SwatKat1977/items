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
import sql_values as misc_tables

# ###############
# All tables related to Test Cases will be prefixed with 'tc'
# ###############

"""
Table: tc_folders

Represents folders used to organize test cases hierarchically within a
project.

Columns:
- id (INTEGER PRIMARY KEY AUTOINCREMENT): Unique ID for the folder.
- project_id (INTEGER NOT NULL): ID of the associated project. References
  projects(id). Deleting the project deletes its folders.
- parent_id (INTEGER NULL): ID of the parent folder. Allows nesting.
  References tc_folders(id). Deleting the parent deletes children.
- name (TEXT NOT NULL): Name of the folder.

Constraints:
- UNIQUE (project_id, parent_id, name): Ensures folder names are unique
  within the same parent folder in a given project.
"""
TABLE_NAME_TC_FOLDERS: str = "tc_folders"
TABLE_SQL_TC_FOLDERS: str = f"""
    CREATE TABLE {TABLE_NAME_TC_FOLDERS} (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER NOT NULL,
        parent_id INTEGER NULL,
        name TEXT NOT NULL,
        FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
        FOREIGN KEY (parent_id) REFERENCES {TABLE_NAME_TC_FOLDERS}(id) ON DELETE CASCADE,
        UNIQUE (project_id, parent_id, name)
    );
"""

TABLE_NAME_TC_TEST_CASES: str = "tc_test_cases"
TABLE_SQL_TC_TEST_CASES: str = f"""
CREATE TABLE {TABLE_NAME_TC_TEST_CASES} (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    folder_id INTEGER NULL,
    name TEXT NOT NULL,
    description TEXT,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY (folder_id) REFERENCES {TABLE_NAME_TC_FOLDERS}(id) ON DELETE CASCADE,
    UNIQUE (project_id, folder_id, name)
);
"""

# Type of field - e.g. 'string', 'text', 'int'
TABLE_NAME_TC_CUSTOM_FIELD_TYPES: str = "tc_custom_field_types"
TABLE_SQL_TC_CUSTOM_FIELD_TYPES: str = f"""
CREATE TABLE {TABLE_NAME_TC_CUSTOM_FIELD_TYPES} (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    supports_default_value BOOLEAN NOT NULL DEFAULT 0,
    supports_is_required BOOLEAN NOT NULL DEFAULT 0
);
"""

# Test Case Fields
TABLE_NAME_TC_CUSTOM_FIELDS: str = "tc_custom_fields"
TABLE_SQL_TC_CUSTOM_FIELDS: str = f"""
CREATE TABLE {TABLE_NAME_TC_CUSTOM_FIELDS} (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    field_name TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    system_name TEXT NOT NULL,
    field_type_id INTEGER NOT NULL,
    entry_type TEXT NOT NULL CHECK(entry_type IN ('system', 'user')),
    enabled INTEGER NOT NULL,
    position INTEGER NOT NULL,
    is_required BOOLEAN NOT NULL DEFAULT 0,
    default_value TEXT NOT NULL DEFAULT '',
    UNIQUE (field_name, system_name),
    FOREIGN KEY (field_type_id) REFERENCES {TABLE_NAME_TC_CUSTOM_FIELD_TYPES}(id)
);
"""

# Table defines the option kinds (e.g. text_format)
TABLE_NAME_TC_CUSTOM_FIELD_OPTION_KINDS: str = "tc_custom_field_option_kinds"
TABLE_SQL_TC_CUSTOM_FIELD_OPTION_KINDS: str = f"""
CREATE TABLE {TABLE_NAME_TC_CUSTOM_FIELD_OPTION_KINDS} (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    option_name TEXT NOT NULL UNIQUE
);
"""

# If a custom field option has a specific series of values, they will be
# defined in this table.
TABLE_NAME_TC_CUSTOM_FIELD_OPTION_KIND_VALUES: str = "tc_custom_field_option_kind_values"
TABLE_SQL_TC_CUSTOM_FIELD_OPTION_KIND_VALUES: str = f"""
CREATE TABLE {TABLE_NAME_TC_CUSTOM_FIELD_OPTION_KIND_VALUES} (
    id INTEGER PRIMARY KEY,
    kind_id INTEGER NOT NULL,
    value TEXT NOT NULL,
    FOREIGN KEY (kind_id) REFERENCES {TABLE_NAME_TC_CUSTOM_FIELD_OPTION_KINDS}(id),
    UNIQUE(kind_id, value)
);
"""

TABLE_NAME_TC_CUSTOM_FIELD_TYPE_OPTIONS: str = "tc_custom_field_type_options"
TABLE_SQL_TC_CUSTOM_FIELD_TYPE_OPTIONS: str = f"""
CREATE TABLE {TABLE_NAME_TC_CUSTOM_FIELD_TYPE_OPTIONS} (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    field_id INTEGER NOT NULL,
    option_kind_id INTEGER NOT NULL,
    option_value TEXT NOT NULL,
    FOREIGN KEY (field_id) REFERENCES {TABLE_NAME_TC_CUSTOM_FIELDS}(id),
    FOREIGN KEY (option_kind_id) REFERENCES {TABLE_NAME_TC_CUSTOM_FIELD_OPTION_KINDS}(id),
    UNIQUE (field_id, option_kind_id)
);
"""

# Link table between test case custom fields and projects.
TABLE_NAME_TC_CUSTOM_FIELD_PROJECTS: str = "tc_custom_field_projects"
TABLE_SQL_TC_CUSTOM_FIELD_PROJECTS: str = f"""
CREATE TABLE {TABLE_NAME_TC_CUSTOM_FIELD_PROJECTS} (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    field_id INTEGER NOT NULL,
    project_id INTEGER NOT NULL,
    FOREIGN KEY (field_id) REFERENCES {TABLE_NAME_TC_CUSTOM_FIELD_TYPES}(id) ON DELETE CASCADE,
    FOREIGN KEY (project_id) REFERENCES {misc_tables.TABLE_NAME_PRJ_PROJECTS}(id) ON DELETE CASCADE
);
"""

# Values for a Test Case field option.
TABLE_NAME_TC_CUSTOM_FIELD_TYPE_OPTION_VALUES: str = "tc_custom_field_type_option_values"
TABLE_SQL_TC_CUSTOM_FIELD_TYPE_OPTION_VALUES: str = f"""
CREATE TABLE test_case_custom_field_type_option_values (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    case_field_id INTEGER NOT NULL,
    field_type_option_id INTEGER NOT NULL,
    option_value TEXT NOT NULL,
    FOREIGN KEY (case_field_id) REFERENCES {TABLE_NAME_TC_CUSTOM_FIELDS}(id),
    FOREIGN KEY (field_type_option_id) REFERENCES custom_field_type_options(id)
);
"""

# Values for a Test Case field option.
TABLE_NAME_TC_CUSTOM_FIELD_OPTION_VALUES: str = "tc_custom_field_option_values"
TABLE_SQL_TC_CUSTOM_FIELD_OPTION_VALUES: str = """
CREATE TABLE custom_field_value_for_test_cases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    test_case_id INTEGER NOT NULL,
    field_id INTEGER NOT NULL,
    value TEXT NOT NULL,
    FOREIGN KEY (test_case_id) REFERENCES {TABLE_NAME_TC_TEST_CASES}(id) ON DELETE CASCADE,
    FOREIGN KEY (field_id) REFERENCES {TABLE_NAME_TC_CUSTOM_FIELDS}(id) ON DELETE CASCADE,
    UNIQUE(test_case_id, field_id) -- one value per field per test case
);
"""
