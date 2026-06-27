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
from items.services.items_cms.routes.testcase_custom_fields.get_custom_field_handler import (
    GetCustomFieldHandler,
)
from items.services.items_cms.routes.testcase_custom_fields.get_custom_fields_handler import (
    GetCustomFieldsHandler,
)
from items.services.items_cms.routes.testcase_custom_fields.add_custom_field_handler import (
    AddCustomFieldHandler,
)
from items.services.items_cms.routes.testcase_custom_fields.delete_custom_field_handler import (
    DeleteCustomFieldHandler,
)
from items.services.items_cms.routes.testcase_custom_fields.move_custom_field_handler import (
    MoveCustomFieldHandler,
)
from items.services.items_cms.routes.testcase_custom_fields.update_custom_field_handler import (
    UpdateCustomFieldHandler,
)
from items.services.items_cms.services.testcase_custom_fields_service import (
    TestcaseCustomFieldsService,
    TestcaseCustomFieldResult,
)

_LOGGER = MagicMock()

_VALID_FIELD_BODY = {
    "field_name": "My Field",
    "description": "A description",
    "system_name": "my_field",
    "field_type": "String",
    "enabled": True,
    "is_required": False,
    "default_value": "",
    "applies_to_all_projects": True,
}


def _ok(**kwargs):
    return TestcaseCustomFieldResult(success=True, **kwargs)


def _internal():
    return TestcaseCustomFieldResult(
        success=False, error_msg="err", is_internal=True)


def _not_found():
    return TestcaseCustomFieldResult(
        success=False, error_msg="not found", not_found=True)


def _conflict(msg="already exists"):
    return TestcaseCustomFieldResult(
        success=False, error_msg=msg, is_conflict=True)


def _bad_request(msg="bad"):
    return TestcaseCustomFieldResult(success=False, error_msg=msg)


# ------------------------------------------------------------------
# GetCustomFieldHandler
# ------------------------------------------------------------------

