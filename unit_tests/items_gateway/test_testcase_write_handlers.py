"""
Unit tests for the gateway test case write route handlers:
  POST   /<project_id>/testcases           - CreateTestcaseHandler
  PATCH  /testcases/<id>?project_id=       - ModifyTestcaseHandler
  DELETE /testcases/<id>?project_id=       - DeleteTestcaseHandler
"""
import json
import unittest
from unittest.mock import AsyncMock, MagicMock
from quart import Quart
from weaver_framework.microservice.api_response import ApiResponse
from items.services.items_gateway.routes.web.testcases.\
    create_testcase_handler import CreateTestcaseHandler
from items.services.items_gateway.routes.web.testcases.\
    delete_testcase_handler import DeleteTestcaseHandler
from items.services.items_gateway.routes.web.testcases.\
    modify_testcase_handler import ModifyTestcaseHandler

_LOGGER = MagicMock()
_CREATE_BODY = {"folder_id": None, "name": "Login", "description": "d"}
_MODIFY_BODY = {"name": "Renamed", "description": "d"}


def _config():
    cfg = MagicMock()
    cfg.apis_cms_svc = "http://cms/"
    return cfg


def _ok(body):
    return ApiResponse(status_code=200, body=body)


def _err(body, status):
    return ApiResponse(status_code=status, body=body)


def _conn_err():
    r = ApiResponse(status_code=0, body=None)
    r.exception_msg = "connection refused"
    return r


# ---------------------------------------------------------------------------
# CreateTestcaseHandler
# ---------------------------------------------------------------------------

