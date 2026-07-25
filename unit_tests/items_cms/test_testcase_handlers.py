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
from items.services.items_cms.routes.testcases.get_testcase_handler import (
    GetTestcaseHandler,
)
from items.services.items_cms.routes.testcases.list_testcases_handler import (
    ListTestcasesHandler,
)
from items.services.items_cms.routes.testcases.add_testcase_handler import (
    AddTestcaseHandler,
)
from items.services.items_cms.routes.testcases.modify_testcase_handler import (
    ModifyTestcaseHandler,
)
from items.services.items_cms.routes.testcases.delete_testcase_handler import (
    DeleteTestcaseHandler,
)
from items.services.items_cms.services.testcase_service import (
    TestcaseService,
    TestcaseResult,
)

_LOGGER = MagicMock()

_VALID_ADD_BODY = {"project_id": 5, "folder_id": None, "name": "Login",
                    "description": "Verify login"}


def _ok(**kwargs):
    return TestcaseResult(success=True, **kwargs)


def _internal():
    return TestcaseResult(success=False, error_msg="err", is_internal=True)


def _not_found(msg="not found"):
    return TestcaseResult(success=False, error_msg=msg, not_found=True)


def _conflict(msg="already exists"):
    return TestcaseResult(success=False, error_msg=msg, is_conflict=True)


def _bad_request(msg="bad"):
    return TestcaseResult(success=False, error_msg=msg)


# ------------------------------------------------------------------
# GetTestcaseHandler
# ------------------------------------------------------------------

