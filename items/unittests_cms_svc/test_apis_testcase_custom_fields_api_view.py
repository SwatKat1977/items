import http
import unittest
from unittest.mock import AsyncMock, patch, MagicMock
import quart
from threadsafe_configuration import ThreadSafeConfiguration
from apis.admin.testcase_custom_fields_api_view import TestcaseCustomFieldsApiView


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

    @patch('apis.admin.testcase_custom_fields_api_view.SqlInterface')
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

    @patch('apis.admin.testcase_custom_fields_api_view.SqlInterface')
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

    @patch('apis.admin.testcase_custom_fields_api_view.SqlInterface')
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

    @patch('apis.admin.testcase_custom_fields_api_view.SqlInterface')
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

    @patch('apis.admin.testcase_custom_fields_api_view.SqlInterface')
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

    @patch('apis.admin.testcase_custom_fields_api_view.SqlInterface')
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

    @patch('apis.admin.testcase_custom_fields_api_view.SqlInterface')
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

    @patch('apis.admin.testcase_custom_fields_api_view.SqlInterface')
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

    @patch('apis.admin.testcase_custom_fields_api_view.SqlInterface')
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

    @patch('apis.admin.testcase_custom_fields_api_view.SqlInterface')
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

    @patch('apis.admin.testcase_custom_fields_api_view.SqlInterface')
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

    @patch('apis.admin.testcase_custom_fields_api_view.SqlInterface')
    async def test_get_all_custom_fields_internal_error(self, mock_sql_interface):
        mock_db = MagicMock()
        mock_db.tc_custom_fields.get_all_fields.return_value = None
        mock_sql_interface.return_value = mock_db

        view = TestcaseCustomFieldsApiView(self.mock_logger, self.mock_state_object)

        # Register route for testing
        self.app.add_url_rule('/testcase_custom_fields/testcase_custom_fields',
                              view_func=view.get_all_custom_fields,
                              methods=['GET'])

        async with self.client as client:
            response = await client.get('/testcase_custom_fields/testcase_custom_fields')
            data = await response.get_json()
            self.assertEqual(response.status_code, 500)
            self.assertEqual(data["status"], 0)
            self.assertIn("error", data)
            self.assertEqual(data["error"], "Internal error")

    @patch('apis.admin.testcase_custom_fields_api_view.SqlInterface')
    async def test_get_all_custom_fields_empty_list(self, mock_sql_interface):
        mock_db = MagicMock()
        mock_db.tc_custom_fields.get_all_fields.return_value = []
        mock_sql_interface.return_value = mock_db

        view = TestcaseCustomFieldsApiView(self.mock_logger, self.mock_state_object)

        # Register route for testing
        self.app.add_url_rule('/testcase_custom_fields/testcase_custom_fields',
                              view_func=view.get_all_custom_fields,
                              methods=['GET'])

        async with self.client as client:
            response = await client.get('/testcase_custom_fields/testcase_custom_fields')
            data = await response.get_json()
            self.assertEqual(response.status_code, 200)
            self.assertIn("custom_fields", data)
            self.assertEqual(data["custom_fields"], [])

    @patch('apis.admin.testcase_custom_fields_api_view.SqlInterface')
    async def test_get_all_custom_fields_global_fields_no_assigned_projects(self,
                                                                            mock_sql_interface):
        mock_fields = [
            (1, "Field1", "Desc", "sys1", "type1", "entry1", True, 1, True, "def", True, None),
            (2, "Field2", "Desc2", "sys2", "type2", "entry2", True, 2, False, "def2", True, None),
        ]
        mock_db = MagicMock()
        mock_db.tc_custom_fields.get_all_fields.return_value = mock_fields
        mock_sql_interface.return_value = mock_db

        view = TestcaseCustomFieldsApiView(self.mock_logger, self.mock_state_object)

        # Register route for testing
        self.app.add_url_rule('/testcase_custom_fields/testcase_custom_fields',
                              view_func=view.get_all_custom_fields,
                              methods=['GET'])

        async with self.client as client:
            response = await client.get('/testcase_custom_fields/testcase_custom_fields')
            data = await response.get_json()
            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(data["custom_fields"]), 2)
            for field in data["custom_fields"]:
                self.assertEqual(field["assigned_projects"], [])

    @patch('apis.admin.testcase_custom_fields_api_view.SqlInterface')
    async def test_get_all_custom_fields_non_global_with_assigned_projects(self,
                                                                           mock_sql_interface):
        mock_fields = [
            (3, "Field3", "Desc3", "sys3", "type3", "entry3", True, 3, False, "def3", False, "1:Project One,2:Project Two")
        ]
        mock_db = MagicMock()
        mock_db.tc_custom_fields.get_all_fields.return_value = mock_fields
        mock_sql_interface.return_value = mock_db

        view = TestcaseCustomFieldsApiView(self.mock_logger, self.mock_state_object)

        # Register route for testing
        self.app.add_url_rule('/testcase_custom_fields/testcase_custom_fields',
                              view_func=view.get_all_custom_fields,
                              methods=['GET'])

        async with self.client as client:
            response = await client.get('/testcase_custom_fields/testcase_custom_fields')
            data = await response.get_json()
            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(data["custom_fields"]), 1)
            field = data["custom_fields"][0]
            self.assertFalse(field["applies_to_all_projects"])
            self.assertEqual(field["assigned_projects"],
                             [{'id': '1', 'name': 'Project One'}, {'id': '2', 'name': 'Project Two'}])

    @patch('apis.admin.testcase_custom_fields_api_view.SqlInterface')
    async def test_get_all_custom_fields_mixed_fields(self,
                                                      mock_sql_interface):
        mock_fields = [
            (1, "GlobalField", "Global Desc", "sys_global", "type_global", "entry_global",
             True, 1, True, "def_global", True, None),
            (2, "ProjectField", "Project Desc", "sys_proj", "type_proj", "entry_proj",
             True, 2, False, "def_proj", False, "3:Project Three,4:Project Four"),
        ]
        mock_db = MagicMock()
        mock_db.tc_custom_fields.get_all_fields.return_value = mock_fields
        mock_sql_interface.return_value = mock_db

        view = TestcaseCustomFieldsApiView(self.mock_logger, self.mock_state_object)

        # Register route for testing
        self.app.add_url_rule('/testcase_custom_fields/testcase_custom_fields',
                              view_func=view.get_all_custom_fields,
                              methods=['GET'])

        async with self.client as client:
            response = await client.get('/testcase_custom_fields/testcase_custom_fields')
            data = await response.get_json()
            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(data["custom_fields"]), 2)

            global_field = data["custom_fields"][0]
            proj_field = data["custom_fields"][1]

            self.assertTrue(global_field["applies_to_all_projects"])
            self.assertEqual(global_field["assigned_projects"], [])

            self.assertFalse(proj_field["applies_to_all_projects"])
            self.assertEqual(proj_field["assigned_projects"],
                             [{'id': '3', 'name': 'Project Three'},
                              {'id': '4', 'name': 'Project Four'}])


    # @blueprint.route('/testcase_custom_fields/<int:project_id>', methods=['GET'])
    # @blueprint.route('/testcase_custom_fields', methods=['GET'])

    '''
        @blueprint.route('/testcase_custom_fields/<int:project_id>',
                     methods=['GET'])
    async def get_project_custom_fields_request(project_id: int):
        return await view.get_project_custom_fields(project_id)

    logger.debug("=> /testcase_custom_fields [GET]")

    @blueprint.route('/testcase_custom_fields', methods=['GET'])
    async def get_all_custom_fields_request():
        return await view.get_all_custom_fields()
    '''