class TestCreateTestcaseHandler(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.mock_rc = AsyncMock()
        handler = CreateTestcaseHandler(_LOGGER, _config(), self.mock_rc)
        app = Quart(__name__)

        @app.route("/<int:project_id>/testcases", methods=["POST"])
        async def route(project_id: int):
            return await handler.create_testcase(project_id)

        self.client = app.test_client()

    async def _post(self, body, project_id=5):
        async with self.client as c:
            return await c.post(f"/{project_id}/testcases", json=body)

    async def test_success_returns_200_with_id(self):
        self.mock_rc.post.return_value = _ok({"testcase_id": 7})
        resp = await self._post(_CREATE_BODY)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(json.loads(await resp.get_data()),
                         {"testcase_id": 7})

    async def test_body_and_path_project_forwarded_to_cms(self):
        self.mock_rc.post.return_value = _ok({"testcase_id": 7})
        await self._post({**_CREATE_BODY, "case_type_id": 3}, project_id=5)
        self.mock_rc.post.assert_called_once_with(
            "http://cms/testcases",
            json_data={"folder_id": None, "name": "Login",
                       "description": "d", "case_type_id": 3,
                       "project_id": 5})

    async def test_project_id_in_the_body_is_rejected(self):
        """The project comes from the URL only. Any project_id in the body
        - matching, different, existing or not, whatever its type - is
        refused and the CMS is never called."""
        for body_project in (5, 99, 20, 0, "5", "abc", None):
            with self.subTest(body_project=body_project):
                resp = await self._post(
                    {**_CREATE_BODY, "project_id": body_project},
                    project_id=5)
                self.assertEqual(resp.status_code, 400)
                body = json.loads(await resp.get_data())
                self.assertIn("project_id must not be in the request body",
                              body["error"])
        self.mock_rc.post.assert_not_called()

    async def test_path_project_is_what_the_cms_receives(self):
        self.mock_rc.post.return_value = _ok({"testcase_id": 7})
        await self._post(_CREATE_BODY, project_id=8)
        sent = self.mock_rc.post.call_args.kwargs["json_data"]
        self.assertEqual(sent["project_id"], 8)

    async def test_cms_errors_are_propagated(self):
        for status in (400, 404, 409, 500):
            with self.subTest(status=status):
                self.mock_rc.post.return_value = _err({"error": "x"}, status)
                resp = await self._post(_CREATE_BODY)
                self.assertEqual(resp.status_code, status)

    async def test_connection_error_returns_500(self):
        self.mock_rc.post.return_value = _conn_err()
        resp = await self._post(_CREATE_BODY)
        self.assertEqual(resp.status_code, 500)

    async def test_invalid_json_returns_400_without_calling_cms(self):
        async with self.client as c:
            resp = await c.post("/5/testcases", data="not json",
                                headers={"Content-Type": "application/json"})
        self.assertEqual(resp.status_code, 400)
        self.mock_rc.post.assert_not_called()

    async def test_non_object_json_returns_400_without_calling_cms(self):
        resp = await self._post([1, 2, 3])
        self.assertEqual(resp.status_code, 400)
        self.mock_rc.post.assert_not_called()

    async def test_response_is_json(self):
        self.mock_rc.post.return_value = _ok({"testcase_id": 7})
        resp = await self._post(_CREATE_BODY)
        self.assertEqual(resp.content_type, "application/json")


# ---------------------------------------------------------------------------
# ModifyTestcaseHandler
# ---------------------------------------------------------------------------

class TestModifyTestcaseHandler(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.mock_rc = AsyncMock()
        handler = ModifyTestcaseHandler(_LOGGER, _config(), self.mock_rc)
        app = Quart(__name__)

        @app.route("/testcases/<int:case_id>", methods=["PATCH"])
        async def route(case_id: int):
            return await handler.modify_testcase(case_id)

        self.client = app.test_client()

    async def _patch(self, body, case_id=3, query="?project_id=5"):
        async with self.client as c:
            return await c.patch(f"/testcases/{case_id}{query}", json=body)

    async def test_success_returns_200(self):
        self.mock_rc.patch.return_value = _ok({"status": 1})
        resp = await self._patch(_MODIFY_BODY)
        self.assertEqual(resp.status_code, 200)

    async def test_url_carries_the_project_and_body_is_forwarded(self):
        self.mock_rc.patch.return_value = _ok({"status": 1})
        body = {**_MODIFY_BODY, "case_type_id": 3}
        await self._patch(body, case_id=9, query="?project_id=7")
        self.mock_rc.patch.assert_called_once_with(
            "http://cms/testcases/9?project_id=7", json_data=body)

    async def test_missing_project_id_returns_400_without_calling_cms(self):
        resp = await self._patch(_MODIFY_BODY, query="")
        self.assertEqual(resp.status_code, 400)
        body = json.loads(await resp.get_data())
        self.assertIn("project_id", body["error"])
        self.mock_rc.patch.assert_not_called()

    async def test_non_integer_project_id_returns_400(self):
        resp = await self._patch(_MODIFY_BODY, query="?project_id=abc")
        self.assertEqual(resp.status_code, 400)
        self.mock_rc.patch.assert_not_called()

    async def test_invalid_json_returns_400_without_calling_cms(self):
        async with self.client as c:
            resp = await c.patch("/testcases/3?project_id=5", data="not json",
                                 headers={"Content-Type": "application/json"})
        self.assertEqual(resp.status_code, 400)
        self.mock_rc.patch.assert_not_called()

    async def test_non_object_json_returns_400_without_calling_cms(self):
        resp = await self._patch([1, 2])
        self.assertEqual(resp.status_code, 400)
        self.mock_rc.patch.assert_not_called()

    async def test_cms_errors_are_propagated(self):
        for status in (400, 404, 409, 500):
            with self.subTest(status=status):
                self.mock_rc.patch.return_value = _err({"error": "x"}, status)
                resp = await self._patch(_MODIFY_BODY)
                self.assertEqual(resp.status_code, status)

    async def test_connection_error_returns_500(self):
        self.mock_rc.patch.return_value = _conn_err()
        resp = await self._patch(_MODIFY_BODY)
        self.assertEqual(resp.status_code, 500)

    async def test_response_is_json(self):
        self.mock_rc.patch.return_value = _ok({"status": 1})
        resp = await self._patch(_MODIFY_BODY)
        self.assertEqual(resp.content_type, "application/json")


# ---------------------------------------------------------------------------
# DeleteTestcaseHandler
# ---------------------------------------------------------------------------

class TestDeleteTestcaseHandler(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.mock_rc = AsyncMock()
        handler = DeleteTestcaseHandler(_LOGGER, _config(), self.mock_rc)
        app = Quart(__name__)

        @app.route("/testcases/<int:case_id>", methods=["DELETE"])
        async def route(case_id: int):
            return await handler.delete_testcase(case_id)

        self.client = app.test_client()

    async def _delete(self, case_id=3, query="?project_id=5"):
        async with self.client as c:
            return await c.delete(f"/testcases/{case_id}{query}")

    async def test_success_returns_200(self):
        self.mock_rc.delete.return_value = _ok({})
        resp = await self._delete()
        self.assertEqual(resp.status_code, 200)

    async def test_url_carries_the_project(self):
        self.mock_rc.delete.return_value = _ok({})
        await self._delete(case_id=9, query="?project_id=7")
        self.mock_rc.delete.assert_called_once_with(
            "http://cms/testcases/9?project_id=7")

    async def test_missing_project_id_returns_400_without_calling_cms(self):
        resp = await self._delete(query="")
        self.assertEqual(resp.status_code, 400)
        self.mock_rc.delete.assert_not_called()

    async def test_non_integer_project_id_returns_400(self):
        resp = await self._delete(query="?project_id=abc")
        self.assertEqual(resp.status_code, 400)
        body = json.loads(await resp.get_data())
        self.assertEqual(body["error"], "project_id must be an integer")
        self.mock_rc.delete.assert_not_called()

    async def test_cms_404_is_propagated(self):
        self.mock_rc.delete.return_value = _err(
            {"error": "Test case not found"}, 404)
        resp = await self._delete()
        self.assertEqual(resp.status_code, 404)

    async def test_connection_error_returns_500(self):
        self.mock_rc.delete.return_value = _conn_err()
        resp = await self._delete()
        self.assertEqual(resp.status_code, 500)

    async def test_response_is_json(self):
        self.mock_rc.delete.return_value = _ok({})
        resp = await self._delete()
        self.assertEqual(resp.content_type, "application/json")


if __name__ == "__main__":
    unittest.main()
