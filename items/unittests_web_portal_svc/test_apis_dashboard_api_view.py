import http
import unittest
from unittest.mock import AsyncMock, MagicMock
import quart
from apis.dashboard_api_view import DashboardApiView
from metadata_settings import MetadataSettings


class TestApisDashboardApiView(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.app = quart.Quart(__name__)
        self.logger = MagicMock()
        self.metadata = MetadataSettings()
        self.view = DashboardApiView(self.logger,
                                     self.metadata)

        self.client = self.app.test_client()  # Client for making requests in tests

        # Register route for testing
        self.app.add_url_rule('/admin/overview',
                              view_func=self.view.admin_overview,
                              methods=['GET'])
        self.app.add_url_rule('/admin/projects',
                              view_func=self.view.admin_projects,
                              methods=['GET'])
        self.app.add_url_rule('/admin/users_roles',
                              view_func=self.view.admin_users_and_roles,
                              methods=['GET'])
        self.app.add_url_rule('/admin/manage_data',
                              view_func=self.view.admin_manage_data,
                              methods=['GET'])
        self.app.add_url_rule('/admin/site_settings',
                              view_func=self.view.admin_site_settings,
                              methods=['GET'])

    async def test_admin_overview(self):
        self.view._render_page = AsyncMock(return_value="Mock Page")

        async with self.client as client:
            response = await client.get('/admin/overview')

            # Check response status
            self.assertEqual(response.status_code,
                             http.HTTPStatus.OK)

    async def test_admin_projects(self):
        self.view._render_page = AsyncMock(return_value="Mock Page")

        async with self.client as client:
            response = await client.get('/admin/projects')

            # Check response status
            self.assertEqual(response.status_code,
                             http.HTTPStatus.OK)

    async def test_admin_admin_users_and_roles(self):
        self.view._render_page = AsyncMock(return_value="Mock Page")

        async with self.client as client:
            response = await client.get('/admin/users_roles')

            # Check response status
            self.assertEqual(response.status_code,
                             http.HTTPStatus.OK)

    async def test_admin_manage_data(self):
        self.view._render_page = AsyncMock(return_value="Mock Page")

        async with self.client as client:
            response = await client.get('/admin/manage_data')

            # Check response status
            self.assertEqual(response.status_code,
                             http.HTTPStatus.OK)

    async def test_admin_site_settings(self):
        self.view._render_page = AsyncMock(return_value="Mock Page")

        async with self.client as client:
            response = await client.get('/admin/site_settings')

            # Check response status
            self.assertEqual(response.status_code,
                             http.HTTPStatus.OK)
