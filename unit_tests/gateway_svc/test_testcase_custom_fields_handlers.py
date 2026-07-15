"""
Copyright 2025-2026 Integrated Test Management Suite Development Team

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
import unittest
from unittest.mock import AsyncMock, MagicMock
from quart import Quart
from weaver_framework.microservice.api_response import ApiResponse
from items.services.items_gateway.routes.web.testcase_custom_fields.\
    add_custom_field_handler import AddCustomFieldHandler
from items.services.items_gateway.routes.web.testcase_custom_fields.\
    delete_custom_field_handler import DeleteCustomFieldHandler
from items.services.items_gateway.routes.web.testcase_custom_fields.\
    get_all_custom_fields_handler import GetAllCustomFieldsHandler
from items.services.items_gateway.routes.web.testcase_custom_fields.\
    modify_custom_field_handler import ModifyCustomFieldHandler
from items.services.items_gateway.routes.web.testcase_custom_fields.\
    move_custom_field_handler import MoveCustomFieldHandler

_LOGGER = MagicMock()

_VALID_FIELD_BODY = {
    "field_name": "Priority",
    "description": "",
    "system_name": "priority",
    "field_type": "String",
    "enabled": True,
    "is_required": False,
    "default_value": "",
    "applies_to_all_projects": True,
}


def _config():
    config = MagicMock()
    config.apis_cms_svc = "http://cms/"
    return config


# ------------------------------------------------------------------
# GetAllCustomFieldsHandler
# ------------------------------------------------------------------

class TestGetAllCustomFieldsHandler(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.mock_rest_client = AsyncMock()
        handler = GetAllCustomFieldsHandler(
            _LOGGER, _config(), self.mock_rest_client)

        app = Quart(__name__)

        @app.route("/testcase_custom_fields", methods=["GET"])
        async def get_all_custom_fields():
            return await handler.get_all_custom_fields()

        self.client = app.test_client()

    async def _get(self, qs=""):
        async with self.client as c:
            return await c.get(f"/testcase_custom_fields{qs}")

    async def test_non_integer_project_id_returns_400(self):
        response = await self._get("?project_id=abc")
        self.assertEqual(response.status_code, 400)
        self.mock_rest_client.get.assert_not_called()

    async def test_non_positive_project_id_returns_400(self):
        response = await self._get("?project_id=0")
        self.assertEqual(response.status_code, 400)
        self.mock_rest_client.get.assert_not_called()

    async def test_no_project_id_lists_all(self):
        self.mock_rest_client.get.return_value = ApiResponse(
            status_code=200, body=[])
        response = await self._get()
        self.assertEqual(response.status_code, 200)
        _, kwargs = self.mock_rest_client.get.call_args
        self.assertIsNone(kwargs.get("params"))

    async def test_valid_project_id_passed_through(self):
        self.mock_rest_client.get.return_value = ApiResponse(
            status_code=200, body=[])
        response = await self._get("?project_id=5")
        self.assertEqual(response.status_code, 200)
        _, kwargs = self.mock_rest_client.get.call_args
        self.assertEqual(kwargs.get("params"), {"project_id": 5})

    async def test_connection_failure_returns_500(self):
        self.mock_rest_client.get.return_value = ApiResponse(
            status_code=None, exception_msg="boom")
        response = await self._get()
        self.assertEqual(response.status_code, 500)

    async def test_cms_error_status_propagated(self):
        self.mock_rest_client.get.return_value = ApiResponse(
            status_code=404, body={"error": "Project id is invalid"})
        response = await self._get("?project_id=999")
        self.assertEqual(response.status_code, 404)


# ------------------------------------------------------------------
# AddCustomFieldHandler
# ------------------------------------------------------------------

class TestAddCustomFieldHandler(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.mock_rest_client = AsyncMock()
        handler = AddCustomFieldHandler(_LOGGER, _config(), self.mock_rest_client)

        app = Quart(__name__)

        @app.route("/testcase_custom_fields", methods=["POST"])
        async def add_custom_field():
            return await handler.add_custom_field()

        self.client = app.test_client()

    async def _post(self, body):
        async with self.client as c:
            return await c.post("/testcase_custom_fields", json=body)

    async def test_missing_field_returns_400(self):
        body = {k: v for k, v in _VALID_FIELD_BODY.items() if k != "field_name"}
        response = await self._post(body)
        self.assertEqual(response.status_code, 400)
        self.mock_rest_client.post.assert_not_called()

    async def test_connection_failure_returns_500(self):
        self.mock_rest_client.post.return_value = ApiResponse(
            status_code=None, exception_msg="boom")
        response = await self._post(_VALID_FIELD_BODY)
        self.assertEqual(response.status_code, 500)

    async def test_cms_error_status_propagated_dict_body(self):
        self.mock_rest_client.post.return_value = ApiResponse(
            status_code=409, body={"error": "already exists"})
        response = await self._post(_VALID_FIELD_BODY)
        self.assertEqual(response.status_code, 409)
        data = await response.get_json()
        self.assertEqual(data["error"], "already exists")

    async def test_cms_error_status_non_dict_body(self):
        self.mock_rest_client.post.return_value = ApiResponse(
            status_code=500, body="not a dict")
        response = await self._post(_VALID_FIELD_BODY)
        self.assertEqual(response.status_code, 500)
        data = await response.get_json()
        self.assertEqual(data["error"], "Unknown error")

    async def test_success_returns_200(self):
        self.mock_rest_client.post.return_value = ApiResponse(status_code=200)
        response = await self._post(_VALID_FIELD_BODY)
        self.assertEqual(response.status_code, 200)
        data = await response.get_json()
        self.assertEqual(data["status"], 1)


# ------------------------------------------------------------------
# DeleteCustomFieldHandler
# ------------------------------------------------------------------

class TestDeleteCustomFieldHandler(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.mock_rest_client = AsyncMock()
        handler = DeleteCustomFieldHandler(
            _LOGGER, _config(), self.mock_rest_client)

        app = Quart(__name__)

        @app.route("/testcase_custom_fields/<int:field_id>", methods=["DELETE"])
        async def delete_custom_field(field_id):
            return await handler.delete_custom_field(field_id)

        self.client = app.test_client()

    async def _delete(self, field_id=1):
        async with self.client as c:
            return await c.delete(f"/testcase_custom_fields/{field_id}")

    async def test_connection_failure_returns_500(self):
        self.mock_rest_client.delete.return_value = ApiResponse(
            status_code=None, exception_msg="boom")
        response = await self._delete()
        self.assertEqual(response.status_code, 500)

    async def test_not_found_returns_404(self):
        self.mock_rest_client.delete.return_value = ApiResponse(status_code=404)
        response = await self._delete(99)
        self.assertEqual(response.status_code, 404)
        data = await response.get_json()
        self.assertIn("99", data["error"])

    async def test_other_error_status_propagated(self):
        self.mock_rest_client.delete.return_value = ApiResponse(
            status_code=400, body={"error": "System custom fields cannot be "
                                            "deleted"})
        response = await self._delete()
        self.assertEqual(response.status_code, 400)

    async def test_success_returns_200(self):
        self.mock_rest_client.delete.return_value = ApiResponse(status_code=200)
        response = await self._delete()
        self.assertEqual(response.status_code, 200)
        data = await response.get_json()
        self.assertEqual(data["status"], 1)


# ------------------------------------------------------------------
# ModifyCustomFieldHandler
# ------------------------------------------------------------------

class TestModifyCustomFieldHandler(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.mock_rest_client = AsyncMock()
        handler = ModifyCustomFieldHandler(
            _LOGGER, _config(), self.mock_rest_client)

        app = Quart(__name__)

        @app.route("/testcase_custom_fields/<int:field_id>", methods=["PUT"])
        async def modify_custom_field(field_id):
            return await handler.modify_custom_field(field_id)

        self.client = app.test_client()

    async def _put(self, field_id, body):
        async with self.client as c:
            return await c.put(f"/testcase_custom_fields/{field_id}", json=body)

    async def test_missing_field_returns_400(self):
        body = {k: v for k, v in _VALID_FIELD_BODY.items() if k != "system_name"}
        response = await self._put(1, body)
        self.assertEqual(response.status_code, 400)
        self.mock_rest_client.put.assert_not_called()

    async def test_error_status_propagated(self):
        self.mock_rest_client.put.return_value = ApiResponse(
            status_code=404, body={"error": "not found"})
        response = await self._put(99, _VALID_FIELD_BODY)
        self.assertEqual(response.status_code, 404)

    async def test_success_returns_200(self):
        self.mock_rest_client.put.return_value = ApiResponse(status_code=200)
        response = await self._put(1, _VALID_FIELD_BODY)
        self.assertEqual(response.status_code, 200)
        data = await response.get_json()
        self.assertEqual(data["status"], 1)


# ------------------------------------------------------------------
# MoveCustomFieldHandler
# ------------------------------------------------------------------

class TestMoveCustomFieldHandler(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.mock_rest_client = AsyncMock()
        handler = MoveCustomFieldHandler(
            _LOGGER, _config(), self.mock_rest_client)

        app = Quart(__name__)

        @app.route("/testcase_custom_fields/<int:field_id>", methods=["PATCH"])
        async def move_custom_field(field_id):
            return await handler.move_custom_field(field_id)

        self.client = app.test_client()

    async def _patch(self, field_id, body):
        async with self.client as c:
            return await c.patch(f"/testcase_custom_fields/{field_id}",
                                 json=body)

    async def test_missing_direction_returns_400(self):
        response = await self._patch(1, {})
        self.assertEqual(response.status_code, 400)
        self.mock_rest_client.patch.assert_not_called()

    async def test_connection_failure_returns_500(self):
        self.mock_rest_client.patch.return_value = ApiResponse(
            status_code=None, exception_msg="boom")
        response = await self._patch(1, {"direction": "up"})
        self.assertEqual(response.status_code, 500)

    async def test_error_status_propagated(self):
        self.mock_rest_client.patch.return_value = ApiResponse(
            status_code=400, body={"error": "already at the boundary"})
        response = await self._patch(1, {"direction": "up"})
        self.assertEqual(response.status_code, 400)

    async def test_success_returns_200(self):
        self.mock_rest_client.patch.return_value = ApiResponse(status_code=200)
        response = await self._patch(1, {"direction": "down"})
        self.assertEqual(response.status_code, 200)
        data = await response.get_json()
        self.assertEqual(data["status"], 1)


if __name__ == "__main__":
    unittest.main()
