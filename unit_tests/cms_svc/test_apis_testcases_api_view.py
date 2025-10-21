import http
import unittest
from unittest.mock import AsyncMock, MagicMock, patch
import quart
from apis.testcases_api_view import TestCasesApiView
from threadsafe_configuration import ThreadSafeConfiguration

app = quart.Quart(__name__)


class TestApiTestCasesApiView(unittest.IsolatedAsyncioTestCase):
    """Unit tests for the TestCasesApiView class."""

    def setUp(self):
        """Set up common test fixtures."""
        self.app = quart.Quart(__name__)
        self.mock_logger = MagicMock()
        self.mock_state_object = MagicMock()

        # Patch configuration
        patcher = patch.object(
            ThreadSafeConfiguration,
            'get_entry',
            return_value=":memory:"
        )
        self.mock_get_entry = patcher.start()
        self.addCleanup(patcher.stop)

        self.client = self.app.test_client()

    @patch('apis.testcases_api_view.SqlInterface')
    async def test_testcase_details_valid_project(self, mock_sql_interface):
        """Test testcase_details with a valid project ID."""
        mock_db = MagicMock()
        mock_sql_interface.return_value = mock_db
        mock_db.projects.is_valid_project_id.return_value = True
        mock_db.testcases.get_testcase_overviews.return_value = [
            (0, 1, 'Functional Tests', [
                {"id": 5, "name": "Invalid Login Test"},
                {"id": 4, "name": "Valid Login Test"}
            ])
        ]

        view = TestCasesApiView(self.mock_logger, self.mock_state_object)

        # Register route for testing
        self.app.add_url_rule('/web/testcases/details', view_func=view.testcase_details, methods=['POST'])

        async with self.client as client:
            response = await client.post('/web/testcases/details', json={"project_id": 123})

            # Assert successful response
            self.assertEqual(response.status_code, http.HTTPStatus.OK)

            # Validate structure of returned JSON
            data = await response.get_json()
            self.assertEqual(data[0][0], 0, 'Level should be 0')
            self.assertEqual(data[0][1], 1, "Folder ID should be 1")
            self.assertEqual(data[0][2], 'Functional Tests', "Folder name should be 'Functional Tests'")
            self.assertEqual(data[0][3][0], {"id": 5, "name": "Invalid Login Test"}, "First test should be 5")
            self.assertEqual(data[0][3][1], {"id": 4, "name": "Valid Login Test"}, "Second test should be 4")

    @patch('apis.testcases_api_view.SqlInterface')
    async def test_testcase_details_invalid_project(self, mock_sql_interface):
        """Test testcase_details when an invalid project ID is provided."""
        mock_db = MagicMock()
        mock_sql_interface.return_value = mock_db
        mock_db.projects.is_valid_project_id.return_value = False

        view = TestCasesApiView(self.mock_logger, self.mock_state_object)

        # Register route for testing
        self.app.add_url_rule('/web/testcases/details', view_func=view.testcase_details, methods=['POST'])

        # Mock _call_api_post to simulate a valid API call response
        mock_call_api_post = AsyncMock()
        mock_call_api_post.return_value = MagicMock(status_code=http.HTTPStatus.OK,
                                                    json=AsyncMock(return_value={"status": 1, "token": "mock_token"}))
        view._call_api_post = mock_call_api_post

        # self.mock_db.is_valid_project_id.return_value = False

        async with self.client as client:
            response = await client.post('/web/testcases/details',
                                         json={"project_id": 123})

            # Assert response status
            self.assertEqual(response.status_code, http.HTTPStatus.INTERNAL_SERVER_ERROR)

            data = await response.get_json()
            self.assertEqual(data["status"], 0, 'Status should be 0')
            self.assertEqual(data["error"], "Invalid project id",
                             "Error should be should be 'Invalid project id'")

    @patch('apis.testcases_api_view.SqlInterface')
    async def test_testcase_details_empty_results(self, mock_sql_interface):
        mock_db = MagicMock()
        mock_db.projects.is_valid_project_id.return_value = True
        mock_db.testcases.get_testcase_overviews.return_value = []

        mock_sql_interface.return_value = mock_db

        # 🔑 Instantiate AFTER setting return_value
        view = TestCasesApiView(self.mock_logger, self.mock_state_object)
        self.app.add_url_rule('/web/testcases/details', view_func=view.testcase_details, methods=['POST'])

        view._call_api_post = AsyncMock()
        view._call_api_post.return_value = MagicMock(
            status_code=http.HTTPStatus.OK,
            json=AsyncMock(return_value={"status": 1, "token": "mock_token"})
        )

        async with self.client as client:
            response = await client.post('/web/testcases/details', json={"project_id": 123})

            data = await response.get_json()
            self.assertEqual(response.status_code, http.HTTPStatus.OK)
            self.assertEqual(len(data), 0, 'List should be empty')

    @patch('apis.testcases_api_view.SqlInterface')
    async def test_testcase_get_case_valid(self, mock_sql_interface):
        """Test `testcase_get_case` with a valid case ID."""
        mock_db = MagicMock()
        mock_db.projects.is_valid_project_id.return_value = True
        mock_db.testcases.get_testcase.return_value = [
            [
                1,
                3,
                "Valid Login Test",
                "Checks login with valid credentials"
            ]
        ]

        mock_sql_interface.return_value = mock_db

        view = TestCasesApiView(self.mock_logger, self.mock_state_object)

        # Register route for testing
        self.app.add_url_rule('/web/testcases/get_case/<case_id>',
                              view_func=view.testcase_get_case,
                              methods=['POST'])

        mock_call_api_post = AsyncMock()
        mock_call_api_post.return_value = MagicMock(status_code=http.HTTPStatus.OK,
                                                    json=AsyncMock(return_value={"status": 1, "token": "mock_token"}))
        view._call_api_post = mock_call_api_post

        async with self.client as client:
            response = await client.post('/web/testcases/get_case/<case_id>',
                                         json={'project_id': 123})

            # Assert response status
            self.assertEqual(response.status_code, http.HTTPStatus.OK)

            # Check response JSON and assert the structure
            data = await response.get_json()
            self.assertEqual(len(data[0]), 4,
                             'Test details should have 4 elements')
            self.assertEqual(data[0][0], 1, 'Test ID should be 1')
            self.assertEqual(data[0][1], 3, 'Folder ID should be 3')
            self.assertEqual(data[0][2], "Valid Login Test",
                             "Test name ID should be 'Valid Login Test'")
            self.assertEqual(data[0][3], 'Checks login with valid credentials',
                             "Test description should be 'Checks login with valid credentials'")

    @patch('apis.testcases_api_view.SqlInterface')
    async def test_testcase_get_case_not_found(self, mock_sql_interface):
        """Test `testcase_get_case` when case ID is not found."""
        mock_db = MagicMock()
        mock_db.testcases.get_testcase.return_value = None

        mock_sql_interface.return_value = mock_db

        view = TestCasesApiView(self.mock_logger, self.mock_state_object)

        # Register route for testing
        self.app.add_url_rule('/web/testcases/get_case/<case_id>',
                              view_func=view.testcase_get_case,
                              methods=['POST'])

        mock_call_api_post = AsyncMock()
        mock_call_api_post.return_value = MagicMock(status_code=http.HTTPStatus.INTERNAL_SERVER_ERROR,
                                                    json=AsyncMock(return_value={"status": 0, "token": "infernal error"}))
        view._call_api_post = mock_call_api_post

        async with self.client as client:
            response = await client.post('/web/testcases/get_case/<case_id>',
                                         json={'project_id': 123})

            # Assert response status
            self.assertEqual(response.status_code, http.HTTPStatus.INTERNAL_SERVER_ERROR)

            # Check response JSON and assert the structure
            data = await response.get_json()


            data = await response.get_json()
            self.assertEqual(data["status"], 0, 'Status should be 0')
            self.assertEqual(data["error"], "Internal error",
                             "Error should be should be 'Internal Error'")
