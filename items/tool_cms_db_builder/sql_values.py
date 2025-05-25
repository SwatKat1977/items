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

SQL_CREATE_PROJECTS_TABLE: str = """
    CREATE TABLE projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        awaiting_purge BOOLEAN NOT NULL DEFAULT 0,
        announcement TEXT NOT NULL DEFAULT '',
        show_announcement_on_overview INTEGER NOT NULL DEFAULT 0,
        creation_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
"""

SQL_CREATE_TEST_CASE_FOLDERS_TABLE: str = """
    CREATE TABLE test_case_folders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER NOT NULL,
        parent_id INTEGER NULL,
        name TEXT NOT NULL,
        FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
        FOREIGN KEY (parent_id) REFERENCES test_case_folders(id) ON DELETE CASCADE,
        UNIQUE (project_id, parent_id, name)
    );
"""

SQL_CREATE_TEST_CASES_TABLE: str = """
CREATE TABLE test_cases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    folder_id INTEGER NULL,
    name TEXT NOT NULL,
    description TEXT,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY (folder_id) REFERENCES test_case_folders(id) ON DELETE CASCADE,
    UNIQUE (project_id, folder_id, name)
);
"""

# Type of field - e.g. 'string', 'text', 'int'
SQL_CREATE_CUSTOM_FIELD_TYPES_TABLE: str = """
CREATE TABLE custom_field_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    supports_default_value BOOLEAN NOT NULL DEFAULT 0,
    supports_is_required BOOLEAN NOT NULL DEFAULT 0
);
"""

# Test Case Fields
SQL_CREATE_TEST_CASE_CUSTOM_FIELDS_TABLE: str = """
CREATE TABLE test_case_custom_fields (
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
    FOREIGN KEY (field_type_id) REFERENCES custom_field_types(id)
);
"""

# Table defines the option kinds (e.g. text_format)
SQL_CREATE_TEST_CASE_CUSTOM_FIELD_OPTION_KINDS_TABLE: str = """
CREATE TABLE test_case_custom_field_option_kinds (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    option_name TEXT NOT NULL UNIQUE
);
"""

SQL_CREATE_TEST_CASE_CUSTOM_FIELD_OPTION_KIND_VALUES_TABLE: str = """
CREATE TABLE test_case_custom_field_option_values (
    id INTEGER PRIMARY KEY,
    kind_id INTEGER NOT NULL,
    value TEXT NOT NULL,
    FOREIGN KEY (kind_id) REFERENCES test_case_custom_field_option_kinds(id),
    UNIQUE(kind_id, value)
);
"""

SQL_CREATE_TEST_CASE_CUSTOM_FIELD_TYPE_OPTIONS_TABLE: str = """
CREATE TABLE test_case_custom_field_type_options (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    field_id INTEGER NOT NULL,
    option_kind_id INTEGER NOT NULL,
    option_value TEXT NOT NULL,
    FOREIGN KEY (field_id) REFERENCES test_case_custom_fields(id),
    FOREIGN KEY (option_kind_id) REFERENCES test_case_custom_field_option_kinds(id),
    UNIQUE (field_id, option_kind_id)
);
"""

# Link table between test case custom fields and projects.
SQL_CREATE_TEST_CASE_CUSTOM_FIELD_PROJECTS_TABLE: str = """
CREATE TABLE test_case_custom_field_projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    field_id INTEGER NOT NULL,
    project_id INTEGER NOT NULL,
    FOREIGN KEY (field_id) REFERENCES custom_field_types(id) ON DELETE CASCADE,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);
"""

# Values for a Test Case field option.
SQL_CREATE_TEST_CASE_CUSTOM_FIELD_TYPE_OPTION_VALUES_TABLE: str = """
CREATE TABLE test_case_custom_field_type_option_values (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    case_field_id INTEGER NOT NULL,
    field_type_option_id INTEGER NOT NULL,
    option_value TEXT NOT NULL,
    FOREIGN KEY (case_field_id) REFERENCES test_case_custom_fields(id),
    FOREIGN KEY (field_type_option_id) REFERENCES custom_field_type_options(id)
);
"""
