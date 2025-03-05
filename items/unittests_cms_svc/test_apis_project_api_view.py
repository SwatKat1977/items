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

        self.app.add_url_rule('/project/delete/<int:project_id>',
                              view_func=self.view.delete_project,
                              methods=['DELETE'])

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

    async def test_delete_project_default_soft_delete(self):
        """Test default case when 'hard_delete' param is missing (soft delete)."""
        self.mock_db.project_id_exists.return_value = True

        async with self.client as client:
            response = await client.delete("/project/delete/1")

            self.mock_db.project_id_exists.assert_called_once_with(1)
            self.mock_db.mark_project_for_awaiting_purge.assert_called_once_with(1)
            self.mock_db.hard_delete_project.assert_not_called()
            self.assertEqual(response.status_code, http.HTTPStatus.OK)

    async def test_delete_project_hard_delete(self):
        """Test when 'hard_delete' param is set to 'true' (hard delete)."""
        self.mock_db.project_id_exists.return_value = True

        async with self.client as client:
            response = await client.delete("/project/delete/1?hard_delete=true")

            self.mock_db.project_id_exists.assert_called_once_with(1)
            self.mock_db.hard_delete_project.assert_called_once_with(1)
            self.mock_db.mark_project_for_awaiting_purge.assert_not_called()
            self.assertEqual(response.status_code, http.HTTPStatus.OK)

    async def test_delete_project_invalid_hard_delete_param(self):
        """Test when 'hard_delete' param is invalid."""

        async with self.client as client:
            response = await client.delete("/project/delete/1?hard_delete=invalid")
            response_data = await response.get_json()

        self.assertEqual(response.status_code, http.HTTPStatus.INTERNAL_SERVER_ERROR)
        self.assertEqual(response_data["status"], 0)
        self.assertEqual(response_data["error_msg"],
                         "Invalid parameter for hard_delete argument")

    async def test_delete_project_db_error(self):
        """Test when project_id_exists returns None (database failure)."""
        self.mock_db.project_id_exists.return_value = None

        async with self.client as client:
            response = await client.delete("/project/delete/1")
            response_data = await response.get_json()

        self.mock_db.project_id_exists.assert_called_once_with(1)
        self.assertEqual(response.status_code, http.HTTPStatus.INTERNAL_SERVER_ERROR)
        self.assertEqual(response_data["error_msg"], "Internal error in CMS")

    async def test_delete_project_id_not_found(self):
        """Test when project_id_exists returns False (invalid project)."""
        self.mock_db.project_id_exists.return_value = False

        async with self.client as client:
            response = await client.delete("/project/delete/1")
            response_data = await response.get_json()

        self.mock_db.project_id_exists.assert_called_once_with(1)
        self.assertEqual(response.status_code, http.HTTPStatus.BAD_REQUEST)
        self.assertEqual(response_data["error_msg"], "Project id is invalid")

    async def test_delete_project_soft_delete(self):
        """Test when 'hard_delete' param is set to 'false' (soft delete)."""
        self.mock_db.project_id_exists.return_value = True

        async with self.client as client:
            response = await client.delete("/project/delete/1?hard_delete=false")

        self.mock_db.project_id_exists.assert_called_once_with(1)
        self.mock_db.mark_project_for_awaiting_purge.assert_called_once_with(1)
        self.mock_db.hard_delete_project.assert_not_called()
        self.assertEqual(response.status_code, http.HTTPStatus.OK)
