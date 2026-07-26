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
from items.services.items_cms.routes.testcase_field_values.get_testcase_field_values_handler import (
    GetTestcaseFieldValuesHandler,
)
from items.services.items_cms.routes.testcase_field_values.set_testcase_field_values_handler import (
    SetTestcaseFieldValuesHandler,
)
from items.services.items_cms.services.testcase_field_values_service import (
    TestcaseFieldValuesService,
    TestcaseFieldValuesResult,
)

_LOGGER = MagicMock()


def _ok(**kwargs):
    return TestcaseFieldValuesResult(success=True, **kwargs)


def _internal():
    return TestcaseFieldValuesResult(
        success=False, error_msg="err", is_internal=True)


def _not_found():
    return TestcaseFieldValuesResult(
        success=False, error_msg="not found", not_found=True)


def _bad_request(msg="bad"):
    return TestcaseFieldValuesResult(success=False, error_msg=msg)


# ------------------------------------------------------------------
# GetTestcaseFieldValuesHandler
# ------------------------------------------------------------------

class TestGetTestcaseFieldValuesHandler(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.mock_service = AsyncMock(spec=TestcaseFieldValuesService)
        handler = GetTestcaseFieldValuesHandler(_LOGGER, self.mock_service)

        app = Quart(__name__)

        @app.route("/testcases/<int:case_id>/custom_fields")
        async def get_field_values(case_id):
            return await handler.get_field_values(case_id)

        self.client = app.test_client()

    async def test_success_returns_200(self):
        payload = [{"field_id": 1, "field_name": "Priority", "value": "High"}]
        self.mock_service.get_field_values.return_value = _ok(data=payload)
        async with self.client as c:
            response = await c.get("/testcases/1/custom_fields")
        self.assertEqual(response.status_code, 200)
        data = await response.get_json()
        self.assertEqual(data[0]["field_name"], "Priority")

    async def test_not_found_returns_404(self):
        self.mock_service.get_field_values.return_value = _not_found()
        async with self.client as c:
            response = await c.get("/testcases/99/custom_fields")
        self.assertEqual(response.status_code, 404)

    async def test_internal_error_returns_500(self):
        self.mock_service.get_field_values.return_value = _internal()
        async with self.client as c:
            response = await c.get("/testcases/1/custom_fields")
        self.assertEqual(response.status_code, 500)


# ------------------------------------------------------------------
# SetTestcaseFieldValuesHandler
# ------------------------------------------------------------------

class TestSetTestcaseFieldValuesHandler(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.mock_service = AsyncMock(spec=TestcaseFieldValuesService)
        handler = SetTestcaseFieldValuesHandler(_LOGGER, self.mock_service)

        app = Quart(__name__)

        @app.route("/testcases/<int:case_id>/custom_fields", methods=["PUT"])
        async def set_field_values(case_id):
            return await handler.set_field_values(case_id)

        self.client = app.test_client()

    async def _put(self, case_id, body):
        async with self.client as c:
            return await c.put(f"/testcases/{case_id}/custom_fields", json=body)

    async def test_success_returns_200(self):
        self.mock_service.set_field_values.return_value = _ok()
        response = await self._put(1, {"values": {"1": "High"}})
        self.assertEqual(response.status_code, 200)
        data = await response.get_json()
        self.assertEqual(data["status"], 1)
        self.mock_service.set_field_values.assert_called_once_with(
            1, {1: "High"})

    async def test_missing_values_key_returns_400(self):
        response = await self._put(1, {})
        self.assertEqual(response.status_code, 400)
        self.mock_service.set_field_values.assert_not_called()

    async def test_non_numeric_field_id_key_returns_400(self):
        response = await self._put(1, {"values": {"not-a-number": "High"}})
        self.assertEqual(response.status_code, 400)
        self.mock_service.set_field_values.assert_not_called()

    async def test_not_found_returns_404(self):
        self.mock_service.set_field_values.return_value = _not_found()
        response = await self._put(99, {"values": {"1": "High"}})
        self.assertEqual(response.status_code, 404)

    async def test_bad_request_returns_400(self):
        self.mock_service.set_field_values.return_value = _bad_request()
        response = await self._put(1, {"values": {"1": "High"}})
        self.assertEqual(response.status_code, 400)

    async def test_internal_error_returns_500(self):
        self.mock_service.set_field_values.return_value = _internal()
        response = await self._put(1, {"values": {"1": "High"}})
        self.assertEqual(response.status_code, 500)


if __name__ == "__main__":
    unittest.main()
