import http
import unittest
from unittest.mock import AsyncMock, MagicMock, patch
from quart import Quart
from apis.projects_api_view import ProjectsApiView
from configuration.configuration_manager import ConfigurationManager
from metadata_settings import MetadataSettings


class TestApisProjectsApiView(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.app = Quart(__name__)
        self.logger = MagicMock()
        self.metadata = MetadataSettings()
        self.view = ProjectsApiView(self.logger,
                                    self.metadata)

        # Set up Quart test client and mock dependencies.
        self.client = self.app.test_client()

        # Register route for testing
        self.app.add_url_rule('/<project_id>/test_cases',
                              view_func=self.view.test_cases,
                              methods=['POST'])

    @patch.object(ConfigurationManager, 'get_entry')
    async def test_test_cases_invalid_gateway_response(self, mock_get_entry):

        # Mock the response of `_call_api_post`
        mock_call_api_post = AsyncMock()
        mock_call_api_post.return_value = MagicMock(
            status_code=http.HTTPStatus.INTERNAL_SERVER_ERROR,
            body={"status": 0, "error": "Test internal error"})
        self.view._call_api_post = mock_call_api_post

        async with self.client as client:
            response = await client.post('/1/test_cases')

            # Check response status
            self.assertEqual(response.status_code,
                             http.HTTPStatus.INTERNAL_SERVER_ERROR)

    @patch.object(ConfigurationManager, 'get_entry')
    async def test_test_cases_success(self, mock_get_entry):

        self.view._render_page = AsyncMock(return_value="Mock Page")

        response_body = {
            'folders': [
                {'id': 1, 'name': 'Level 0 Folder #1', "parent_id": None},
                {'id': 2, 'name': 'Level 0 Folder #2', "parent_id": None},
                {'id': 3, 'name': 'Level 0 Folder #2-1', "parent_id": 2},
                {'id': 4, 'name': 'Level 0 Folder #2-1', "parent_id": 3}
            ],
            'test_cases': []
        }

        # Mock the response of `_call_api_post`
        mock_call_api_post = AsyncMock()
        mock_call_api_post.return_value = MagicMock(
            status_code=http.HTTPStatus.OK,
            body=response_body)
        self.view._call_api_post = mock_call_api_post

        async with self.client as client:
            response = await client.post('/1/test_cases')

            # Check response status
            self.assertEqual(response.status_code,
                             http.HTTPStatus.OK)

    def test_transform_empty_data(self):
        """Test with empty input data."""
        data = {"folders": [], "test_cases": []}
        result = self.view._transform_tests_details_data(data)
        self.assertEqual(result, [])

    def test_transform_single_folder_no_tests(self):
        """Test with a single root folder and no test cases."""
        data = {
            "folders": [{"id": 1, "name": "Root Folder", "parent_id": None}],
            "test_cases": [],
        }
        result = self.view._transform_tests_details_data(data)
        expected = [{"id": 1, "name": "Root Folder", "parent_id": None, "subfolders": [], "test_cases": []}]
        self.assertEqual(result, expected)

    def test_transform_nested_folders(self):
        """Test with nested folders but no test cases."""
        data = {
            "folders": [
                {"id": 1, "name": "Root", "parent_id": None},
                {"id": 2, "name": "Child", "parent_id": 1},
                {"id": 3, "name": "Subchild", "parent_id": 2},
            ],
            "test_cases": [],
        }
        result = self.view._transform_tests_details_data(data)
        expected = [
            {
                "id": 1,
                "name": "Root",
                "parent_id": None,
                "subfolders": [
                    {
                        "id": 2,
                        "name": "Child",
                        "parent_id": 1,
                        "subfolders": [
                            {
                                "id": 3,
                                "name": "Subchild",
                                "parent_id": 2,
                                "subfolders": [],
                                "test_cases": [],
                            }
                        ],
                        "test_cases": [],
                    }
                ],
                "test_cases": [],
            }
        ]
        self.assertEqual(result, expected)

    def test_transform_folders_with_test_cases(self):
        """Test folders with associated test cases."""
        data = {
            "folders": [{"id": 1, "name": "Root", "parent_id": None}],
            "test_cases": [
                {"id": 101, "name": "Test A", "folder_id": 1},
                {"id": 102, "name": "Test B", "folder_id": 1},
            ],
        }
        result = self.view._transform_tests_details_data(data)
        expected = [
            {
                "id": 1,
                "name": "Root",
                "parent_id": None,
                "subfolders": [],
                "test_cases": [
                    {"id": 101, "name": "Test A", "folder_id": 1},
                    {"id": 102, "name": "Test B", "folder_id": 1},
                ],
            }
        ]
        self.assertEqual(result, expected)

    def test_transform_mixed_structure(self):
        """Test a complex structure with multiple folders and test cases."""
        data = {
            "folders": [
                {"id": 1, "name": "Root", "parent_id": None},
                {"id": 2, "name": "Child", "parent_id": 1},
            ],
            "test_cases": [
                {"id": 101, "name": "Test A", "folder_id": 1},
                {"id": 102, "name": "Test B", "folder_id": 2},
            ],
        }
        result = self.view._transform_tests_details_data(data)
        expected = [
            {
                "id": 1,
                "name": "Root",
                "parent_id": None,
                "subfolders": [
                    {
                        "id": 2,
                        "name": "Child",
                        "parent_id": 1,
                        "subfolders": [],
                        "test_cases": [
                            {"id": 102, "name": "Test B", "folder_id": 2}
                        ],
                    }
                ],
                "test_cases": [
                    {"id": 101, "name": "Test A", "folder_id": 1}
                ],
            }
        ]
        self.assertEqual(result, expected)

    def test_transform_handles_missing_parent_folder(self):
        """Test where a test case references a missing folder."""
        data = {
            "folders": [{"id": 1, "name": "Root", "parent_id": None}],
            "test_cases": [{"id": 101, "name": "Test A", "folder_id": 999}],  # Invalid folder_id
        }
        result = self.view._transform_tests_details_data(data)
        expected = [
            {
                "id": 1,
                "name": "Root",
                "parent_id": None,
                "subfolders": [],
                "test_cases": [],
            }
        ]
        self.assertEqual(result, expected)
