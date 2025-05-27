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

"""
Table: projects

Represents a project entity which groups test cases and associated
configurations.

Columns:
- id (INTEGER PRIMARY KEY AUTOINCREMENT): Unique identifier for the project.
- name (TEXT NOT NULL UNIQUE): Name of the project. Must be unique across all
  projects.
- awaiting_purge (BOOLEAN NOT NULL DEFAULT 0): Flag indicating if the project
  is scheduled for purging.
- announcement (TEXT NOT NULL DEFAULT ''): Optional announcement message
  associated with the project.
- show_announcement_on_overview (INTEGER NOT NULL DEFAULT 0): Flag (0 or 1) to
  indicate whether the announcement should be shown on the overview page.
- creation_date (TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP): The timestamp
  when the project was created.
"""

TABLE_NAME_PRJ_PROJECTS: str = "prj_projects"
TABLE_SQL_PRJ_PROJECTS: str = f"""
    CREATE TABLE {TABLE_NAME_PRJ_PROJECTS} (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        awaiting_purge BOOLEAN NOT NULL DEFAULT 0,
        announcement TEXT NOT NULL DEFAULT '',
        show_announcement_on_overview INTEGER NOT NULL DEFAULT 0,
        creation_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
"""
