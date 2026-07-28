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
from http import HTTPStatus
from weaver_framework.microservice.api_response import ApiResponse
from _test_utils import make_app
from items.services.items_web_portal.page_handlers.admin.dashboard.\
    admin_overview_page_handler import AdminOverviewPageHandler
from items.services.items_web_portal.page_handlers.admin.\
    admin_integrations_page_handler import AdminIntegrationsPageHandler
from items.services.items_web_portal.page_handlers.admin.\
    admin_manage_data_page_handler import AdminManageDataPageHandler
from items.services.items_web_portal.page_handlers.admin.\
    admin_site_settings_page_handler import AdminSiteSettingsPageHandler
from items.services.items_web_portal.page_handlers.admin.\
    admin_users_and_roles_page_handler import AdminUsersAndRolesPageHandler

_LOGGER = MagicMock()


def _config():
    config = MagicMock()
    config.apis_gateway_svc = "http://gateway/"
    return config


def _metadata():
    metadata = MagicMock()
    metadata.instance_name = "INSTANCE"
    return metadata


_AUTH_HEADERS = {"Cookie": "items_token=abc; items_user=bob"}


def _make_stub_test(handler_cls, method_name, route_path):
    """Build a self-contained test case class for one of the trivial,
    identically-shaped admin stub page handlers (render-only, no branches
    beyond the @require_session guard already covered by test_decorators)."""

    class _Test(unittest.IsolatedAsyncioTestCase):

        async def asyncSetUp(self):
            self.rest_client = AsyncMock()
            self.rest_client.post.return_value = ApiResponse(
                status_code=HTTPStatus.OK, body={"status": "VALID"})
            handler = handler_cls(_LOGGER, _config(), self.rest_client,
                                  _metadata())

            app = make_app()

            @app.route(route_path, methods=["GET"])
            async def _route():
                return await getattr(handler, method_name)()

            self.client = app.test_client()

        async def test_renders_page(self):
            async with self.client as c:
                response = await c.get(route_path, headers=_AUTH_HEADERS)
            self.assertEqual(response.status_code, 200)
            text = await response.get_data(as_text=True)
            self.assertNotIn("Refresh", text)

        async def test_redirects_when_not_authenticated(self):
            async with self.client as c:
                response = await c.get(route_path)
            self.assertEqual(response.status_code, 200)
            text = await response.get_data(as_text=True)
            self.assertIn("Refresh", text)

    return _Test


TestAdminOverviewPageHandler = _make_stub_test(
    AdminOverviewPageHandler, "overview", "/admin/")
TestAdminIntegrationsPageHandler = _make_stub_test(
    AdminIntegrationsPageHandler, "integrations", "/admin/integrations")
TestAdminManageDataPageHandler = _make_stub_test(
    AdminManageDataPageHandler, "manage_data", "/admin/manage_data")
TestAdminSiteSettingsPageHandler = _make_stub_test(
    AdminSiteSettingsPageHandler, "site_settings", "/admin/site_settings")
TestAdminUsersAndRolesPageHandler = _make_stub_test(
    AdminUsersAndRolesPageHandler, "users_and_roles", "/admin/users_roles")


if __name__ == "__main__":
    unittest.main()
