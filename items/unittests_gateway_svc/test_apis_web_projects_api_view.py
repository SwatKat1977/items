import http
import logging
import unittest
from unittest.mock import AsyncMock, MagicMock, patch
from quart import Quart
from configuration.configuration_manager import ConfigurationManager
from apis.web.projects_api_view import ProjectsApiView
from threadsafe_configuration import ThreadSafeConfiguration


class TestApiProjectApiView(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.mock_logger = MagicMock(spec=logging.Logger)
        self.view = ProjectsApiView(self.mock_logger)

        # Set up Quart test client and mock dependencies.
        self.app = Quart(__name__)
        self.client = self.app.test_client()

        # Register route for testing
        self.app.add_url_rule('/web/projects/<project_id>',
                              view_func=self.view.retrieve_a_project,
                              methods=['GET'])
        self.app.add_url_rule('/web/projects',
                              view_func=self.view.list_all_projects,
                              methods=['GET'])

    @patch.object(ConfigurationManager, 'get_entry')
    async def test_project_overviews_internal_error(self, mock_get_entry):

        # Mock the response of `_call_api_post`
        mock_call_api_get = AsyncMock()
        mock_call_api_get.return_value = MagicMock(status_code=http.HTTPStatus.INTERNAL_SERVER_ERROR,
                                                   body={"status": True})
        self.view._call_api_get = mock_call_api_get

        async with self.client as client:
            response = await client.get('/web/projects')

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
            response = await client.get('/web/projects')

            # Check response status
            self.assertEqual(response.status_code, http.HTTPStatus.OK)

            # Check response JSON
            data = await response.get_json()
            self.assertEqual(data['projects'][0],
                             {'id': 1, 'name': 'Project Alpha', 'no_of_milestones': 0, 'no_of_test_runs': 0})

    @patch.object(ThreadSafeConfiguration, "apis_cms_svc", "http://localhost/")
    async def test_project_details_success(self):
        mock_call_api_get = AsyncMock()
        mock_call_api_get.return_value = AsyncMock(status_code=http.HTTPStatus.OK, body={"id": 123, "name": "Test Project"})
        self.view._call_api_get = mock_call_api_get

        async with self.client as client:
            response = await client.get('/web/projects/123')

        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        self.assertEqual(await response.get_json(), {"id": 123, "name": "Test Project"})
        mock_call_api_get.assert_called_once_with("http://localhost/projects/details/123")

    @patch.object(ThreadSafeConfiguration, "apis_cms_svc", "http://localhost/")
    async def test_project_details_invalid_project_id(self):
        mock_call_api_get = AsyncMock()
        mock_call_api_get.return_value = AsyncMock(status_code=http.HTTPStatus.BAD_REQUEST)
        self.view._call_api_get = mock_call_api_get

        async with self.client as client:
            response = await client.get('/web/projects/999')

        self.assertEqual(response.status_code, http.HTTPStatus.INTERNAL_SERVER_ERROR)
        self.assertEqual(await response.get_json(), {"status": 0, "error": "Invalid project ID"})
        mock_call_api_get.assert_called_once_with("http://localhost/projects/details/999")

    @patch.object(ThreadSafeConfiguration, "apis_cms_svc", "http://localhost/")
    async def test_project_details_internal_error(self):
        mock_call_api_get = AsyncMock()
        mock_call_api_get.return_value = AsyncMock(status_code=http.HTTPStatus.INTERNAL_SERVER_ERROR, exception_msg="Database Error")
        self.view._call_api_get = mock_call_api_get
        self.view._logger = MagicMock()

        async with self.client as client:
            response = await client.get('/web/projects/456')

        self.assertEqual(response.status_code, http.HTTPStatus.INTERNAL_SERVER_ERROR)
        self.assertEqual(await response.get_json(), {"status": 0, "error": "Internal error!"})
        mock_call_api_get.assert_called_once_with("http://localhost/projects/details/456")
        self.view._logger.critical.assert_called_once_with(
            "CMS SVC /projects/details request invalid - Reason: %s",
            "Database Error"
        )
