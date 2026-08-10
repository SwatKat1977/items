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
import unittest
from unittest.mock import AsyncMock, MagicMock
from weaver_framework.microservice.api_response import ApiResponse
from _test_utils import make_app
from items.services.items_web_portal.page_handler_injections import (
    PageHandlerInjections)
from items.services.items_web_portal.page_handlers import create_page_handlers

_VALID_PROJECT_BODY = {
    "project_name": "Wiring Test",
    "announcement": "",
}


class TestRouteWiring(unittest.IsolatedAsyncioTestCase):
    """
    Exercises every route factory and every registered endpoint.

    The goal is coverage of page_handlers/__init__.py and every
    page_handlers/*/__init__.py factory - specifically the factory function
    bodies and the one-line delegate closures inside each route. Response
    correctness is not asserted here; that belongs to the handler unit tests.
    """

    async def asyncSetUp(self):
        config = MagicMock()
        config.apis_gateway_svc = "http://gateway/"
        rest_client = AsyncMock()
        rest_client.get.return_value = ApiResponse(
            status_code=200,
            body={
                "name": "Project X",
                "announcement": "",
                "show_announcement_on_overview": False,
                "projects": [],
                "users": [],
                "invites": [],
                "folders": [],
                "test_cases": [],
            })
        rest_client.post.return_value = ApiResponse(status_code=200, body={})
        rest_client.patch.return_value = ApiResponse(status_code=200, body={})
        rest_client.delete.return_value = ApiResponse(status_code=200, body={})
        metadata = MagicMock()
        metadata.instance_name = "INSTANCE"

        injections = PageHandlerInjections(
            config=config,
            logger=MagicMock(),
            metadata=metadata,
            rest_client=rest_client)

        blueprint = create_page_handlers(injections)

        self.app = make_app()
        self.app.register_blueprint(blueprint)
        self.client = self.app.test_client()

    # ------------------------------------------------------------------
    # Auth routes
    # ------------------------------------------------------------------

    async def test_index_route_is_reachable(self):
        async with self.client as c:
            response = await c.get("/")
        self.assertNotEqual(response.status_code, 405)

    async def test_login_get_route_is_reachable(self):
        async with self.client as c:
            response = await c.get("/login")
        self.assertNotEqual(response.status_code, 405)

    async def test_login_post_route_is_reachable(self):
        async with self.client as c:
            response = await c.post(
                "/login", form={"user_email": "a@b.com",
                                "password": "password1"})
        self.assertNotEqual(response.status_code, 405)

    async def test_logout_route_is_reachable(self):
        async with self.client as c:
            response = await c.get("/logout")
        self.assertNotEqual(response.status_code, 405)

    # ------------------------------------------------------------------
    # Admin dashboard / stub pages
    # ------------------------------------------------------------------

    async def test_admin_overview_route_is_reachable(self):
        async with self.client as c:
            response = await c.get("/admin/")
        self.assertNotEqual(response.status_code, 405)

    async def test_admin_users_roles_route_is_reachable(self):
        async with self.client as c:
            response = await c.get("/admin/users_roles")
        self.assertNotEqual(response.status_code, 405)

    async def test_admin_invite_user_route_is_reachable(self):
        async with self.client as c:
            response = await c.post(
                "/admin/users_roles/invite",
                form={"email_address": "a@b.com"})
        self.assertNotEqual(response.status_code, 405)

    async def test_admin_resend_invite_route_is_reachable(self):
        async with self.client as c:
            response = await c.post(
                "/admin/users_roles/invite/resend",
                form={"email_address": "a@b.com"})
        self.assertNotEqual(response.status_code, 405)

    async def test_admin_uninvite_route_is_reachable(self):
        async with self.client as c:
            response = await c.post(
                "/admin/users_roles/invite/uninvite",
                form={"email_address": "a@b.com"})
        self.assertNotEqual(response.status_code, 405)

    async def test_admin_manage_data_route_is_reachable(self):
        async with self.client as c:
            response = await c.get("/admin/manage_data")
        self.assertNotEqual(response.status_code, 405)

    async def test_admin_customisations_route_is_reachable(self):
        async with self.client as c:
            response = await c.get("/admin/customisations")
        self.assertNotEqual(response.status_code, 405)

    async def test_admin_case_field_add_route_is_reachable(self):
        async with self.client as c:
            response = await c.post(
                "/admin/customisations/case_fields",
                form={"field_name": "Wiring Field",
                     "system_name": "wiring_field", "field_type": "String"})
        self.assertNotEqual(response.status_code, 405)

    async def test_admin_case_field_modify_route_is_reachable(self):
        async with self.client as c:
            response = await c.post(
                "/admin/customisations/case_fields/1/modify",
                form={"field_name": "Wiring Field",
                     "system_name": "wiring_field", "field_type": "String"})
        self.assertNotEqual(response.status_code, 405)

    async def test_admin_case_field_move_route_is_reachable(self):
        async with self.client as c:
            response = await c.post(
                "/admin/customisations/case_fields/1/move",
                form={"direction": "up"})
        self.assertNotEqual(response.status_code, 405)

    async def test_admin_case_field_delete_route_is_reachable(self):
        async with self.client as c:
            response = await c.post(
                "/admin/customisations/case_fields/1/delete")
        self.assertNotEqual(response.status_code, 405)

    async def test_admin_integrations_route_is_reachable(self):
        async with self.client as c:
            response = await c.get("/admin/integrations")
        self.assertNotEqual(response.status_code, 405)

    async def test_admin_site_settings_route_is_reachable(self):
        async with self.client as c:
            response = await c.get("/admin/site_settings")
        self.assertNotEqual(response.status_code, 405)

    # ------------------------------------------------------------------
    # Admin projects
    # ------------------------------------------------------------------

    async def test_admin_projects_get_route_is_reachable(self):
        async with self.client as c:
            response = await c.get("/admin/projects")
        self.assertNotEqual(response.status_code, 405)

    async def test_admin_projects_post_route_is_reachable(self):
        async with self.client as c:
            response = await c.post("/admin/projects", form={"projectId": "1"})
        self.assertNotEqual(response.status_code, 405)

    async def test_admin_add_project_get_route_is_reachable(self):
        async with self.client as c:
            response = await c.get("/admin/add_project")
        self.assertNotEqual(response.status_code, 405)

    async def test_admin_add_project_post_route_is_reachable(self):
        async with self.client as c:
            response = await c.post("/admin/add_project",
                                    form=_VALID_PROJECT_BODY)
        self.assertNotEqual(response.status_code, 405)

    async def test_admin_modify_project_get_route_is_reachable(self):
        async with self.client as c:
            response = await c.get("/admin/1/modify_project")
        self.assertNotEqual(response.status_code, 405)

    async def test_admin_modify_project_post_route_is_reachable(self):
        async with self.client as c:
            response = await c.post("/admin/1/modify_project",
                                    form=_VALID_PROJECT_BODY)
        self.assertNotEqual(response.status_code, 405)

    # ------------------------------------------------------------------
    # Admin users
    # ------------------------------------------------------------------

    async def test_admin_add_user_get_route_is_reachable(self):
        async with self.client as c:
            response = await c.get("/admin/users_roles/add")
        self.assertNotEqual(response.status_code, 405)

    async def test_admin_add_user_post_route_is_reachable(self):
        async with self.client as c:
            response = await c.post("/admin/users_roles/add",
                                    form={"full_name": "Alice",
                                          "display_name": "Alice",
                                          "email_address": "a@b.com",
                                          "password": "password1"})
        self.assertNotEqual(response.status_code, 405)

    async def test_admin_modify_user_get_route_is_reachable(self):
        async with self.client as c:
            response = await c.get("/admin/users_roles/1/modify")
        self.assertNotEqual(response.status_code, 405)

    async def test_admin_modify_user_post_route_is_reachable(self):
        async with self.client as c:
            response = await c.post("/admin/users_roles/1/modify",
                                    form={"full_name": "Alice",
                                          "display_name": "Alice"})
        self.assertNotEqual(response.status_code, 405)

    async def test_admin_reset_password_get_route_is_reachable(self):
        async with self.client as c:
            response = await c.get("/admin/users_roles/1/reset_password")
        self.assertNotEqual(response.status_code, 405)

    async def test_admin_reset_password_post_route_is_reachable(self):
        async with self.client as c:
            response = await c.post("/admin/users_roles/1/reset_password",
                                    form={"new_password": "password1",
                                          "confirm_password": "password1"})
        self.assertNotEqual(response.status_code, 405)

    # ------------------------------------------------------------------
    # Projects / testcases
    # ------------------------------------------------------------------

    async def test_project_overview_route_is_reachable(self):
        async with self.client as c:
            response = await c.get("/1/overview")
        self.assertNotEqual(response.status_code, 405)

    async def test_project_testcases_route_is_reachable(self):
        async with self.client as c:
            response = await c.get("/1/testcases")
        self.assertNotEqual(response.status_code, 405)


if __name__ == "__main__":
    unittest.main()
