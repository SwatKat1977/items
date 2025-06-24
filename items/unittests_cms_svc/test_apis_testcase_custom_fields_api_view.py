import http
import unittest
from unittest.mock import AsyncMock, patch, MagicMock
import quart
from threadsafe_configuration import ThreadSafeConfiguration
from apis.web.admin.testcase_custom_fields_api_view import TestcaseCustomFieldsApiView


class TestApisTestcaseCustomFieldsApiView(unittest.IsolatedAsyncioTestCase):
    """Unit tests for the TestcaseCustomFieldsApiView class."""

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

    @patch('apis.web.admin.testcase_custom_fields_api_view.SqlInterface')
    async def test_add_custom_field_custom_field_name_exists_failure(self, mock_sql_interface):
        mock_db = MagicMock()
        mock_db.tc_custom_fields.custom_field_name_exists.return_value = None
        mock_sql_interface.return_value = mock_db

        view = TestcaseCustomFieldsApiView(self.mock_logger, self.mock_state_object)

        # Register route for testing
        self.app.add_url_rule('/web/admin/testcase_custom_fields/testcase_custom_fields',
                              view_func=view.add_custom_field,
                              methods=['POST'])

        test_json_body: dict = {
            "field_name": "new type string",
            "description": "default",
            "system_name": "new_system_name",
            "field_type": "String",
            "enabled": True,
            "is_required": False,
            "default_value": "",
            "applies_to_all_projects": False,
            "projects": [
                  "Project Delta_1",
                  "Project Beta_2"
            ]
        }

        async with self.client as client:
            response = await client.post('/web/admin/testcase_custom_fields/testcase_custom_fields',
                                         json=test_json_body)
            data = await response.get_json()
            # Assert response status
            self.assertEqual(response.status_code, http.HTTPStatus.INTERNAL_SERVER_ERROR)
            self.assertEqual(data,
                             {"status": 0, "error": "Internal error"})

    @patch('apis.web.admin.testcase_custom_fields_api_view.SqlInterface')
    async def test_add_custom_field_field_name_exists(self, mock_sql_interface):
        mock_db = MagicMock()
        mock_db.tc_custom_fields.custom_field_name_exists.return_value = True
        mock_sql_interface.return_value = mock_db

        view = TestcaseCustomFieldsApiView(self.mock_logger, self.mock_state_object)

        # Register route for testing
        self.app.add_url_rule('/web/admin/testcase_custom_fields/testcase_custom_fields',
                              view_func=view.add_custom_field,
                              methods=['POST'])

        test_json_body: dict = {
            "field_name": "new type string",
            "description": "default",
            "system_name": "new_system_name",
            "field_type": "String",
            "enabled": True,
            "is_required": False,
            "default_value": "",
            "applies_to_all_projects": False,
            "projects": [
                  "Project Delta_1",
                  "Project Beta_2"
            ]
        }

        async with self.client as client:
            response = await client.post('/web/admin/testcase_custom_fields/testcase_custom_fields',
                                         json=test_json_body)
            data = await response.get_json()
            # Assert response status
            self.assertEqual(response.status_code, http.HTTPStatus.OK)
            self.assertEqual(data,
                             {'error': 'Duplicate field_name', 'status': 0})

    @patch('apis.web.admin.testcase_custom_fields_api_view.SqlInterface')
    async def test_add_custom_field_system_name_exists(self, mock_sql_interface):
        mock_db = MagicMock()
        mock_db.tc_custom_fields.custom_field_name_exists.return_value = False
        mock_db.tc_custom_fields.system_name_exists.return_value = True
        mock_sql_interface.return_value = mock_db

        view = TestcaseCustomFieldsApiView(self.mock_logger, self.mock_state_object)

        # Register route for testing
        self.app.add_url_rule('/web/admin/testcase_custom_fields/testcase_custom_fields',
                              view_func=view.add_custom_field,
                              methods=['POST'])

        test_json_body: dict = {
            "field_name": "new type string",
            "description": "default",
            "system_name": "new_system_name",
            "field_type": "String",
            "enabled": True,
            "is_required": False,
            "default_value": "",
            "applies_to_all_projects": False,
            "projects": [
                  "Project Delta_1",
                  "Project Beta_2"
            ]
        }

        async with self.client as client:
            response = await client.post('/web/admin/testcase_custom_fields/testcase_custom_fields',
                                         json=test_json_body)
            data = await response.get_json()
            # Assert response status
            self.assertEqual(response.status_code, http.HTTPStatus.OK)
            self.assertEqual(data,
                             {'error': 'Duplicate system_name', 'status': 0})

    @patch('apis.web.admin.testcase_custom_fields_api_view.SqlInterface')
    async def test_add_custom_field_system_exists_failure(self, mock_sql_interface):
        mock_db = MagicMock()
        mock_db.tc_custom_fields.custom_field_name_exists.return_value = False
        mock_db.tc_custom_fields.system_name_exists.return_value = None
        mock_sql_interface.return_value = mock_db

        view = TestcaseCustomFieldsApiView(self.mock_logger, self.mock_state_object)

        # Register route for testing
        self.app.add_url_rule('/web/admin/testcase_custom_fields/testcase_custom_fields',
                              view_func=view.add_custom_field,
                              methods=['POST'])

        test_json_body: dict = {
            "field_name": "new type string",
            "description": "default",
            "system_name": "new_system_name",
            "field_type": "String",
            "enabled": True,
            "is_required": False,
            "default_value": "",
            "applies_to_all_projects": False,
            "projects": [
                  "Project Delta_1",
                  "Project Beta_2"
            ]
        }

        async with self.client as client:
            response = await client.post('/web/admin/testcase_custom_fields/testcase_custom_fields',
                                         json=test_json_body)
            data = await response.get_json()
            # Assert response status
            self.assertEqual(response.status_code, http.HTTPStatus.INTERNAL_SERVER_ERROR)
            self.assertEqual(data,
                             {"status": 0, "error": "Internal error"})

    @patch('apis.web.admin.testcase_custom_fields_api_view.SqlInterface')
    async def test_add_custom_field_duplicate_projects(self, mock_sql_interface):
        mock_db = MagicMock()
        mock_db.tc_custom_fields.custom_field_name_exists.return_value = False
        mock_db.tc_custom_fields.system_name_exists.return_value = False
        mock_sql_interface.return_value = mock_db

        view = TestcaseCustomFieldsApiView(self.mock_logger, self.mock_state_object)

        # Register route for testing
        self.app.add_url_rule('/web/admin/testcase_custom_fields/testcase_custom_fields',
                              view_func=view.add_custom_field,
                              methods=['POST'])

        test_json_body: dict = {
            "field_name": "new type string",
            "description": "default",
            "system_name": "new_system_name",
            "field_type": "String",
            "enabled": True,
            "is_required": False,
            "default_value": "",
            "applies_to_all_projects": False,
            "projects": [
                "alpha",
                "beta",
                "alpha"
            ]
        }

        async with self.client as client:
            response = await client.post('/web/admin/testcase_custom_fields/testcase_custom_fields',
                                         json=test_json_body)
            data = await response.get_json()
            # Assert response status
            self.assertEqual(response.status_code, http.HTTPStatus.BAD_REQUEST)
            self.assertEqual(data,
                             {'error': 'Duplicate projects', 'status': 0})

    @patch('apis.web.admin.testcase_custom_fields_api_view.SqlInterface')
    async def test_add_custom_field_add_custom_field_failure(self, mock_sql_interface):
        mock_db = MagicMock()
        mock_db.tc_custom_fields.custom_field_name_exists.return_value = False
        mock_db.tc_custom_fields.system_name_exists.return_value = False
        mock_db.tc_custom_fields.add_custom_field.return_value = None
        mock_sql_interface.return_value = mock_db

        view = TestcaseCustomFieldsApiView(self.mock_logger, self.mock_state_object)

        # Register route for testing
        self.app.add_url_rule('/web/admin/testcase_custom_fields/testcase_custom_fields',
                              view_func=view.add_custom_field,
                              methods=['POST'])

        test_json_body: dict = {
            "field_name": "new type string",
            "description": "default",
            "system_name": "new_system_name",
            "field_type": "String",
            "enabled": True,
            "is_required": False,
            "default_value": "",
            "applies_to_all_projects": False,
            "projects": [
                "alpha",
                "beta"
            ]
        }

        async with self.client as client:
            response = await client.post('/web/admin/testcase_custom_fields/testcase_custom_fields',
                                         json=test_json_body)
            data = await response.get_json()
            self.assertEqual(response.status_code, http.HTTPStatus.INTERNAL_SERVER_ERROR)
            self.assertEqual(data,
                             {'error': 'Internal error', 'status': 0})

    @patch('apis.web.admin.testcase_custom_fields_api_view.SqlInterface')
    async def test_add_custom_field_successful(self, mock_sql_interface):
        mock_db = MagicMock()
        mock_db.tc_custom_fields.custom_field_name_exists.return_value = False
        mock_db.tc_custom_fields.system_name_exists.return_value = False
        mock_db.tc_custom_fields.add_custom_field.return_value = 10
        mock_db.tc_custom_fields.assign_custom_field_to_project.return_value = 1
        mock_sql_interface.return_value = mock_db

        view = TestcaseCustomFieldsApiView(self.mock_logger, self.mock_state_object)

        # Register route for testing
        self.app.add_url_rule('/web/admin/testcase_custom_fields/testcase_custom_fields',
                              view_func=view.add_custom_field,
                              methods=['POST'])

        test_json_body: dict = {
            "field_name": "new type string",
            "description": "default",
            "system_name": "new_system_name",
            "field_type": "String",
            "enabled": True,
            "is_required": False,
            "default_value": "",
            "applies_to_all_projects": False,
            "projects": [
                "alpha",
                "beta"
            ]
        }

        async with self.client as client:
            response = await client.post('/web/admin/testcase_custom_fields/testcase_custom_fields',
                                         json=test_json_body)
            data = await response.get_json()
            self.assertEqual(response.status_code, http.HTTPStatus.OK)
            self.assertEqual(data, {'status': 1})

    @patch('apis.web.admin.testcase_custom_fields_api_view.SqlInterface')
    async def test_move_custom_field_invalid_direction(self, mock_sql_interface):
        mock_db = MagicMock()

        mock_sql_interface.return_value = mock_db

        view = TestcaseCustomFieldsApiView(self.mock_logger, self.mock_state_object)

        # Register route for testing
        self.app.add_url_rule('/web/admin/testcase_custom_fields/<int:field_id>/<string:direction>',
                              view_func=view.move_testcase_custom_field,
                              methods=['PATCH'])

        async with self.client as client:
            response = await client.patch('/web/admin/testcase_custom_fields/20/invalid_dir')
            data = await response.get_json()
            self.assertEqual(response.status_code, http.HTTPStatus.BAD_REQUEST)
            self.assertEqual(data,
                             {'error': "Invalid direction. Must be 'up' or 'down'.",
                              'status': 0})

    @patch('apis.web.admin.testcase_custom_fields_api_view.SqlInterface')
    async def test_move_custom_field_db_failed(self, mock_sql_interface):
        mock_db = MagicMock()
        mock_db.tc_custom_fields.move_custom_field.return_value = None
        mock_sql_interface.return_value = mock_db

        view = TestcaseCustomFieldsApiView(self.mock_logger, self.mock_state_object)

        # Register route for testing
        self.app.add_url_rule('/web/admin/testcase_custom_fields/<int:field_id>/<string:direction>',
                              view_func=view.move_testcase_custom_field,
                              methods=['PATCH'])

        async with self.client as client:
            response = await client.patch('/web/admin/testcase_custom_fields/20/up')
            data = await response.get_json()
            self.assertEqual(response.status_code, http.HTTPStatus.INTERNAL_SERVER_ERROR)
            self.assertEqual(data,{'error': "Internal error", 'status': 0})

    @patch('apis.web.admin.testcase_custom_fields_api_view.SqlInterface')
    async def test_move_custom_field_invalid_move(self, mock_sql_interface):
        mock_db = MagicMock()
        mock_db.tc_custom_fields.move_custom_field.return_value = False
        mock_sql_interface.return_value = mock_db

        view = TestcaseCustomFieldsApiView(self.mock_logger, self.mock_state_object)

        # Register route for testing
        self.app.add_url_rule('/web/admin/testcase_custom_fields/<int:field_id>/<string:direction>',
                              view_func=view.move_testcase_custom_field,
                              methods=['PATCH'])

        async with self.client as client:
            response = await client.patch('/web/admin/testcase_custom_fields/20/up')
            data = await response.get_json()
            self.assertEqual(response.status_code, http.HTTPStatus.OK)
            self.assertEqual(data,{'error': "Invalid field or move operation", 'status': 0})

    @patch('apis.web.admin.testcase_custom_fields_api_view.SqlInterface')
    async def test_move_custom_field_valid_move(self, mock_sql_interface):
        mock_db = MagicMock()
        mock_db.tc_custom_fields.move_custom_field.return_value = True
        mock_sql_interface.return_value = mock_db

        view = TestcaseCustomFieldsApiView(self.mock_logger, self.mock_state_object)

        # Register route for testing
        self.app.add_url_rule('/web/admin/testcase_custom_fields/<int:field_id>/<string:direction>',
                              view_func=view.move_testcase_custom_field,
                              methods=['PATCH'])

        async with self.client as client:
            response = await client.patch('/web/admin/testcase_custom_fields/20/up')
            data = await response.get_json()
            self.assertEqual(response.status_code, http.HTTPStatus.OK)
            self.assertEqual(data,{'status': 1})
