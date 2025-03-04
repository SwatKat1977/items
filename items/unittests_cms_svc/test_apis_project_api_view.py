import http
import json
import unittest
from unittest.mock import AsyncMock, patch, MagicMock
import quart
from sqlite_interface import SqliteInterface, SqliteInterfaceException
from apis.project_api_view import ProjectApiView
from base_view import ApiResponse


class TestApiProjectApiView(unittest.IsolatedAsyncioTestCase):
    """Unit tests for the ProjectApiView class."""

    async def asyncSetUp(self):
        """Set up common test fixtures."""
        self.mock_logger = MagicMock()
        self.mock_db = MagicMock(spec=SqliteInterface)
        self.view = ProjectApiView(self.mock_logger, self.mock_db)

        self.app = quart.Quart(__name__)
        self.client = self.app.test_client()

        # Register route for testing
        self.app.add_url_rule('/project/overviews',
                              view_func=self.view.project_overviews,
                              methods=['GET'])

        self.app.add_url_rule('/project/add',
                              view_func=self.view.add_project,
                              methods=['POST'])

    async def test_project_overviews_default(self):
        """Test default behavior when no fields are specified"""
        self.mock_db.get_projects_details.return_value = [(1, "Demo Project")]
        response = await self.client.get("/project/overviews")
        data = await response.get_json()
        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        self.assertEqual(data["projects"], [{"id": 1, "name": "Demo Project"}])

    async def test_project_overviews_valid_value_fields(self):
        """Test when valid value_fields are provided"""
        self.mock_db.get_projects_details.return_value = [(1, "Test Project")]
        response = await self.client.get("/project/overviews?value_fields=name")
        data = await response.get_json()
        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        self.assertEqual(data["projects"], [{"id": 1, "name": "Test Project"}])

    async def test_project_overviews_invalid_value_field(self):
        """Test when an invalid field is requested"""
        response = await self.client.get("/project/overviews?value_fields=invalid_field")
        data = await response.get_json()
        self.assertEqual(response.status_code, http.HTTPStatus.BAD_REQUEST)
        self.assertEqual(data, {"error": "Invalid value field"})

    async def test_project_overviews_invalid_count_field(self):
        """Test when an invalid field is requested"""
        response = await self.client.get("/project/overviews?count_fields=invalid_field")
        data = await response.get_json()
        self.assertEqual(response.status_code, http.HTTPStatus.BAD_REQUEST)
        self.assertEqual(data, {"error": "Invalid count field"})

    async def test_project_overviews_with_milestones(self):
        """Test count_fields including milestones"""
        self.mock_db.get_projects_details.return_value = [(1, "Test Project")]
        self.mock_db.get_no_of_milestones_for_project.return_value = 5
        response = await self.client.get("/project/overviews?count_fields=no_of_milestones")
        data = await response.get_json()
        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        self.assertEqual(data["projects"], [{"id": 1, "name": "Test Project", "no_of_milestones": 5}])

    async def test_project_overviews_with_test_runs(self):
        """Test count_fields including test runs"""
        self.mock_db.get_projects_details.return_value = [(1, "Test Project")]
        self.mock_db.get_no_of_testruns_for_project.return_value = 3
        response = await self.client.get("/project/overviews?count_fields=no_of_test_runs")
        data = await response.get_json()
        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        self.assertEqual(data["projects"], [{"id": 1, "name": "Test Project", "no_of_test_runs": 3}])

    async def test_add_project_success(self):
        """Test successful project creation."""
        self.mock_db.project_name_exists = MagicMock(return_value=False)
        self.mock_db.add_project = MagicMock(return_value=42)

        # Mock _call_api_post to simulate a valid API call response
        mock_call_api_post = AsyncMock()
        mock_call_api_post.return_value = MagicMock(
            status_code=http.HTTPStatus.OK,
            json=AsyncMock(return_value={"status": 1, "token": "mock_token"}))
        self.view._call_api_post = mock_call_api_post

        self.mock_db.project_name_exists.return_value = False

        async with self.client as client:
            response = await client.post('/project/add',
                                         json={"name": "123"})

            # Assert response status
            self.assertEqual(response.status_code, http.HTTPStatus.OK)
            self.assertEqual(json.loads(await response.get_data()),
                             {"project_id": 42})

    async def test_add_project_name_exists(self):
        """Test when the project name already exists."""
        self.mock_db.project_name_exists = MagicMock(return_value=True)

        # Mock _call_api_post to simulate a valid API call response
        mock_call_api_post = AsyncMock()
        mock_call_api_post.return_value = MagicMock(
            status_code=http.HTTPStatus.BAD_REQUEST,
            json=AsyncMock(return_value={"status": 0, "error_msg": "Project name already exists"}))
        self.view._call_api_post = mock_call_api_post

        async with self.client as client:
            response = await client.post('/project/add',
                                         json={"name": "123"})

            # Assert response status
            self.assertEqual(response.status_code, http.HTTPStatus.BAD_REQUEST)
            self.assertEqual(json.loads(await response.get_data()),
                             {'error_msg': 'Project name already exists', 'status': 0})

    async def test_add_project_query_failure_checking_name(self):
        """Test database query failure while checking if project name exists."""
        self.mock_db.project_name_exists = MagicMock(return_value=None)

        async with self.client as client:
            response = await client.post('/project/add',
                                         json={"name": "123"})

            # Assert response status
            self.assertEqual(response.status_code, http.HTTPStatus.INTERNAL_SERVER_ERROR)
            self.assertEqual(json.loads(await response.get_data()),
                             {'error_msg': 'Internal error in CMS', 'status': 0})

    async def test_add_project_query_failure_adding_project(self):
        """Test database query failure when inserting a new project."""
        self.mock_db.project_name_exists = MagicMock(return_value=False)
        self.mock_db.add_project = MagicMock(return_value=None)

        # Mock _call_api_post to simulate a valid API call response
        mock_call_api_post = AsyncMock()
        mock_call_api_post.return_value = MagicMock(
            status_code=http.HTTPStatus.BAD_REQUEST,
            json=AsyncMock(return_value={"status": 0, "error_msg": "Project name already exists"}))
        self.view._call_api_post = mock_call_api_post

        async with self.client as client:
            response = await client.post('/project/add',
                                         json={"name": "123"})

            # Assert response status
            self.assertEqual(response.status_code, http.HTTPStatus.INTERNAL_SERVER_ERROR)
            self.assertEqual(json.loads(await response.get_data()),
                             {'error_msg': 'Internal SQL error in CMS', 'status': 0})