class TestGetCustomFieldHandler(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.mock_service = AsyncMock(spec=TestcaseCustomFieldsService)
        handler = GetCustomFieldHandler(_LOGGER, self.mock_service)

        app = Quart(__name__)

        @app.route("/custom_fields/<int:field_id>")
        async def get_field(field_id):
            return await handler.get_custom_field(field_id)

        self.client = app.test_client()

    async def test_get_field_success_returns_200(self):
        self.mock_service.get_custom_field.return_value = _ok(
            data={"id": 1, "field_name": "Priority"})
        async with self.client as c:
            response = await c.get("/custom_fields/1")
        self.assertEqual(response.status_code, 200)
        data = await response.get_json()
        self.assertEqual(data["field_name"], "Priority")

    async def test_get_field_not_found_returns_404(self):
        self.mock_service.get_custom_field.return_value = _not_found()
        async with self.client as c:
            response = await c.get("/custom_fields/99")
        self.assertEqual(response.status_code, 404)

    async def test_get_field_bad_request_returns_400(self):
        self.mock_service.get_custom_field.return_value = _bad_request()
        async with self.client as c:
            response = await c.get("/custom_fields/1")
        self.assertEqual(response.status_code, 400)

    async def test_get_field_internal_error_returns_500(self):
        self.mock_service.get_custom_field.return_value = _internal()
        async with self.client as c:
            response = await c.get("/custom_fields/1")
        self.assertEqual(response.status_code, 500)


# ------------------------------------------------------------------
# GetCustomFieldsHandler
# ------------------------------------------------------------------

class TestGetCustomFieldsHandler(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.mock_service = AsyncMock(spec=TestcaseCustomFieldsService)
        handler = GetCustomFieldsHandler(_LOGGER, self.mock_service)

        app = Quart(__name__)

        @app.route("/custom_fields")
        async def get_fields():
            return await handler.get_custom_fields()

        self.client = app.test_client()

    async def test_get_all_fields_no_param_returns_200(self):
        self.mock_service.get_custom_fields.return_value = _ok(data=[])
        async with self.client as c:
            response = await c.get("/custom_fields")
        self.assertEqual(response.status_code, 200)
        self.mock_service.get_custom_fields.assert_called_once_with(None)

    async def test_get_fields_for_project_returns_200(self):
        self.mock_service.get_custom_fields.return_value = _ok(data=[])
        async with self.client as c:
            response = await c.get("/custom_fields?project_id=5")
        self.assertEqual(response.status_code, 200)
        self.mock_service.get_custom_fields.assert_called_once_with(5)

    async def test_get_fields_invalid_project_id_returns_400(self):
        async with self.client as c:
            response = await c.get("/custom_fields?project_id=abc")
        self.assertEqual(response.status_code, 400)
        self.mock_service.get_custom_fields.assert_not_called()

    async def test_get_fields_service_error_returns_500(self):
        self.mock_service.get_custom_fields.return_value = _internal()
        async with self.client as c:
            response = await c.get("/custom_fields")
        self.assertEqual(response.status_code, 500)


# ------------------------------------------------------------------
# AddCustomFieldHandler
# ------------------------------------------------------------------

class TestAddCustomFieldHandler(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.mock_service = AsyncMock(spec=TestcaseCustomFieldsService)
        handler = AddCustomFieldHandler(_LOGGER, self.mock_service)

        app = Quart(__name__)

        @app.route("/custom_fields", methods=["POST"])
        async def add_field():
            return await handler.add_custom_field()

        self.client = app.test_client()

    async def _post(self, body):
        async with self.client as c:
            return await c.post("/custom_fields", json=body)

    async def test_add_field_success_returns_200(self):
        self.mock_service.add_custom_field.return_value = _ok(data=7)
        response = await self._post(_VALID_FIELD_BODY)
        self.assertEqual(response.status_code, 200)
        data = await response.get_json()
        self.assertEqual(data["field_id"], 7)

    async def test_add_field_missing_required_field_returns_400(self):
        body = {k: v for k, v in _VALID_FIELD_BODY.items()
                if k != "field_name"}
        response = await self._post(body)
        self.assertEqual(response.status_code, 400)
        self.mock_service.add_custom_field.assert_not_called()

    async def test_add_field_conflict_returns_409(self):
        self.mock_service.add_custom_field.return_value = _conflict()
        response = await self._post(_VALID_FIELD_BODY)
        self.assertEqual(response.status_code, 409)

    async def test_add_field_bad_request_returns_400(self):
        self.mock_service.add_custom_field.return_value = _bad_request()
        response = await self._post(_VALID_FIELD_BODY)
        self.assertEqual(response.status_code, 400)

    async def test_add_field_internal_error_returns_500(self):
        self.mock_service.add_custom_field.return_value = _internal()
        response = await self._post(_VALID_FIELD_BODY)
        self.assertEqual(response.status_code, 500)


# ------------------------------------------------------------------
# DeleteCustomFieldHandler
# ------------------------------------------------------------------

class TestDeleteCustomFieldHandler(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.mock_service = AsyncMock(spec=TestcaseCustomFieldsService)
        handler = DeleteCustomFieldHandler(_LOGGER, self.mock_service)

        app = Quart(__name__)

        @app.route("/custom_fields/<int:field_id>", methods=["DELETE"])
        async def delete_field(field_id):
            return await handler.delete_custom_field(field_id)

        self.client = app.test_client()

    async def test_delete_field_success_returns_200(self):
        self.mock_service.delete_custom_field.return_value = _ok()
        async with self.client as c:
            response = await c.delete("/custom_fields/1")
        self.assertEqual(response.status_code, 200)

    async def test_delete_field_not_found_returns_404(self):
        self.mock_service.delete_custom_field.return_value = _not_found()
        async with self.client as c:
            response = await c.delete("/custom_fields/99")
        self.assertEqual(response.status_code, 404)

    async def test_delete_system_field_returns_400(self):
        self.mock_service.delete_custom_field.return_value = _bad_request(
            "System custom fields cannot be deleted")
        async with self.client as c:
            response = await c.delete("/custom_fields/1")
        self.assertEqual(response.status_code, 400)

    async def test_delete_field_internal_error_returns_500(self):
        self.mock_service.delete_custom_field.return_value = _internal()
        async with self.client as c:
            response = await c.delete("/custom_fields/1")
        self.assertEqual(response.status_code, 500)


# ------------------------------------------------------------------
# MoveCustomFieldHandler
# ------------------------------------------------------------------

class TestMoveCustomFieldHandler(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.mock_service = AsyncMock(spec=TestcaseCustomFieldsService)
        handler = MoveCustomFieldHandler(_LOGGER, self.mock_service)

        app = Quart(__name__)

        @app.route("/custom_fields/<int:field_id>/move", methods=["PATCH"])
        async def move_field(field_id):
            return await handler.move_custom_field(field_id)

        self.client = app.test_client()

    async def _patch(self, field_id, body):
        async with self.client as c:
            return await c.patch(f"/custom_fields/{field_id}/move", json=body)

    async def test_move_field_success_returns_200(self):
        self.mock_service.move_custom_field.return_value = _ok()
        response = await self._patch(1, {"direction": "up"})
        self.assertEqual(response.status_code, 200)

    async def test_move_field_missing_direction_returns_400(self):
        response = await self._patch(1, {})
        self.assertEqual(response.status_code, 400)
        self.mock_service.move_custom_field.assert_not_called()

    async def test_move_field_not_found_returns_404(self):
        self.mock_service.move_custom_field.return_value = _not_found()
        response = await self._patch(99, {"direction": "up"})
        self.assertEqual(response.status_code, 404)

    async def test_move_field_at_boundary_returns_400(self):
        self.mock_service.move_custom_field.return_value = _bad_request(
            "Custom field is already at the boundary")
        response = await self._patch(1, {"direction": "up"})
        self.assertEqual(response.status_code, 400)

    async def test_move_field_internal_error_returns_500(self):
        self.mock_service.move_custom_field.return_value = _internal()
        response = await self._patch(1, {"direction": "down"})
        self.assertEqual(response.status_code, 500)


# ------------------------------------------------------------------
# UpdateCustomFieldHandler
# ------------------------------------------------------------------

class TestUpdateCustomFieldHandler(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.mock_service = AsyncMock(spec=TestcaseCustomFieldsService)
        handler = UpdateCustomFieldHandler(_LOGGER, self.mock_service)

        app = Quart(__name__)

        @app.route("/custom_fields/<int:field_id>", methods=["PUT"])
        async def update_field(field_id):
            return await handler.update_custom_field(field_id)

        self.client = app.test_client()

    async def _put(self, field_id, body):
        async with self.client as c:
            return await c.put(f"/custom_fields/{field_id}", json=body)

    async def test_update_field_success_returns_200(self):
        self.mock_service.update_custom_field.return_value = _ok()
        response = await self._put(1, _VALID_FIELD_BODY)
        self.assertEqual(response.status_code, 200)

    async def test_update_field_missing_required_field_returns_400(self):
        body = {k: v for k, v in _VALID_FIELD_BODY.items()
                if k != "system_name"}
        response = await self._put(1, body)
        self.assertEqual(response.status_code, 400)
        self.mock_service.update_custom_field.assert_not_called()

    async def test_update_field_not_found_returns_404(self):
        self.mock_service.update_custom_field.return_value = _not_found()
        response = await self._put(99, _VALID_FIELD_BODY)
        self.assertEqual(response.status_code, 404)

    async def test_update_field_conflict_returns_409(self):
        self.mock_service.update_custom_field.return_value = _conflict()
        response = await self._put(1, _VALID_FIELD_BODY)
        self.assertEqual(response.status_code, 409)

    async def test_update_field_bad_request_returns_400(self):
        self.mock_service.update_custom_field.return_value = _bad_request(
            "System custom fields cannot be modified")
        response = await self._put(1, _VALID_FIELD_BODY)
        self.assertEqual(response.status_code, 400)

    async def test_update_field_internal_error_returns_500(self):
        self.mock_service.update_custom_field.return_value = _internal()
        response = await self._put(1, _VALID_FIELD_BODY)
        self.assertEqual(response.status_code, 500)


if __name__ == "__main__":
    unittest.main()