class TestGetTestcaseHandler(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.mock_service = AsyncMock(spec=TestcaseService)
        handler = GetTestcaseHandler(_LOGGER, self.mock_service)

        app = Quart(__name__)

        @app.route("/testcases/<int:case_id>")
        async def get_testcase(case_id):
            return await handler.get_testcase(case_id)

        self.client = app.test_client()

    async def test_get_testcase_success_returns_200(self):
        tc = {"id": 10, "folder_id": 1, "name": "Login test",
              "description": "Verify login"}
        self.mock_service.get_testcase.return_value = _ok(data=tc)
        async with self.client as c:
            response = await c.get("/testcases/10")
        self.assertEqual(response.status_code, 200)
        data = await response.get_json()
        self.assertEqual(data["name"], "Login test")

    async def test_get_testcase_not_found_returns_404(self):
        self.mock_service.get_testcase.return_value = _not_found()
        async with self.client as c:
            response = await c.get("/testcases/99")
        self.assertEqual(response.status_code, 404)

    async def test_get_testcase_internal_error_returns_500(self):
        self.mock_service.get_testcase.return_value = _internal()
        async with self.client as c:
            response = await c.get("/testcases/1")
        self.assertEqual(response.status_code, 500)


# ------------------------------------------------------------------
# ListTestcasesHandler
# ------------------------------------------------------------------

class TestListTestcasesHandler(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.mock_service = AsyncMock(spec=TestcaseService)
        handler = ListTestcasesHandler(_LOGGER, self.mock_service)

        app = Quart(__name__)

        @app.route("/testcases")
        async def list_testcases():
            return await handler.list_testcases()

        self.client = app.test_client()

    async def test_list_testcases_missing_project_id_returns_400(self):
        async with self.client as c:
            response = await c.get("/testcases")
        self.assertEqual(response.status_code, 400)
        self.mock_service.list_testcases.assert_not_called()

    async def test_list_testcases_non_integer_project_id_returns_400(self):
        async with self.client as c:
            response = await c.get("/testcases?project_id=abc")
        self.assertEqual(response.status_code, 400)
        self.mock_service.list_testcases.assert_not_called()

    async def test_list_testcases_success_returns_200(self):
        payload = {"folders": [], "test_cases": [{"id": 1, "name": "TC-1"}]}
        self.mock_service.list_testcases.return_value = _ok(data=payload)
        async with self.client as c:
            response = await c.get("/testcases?project_id=3")
        self.assertEqual(response.status_code, 200)
        self.mock_service.list_testcases.assert_called_once_with(3)
        data = await response.get_json()
        self.assertEqual(data["test_cases"][0]["name"], "TC-1")

    async def test_list_testcases_service_error_returns_500(self):
        self.mock_service.list_testcases.return_value = _internal()
        async with self.client as c:
            response = await c.get("/testcases?project_id=3")
        self.assertEqual(response.status_code, 500)

    async def test_list_testcases_invalid_project_id_returns_404(self):
        self.mock_service.list_testcases.return_value = _not_found()
        async with self.client as c:
            response = await c.get("/testcases?project_id=3")
        self.assertEqual(response.status_code, 404)


# ------------------------------------------------------------------
# AddTestcaseHandler
# ------------------------------------------------------------------

class TestAddTestcaseHandler(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.mock_service = AsyncMock(spec=TestcaseService)
        handler = AddTestcaseHandler(_LOGGER, self.mock_service)

        app = Quart(__name__)

        @app.route("/testcases", methods=["POST"])
        async def add_testcase():
            return await handler.add_testcase()

        self.client = app.test_client()

    async def _post(self, body):
        async with self.client as c:
            return await c.post("/testcases", json=body)

    async def test_success_returns_200(self):
        self.mock_service.create_testcase.return_value = _ok(data=7)
        response = await self._post(_VALID_ADD_BODY)
        self.assertEqual(response.status_code, 200)
        data = await response.get_json()
        self.assertEqual(data["testcase_id"], 7)
        self.mock_service.create_testcase.assert_called_once_with(
            project_id=5, folder_id=None, name="Login",
            description="Verify login")

    async def test_missing_field_returns_400(self):
        response = await self._post({"project_id": 5, "name": "Login"})
        self.assertEqual(response.status_code, 400)
        self.mock_service.create_testcase.assert_not_called()

    async def test_project_not_found_returns_404(self):
        self.mock_service.create_testcase.return_value = _not_found(
            "Project id is invalid")
        response = await self._post(_VALID_ADD_BODY)
        self.assertEqual(response.status_code, 404)

    async def test_conflict_returns_409(self):
        self.mock_service.create_testcase.return_value = _conflict()
        response = await self._post(_VALID_ADD_BODY)
        self.assertEqual(response.status_code, 409)

    async def test_bad_request_returns_400(self):
        self.mock_service.create_testcase.return_value = _bad_request()
        response = await self._post(_VALID_ADD_BODY)
        self.assertEqual(response.status_code, 400)

    async def test_internal_error_returns_500(self):
        self.mock_service.create_testcase.return_value = _internal()
        response = await self._post(_VALID_ADD_BODY)
        self.assertEqual(response.status_code, 500)


# ------------------------------------------------------------------
# ModifyTestcaseHandler
# ------------------------------------------------------------------

class TestModifyTestcaseHandler(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.mock_service = AsyncMock(spec=TestcaseService)
        handler = ModifyTestcaseHandler(_LOGGER, self.mock_service)

        app = Quart(__name__)

        @app.route("/testcases/<int:case_id>", methods=["PATCH"])
        async def modify_testcase(case_id):
            return await handler.modify_testcase(case_id)

        self.client = app.test_client()

    async def _patch(self, case_id, body):
        async with self.client as c:
            return await c.patch(f"/testcases/{case_id}", json=body)

    async def test_success_returns_200(self):
        self.mock_service.update_testcase.return_value = _ok()
        response = await self._patch(
            1, {"name": "New", "description": "New desc"})
        self.assertEqual(response.status_code, 200)
        data = await response.get_json()
        self.assertEqual(data["status"], 1)
        self.mock_service.update_testcase.assert_called_once_with(
            case_id=1, name="New", description="New desc")

    async def test_missing_field_returns_400(self):
        response = await self._patch(1, {"name": "New"})
        self.assertEqual(response.status_code, 400)
        self.mock_service.update_testcase.assert_not_called()

    async def test_not_found_returns_404(self):
        self.mock_service.update_testcase.return_value = _not_found()
        response = await self._patch(
            99, {"name": "New", "description": ""})
        self.assertEqual(response.status_code, 404)

    async def test_conflict_returns_409(self):
        self.mock_service.update_testcase.return_value = _conflict()
        response = await self._patch(
            1, {"name": "New", "description": ""})
        self.assertEqual(response.status_code, 409)

    async def test_bad_request_returns_400(self):
        self.mock_service.update_testcase.return_value = _bad_request()
        response = await self._patch(
            1, {"name": "New", "description": ""})
        self.assertEqual(response.status_code, 400)

    async def test_internal_error_returns_500(self):
        self.mock_service.update_testcase.return_value = _internal()
        response = await self._patch(
            1, {"name": "New", "description": ""})
        self.assertEqual(response.status_code, 500)


# ------------------------------------------------------------------
# DeleteTestcaseHandler
# ------------------------------------------------------------------

class TestDeleteTestcaseHandler(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.mock_service = AsyncMock(spec=TestcaseService)
        handler = DeleteTestcaseHandler(_LOGGER, self.mock_service)

        app = Quart(__name__)

        @app.route("/testcases/<int:case_id>", methods=["DELETE"])
        async def delete_testcase(case_id):
            return await handler.delete_testcase(case_id)

        self.client = app.test_client()

    async def test_success_returns_200(self):
        self.mock_service.delete_testcase.return_value = _ok()
        async with self.client as c:
            response = await c.delete("/testcases/1")
        self.assertEqual(response.status_code, 200)

    async def test_not_found_returns_404(self):
        self.mock_service.delete_testcase.return_value = _not_found()
        async with self.client as c:
            response = await c.delete("/testcases/99")
        self.assertEqual(response.status_code, 404)

    async def test_internal_error_returns_500(self):
        self.mock_service.delete_testcase.return_value = _internal()
        async with self.client as c:
            response = await c.delete("/testcases/1")
        self.assertEqual(response.status_code, 500)


if __name__ == "__main__":
    unittest.main()
