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
        self.app.add_url_rule('/project/overviews', view_func=self.view.project_overviews,
                              methods=['GET'])

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
