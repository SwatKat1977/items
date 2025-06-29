import http
import json
import unittest
from unittest.mock import AsyncMock, patch, MagicMock
import quart
from apis.web.projects_api_view import ProjectsApiView
from threadsafe_configuration import ThreadSafeConfiguration


class TestApiProjectApiView(unittest.IsolatedAsyncioTestCase):
    """Unit tests for the ProjectApiView class."""

    async def asyncSetUp(self):
        """Set up common test fixtures."""
        self.mock_logger = MagicMock()
        self.mock_state_object = MagicMock()

        self.app = quart.Quart(__name__)

        # Patch configuration
        patcher = patch.object(
            ThreadSafeConfiguration,
            'get_entry',
            return_value=":memory:"
        )
        self.mock_get_entry = patcher.start()
        self.addCleanup(patcher.stop)

        self.client = self.app.test_client()

    @patch('apis.web.projects_api_view.SqlInterface')
    async def test_project_overviews_default(self, mock_sql_interface):
        """Test default behavior when no fields are specified"""

        mock_db = MagicMock()
        mock_db.projects.get_projects_details.return_value = [(1, "Demo Project")]
        mock_sql_interface.return_value = mock_db

        view = ProjectsApiView(self.mock_logger, self.mock_state_object)

        # Register route for testing
        self.app.add_url_rule('/web/projects/overviews',
                              view_func=view.project_overviews,
                              methods=['GET'])

        response = await self.client.get("/web/projects/overviews")
        data = await response.get_json()
        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        self.assertEqual(data["projects"], [{"id": 1, "name": "Demo Project"}])

    @patch('apis.web.projects_api_view.SqlInterface')
    async def test_project_overviews_valid_value_fields(self, mock_sql_interface):
        """Test when valid value_fields are provided"""
        mock_db = MagicMock()
        mock_db.projects.get_projects_details.return_value = [(1, "Test Project")]
        mock_sql_interface.return_value = mock_db

        view = ProjectsApiView(self.mock_logger, self.mock_state_object)

        # Register route for testing
        self.app.add_url_rule('/web/projects/overviews',
                              view_func=view.project_overviews,
                              methods=['GET'])

        response = await self.client.get("/web/projects/overviews?value_fields=name")
        data = await response.get_json()
        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        self.assertEqual(data["projects"], [{"id": 1, "name": "Test Project"}])

    async def test_project_overviews_invalid_value_field(self):
        view = ProjectsApiView(self.mock_logger, self.mock_state_object)

        # Register route for testing
        self.app.add_url_rule('/web/projects/overviews',
                              view_func=view.project_overviews,
                              methods=['GET'])

        """Test when an invalid field is requested"""
        response = await self.client.get("/web/projects/overviews?value_fields=invalid_field")
        data = await response.get_json()
        self.assertEqual(response.status_code, http.HTTPStatus.BAD_REQUEST)
        self.assertEqual(data, {"error": "Invalid value field"})

    async def test_project_overviews_invalid_count_field(self):
        """Test when an invalid field is requested"""

        view = ProjectsApiView(self.mock_logger, self.mock_state_object)

        # Register route for testing
        self.app.add_url_rule('/web/projects/overviews',
                              view_func=view.project_overviews,
                              methods=['GET'])

        response = await self.client.get("/web/projects/overviews?count_fields=invalid_field")
        data = await response.get_json()
        self.assertEqual(response.status_code, http.HTTPStatus.BAD_REQUEST)
        self.assertEqual(data, {"error": "Invalid count field"})

    @patch('apis.web.projects_api_view.SqlInterface')
    async def test_project_overviews_with_milestones(self, mock_sql_interface):
        """Test count_fields including milestones"""
        mock_db = MagicMock()
        mock_db.projects.get_projects_details.return_value = [(1, "Test Project")]
        mock_sql_interface.return_value = mock_db
        mock_db.projects.get_no_of_milestones_for_project.return_value = 5

        view = ProjectsApiView(self.mock_logger, self.mock_state_object)

        # Register route for testing
        self.app.add_url_rule('/web/projects/overviews',
                              view_func=view.project_overviews,
                              methods=['GET'])

        response = await self.client.get("/web/projects/overviews?count_fields=no_of_milestones")
        data = await response.get_json()
        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        self.assertEqual(data["projects"], [{"id": 1, "name": "Test Project", "no_of_milestones": 5}])

    @patch('apis.web.projects_api_view.SqlInterface')
    async def test_project_overviews_get_projects_details_failure(self, mock_sql_interface):
        """Test count_fields including test runs"""
        mock_db = MagicMock()
        mock_db.projects.get_projects_details.return_value = None
        mock_sql_interface.return_value = mock_db
        mock_db.projects.get_no_of_testruns_for_project.return_value = 3

        #  47-48, 51-58, 64-146,
        view = ProjectsApiView(self.mock_logger, self.mock_state_object)

        # Register route for testing
        self.app.add_url_rule('/web/projects/overviews',
                              view_func=view.project_overviews,
                              methods=['GET'])

        response = await self.client.get("/web/projects/overviews?count_fields=no_of_test_runs")
        data = await response.get_json()
        self.assertEqual(response.status_code, http.HTTPStatus.INTERNAL_SERVER_ERROR)
        self.assertEqual(data, {'error': 'Internal error in CMS'})

    @patch('apis.web.projects_api_view.SqlInterface')
    async def test_project_overviews_with_test_runs(self, mock_sql_interface):
        """Test count_fields including test runs"""
        mock_db = MagicMock()
        mock_db.projects.get_projects_details.return_value = [(1, "Test Project")]
        mock_sql_interface.return_value = mock_db
        mock_db.projects.get_no_of_testruns_for_project.return_value = 3

        view = ProjectsApiView(self.mock_logger, self.mock_state_object)

        # Register route for testing
        self.app.add_url_rule('/web/projects/overviews',
                              view_func=view.project_overviews,
                              methods=['GET'])

        response = await self.client.get("/web/projects/overviews?count_fields=no_of_test_runs")
        data = await response.get_json()
        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        self.assertEqual(data["projects"], [{"id": 1, "name": "Test Project", "no_of_test_runs": 3}])

    @patch('apis.web.projects_api_view.SqlInterface')
    async def test_add_project_success(self, mock_sql_interface):
        """Test successful project creation."""
        mock_db = MagicMock()
        mock_db.projects.project_name_exists.return_value = False
        mock_db.projects.add_project.return_value = 42
        mock_sql_interface.return_value = mock_db

        view = ProjectsApiView(self.mock_logger, self.mock_state_object)

        # Register route for testing
        self.app.add_url_rule('/web/projects/add',
                              view_func=view.add_project,
                              methods=['POST'])

        test_json_body: dict = {
            "name": "Project Delta_4",
            "announcement": "hello world!",
            "announcement_on_overview": True
        }

        # Mock _call_api_post to simulate a valid API call response
        mock_call_api_post = AsyncMock()
        mock_call_api_post.return_value = MagicMock(
            status_code=http.HTTPStatus.OK,
            json=AsyncMock(return_value={"status": 1, "token": "mock_token"}))
        view._call_api_post = mock_call_api_post

        async with self.client as client:
            response = await client.post('/web/projects/add',
                                         json=test_json_body)
            data = await response.get_json()
            # Assert response status
            self.assertEqual(response.status_code, http.HTTPStatus.OK)
            self.assertEqual(data, {"project_id": 42})

    @patch('apis.web.projects_api_view.SqlInterface')
    async def test_add_project_name_exists(self, mock_sql_interface):
        """Test when the project name already exists."""
        mock_db = MagicMock()
        mock_db.projects.project_name_exists.return_value = True
        mock_sql_interface.return_value = mock_db

        view = ProjectsApiView(self.mock_logger, self.mock_state_object)

        # Register route for testing
        self.app.add_url_rule('/web/projects/add',
                              view_func=view.add_project,
                              methods=['POST'])

        test_json_body: dict = {
            "name": "Project Delta_4",
            "announcement": "hello world!",
            "announcement_on_overview": True
        }

        async with self.client as client:
            response = await client.post('/web/projects/add',
                                         json=test_json_body)

            # Assert response status
            self.assertEqual(response.status_code, http.HTTPStatus.BAD_REQUEST)
            self.assertEqual(json.loads(await response.get_data()),
                             {'error_msg': 'Project name already exists', 'status': 0})

    @patch('apis.web.projects_api_view.SqlInterface')
    async def test_add_project_query_failure_checking_name(self, mock_sql_interface):
        """Test database query failure while checking if project name exists."""
        mock_db = MagicMock()
        mock_db.projects.project_name_exists.return_value = None
        mock_sql_interface.return_value = mock_db

        view = ProjectsApiView(self.mock_logger, self.mock_state_object)

        # Register route for testing
        self.app.add_url_rule('/web/projects/add',
                              view_func=view.add_project,
                              methods=['POST'])

        test_json_body: dict = {
            "name": "Project Delta_4",
            "announcement": "hello world!",
            "announcement_on_overview": True
        }
        async with self.client as client:
            response = await client.post('/web/projects/add',
                                         json=test_json_body)

            # Assert response status
            self.assertEqual(response.status_code, http.HTTPStatus.INTERNAL_SERVER_ERROR)
            self.assertEqual(json.loads(await response.get_data()),
                             {'error_msg': 'Internal error in CMS', 'status': 0})

    @patch('apis.web.projects_api_view.SqlInterface')
    async def test_add_project_query_failure_adding_project(self, mock_sql_interface):
        """Test database query failure when inserting a new project."""
        mock_db = MagicMock()
        mock_db.projects.project_name_exists.return_value = False
        mock_db.projects.add_project.return_value = None
        mock_sql_interface.return_value = mock_db

        view = ProjectsApiView(self.mock_logger, self.mock_state_object)

        # Register route for testing
        self.app.add_url_rule('/web/projects/add',
                              view_func=view.add_project,
                              methods=['POST'])

        test_json_body: dict = {
            "name": "Project Delta_4",
            "announcement": "hello world!",
            "announcement_on_overview": True
        }

        # Mock _call_api_post to simulate a valid API call response
        mock_call_api_post = AsyncMock()
        mock_call_api_post.return_value = MagicMock(
            status_code=http.HTTPStatus.BAD_REQUEST,
            json=AsyncMock(return_value={"status": 0, "error_msg": "Project name already exists"}))
        view._call_api_post = mock_call_api_post

        async with self.client as client:
            response = await client.post('/web/projects/add',
                                         json=test_json_body)

            # Assert response status
            self.assertEqual(response.status_code, http.HTTPStatus.INTERNAL_SERVER_ERROR)
            self.assertEqual(json.loads(await response.get_data()),
                             {'error_msg': 'Internal SQL error in CMS', 'status': 0})

    @patch('apis.web.projects_api_view.SqlInterface')
    async def test_delete_project_default_soft_delete(self, mock_sql_interface):
        """Test default case when 'hard_delete' param is missing (soft delete)."""
        mock_db = MagicMock()
        mock_db.projects.is_valid_project_id.return_value = True
        mock_sql_interface.return_value = mock_db

        view = ProjectsApiView(self.mock_logger, self.mock_state_object)

        self.app.add_url_rule('/web/projects/delete/<int:project_id>',
                              view_func=view.delete_project,
                              methods=['DELETE'])

        async with self.client as client:
            response = await client.delete("/web/projects/delete/1")
            self.assertEqual(response.status_code, http.HTTPStatus.OK)
            self.assertEqual(json.loads(await response.get_data()), {})
            mock_db.projects.is_valid_project_id.assert_called_once_with(1)
            mock_db.projects.mark_project_for_awaiting_purge.assert_called_once_with(1)
            mock_db.projects.hard_delete_project.assert_not_called()

    @patch('apis.web.projects_api_view.SqlInterface')
    async def test_delete_project_soft_delete_mark_project_for_awaiting_purge_fails(self, mock_sql_interface):
        """Test default case when 'hard_delete' param is missing (soft delete)."""
        mock_db = MagicMock()
        mock_db.projects.is_valid_project_id.return_value = True
        mock_db.projects.mark_project_for_awaiting_purge.return_value = None
        mock_sql_interface.return_value = mock_db

        view = ProjectsApiView(self.mock_logger, self.mock_state_object)

        self.app.add_url_rule('/web/projects/delete/<int:project_id>',
                              view_func=view.delete_project,
                              methods=['DELETE'])

        async with self.client as client:
            response = await client.delete("/web/projects/delete/1")
            self.assertEqual(response.status_code, http.HTTPStatus.INTERNAL_SERVER_ERROR)
            self.assertEqual(json.loads(await response.get_data()),
                             {'error_msg': 'Internal error in CMS', 'status': 0})
            mock_db.projects.is_valid_project_id.assert_called_once_with(1)
            mock_db.projects.mark_project_for_awaiting_purge.assert_called_once_with(1)
            mock_db.projects.hard_delete_project.assert_not_called()

    @patch('apis.web.projects_api_view.SqlInterface')
    async def test_delete_project_hard_delete_hard_delete_sql_error(self, mock_sql_interface):
        """Test when 'hard_delete' param is set to 'true' (hard delete)."""
        mock_db = MagicMock()
        mock_db.projects.is_valid_project_id.return_value = True
        mock_db.projects.hard_delete_project.return_value = None

        mock_sql_interface.return_value = mock_db

        view = ProjectsApiView(self.mock_logger, self.mock_state_object)

        self.app.add_url_rule('/web/projects/delete/<int:project_id>',
                              view_func=view.delete_project,
                              methods=['DELETE'])

        async with self.client as client:
            response = await client.delete("/web/projects/delete/1?hard_delete=true")

            mock_db.projects.is_valid_project_id.assert_called_once_with(1)
            mock_db.projects.hard_delete_project.assert_called_once_with(1)
            mock_db.projects.mark_project_for_awaiting_purge.assert_not_called()
            self.assertEqual(response.status_code, http.HTTPStatus.INTERNAL_SERVER_ERROR)

    @patch('apis.web.projects_api_view.SqlInterface')
    async def test_delete_project_hard_delete(self, mock_sql_interface):
        """Test when 'hard_delete' param is set to 'true' (hard delete)."""
        mock_db = MagicMock()
        mock_db.projects.is_valid_project_id.return_value = True
        mock_sql_interface.return_value = mock_db

        view = ProjectsApiView(self.mock_logger, self.mock_state_object)

        self.app.add_url_rule('/web/projects/delete/<int:project_id>',
                              view_func=view.delete_project,
                              methods=['DELETE'])

        async with self.client as client:
            response = await client.delete("/web/projects/delete/1?hard_delete=true")

            mock_db.projects.is_valid_project_id.assert_called_once_with(1)
            mock_db.projects.hard_delete_project.assert_called_once_with(1)
            mock_db.projects.mark_project_for_awaiting_purge.assert_not_called()
            self.assertEqual(response.status_code, http.HTTPStatus.OK)

    async def test_delete_project_invalid_hard_delete_param(self):
        """Test when 'hard_delete' param is invalid."""
        view = ProjectsApiView(self.mock_logger, self.mock_state_object)

        self.app.add_url_rule('/web/projects/delete/<int:project_id>',
                              view_func=view.delete_project,
                              methods=['DELETE'])

        async with self.client as client:
            response = await client.delete("/web/projects/delete/1?hard_delete=invalid")
            response_data = await response.get_json()

        self.assertEqual(response.status_code, http.HTTPStatus.INTERNAL_SERVER_ERROR)
        self.assertEqual(response_data["status"], 0)
        self.assertEqual(response_data["error_msg"],
                         "Invalid parameter for hard_delete argument")

    @patch('apis.web.projects_api_view.SqlInterface')
    async def test_delete_project_db_error(self, mock_sql_interface):
        """Test when project_id_exists returns None (database failure)."""
        mock_db = MagicMock()
        mock_db.projects.is_valid_project_id.return_value = None
        mock_sql_interface.return_value = mock_db

        view = ProjectsApiView(self.mock_logger, self.mock_state_object)

        self.app.add_url_rule('/web/projects/delete/<int:project_id>',
                              view_func=view.delete_project,
                              methods=['DELETE'])

        async with self.client as client:
            response = await client.delete("/web/projects/delete/1")
            response_data = await response.get_json()

        mock_db.projects.is_valid_project_id.assert_called_once_with(1)
        self.assertEqual(response.status_code, http.HTTPStatus.INTERNAL_SERVER_ERROR)
        self.assertEqual(response_data["error_msg"], "Internal error in CMS")

    @patch('apis.web.projects_api_view.SqlInterface')
    async def test_delete_project_id_not_found(self, mock_sql_interface):
        """Test when project_id_exists returns False (invalid project)."""
        mock_db = MagicMock()
        mock_db.projects.is_valid_project_id.return_value = False
        mock_sql_interface.return_value = mock_db

        view = ProjectsApiView(self.mock_logger, self.mock_state_object)

        self.app.add_url_rule('/web/projects/delete/<int:project_id>',
                              view_func=view.delete_project,
                              methods=['DELETE'])

        async with self.client as client:
            response = await client.delete("/web/projects/delete/1")
            response_data = await response.get_json()

        mock_db.projects.is_valid_project_id.assert_called_once_with(1)
        self.assertEqual(response.status_code, http.HTTPStatus.BAD_REQUEST)
        self.assertEqual(response_data["error_msg"], "Project id is invalid")

    @patch('apis.web.projects_api_view.SqlInterface')
    async def test_delete_project_soft_delete(self, mock_sql_interface):
        """Test when 'hard_delete' param is set to 'false' (soft delete)."""
        mock_db = MagicMock()
        mock_db.projects.is_valid_project_id.return_value = True
        mock_sql_interface.return_value = mock_db

        view = ProjectsApiView(self.mock_logger, self.mock_state_object)

        self.app.add_url_rule('/web/projects/delete/<int:project_id>',
                              view_func=view.delete_project,
                              methods=['DELETE'])

        async with self.client as client:
            response = await client.delete("/web/projects/delete/1?hard_delete=false")

        mock_db.projects.is_valid_project_id.assert_called_once_with(1)
        mock_db.projects.mark_project_for_awaiting_purge.assert_called_once_with(1)
        mock_db.projects.hard_delete_project.assert_not_called()
        self.assertEqual(response.status_code, http.HTTPStatus.OK)

    @patch('apis.web.projects_api_view.SqlInterface')
    async def test_project_details_has_details(self, mock_sql_interface):
        mock_db = MagicMock()

        returned_response_body: dict = {
            "id": 2,
            "name": "Project Delta",
            "announcement": "Delta test 1234567890",
            "show_announcement_on_overview": 1
        }
        mock_db.projects.get_project_details.return_value = returned_response_body

        mock_sql_interface.return_value = mock_db

        view = ProjectsApiView(self.mock_logger, self.mock_state_object)

        self.app.add_url_rule('/web/projects/details/<project_id>',
                              view_func=view.project_details,
                              methods=['GET'])

        async with self.client as client:
            response = await client.get("/web/projects/details/1")
            self.assertEqual(response.status_code, http.HTTPStatus.OK)
            self.assertEqual(await response.get_json(), returned_response_body)

    @patch('apis.web.projects_api_view.SqlInterface')
    async def test_project_details_sql_error(self, mock_sql_interface):
        mock_db = MagicMock()
        mock_db.projects.get_project_details.return_value = None
        mock_sql_interface.return_value = mock_db

        view = ProjectsApiView(self.mock_logger, self.mock_state_object)

        self.app.add_url_rule('/web/projects/details/<project_id>',
                              view_func=view.project_details,
                              methods=['GET'])

        async with self.client as client:
            response = await client.get("/web/projects/details/1")
            self.assertEqual(response.status_code, http.HTTPStatus.BAD_REQUEST)
            self.assertEqual(await response.get_json(), {})

    @patch('apis.web.projects_api_view.SqlInterface')
    async def test_project_details_no_details(self, mock_sql_interface):
        mock_db = MagicMock()
        mock_db.projects.get_project_details.return_value = {}
        mock_sql_interface.return_value = mock_db

        view = ProjectsApiView(self.mock_logger, self.mock_state_object)

        self.app.add_url_rule('/web/projects/details/<project_id>',
                              view_func=view.project_details,
                              methods=['GET'])

        async with self.client as client:
            response = await client.get("/web/projects/details/1")
            self.assertEqual(response.status_code, http.HTTPStatus.OK)
            self.assertEqual(await response.get_json(), {})

    @patch('apis.web.projects_api_view.SqlInterface')
    async def test_modify_project_success(self, mock_sql_interface):
        mock_db = MagicMock()
        mock_db.projects.get_project_details.return_value = {
            "name": "Old Project",
            "announcement": "Old Announcement",
            "announcement_on_overview": False
        }
        mock_db.projects.project_name_exists.return_value = False
        mock_db.projects.modify_project.return_value = True
        mock_sql_interface.return_value = mock_db

        view = ProjectsApiView(self.mock_logger, self.mock_state_object)

        self.app.add_url_rule('/web/projects/modify/<project_id>',
                              view_func=view.modify_project,
                              methods=['POST'])

        request_data = {
            "name": "New Project",
            "announcement": "New Announcement",
            "announcement_on_overview": True
        }
        async with self.client as client:
            response = await client.post("/web/projects/modify/1",
                                         json=request_data)

        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        self.assertEqual(await response.get_json(), {"status": 1})

    @patch('apis.web.projects_api_view.SqlInterface')
    async def test_modify_project_internal_error_on_fetch(self, mock_sql_interface):
        mock_db = MagicMock()
        mock_db.projects.get_project_details.return_value = None
        mock_sql_interface.return_value = mock_db

        view = ProjectsApiView(self.mock_logger, self.mock_state_object)

        self.app.add_url_rule('/web/projects/modify/<project_id>',
                              view_func=view.modify_project,
                              methods=['POST'])

        request_data = {
            "name": "Failed Project",
            "announcement": "New Announcement",
            "announcement_on_overview": True
        }
        async with self.client as client:
            response = await client.post("/web/projects/modify/1",
                                         json=request_data)

        self.assertEqual(response.status_code, http.HTTPStatus.INTERNAL_SERVER_ERROR)
        self.assertEqual(await response.get_json(),
                         {"status": 0, "error_msg": "Internal error : Cannot get project details"})

    @patch('apis.web.projects_api_view.SqlInterface')
    async def test_modify_project_invalid_project_id_on_fetch(self, mock_sql_interface):
        mock_db = MagicMock()
        mock_db.projects.get_project_details.return_value = {}
        mock_sql_interface.return_value = mock_db

        view = ProjectsApiView(self.mock_logger, self.mock_state_object)

        self.app.add_url_rule('/web/projects/modify/<project_id>',
                              view_func=view.modify_project,
                              methods=['POST'])

        request_data = {
            "name": "Failed Project",
            "announcement": "New Announcement",
            "announcement_on_overview": True
        }
        async with self.client as client:
            response = await client.post("/web/projects/modify/1",
                                         json=request_data)

        self.assertEqual(response.status_code, http.HTTPStatus.BAD_REQUEST)
        self.assertEqual(await response.get_json(),
                         {"status": 0, "error_msg": "Invalid project ID"})

    @patch('apis.web.projects_api_view.SqlInterface')
    async def test_modify_project_name_conflict(self, mock_sql_interface):
        mock_db = MagicMock()
        mock_db.projects.get_project_details.return_value = {"name": "Old Project"}
        mock_db.projects.project_name_exists.return_value = True
        mock_sql_interface.return_value = mock_db

        view = ProjectsApiView(self.mock_logger, self.mock_state_object)

        self.app.add_url_rule('/web/projects/modify/<project_id>',
                              view_func=view.modify_project,
                              methods=['POST'])

        request_data = {
            "name": "New Project",
            "announcement": "New Announcement",
            "announcement_on_overview": True
        }

        async with self.client as client:
            response = await client.post("/web/projects/modify/1",
                                         json=request_data)

        self.assertEqual(response.status_code, http.HTTPStatus.BAD_REQUEST)
        self.assertEqual(json.loads(await response.get_data()),
                         {"status": 0, "error_msg": "New project name already exists"})

    @patch('apis.web.projects_api_view.SqlInterface')
    async def test_modify_project_internal_error_on_name_check(self, mock_sql_interface):
        mock_db = MagicMock()
        mock_db.projects.get_project_details.return_value = {"name": "Old Project"}
        mock_db.projects.project_name_exists.return_value = None
        mock_sql_interface.return_value = mock_db

        view = ProjectsApiView(self.mock_logger, self.mock_state_object)

        self.app.add_url_rule('/web/projects/modify/<project_id>',
                              view_func=view.modify_project,
                              methods=['POST'])

        request_data = {
            "name": "New Project",
            "announcement": "New Announcement",
            "announcement_on_overview": True
        }

        async with self.client as client:
            response = await client.post("/web/projects/modify/1",
                                         json=request_data)

        self.assertEqual(response.status_code, http.HTTPStatus.INTERNAL_SERVER_ERROR)
        self.assertEqual(await response.get_json(),
                         {"status": 0, "error_msg": "Internal error : Cannot check project name"})
