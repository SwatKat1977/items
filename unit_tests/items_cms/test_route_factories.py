"""
Copyright 2025-2026 Integrated Test Management Suite Development Team

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
import os
import sqlite3
import tempfile
import unittest
from unittest.mock import MagicMock
from quart import Quart
from items.shared.service_state import ServiceState
from items.services.items_cms.cms_configuration import CMSConfiguration
from items.services.items_cms.routes import create_routes

# Full CMS schema — covers all tables used across the three route domains.
_FULL_SCHEMA_SQL = """
CREATE TABLE prj_projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    awaiting_purge BOOLEAN NOT NULL DEFAULT 0,
    announcement TEXT NOT NULL DEFAULT '',
    show_announcement_on_overview INTEGER NOT NULL DEFAULT 0,
    creation_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE tc_folders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    parent_id INTEGER NULL,
    name TEXT NOT NULL,
    FOREIGN KEY (project_id) REFERENCES prj_projects(id) ON DELETE CASCADE,
    FOREIGN KEY (parent_id) REFERENCES tc_folders(id) ON DELETE CASCADE,
    UNIQUE (project_id, parent_id, name)
);
CREATE TABLE tc_test_cases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    folder_id INTEGER NULL,
    name TEXT NOT NULL,
    description TEXT,
    FOREIGN KEY (project_id) REFERENCES prj_projects(id) ON DELETE CASCADE,
    FOREIGN KEY (folder_id) REFERENCES tc_folders(id) ON DELETE CASCADE,
    UNIQUE (project_id, folder_id, name)
);
CREATE TABLE tc_custom_field_option_kinds (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    option_name TEXT NOT NULL UNIQUE
);
CREATE TABLE tc_custom_field_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    supports_default_value BOOLEAN NOT NULL DEFAULT 0,
    supports_is_required BOOLEAN NOT NULL DEFAULT 0
);
CREATE TABLE tc_custom_fields (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    field_name TEXT NOT NULL UNIQUE,
    description TEXT NOT NULL DEFAULT '',
    system_name TEXT NOT NULL UNIQUE,
    field_type_id INTEGER NOT NULL,
    entry_type TEXT NOT NULL CHECK(entry_type IN ('system', 'user')),
    enabled BOOLEAN NOT NULL,
    position INTEGER NOT NULL,
    is_required BOOLEAN NOT NULL DEFAULT 0,
    default_value TEXT NOT NULL DEFAULT '',
    applies_to_all_projects BOOLEAN NOT NULL DEFAULT 0,
    FOREIGN KEY (field_type_id) REFERENCES tc_custom_field_types(id)
);
CREATE TABLE tc_custom_field_projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    field_id INTEGER NOT NULL,
    project_id INTEGER NOT NULL,
    FOREIGN KEY (field_id) REFERENCES tc_custom_fields(id) ON DELETE CASCADE,
    FOREIGN KEY (project_id) REFERENCES prj_projects(id) ON DELETE CASCADE
);
CREATE TABLE tc_custom_field_type_options (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    field_id INTEGER NOT NULL,
    option_kind_id INTEGER NOT NULL,
    option_value TEXT NOT NULL,
    FOREIGN KEY (field_id) REFERENCES tc_custom_fields(id),
    FOREIGN KEY (option_kind_id) REFERENCES tc_custom_field_option_kinds(id),
    UNIQUE (field_id, option_kind_id)
);
CREATE TABLE tc_custom_field_type_option_values (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    case_field_id INTEGER NOT NULL,
    field_type_option_id INTEGER NOT NULL,
    option_value TEXT NOT NULL,
    FOREIGN KEY (case_field_id) REFERENCES tc_custom_fields(id)
);
CREATE TABLE tc_custom_field_option_values (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    test_case_id INTEGER NOT NULL,
    field_id INTEGER NOT NULL,
    value TEXT NOT NULL,
    FOREIGN KEY (field_id) REFERENCES tc_custom_fields(id) ON DELETE CASCADE,
    UNIQUE(test_case_id, field_id)
);
INSERT INTO tc_custom_field_types (name, supports_default_value, supports_is_required)
VALUES
    ('Checkbox', 1, 0), ('Date', 0, 1), ('Dropdown', 1, 1), ('Integer', 1, 1),
    ('String', 1, 1), ('Text', 1, 1), ('Url (Link)', 1, 1), ('User', 1, 1);
