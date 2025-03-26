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
