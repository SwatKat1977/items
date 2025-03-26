import http
import logging
import unittest
from unittest.mock import AsyncMock, MagicMock, patch
from quart import Quart
from configuration.configuration_manager import ConfigurationManager
from apis.project_api_view import ProjectApiView


class TestApiProjectApiView(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.mock_logger = MagicMock(spec=logging.Logger)
        self.view = ProjectApiView(self.mock_logger)

        # Set up Quart test client and mock dependencies.
        self.app = Quart(__name__)
        self.client = self.app.test_client()

        # Register route for testing
        self.app.add_url_rule('/project/overviews',
                              view_func=self.view.project_overviews,
                              methods=['GET'])
        self.app.add_url_rule('/project/add',
                              view_func=self.view.add_project,
                              methods=['POST'])
        self.app.add_url_rule('/<project_id>/delete_project',
                              view_func=self.view.delete_project,
                              methods=['DELETE'])

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
            "name": "test project"
        }
        async with self.client as client:
            response = await client.post('/project/add',
                                         json=request_body)

            self.assertEqual(response.status_code,
                             http.HTTPStatus.INTERNAL_SERVER_ERROR)
