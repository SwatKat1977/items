import http
import json
import unittest
from unittest.mock import AsyncMock, patch, MagicMock
import quart
from sqlite_interface import SqliteInterface, SqliteInterfaceException
from apis.testcases_api_view import TestCasesApiView
from base_view import ApiResponse, BaseView, validate_json

app = quart.Quart(__name__)


class TestApiTestCasesApiView(unittest.IsolatedAsyncioTestCase):
    """Unit tests for the TestCasesApiView class."""

    def setUp(self):
        """Set up common test fixtures."""
        self.mock_logger = MagicMock()
        self.mock_db = MagicMock(spec=SqliteInterface)
        self.view = TestCasesApiView(self.mock_logger, self.mock_db)

        self.app = quart.Quart(__name__)
        self.client = self.app.test_client()

        # Register route for testing
        self.app.add_url_rule('/testcases/details', view_func=self.view.testcase_details, methods=['POST'])

    async def test_testcase_details_valid_project(self):
        """Test testcase_details with a valid project ID."""

        # Mock _validate_json_body to return valid data for request
        self.view._validate_json_body = MagicMock(return_value=ApiResponse(
            status_code=http.HTTPStatus.OK,
            body=MagicMock(email_address="test@example.com", password="mysecretpassword")
        ))

        # Mock _call_api_post to simulate a valid API call response
        mock_call_api_post = AsyncMock()
        mock_call_api_post.return_value = MagicMock(status_code=http.HTTPStatus.OK,
                                                    json=AsyncMock(return_value={"status": 1, "token": "mock_token"}))
        self.view._call_api_post = mock_call_api_post

        # Mock your database response (assuming your db call)
        self.mock_db.is_valid_project_id.return_value = True

        self.mock_db.get_testcase_overviews.return_value = \
            [(0, 1, 'Functional Tests', [{'id': 5, 'name': 'Invalid Login Test'}, {'id': 4, 'name': 'Valid Login Test'}])]

        async with self.client as client:
            response = await client.post('/testcases/details',
                                         json={"project_id": 123})

            # Assert response status
            self.assertEqual(response.status_code, http.HTTPStatus.OK)

            # Check response JSON and assert the structure
            data = await response.get_json()
            self.assertEqual(data[0][0], 0, 'Level should be 0')
            self.assertEqual(data[0][1], 1,
                             "Folder ID should be 1")
            self.assertEqual(data[0][2], 'Functional Tests',
                             "Folder name should be 'Functional Tests'")
            self.assertEqual(data[0][3][0], {"id": 5, "name": "Invalid Login Test"},
                             "First test should be 5")
            self.assertEqual(data[0][3][1], {"id": 4, "name": "Valid Login Test"},
                             "Second test should be 4")

    async def test_testcase_details_invalid_project(self):
        """Test testcase_details when an invalid project ID is provided."""

        # Mock _call_api_post to simulate a valid API call response
        mock_call_api_post = AsyncMock()
        mock_call_api_post.return_value = MagicMock(status_code=http.HTTPStatus.OK,
                                                    json=AsyncMock(return_value={"status": 1, "token": "mock_token"}))
        self.view._call_api_post = mock_call_api_post

        self.mock_db.is_valid_project_id.return_value = False

        async with self.client as client:
            response = await client.post('/testcases/details',
                                         json={"project_id": 123})

            # Assert response status
            self.assertEqual(response.status_code, http.HTTPStatus.INTERNAL_SERVER_ERROR)

            data = await response.get_json()
            self.assertEqual(data["status"], 0, 'Status should be 0')
            self.assertEqual(data["error"], "Invalid project id",
                             "Error should be should be 'Invalid project id'")

    async def test_testcase_details_empty_results(self):
        """Test testcase_details when there are no test cases for a valid project."""

        # Mock _validate_json_body to return valid data for request
        self.view._validate_json_body = MagicMock(return_value=ApiResponse(
            status_code=http.HTTPStatus.OK,
            body=MagicMock(email_address="test@example.com", password="mysecretpassword")
        ))

        # Mock _call_api_post to simulate a valid API call response
        mock_call_api_post = AsyncMock()
        mock_call_api_post.return_value = MagicMock(status_code=http.HTTPStatus.OK,
                                                    json=AsyncMock(return_value={"status": 1, "token": "mock_token"}))
        self.view._call_api_post = mock_call_api_post

        # Mock your database response (assuming your db call)
        self.mock_db.is_valid_project_id.return_value = True

        self.mock_db.get_testcase_overviews.return_value = []

        async with self.client as client:
            response = await client.post('/testcases/details',
                                         json={"project_id": 123})

            # Assert response status
            self.assertEqual(response.status_code, http.HTTPStatus.OK)

            # Check response JSON and assert the structure
            data = await response.get_json()
            self.assertEqual(len(data), 0, 'List should be empty')
