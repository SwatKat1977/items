import http
import logging
import unittest
from unittest.mock import AsyncMock, MagicMock, patch
from quart import Quart
from configuration.configuration_manager import ConfigurationManager
from apis.web.admin.projects_api_view import ProjectsApiView
from threadsafe_configuration import ThreadSafeConfiguration


class TestApiWebAdminProjectApiView(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.mock_logger = MagicMock(spec=logging.Logger)
        self.view = ProjectsApiView(self.mock_logger)

        # Set up Quart test client and mock dependencies.
        self.app = Quart(__name__)
        self.client = self.app.test_client()

        # Register route for testing
        self.app.add_url_rule('/web/admin/projects',
                              view_func=self.view.add_project,
                              methods=['POST'])
        self.app.add_url_rule('/web/admin/projects/<project_id>',
                              view_func=self.view.delete_project,
                              methods=['DELETE'])
        self.app.add_url_rule('/web/admin/projects/<project_id>',
                              view_func=self.view.modify_project,
                              methods=['PATCH'])

    @patch.object(ConfigurationManager, 'get_entry')
    async def test_delete_project_success(self, mock_get_entry):

        # Mock the response of `_call_api_delete`
        mock_call_api_delete = AsyncMock()
        mock_call_api_delete.return_value = MagicMock(status_code=http.HTTPStatus.OK,
                                                      body={})
        self.view._call_api_delete = mock_call_api_delete

        async with self.client as client:
            response = await client.delete('/web/admin/projects/1')

            # Check response status
            self.assertEqual(response.status_code, http.HTTPStatus.OK)

    @patch.object(ConfigurationManager, 'get_entry')
    async def test_delete_project_internal_error(self, mock_get_entry):

        # Mock the response of `_call_api_post`
        mock_call_api_delete = AsyncMock()
        mock_call_api_delete.return_value = MagicMock(
            status_code=http.HTTPStatus.INTERNAL_SERVER_ERROR,
            body={"status": True})
        self.view._call_api_delete = mock_call_api_delete

        async with self.client as client:
            response = await client.delete('/web/admin/projects/1')

            # Check response status
            self.assertEqual(response.status_code,
                             http.HTTPStatus.INTERNAL_SERVER_ERROR)

    @patch.object(ConfigurationManager, 'get_entry')
    async def test_delete_project_bad_request(self, mock_get_entry):

        # Mock the response of `_call_api_delete`
        mock_call_api_delete = AsyncMock()
        mock_call_api_delete.return_value = MagicMock(
            status_code=http.HTTPStatus.BAD_REQUEST,
            body={})
        self.view._call_api_delete = mock_call_api_delete

        async with self.client as client:
            response = await client.delete('/web/admin/projects/1')

            # Check response status
            self.assertEqual(response.status_code, http.HTTPStatus.BAD_REQUEST)

    @patch.object(ConfigurationManager, 'get_entry')
    async def test_add_project_success(self, mock_get_entry):
        # Mock the response of `_call_api_delete`
        mock_call_api_post = AsyncMock()
        mock_call_api_post.return_value = MagicMock(
            status_code=http.HTTPStatus.OK,
            body={'status': 1})
        self.view._call_api_post = mock_call_api_post

        request_body: dict = {
            "name": "test project",
            "announcement": "Test that announcement are written",
            "announcement_on_overview": False
        }
        async with self.client as client:
            response = await client.post('/web/admin/projects',
                                         json=request_body)

            # Check response status
            self.assertEqual(response.status_code, http.HTTPStatus.OK)

    @patch.object(ConfigurationManager, 'get_entry')
    async def test_add_project_internal_error(self, mock_get_entry):
        mock_call_api_post = AsyncMock()
        mock_call_api_post.return_value = MagicMock(
            status_code=http.HTTPStatus.BAD_REQUEST)
        self.view._call_api_post = mock_call_api_post

        request_body: dict = {
            "name": "test project",
            "announcement": "Test that announcement are written",
            "announcement_on_overview": False
        }
        async with self.client as client:
            response = await client.post('/web/admin/projects',
                                         json=request_body)

            self.assertEqual(response.status_code,
                             http.HTTPStatus.INTERNAL_SERVER_ERROR)

    @patch.object(ThreadSafeConfiguration, "apis_cms_svc", "http://localhost/")
    async def test_modify_project_success(self):
        mock_call_api_post = AsyncMock()
        mock_call_api_post.return_value = AsyncMock(status_code=http.HTTPStatus.OK)
        self.view._call_api_post = mock_call_api_post

        request_body = {
            "name": "Updated Project",
            "announcement": "New announcement",
            "announcement_on_overview": True
        }

        async with self.client as client:
            response = await client.patch('/web/admin/projects/123', json=request_body)

        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        self.assertEqual(await response.get_json(), {"status": 1})

        # Verify URL was correctly constructed
        mock_call_api_post.assert_called_once_with(
            "http://localhost/projects/modify/123", request_body)

    @patch.object(ThreadSafeConfiguration, "apis_cms_svc", "http://localhost/")
    async def test_modify_project_failure(self):
        mock_call_api_post = AsyncMock()
        mock_call_api_post.return_value = AsyncMock(
            status_code=http.HTTPStatus.BAD_REQUEST,
            exception_msg="Invalid Project Name",
            body={'error_msg': "Invalid Project Name"}
        )
        self.view._call_api_post = mock_call_api_post

        request_body = {
            "name": "Invalid Project",
            "announcement": "Error Announcement",
            "announcement_on_overview": False
        }

        async with self.client as client:
            response = await client.patch('/web/admin/projects/123', json=request_body)

        self.assertEqual(response.status_code, http.HTTPStatus.BAD_REQUEST)
        self.assertEqual(await response.get_json(), {
            "status": 0,
            "error": "Invalid Project Name"
        })
        mock_call_api_post.assert_called_once_with(
            "http://localhost/projects/modify/123", request_body
        )

