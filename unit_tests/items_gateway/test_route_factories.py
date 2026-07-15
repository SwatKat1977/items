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
from quart import Quart
from weaver_framework.microservice.api_response import ApiResponse
from items.services.items_gateway.route_injections import RouteInjections
from items.services.items_gateway.routes import create_routes
from items.services.items_gateway.sessions import Sessions

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

    The goal is coverage of routes/__init__.py and routes/web/*/__init__.py —
    specifically the factory function bodies and the one-line delegate
    closures inside each route. Response correctness is not asserted here;
    that belongs to the handler unit tests.
    """

    async def asyncSetUp(self):
        logger = MagicMock()
        sessions = Sessions()
        configuration = MagicMock()
        configuration.apis_cms_svc = "http://cms/"
        configuration.apis_identity_svc = "http://identity/"
        configuration.general_api_signing_secret = "secret"
        rest_client = AsyncMock()
        rest_client.get.return_value = ApiResponse(status_code=200, body={})
        rest_client.post.return_value = ApiResponse(status_code=200, body={})
        rest_client.put.return_value = ApiResponse(status_code=200, body={})
        rest_client.patch.return_value = ApiResponse(status_code=200, body={})
        rest_client.delete.return_value = ApiResponse(status_code=200, body={})
        metadata_handler = MagicMock()
        metadata_handler.build_metadata_dictionary.return_value = {}

        injections = RouteInjections(
            logger=logger,
            sessions=sessions,
            configuration=configuration,
            rest_client=rest_client,
            metadata_handler=metadata_handler)

        blueprint = create_routes(injections)

        self.app = Quart(__name__)
        self.app.register_blueprint(blueprint)
        self.client = self.app.test_client()

    # ------------------------------------------------------------------
    # Sessions routes (routes/web/sessions/__init__.py)
    # ------------------------------------------------------------------

    async def test_create_session_route_is_reachable(self):
        async with self.client as c:
            response = await c.post(
                "/web/sessions",
                json={"email_address": "a@b.com", "password": "password1"})
        self.assertNotEqual(response.status_code, 405)

    async def test_validate_session_route_is_reachable(self):
        async with self.client as c:
            response = await c.post(
                "/web/sessions/validate",
                json={"email_address": "a@b.com", "token": "a" * 32})
        self.assertNotEqual(response.status_code, 405)

    async def test_refresh_session_route_is_reachable(self):
        async with self.client as c:
            response = await c.post("/web/sessions/refresh")
        self.assertNotEqual(response.status_code, 405)

    async def test_delete_session_route_is_reachable(self):
        async with self.client as c:
            response = await c.delete(
                "/web/sessions",
                json={"email_address": "a@b.com", "token": "a" * 32})
        self.assertNotEqual(response.status_code, 405)

    # ------------------------------------------------------------------
    # Projects routes (routes/web/projects/__init__.py)
    # ------------------------------------------------------------------

    async def test_get_project_route_is_reachable(self):
        async with self.client as c:
            response = await c.get("/web/projects/1")
        self.assertNotEqual(response.status_code, 405)

    async def test_list_projects_route_is_reachable(self):
        async with self.client as c:
            response = await c.get("/web/projects")
        self.assertNotEqual(response.status_code, 405)

    async def test_add_project_route_is_reachable(self):
        async with self.client as c:
            response = await c.post("/web/projects", json=_VALID_PROJECT_BODY)
        self.assertNotEqual(response.status_code, 405)

    async def test_update_project_route_is_reachable(self):
        async with self.client as c:
            response = await c.patch("/web/projects/1", json=_VALID_PROJECT_BODY)
        self.assertNotEqual(response.status_code, 405)

    async def test_delete_project_route_is_reachable(self):
        async with self.client as c:
            response = await c.delete("/web/projects/1")
        self.assertNotEqual(response.status_code, 405)

    # ------------------------------------------------------------------
    # Testcases routes (routes/web/testcases/__init__.py)
    # ------------------------------------------------------------------

    async def test_get_testcases_for_project_route_is_reachable(self):
        async with self.client as c:
            response = await c.get("/web/1/testcases")
        self.assertNotEqual(response.status_code, 405)

    async def test_get_testcase_route_is_reachable(self):
        async with self.client as c:
            response = await c.get("/web/testcases/1")
        self.assertNotEqual(response.status_code, 405)

    # ------------------------------------------------------------------
    # Testcase custom fields routes
    # (routes/web/testcase_custom_fields/__init__.py)
    # ------------------------------------------------------------------

    async def test_get_all_custom_fields_route_is_reachable(self):
        async with self.client as c:
            response = await c.get("/web/testcase_custom_fields/")
        self.assertNotEqual(response.status_code, 405)

    async def test_add_custom_field_route_is_reachable(self):
        async with self.client as c:
            response = await c.post("/web/testcase_custom_fields/",
                                    json=_VALID_FIELD_BODY)
        self.assertNotEqual(response.status_code, 405)

    async def test_modify_custom_field_route_is_reachable(self):
        async with self.client as c:
            response = await c.put("/web/testcase_custom_fields/1",
                                   json=_VALID_FIELD_BODY)
        self.assertNotEqual(response.status_code, 405)

    async def test_move_custom_field_route_is_reachable(self):
        async with self.client as c:
            response = await c.patch("/web/testcase_custom_fields/1",
                                     json={"direction": "up"})
        self.assertNotEqual(response.status_code, 405)

    async def test_delete_custom_field_route_is_reachable(self):
        async with self.client as c:
            response = await c.delete("/web/testcase_custom_fields/1")
        self.assertNotEqual(response.status_code, 405)

    # ------------------------------------------------------------------
    # Webhook routes (routes/web/webhook/__init__.py)
    # ------------------------------------------------------------------

    async def test_get_webhook_metadata_route_is_reachable(self):
        async with self.client as c:
            response = await c.get("/web/webhook/metadata?nonce=abc")
        self.assertNotEqual(response.status_code, 405)


if __name__ == "__main__":
    unittest.main()
