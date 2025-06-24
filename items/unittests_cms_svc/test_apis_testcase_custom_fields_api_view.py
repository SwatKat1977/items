import http
import unittest
from unittest.mock import AsyncMock, patch, MagicMock
import quart
from threadsafe_configuration import ThreadSafeConfiguration
from apis.web.admin.testcase_custom_fields_api_view import TestcaseCustomFieldsApiView


class TestApisTestcaseCustomFieldsApiView(unittest.IsolatedAsyncioTestCase):
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

    @patch('apis.web.admin.testcase_custom_fields_api_view.SqlInterface')
    async def test_add_custom_field_custom_field_name_exists_failure(self, mock_sql_interface):
        """Test default behavior when no fields are specified"""
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
        """Test default behavior when no fields are specified"""
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
        """Test default behavior when no fields are specified"""
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
        """Test default behavior when no fields are specified"""
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
        """Test default behavior when no fields are specified"""
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
            print(f"\n\n[duplicate_projects] Resp: {await response.get_json()}")
            data = await response.get_json()
            # Assert response status
            self.assertEqual(response.status_code, http.HTTPStatus.BAD_REQUEST)
            self.assertEqual(data,
                             {'error': 'Duplicate projects', 'status': 0})

'''
cms_svc/apis/web/admin/testcase_custom_fields_api_view.py      56     32    43%   60-115, 141-177
cms_svc/apis/web/admin/testcase_custom_fields_api_view.py      56     27    52%   63-66, 78-115, 141-177
cms_svc/apis/web/admin/testcase_custom_fields_api_view.py      58     23    60%   63-66, 89-116, 142-178
cms_svc/apis/web/admin/testcase_custom_fields_api_view.py      58     23    60%   63-66, 89-116, 142-178
'''

'''

class TestcaseCustomFieldsApiView(BaseView):
    __slots__ = ['_logger']

    def __init__(self, logger: logging.Logger,
                 state_object: StateObject) -> None:
        self._logger = logger.getChild(__name__)
        self._db: SqlInterface = SqlInterface(logger, state_object)

    @validate_json(json_schemas.SCHEMA_ADD_TEST_CASE_CUSTOM_FIELD_REQUEST)
    async def add_custom_field(self, request_msg: ApiResponse):

        # Check to see if the field name is already in use, None means an
        # internal error and True means it already exists/
        field_name_exists = self._db.tc_custom_fields.custom_field_name_exists(
            request_msg.body.field_name)
        if field_name_exists is None:
            response_json = {
                'status': 0,
                'error': "Internal error"}
            return quart.Response(json.dumps(response_json),
                                  status=http.HTTPStatus.INTERNAL_SERVER_ERROR,
                                  content_type="application/json")

        if field_name_exists:
            response_json = {
                'status': 0,
                'error': "Duplicate field_name"}
            return quart.Response(json.dumps(response_json),
                                  status=http.HTTPStatus.OK,
                                  content_type="application/json")

        # Check to see if the system name is already in use, None means an
        # internal error and True means it already exists/
        system_name_exists = self._db.tc_custom_fields.custom_field_name_exists(
            request_msg.body.system_name)
        if system_name_exists is None:
            response_json = {
                'status': 0,
                'error': "Internal error"}
            return quart.Response(json.dumps(response_json),
                                  status=http.HTTPStatus.INTERNAL_SERVER_ERROR,
                                  content_type="application/json")

        if system_name_exists:
            response_json = {
                'status': 0,
                'error': "Duplicate system_name"}
            return quart.Response(json.dumps(response_json),
                                  status=http.HTTPStatus.OK,
                                  content_type="application/json")

        if request_msg.body.projects:
            if len(request_msg.body.projects) \
                    != len(set(request_msg.body.projects)):
                response_json = {
                    'status': 0,
                    'error': "Duplicate projects"}
                return quart.Response(json.dumps(response_json),
                                      status=http.HTTPStatus.OK,
                                      content_type="application/json")

        custom_field_id: int = self._db.tc_custom_fields.add_custom_field(
            request_msg.body.field_name, request_msg.body.description,
            request_msg.body.system_name, request_msg.body.field_type,
            request_msg.body.enabled, request_msg.body.is_required,
            request_msg.body.default_value,
            request_msg.body.applies_to_all_projects)

        if not custom_field_id:
            response_json = {
                'status': 0,
                'error': "Internal error"}
            return quart.Response(json.dumps(response_json),
                                  status=http.HTTPStatus.INTERNAL_SERVER_ERROR,
                                  content_type="application/json")

        # ===========================================
        # TO BE DONE: Upon failing to add projects (if there are any) we should
        #             perform some form of roll-back on custom field add.
        # ===========================================

        if request_msg.body.projects and len(request_msg.body.projects):
            status = self._db.tc_custom_fields.assign_custom_field_to_project(
                custom_field_id, request_msg.body.projects)

        response_json = {
            'status': 1
        }
        return quart.Response(json.dumps(response_json),
                              status=http.HTTPStatus.OK,
                              content_type="application/json")

'''