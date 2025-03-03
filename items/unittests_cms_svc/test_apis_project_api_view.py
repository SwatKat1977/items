import http
import unittest
from unittest.mock import AsyncMock, patch, MagicMock
import quart
from sqlite_interface import SqliteInterface, SqliteInterfaceException
from apis.project_api_view import ProjectApiView


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