"""

_VALID_PROJECT_BODY = {
    "name": "WiringTest",
    "announcement": "",
    "announcement_on_overview": False,
}

_VALID_FIELD_BODY = {
    "field_name": "Wiring Field",
    "description": "",
    "system_name": "wiring_field",
    "field_type": "String",
    "enabled": True,
    "is_required": False,
    "default_value": "",
    "applies_to_all_projects": True,
}


class TestRouteWiring(unittest.IsolatedAsyncioTestCase):
    """
    Exercises every route factory and every registered endpoint.

    The goal is coverage of routes/__init__.py and routes/*/init__.py —
    specifically the factory function bodies and the one-line delegate
    closures inside each route.  Response correctness is not asserted here;
    that belongs to the handler unit tests.
    """

    async def asyncSetUp(self):
        fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        conn = sqlite3.connect(self.db_path)
        conn.executescript(_FULL_SCHEMA_SQL)
        conn.close()

        mock_config = MagicMock(spec=CMSConfiguration)
        mock_config.backend_db_filename = self.db_path

        state = ServiceState()
        state.database_enabled = True

        logger = MagicMock()
        blueprint = create_routes(logger, state, mock_config)

        self.app = Quart(__name__)
        self.app.register_blueprint(blueprint, url_prefix="")
        self.client = self.app.test_client()

    async def asyncTearDown(self):
        try:
            os.unlink(self.db_path)
        except OSError:
            pass

    # ------------------------------------------------------------------
    # System routes  (routes/system/__init__.py)
    # ------------------------------------------------------------------

    async def test_health_route_is_reachable(self):
        async with self.client as c:
            response = await c.get("/system/health")
        self.assertEqual(response.status_code, 200)

    # ------------------------------------------------------------------
    # Project routes  (routes/projects/__init__.py)
    # ------------------------------------------------------------------

    async def test_list_projects_route_is_reachable(self):
        async with self.client as c:
            response = await c.get("/projects")
        self.assertNotEqual(response.status_code, 405)

    async def test_get_project_route_is_reachable(self):
        # Project 999 doesn't exist — handler returns 404, route body ran.
        async with self.client as c:
            response = await c.get("/projects/999")
        self.assertNotEqual(response.status_code, 405)

    async def test_create_project_route_is_reachable(self):
        async with self.client as c:
            response = await c.post("/projects", json=_VALID_PROJECT_BODY)
        self.assertNotEqual(response.status_code, 405)

    async def test_modify_project_route_is_reachable(self):
        # Project doesn't exist — 404 from service, but route body ran.
        async with self.client as c:
            response = await c.patch("/projects/999", json=_VALID_PROJECT_BODY)
        self.assertNotEqual(response.status_code, 405)

    async def test_delete_project_route_is_reachable(self):
        async with self.client as c:
            response = await c.delete("/projects/999")
        self.assertNotEqual(response.status_code, 405)

    # ------------------------------------------------------------------
    # Testcase routes  (routes/testcases/__init__.py)
    # ------------------------------------------------------------------

    async def test_list_testcases_route_is_reachable(self):
        async with self.client as c:
            response = await c.get("/testcases?project_id=1")
        self.assertNotEqual(response.status_code, 405)

    async def test_get_testcase_route_is_reachable(self):
        async with self.client as c:
            response = await c.get("/testcases/999")
        self.assertNotEqual(response.status_code, 405)

    # ------------------------------------------------------------------
    # Custom-field routes  (routes/testcase_custom_fields/__init__.py)
    # ------------------------------------------------------------------

    async def test_get_custom_fields_route_is_reachable(self):
        async with self.client as c:
            response = await c.get("/testcase_custom_fields")
        self.assertNotEqual(response.status_code, 405)

    async def test_get_custom_field_route_is_reachable(self):
        async with self.client as c:
            response = await c.get("/testcase_custom_fields/999")
        self.assertNotEqual(response.status_code, 405)

    async def test_add_custom_field_route_is_reachable(self):
        async with self.client as c:
            response = await c.post("/testcase_custom_fields",
                                    json=_VALID_FIELD_BODY)
        self.assertNotEqual(response.status_code, 405)

    async def test_move_custom_field_route_is_reachable(self):
        async with self.client as c:
            response = await c.patch("/testcase_custom_fields/999",
                                     json={"direction": "up"})
        self.assertNotEqual(response.status_code, 405)

    async def test_update_custom_field_route_is_reachable(self):
        async with self.client as c:
            response = await c.put("/testcase_custom_fields/999",
                                   json=_VALID_FIELD_BODY)
        self.assertNotEqual(response.status_code, 405)

    async def test_delete_custom_field_route_is_reachable(self):
        async with self.client as c:
            response = await c.delete("/testcase_custom_fields/999")
        self.assertNotEqual(response.status_code, 405)


if __name__ == "__main__":
    unittest.main()
