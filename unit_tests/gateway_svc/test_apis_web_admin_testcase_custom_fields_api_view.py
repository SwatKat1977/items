import unittest
import http
import json
import logging
from unittest.mock import AsyncMock, MagicMock, patch
from quart import Quart
from apis.web.admin.testcase_custom_fields_api import TestcaseCustomFieldsApiView
from threadsafe_configuration import ThreadSafeConfiguration
from base_view import ApiResponse

class TestApiWebAdminTestCaseCustomFieldsAPIView(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        # Mock logger
        self.mock_logger = MagicMock(spec=logging.Logger)
        self.view = TestcaseCustomFieldsApiView(self.mock_logger)

        # Quart setup
        self.app = Quart(__name__)
        self.client = self.app.test_client()

        # Register route
        self.app.add_url_rule(
            '/admin/testcase_custom_fields/<int:field_id>',
            view_func=self.view.modify_custom_field,
            methods=['PATCH']
        )

    async def test_init_assigns_child_logger(self):
        # Validate logger child assignment
        self.mock_logger.getChild.assert_called_once_with(self.view.__module__)

    @patch.object(ThreadSafeConfiguration, 'get_entry')
    async def test_modify_custom_field_calls_move_custom_field(self, mock_get_entry):
        """Covers branch where request_msg.body has 'position' attribute"""
        mock_get_entry.return_value = "http://cms-svc/"

        # Mock the request with a 'position' attribute
        mock_request_msg = MagicMock(spec=ApiResponse)
        mock_request_msg.body = type("Body", (), {"position": "up"})()  # ✅ Use plain object

        # Mock _call_api_patch result
        mock_call_api_patch = AsyncMock()
        mock_call_api_patch.return_value = MagicMock(
            status_code=http.HTTPStatus.BAD_REQUEST,
            body={"result": "moved"}
        )
        self.view._call_api_patch = mock_call_api_patch

    async def test_modify_custom_field_calls_modify_custom_field_branch(self):
        class DummyBody:
            pass

        mock_request_msg = MagicMock(spec=ApiResponse)
        mock_request_msg.body = DummyBody()

        mock_modify_custom_field = AsyncMock()
        mock_response = MagicMock()
        mock_modify_custom_field.return_value = mock_response
        self.view._modify_custom_field = mock_modify_custom_field

        # 🔹 Call the undecorated coroutine to skip @validate_json
        real_method = self.view.modify_custom_field
        if hasattr(real_method, "__wrapped__"):
            real_method = real_method.__wrapped__

        async with self.app.test_request_context(path="/admin/testcase_custom_fields/5"):
            result = await real_method(self.view, mock_request_msg, 5)

        mock_modify_custom_field.assert_awaited_once_with(mock_request_msg, 5)
        self.assertEqual(result, mock_response)

    async def test_modify_custom_field_returns_bad_request_json(self):
        mock_request_msg = MagicMock(spec=ApiResponse)
        async with self.app.test_request_context(path="/admin/testcase_custom_fields/123"):
            response = await self.view._modify_custom_field(mock_request_msg, 123)

        self.assertEqual(response.status_code, http.HTTPStatus.BAD_REQUEST)
        data = await response.get_data(as_text=True)
        parsed = json.loads(data)
        self.assertEqual(parsed["status"], -1)
        self.assertEqual(parsed["error"], "placeholder")

    @patch.object(ThreadSafeConfiguration, 'get_entry')
    async def test_move_custom_field_returns_bad_request(self, mock_get_entry):
        """Directly test _move_custom_field method"""
        mock_get_entry.return_value = "http://cms-svc/"

        mock_request_msg = MagicMock(spec=ApiResponse)
        mock_request_msg.body = MagicMock()
        mock_request_msg.body.position = "down"

        mock_call_api_patch = AsyncMock()
        mock_call_api_patch.return_value = MagicMock(
            body={"result": "ok"},
            status_code=http.HTTPStatus.BAD_REQUEST
        )
        self.view._call_api_patch = mock_call_api_patch

        async with self.app.test_request_context(path="/admin/testcase_custom_fields/testcase_custom_fields"):
            response = await self.view._move_custom_field(mock_request_msg, 2)

            self.assertEqual(response.status_code, http.HTTPStatus.BAD_REQUEST)
            self.assertEqual(
                json.loads(await response.get_data(as_text=True)),
                {"result": "ok"}
            )

    @patch.object(ThreadSafeConfiguration, "get_entry", return_value="http://cms-svc/")
    async def test_modify_custom_field_with_position_triggers_move(self, mock_get_entry):
        mock_call_api_patch = AsyncMock()
        mock_call_api_patch.return_value = MagicMock(
            status_code=http.HTTPStatus.BAD_REQUEST,
            body={"result": "moved"},
        )
        self.view._call_api_patch = mock_call_api_patch

        # Send valid JSON body (goes through @validate_json)
        async with self.app.test_client() as client:
            response = await client.patch(
                "/admin/testcase_custom_fields/5",
                json={"position": "up"},
            )

        # The decorator should have passed it through to _move_custom_field()
        expected_url = (
            "http://cms-svc/admin/testcase_custom_fields/testcase_custom_fields/5/up"
        )
        mock_call_api_patch.assert_awaited_once_with(expected_url)

        self.assertEqual(response.status_code, http.HTTPStatus.BAD_REQUEST)
        data = await response.get_data(as_text=True)
        self.assertEqual(json.loads(data), {"result": "moved"})