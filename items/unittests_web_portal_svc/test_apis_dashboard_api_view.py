import http
import unittest
from unittest.mock import AsyncMock, MagicMock, patch
import quart
from apis.dashboard_api_view import DashboardApiView
from metadata_settings import MetadataSettings
from configuration.configuration_manager import ConfigurationManager
import page_locations as pages
from base_view import ApiResponse


class RealFormMock:
    def __init__(self, data):
        self._data = data

    def get(self, key):
        return self._data.get(key)

    def to_dict(self):
        return self._data.copy()

    def __await__(self):
        async def _wrapper():
            return self

        return _wrapper().__await__()


class TestApisDashboardApiView(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.app = quart.Quart(__name__)
        self.logger = MagicMock()
        self.metadata = MetadataSettings()
        self.view = DashboardApiView(self.logger,
                                     self.metadata)
        self.view._render_page = AsyncMock()
        self.view._generate_redirect = MagicMock(return_value="redirect_url")


        self.client = self.app.test_client()

        # Register route for testing
        self.app.add_url_rule('/admin/overview',
                              view_func=self.view.admin_overview,
                              methods=['GET'])
        self.app.add_url_rule('/admin/projects',
                              view_func=self.view.admin_projects,
                              methods=['GET', 'POST'])
        self.app.add_url_rule('/admin/users_roles',
                              view_func=self.view.admin_users_and_roles,
                              methods=['GET'])
        self.app.add_url_rule('/admin/manage_data',
                              view_func=self.view.admin_manage_data,
                              methods=['GET'])
        self.app.add_url_rule('/admin/site_settings',
                              view_func=self.view.admin_site_settings,
                              methods=['GET'])
        self.app.add_url_rule('/admin/add_project',
                              view_func=self.view.admin_add_project,
                              methods=['GET', 'POST'])
        self.app.add_url_rule('/admin/<project_id>/modify_project',
                              view_func=self.view.admin_modify_project,
                              methods=['GET', 'POST'])

        """Ensure Quart test request context is available."""
        self.test_client = self.app.test_client()
        self.context = self.app.test_request_context('/')
        await self.context.__aenter__()

    async def test_admin_overview(self):
        self.view._render_page = AsyncMock(return_value="Mock Page")

        async with self.client as client:
            response = await client.get('/admin/overview')

            # Check response status
            self.assertEqual(response.status_code,
                             http.HTTPStatus.OK)

    @patch.object(ConfigurationManager, 'get_entry')
    async def test_admin_projects_GET_success(self, mock_get_entry):
        mock_call_api_get = AsyncMock()
        mock_call_api_get.return_value = MagicMock(
            status_code=http.HTTPStatus.OK,
            body={'projects': []})
        self.view._call_api_get = mock_call_api_get
        self.view._render_page = AsyncMock(return_value="Mock Page")

        async with self.client as client:
            response = await client.get('/admin/projects')

            # Check response status
            self.assertEqual(response.status_code,
                             http.HTTPStatus.OK)

    @patch.object(ConfigurationManager, 'get_entry')
    async def test_admin_projects_GET_internal_error(self, mock_get_entry):
        mock_call_api_get = AsyncMock()
        mock_call_api_get.return_value = MagicMock(
            status_code=http.HTTPStatus.BAD_REQUEST,
            body={'projects': []})
        self.view._call_api_get = mock_call_api_get
        self.view._render_page = AsyncMock(return_value="Mock Page")

        async with self.client as client:
            response = await client.get('/admin/projects')

            # Check response status
            self.assertEqual(response.status_code,
                             http.HTTPStatus.OK)

        # Check that the internal error page is rendered
        self.view._render_page.assert_called_once_with(pages.TEMPLATE_INTERNAL_ERROR_PAGE)

    @patch.object(ConfigurationManager, 'get_entry')
    async def test_admin_projects_POST_success(self, mock_get_entry):
        mock_call_api_post = AsyncMock()
        mock_call_api_post.return_value = MagicMock(
            status_code=http.HTTPStatus.OK,
            body={})
        self.view._call_api_post = mock_call_api_post
        self.view._render_page = AsyncMock(return_value="Mock Page")

        async with self.client as client:
            response = await client.post('/admin/projects')

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

    async def test_admin_add_project_GET(self):
        self.view._render_page = AsyncMock(return_value="Mock Page")

        async with self.client as client:
            response = await client.get('/admin/add_project')

            # Check that the internal error page is rendered
            self.view._render_page.assert_called_once_with(
                pages.PAGE_INSTANCE_ADMIN_ADD_PROJECT,
                instance_name='', active_page='administration',
                active_admin_page='admin_page_site_settings',
                form_data={})

    @patch.object(ConfigurationManager, 'get_entry')
    async def test_admin_add_project_POST_success(self, mock_get_entry):
        response_body = ApiResponse(
            status_code=http.HTTPStatus.OK,
            body={'status': 1}, content_type='application/json', exception_msg=None)

        self.view._call_api_post = AsyncMock(
            return_value=response_body,
            status_code=http.HTTPStatus.OK)
        self.view._generate_redirect = MagicMock(return_value="redirect_response")

        mock_request = MagicMock()
        mock_request.method = 'POST'
        mock_request.form = RealFormMock({
            'project_name': 'Test',
            'announcement': 'Test',
            'show_announcement': 'on'
        })

        with patch('quart.request', mock_request):
            result = await self.view.admin_add_project()
            self.view._generate_redirect.assert_called_once_with('/admin/projects')

    @patch.object(ConfigurationManager, 'get_entry')
    async def test_admin_add_project_POST_failed_internal_error(self, mock_get_entry):
        self.view._render_page = AsyncMock(return_value="Mock Page")

        response_body = ApiResponse(
            status_code=http.HTTPStatus.INTERNAL_SERVER_ERROR,
            body={'status': 1}, content_type='application/json', exception_msg=None)

        self.view._call_api_post = AsyncMock(
            return_value=response_body,
            status_code=http.HTTPStatus.INTERNAL_SERVER_ERROR)

        mock_request = MagicMock()
        mock_request.method = 'POST'
        mock_request.form = RealFormMock({
            'project_name': 'Test',
            'announcement': 'Test',
            'show_announcement': 'on'
        })

        with patch('quart.request', mock_request):
            result = await self.view.admin_add_project()
            self.view._render_page.assert_called_once_with(
                'instance_admin_add_project.html',
                instance_name='',
                active_page='administration',
                active_admin_page='admin_page_site_settings',
                error_msg_str='Internal server error!',
                form_data={'project_name': 'Test',
                           'announcement': 'Test',
                           'show_announcement': 'on'})

    @patch.object(ConfigurationManager, 'get_entry')
    async def test_admin_add_project_POST_failed_bad_request(self, mock_get_entry):
        self.view._render_page = AsyncMock(return_value="Mock Page")

        response_body = ApiResponse(
            status_code=http.HTTPStatus.BAD_REQUEST,
            body={'status': 0, 'error': 'test_error'},
            content_type='application/json',
            exception_msg=None)

        self.view._call_api_post = AsyncMock(
            return_value=response_body,
            status_code=http.HTTPStatus.INTERNAL_SERVER_ERROR)

        mock_request = MagicMock()
        mock_request.method = 'POST'
        mock_request.form = RealFormMock({
            'project_name': 'Test',
            'announcement': 'Test',
            'show_announcement': 'on'
        })

        with patch('quart.request', mock_request):
            result = await self.view.admin_add_project()
            self.view._render_page.assert_called_once_with(
                'instance_admin_add_project.html',
                instance_name='',
                active_page='administration',
                active_admin_page='admin_page_site_settings',
                error_msg_str='test_error',
                form_data={'project_name': 'Test',
                           'announcement': 'Test',
                           'show_announcement': 'on'})

    @patch.object(ConfigurationManager, 'get_entry')
    async def test_admin_modify_project_get_success(self, mock_get_entry):
        self.view._metadata_settings = MagicMock()
        self.view._metadata_settings.instance_name = "Test Instance"

        mock_get_entry.return_value = "http://localhost"

        response_body = {
            "name": "Demo Project",
            "announcement": "This is a test project.",
            "show_announcement_on_overview": True
        }
        mock_call_api_get = AsyncMock()
        mock_call_api_get.return_value = MagicMock(
            status_code=http.HTTPStatus.OK,
            body=response_body)
        self.view._call_api_get = mock_call_api_get
        self.view._render_page = AsyncMock(return_value="Mock Page")

        async with self.client as client:
            response = await client.get('/admin/123/modify_project')
            self.assertIsNotNone(response, "Response is None. Check logs.")
            self.assertEqual(response.status_code, http.HTTPStatus.OK)

        self.view._call_api_get.assert_called_once_with("http://localhost/web/projects/123")
        self.view._render_page.assert_called_once_with(
            'instance_admin_modify_project.html',
            instance_name="Test Instance",
            active_page="administration",
            active_admin_page="admin_page_site_settings",
            form_data={
                "id": "123",
                "project_name": "Demo Project",
                "announcement": "This is a test project.",
                "show_announcement": True,
            }
        )

    @patch.object(ConfigurationManager, 'get_entry')
    async def test_admin_modify_project_get_fail(self, mock_get_entry):
        mock_get_entry.return_value = "http://localhost"

        mock_call_api_get = AsyncMock()
        mock_call_api_get.return_value = MagicMock(
            status_code=http.HTTPStatus.INTERNAL_SERVER_ERROR,
            body={'status': 0})
        self.view._call_api_get = mock_call_api_get
        self.view._render_page = AsyncMock(return_value="Mock Page")

        self.view._generate_redirect.return_value = "Redirected to admin/projects"

        async with self.client as client:
            response = await client.get('http://localhost/admin/123/modify_project')

        self.view._call_api_get.assert_called_once_with("http://localhost/web/projects/123")
        self.view._generate_redirect.assert_called_once_with('admin/projects')

    @patch.object(ConfigurationManager, 'get_entry')
    async def test_admin_modify_project_post_success(self, mock_get_entry):
        mock_get_entry.return_value = "http://localhost/"

        self.view._call_api_patch = AsyncMock()
        self.view._call_api_patch.return_value = ApiResponse(
            status_code=http.HTTPStatus.OK
        )
        self.view._generate_redirect.return_value = "Redirected to admin/projects"

        request_data = {
            "project_name": "Updated Project",
            "announcement": "Updated Announcement",
            "show_announcement": "on"
        }

        async with self.client as client:
            response = await client.post('/admin/123/modify_project', form=request_data)

        self.view._call_api_patch.assert_called_once_with(
            "http://localhost/web/admin/projects/123",
            {
                "name": "Updated Project",
                "announcement": "Updated Announcement",
                "announcement_on_overview": True
            }
        )
        self.view._generate_redirect.assert_called_once_with('admin/projects')

    @patch.object(ConfigurationManager, 'get_entry')
    async def test_admin_modify_project_post_fail(self, mock_get_entry):
        mock_get_entry.return_value = "http://localhost/"

        self.view._call_api_patch = AsyncMock()
        self.view._call_api_patch.return_value = ApiResponse(
            status_code=http.HTTPStatus.BAD_REQUEST,
            body={"error": "Invalid data"}
        )
        self.view._render_page.return_value = "Error Page Rendered"

        request_data = {
            "project_name": "Invalid Project",
            "announcement": "Invalid Announcement",
            "show_announcement": "off"
        }

        async with self.client as client:
            response = await client.post('/admin/123/modify_project', form=request_data)

        self.view._call_api_patch.assert_called_once_with(
            "http://localhost/web/admin/projects/123",
            {
                "name": "Invalid Project",
                "announcement": "Invalid Announcement",
                "announcement_on_overview": False
            }
        )
        self.view._render_page.assert_called_once_with(
            "instance_admin_modify_project.html",
            instance_name=self.view._metadata_settings.instance_name,
            active_page="administration",
            active_admin_page="admin_page_site_settings",
            form_data={
                "project_name": "Invalid Project",
                "announcement": "Invalid Announcement",
                "show_announcement": False
            },
            error_msg_str="Internal error modifying project"
        )
