import http
import logging
import unittest
from unittest.mock import AsyncMock, MagicMock, patch
from quart import Quart
from configuration.configuration_manager import ConfigurationManager
from apis.project_api_view import ProjectApiView
from threadsafe_configuration import ThreadSafeConfiguration


class TestApiProjectApiView(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.mock_logger = MagicMock(spec=logging.Logger)
        self.view = ProjectApiView(self.mock_logger)

        # Set up Quart test client and mock dependencies.
        self.app = Quart(__name__)
        self.client = self.app.test_client()

        # Register route for testing
        self.app.add_url_rule('/project/details/<project_id>',
                              view_func=self.view.project_details,
                              methods=['GET'])
        self.app.add_url_rule('/project/overviews',
                              view_func=self.view.project_overviews,
                              methods=['GET'])
        self.app.add_url_rule('/project/add',
                              view_func=self.view.add_project,
                              methods=['POST'])
        self.app.add_url_rule('/<project_id>/delete_project',
                              view_func=self.view.delete_project,
                              methods=['DELETE'])
        self.app.add_url_rule('/project/modify/<project_id>',
                              view_func=self.view.modify_project,
                              methods=['POST'])

    @patch.object(ConfigurationManager, 'get_entry')
    async def test_project_overviews_internal_error(self, mock_get_entry):

        # Mock the response of `_call_api_post`
        mock_call_api_get = AsyncMock()
        mock_call_api_get.return_value = MagicMock(status_code=http.HTTPStatus.INTERNAL_SERVER_ERROR,
                                                   body={"status": True})
        self.view._call_api_get = mock_call_api_get

        async with self.client as client:
            response = await client.get('/project/overviews')

            # Check response status
            self.assertEqual(response.status_code, http.HTTPStatus.INTERNAL_SERVER_ERROR)

            # Check response JSON
            data = await response.get_json()
            self.assertEqual(data['status'], 0)

    @patch.object(ConfigurationManager, 'get_entry')
    async def test_project_overviews_success(self, mock_get_entry):

        call_return: dict = {
            "projects": [
                {
                    "id": 1,
                    "name": "Project Alpha",
                    "no_of_milestones": 0,
                    "no_of_test_runs": 0
                }
            ]
        }

        # Mock the response of `_call_api_post`
        mock_call_api_get = AsyncMock()
        mock_call_api_get.return_value = MagicMock(status_code=http.HTTPStatus.OK,
                                                   body=call_return)
        self.view._call_api_get = mock_call_api_get

        async with self.client as client:
            response = await client.get('/project/overviews')

            # Check response status
            self.assertEqual(response.status_code, http.HTTPStatus.OK)

            # Check response JSON
            data = await response.get_json()
            self.assertEqual(data['projects'][0],
                             {'id': 1, 'name': 'Project Alpha', 'no_of_milestones': 0, 'no_of_test_runs': 0})

    @patch.object(ConfigurationManager, 'get_entry')
    async def test_delete_project_success(self, mock_get_entry):

        # Mock the response of `_call_api_delete`
        mock_call_api_delete = AsyncMock()
        mock_call_api_delete.return_value = MagicMock(status_code=http.HTTPStatus.OK,
                                                      body={})
        self.view._call_api_delete = mock_call_api_delete

        async with self.client as client:
            response = await client.delete('/1/delete_project')

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
            response = await client.delete('/1/delete_project')

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
            response = await client.delete('/1/delete_project')

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
            response = await client.post('/project/add',
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
            response = await client.post('/project/add',
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
            response = await client.post('/project/modify/123', json=request_body)

        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        self.assertEqual(await response.get_json(), {"status": 1})

        # Verify URL was correctly constructed
        mock_call_api_post.assert_called_once_with(
            "http://localhost/project/modify/123", request_body)

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
            response = await client.post('/project/modify/123', json=request_body)

        self.assertEqual(response.status_code, http.HTTPStatus.BAD_REQUEST)
        self.assertEqual(await response.get_json(), {
            "status": 0,
            "error": "Invalid Project Name"
        })
        mock_call_api_post.assert_called_once_with(
            "http://localhost/project/modify/123", request_body
        )


















    @patch.object(ThreadSafeConfiguration, "apis_cms_svc", "http://localhost/")
    async def test_project_details_success(self):
        mock_call_api_get = AsyncMock()
        mock_call_api_get.return_value = AsyncMock(status_code=http.HTTPStatus.OK, body={"id": 123, "name": "Test Project"})
        self.view._call_api_get = mock_call_api_get

        async with self.client as client:
            response = await client.get('/project/details/123')

        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        self.assertEqual(await response.get_json(), {"id": 123, "name": "Test Project"})
        mock_call_api_get.assert_called_once_with("http://localhost/project/details/123")

    @patch.object(ThreadSafeConfiguration, "apis_cms_svc", "http://localhost/")
    async def test_project_details_invalid_project_id(self):
        mock_call_api_get = AsyncMock()
        mock_call_api_get.return_value = AsyncMock(status_code=http.HTTPStatus.BAD_REQUEST)
        self.view._call_api_get = mock_call_api_get

        async with self.client as client:
            response = await client.get('/project/details/999')

        self.assertEqual(response.status_code, http.HTTPStatus.INTERNAL_SERVER_ERROR)
        self.assertEqual(await response.get_json(), {"status": 0, "error": "Invalid project ID"})
        mock_call_api_get.assert_called_once_with("http://localhost/project/details/999")

    @patch.object(ThreadSafeConfiguration, "apis_cms_svc", "http://localhost/")
    async def test_project_details_internal_error(self):
        mock_call_api_get = AsyncMock()
        mock_call_api_get.return_value = AsyncMock(status_code=http.HTTPStatus.INTERNAL_SERVER_ERROR, exception_msg="Database Error")
        self.view._call_api_get = mock_call_api_get
        self.view._logger = MagicMock()

        async with self.client as client:
            response = await client.get('/project/details/456')

        self.assertEqual(response.status_code, http.HTTPStatus.INTERNAL_SERVER_ERROR)
        self.assertEqual(await response.get_json(), {"status": 0, "error": "Internal error!"})
        mock_call_api_get.assert_called_once_with("http://localhost/project/details/456")
        self.view._logger.critical.assert_called_once_with(
            "CMS svc /project/details request invalid - Reason: %s",
            "Database Error"
        )
