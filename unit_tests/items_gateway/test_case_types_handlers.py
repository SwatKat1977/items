"""
Unit tests for gateway test case type route handlers:
  GET   /case_types                        - ListCaseTypesHandler
  GET   /case_types/<id>                   - GetCaseTypeHandler
  POST  /case_types                        - CreateCaseTypeHandler
  PATCH /case_types/<id>                   - ModifyCaseTypeHandler
  POST  /case_types/<id>/set_default       - SetDefaultCaseTypeHandler
"""
import json
import unittest
from unittest.mock import AsyncMock, MagicMock
from quart import Quart
from weaver_framework.microservice.api_response import ApiResponse
from items.services.items_gateway.routes.web.case_types.\
    create_case_type_handler import CreateCaseTypeHandler
from items.services.items_gateway.routes.web.case_types.\
    get_case_type_handler import GetCaseTypeHandler
from items.services.items_gateway.routes.web.case_types.\
    list_case_types_handler import ListCaseTypesHandler
from items.services.items_gateway.routes.web.case_types.\
    modify_case_type_handler import ModifyCaseTypeHandler
from items.services.items_gateway.routes.web.case_types.\
    set_default_case_type_handler import SetDefaultCaseTypeHandler

_LOGGER = MagicMock()
_CASE_TYPE = {"id": 1, "name": "Smoke", "description": "desc",
              "is_default": False}


def _config():
    cfg = MagicMock()
    cfg.apis_cms_svc = "http://cms/"
    return cfg


def _ok(body):
    return ApiResponse(status_code=200, body=body)


def _err(body, status=500):
    return ApiResponse(status_code=status, body=body)


def _conn_err():
    r = ApiResponse(status_code=0, body=None)
    r.exception_msg = "connection refused"
    return r


# ---------------------------------------------------------------------------
# ListCaseTypesHandler
# ---------------------------------------------------------------------------

class TestListCaseTypesHandler(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.mock_rc = AsyncMock()
        handler = ListCaseTypesHandler(_LOGGER, _config(), self.mock_rc)
        app = Quart(__name__)

        @app.route("/case_types", methods=["GET"])
        async def route():
            return await handler.list_case_types()

        self.client = app.test_client()

    async def _get(self):
        async with self.client as c:
            return await c.get("/case_types")

    async def test_success_returns_200_with_body(self):
        self.mock_rc.get.return_value = _ok([_CASE_TYPE])
        resp = await self._get()
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(json.loads(await resp.get_data()), [_CASE_TYPE])

    async def test_cms_url_is_correct(self):
        self.mock_rc.get.return_value = _ok([])
        await self._get()
        self.mock_rc.get.assert_called_once_with("http://cms/case_types")

    async def test_cms_error_is_propagated(self):
        self.mock_rc.get.return_value = _err({"error": "Internal"}, 500)
        resp = await self._get()
        self.assertEqual(resp.status_code, 500)

    async def test_connection_error_returns_500(self):
        self.mock_rc.get.return_value = _conn_err()
        resp = await self._get()
        self.assertEqual(resp.status_code, 500)

    async def test_response_is_json(self):
        self.mock_rc.get.return_value = _ok([])
        resp = await self._get()
        self.assertEqual(resp.content_type, "application/json")


# ---------------------------------------------------------------------------
# GetCaseTypeHandler
# ---------------------------------------------------------------------------

class TestGetCaseTypeHandler(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.mock_rc = AsyncMock()
        handler = GetCaseTypeHandler(_LOGGER, _config(), self.mock_rc)
        app = Quart(__name__)

        @app.route("/case_types/<int:type_id>", methods=["GET"])
        async def route(type_id: int):
            return await handler.get_case_type(type_id)

        self.client = app.test_client()

    async def _get(self, type_id=1):
        async with self.client as c:
            return await c.get(f"/case_types/{type_id}")

    async def test_success_returns_200_with_case_type(self):
        self.mock_rc.get.return_value = _ok(_CASE_TYPE)
        resp = await self._get(1)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(json.loads(await resp.get_data()), _CASE_TYPE)

    async def test_type_id_included_in_url(self):
        self.mock_rc.get.return_value = _ok(_CASE_TYPE)
        await self._get(7)
        self.mock_rc.get.assert_called_once_with("http://cms/case_types/7")

    async def test_cms_404_is_propagated(self):
        self.mock_rc.get.return_value = _err(
            {"error": "Case type not found"}, 404)
        resp = await self._get()
        self.assertEqual(resp.status_code, 404)

    async def test_connection_error_returns_500(self):
        self.mock_rc.get.return_value = _conn_err()
        resp = await self._get()
        self.assertEqual(resp.status_code, 500)

    async def test_response_is_json(self):
        self.mock_rc.get.return_value = _ok(_CASE_TYPE)
        resp = await self._get()
        self.assertEqual(resp.content_type, "application/json")


# ---------------------------------------------------------------------------
# CreateCaseTypeHandler
# ---------------------------------------------------------------------------

class TestCreateCaseTypeHandler(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.mock_rc = AsyncMock()
        handler = CreateCaseTypeHandler(_LOGGER, _config(), self.mock_rc)
        app = Quart(__name__)

        @app.route("/case_types", methods=["POST"])
        async def route():
            return await handler.create_case_type()

        self.client = app.test_client()

    async def _post(self, body):
        async with self.client as c:
            return await c.post("/case_types", json=body)

    async def test_success_returns_200_with_id(self):
        self.mock_rc.post.return_value = _ok({"case_type_id": 16})
        resp = await self._post({"name": "Exploratory", "description": ""})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(json.loads(await resp.get_data()),
                         {"case_type_id": 16})

    async def test_body_forwarded_to_cms(self):
        self.mock_rc.post.return_value = _ok({"case_type_id": 16})
        body = {"name": "Exploratory", "description": "Unscripted"}
        await self._post(body)
        self.mock_rc.post.assert_called_once_with(
            "http://cms/case_types", json_data=body)

    async def test_cms_conflict_is_propagated(self):
        self.mock_rc.post.return_value = _err(
            {"error": "Case type name 'Smoke' already exists"}, 409)
        resp = await self._post({"name": "Smoke", "description": ""})
        self.assertEqual(resp.status_code, 409)

    async def test_cms_validation_error_is_propagated(self):
        self.mock_rc.post.return_value = _err({"error": "bad"}, 400)
        resp = await self._post({"name": "  ", "description": ""})
        self.assertEqual(resp.status_code, 400)

    async def test_connection_error_returns_500(self):
        self.mock_rc.post.return_value = _conn_err()
        resp = await self._post({"name": "A", "description": ""})
        self.assertEqual(resp.status_code, 500)

    async def test_invalid_json_body_returns_400_without_calling_cms(self):
        async with self.client as c:
            resp = await c.post("/case_types", data="not json",
                                headers={"Content-Type": "application/json"})
        self.assertEqual(resp.status_code, 400)
        self.mock_rc.post.assert_not_called()

    async def test_response_is_json(self):
        self.mock_rc.post.return_value = _ok({"case_type_id": 16})
        resp = await self._post({"name": "A", "description": ""})
        self.assertEqual(resp.content_type, "application/json")


# ---------------------------------------------------------------------------
# ModifyCaseTypeHandler
# ---------------------------------------------------------------------------

class TestModifyCaseTypeHandler(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.mock_rc = AsyncMock()
        handler = ModifyCaseTypeHandler(_LOGGER, _config(), self.mock_rc)
        app = Quart(__name__)

        @app.route("/case_types/<int:type_id>", methods=["PATCH"])
        async def route(type_id: int):
            return await handler.modify_case_type(type_id)

        self.client = app.test_client()

    async def _patch(self, body, type_id=1):
        async with self.client as c:
            return await c.patch(f"/case_types/{type_id}", json=body)

    async def test_success_returns_200(self):
        self.mock_rc.patch.return_value = _ok({})
        resp = await self._patch({"name": "New", "description": ""})
        self.assertEqual(resp.status_code, 200)

    async def test_type_id_and_body_forwarded_to_cms(self):
        self.mock_rc.patch.return_value = _ok({})
        body = {"name": "New", "description": "d"}
        await self._patch(body, type_id=9)
        self.mock_rc.patch.assert_called_once_with(
            "http://cms/case_types/9", json_data=body)

    async def test_cms_404_is_propagated(self):
        self.mock_rc.patch.return_value = _err(
            {"error": "Case type not found"}, 404)
        resp = await self._patch({"name": "New", "description": ""})
        self.assertEqual(resp.status_code, 404)

    async def test_cms_conflict_is_propagated(self):
        self.mock_rc.patch.return_value = _err(
            {"error": "Case type name 'Taken' already exists"}, 409)
        resp = await self._patch({"name": "Taken", "description": ""})
        self.assertEqual(resp.status_code, 409)

    async def test_cms_validation_error_is_propagated(self):
        self.mock_rc.patch.return_value = _err({"error": "bad"}, 400)
        resp = await self._patch({"name": "New", "is_default": True})
        self.assertEqual(resp.status_code, 400)

    async def test_connection_error_returns_500(self):
        self.mock_rc.patch.return_value = _conn_err()
        resp = await self._patch({"name": "New", "description": ""})
        self.assertEqual(resp.status_code, 500)

    async def test_invalid_json_body_returns_400_without_calling_cms(self):
        async with self.client as c:
            resp = await c.patch("/case_types/1", data="not json",
                                 headers={"Content-Type": "application/json"})
        self.assertEqual(resp.status_code, 400)
        self.mock_rc.patch.assert_not_called()

    async def test_response_is_json(self):
        self.mock_rc.patch.return_value = _ok({})
        resp = await self._patch({"name": "New", "description": ""})
        self.assertEqual(resp.content_type, "application/json")


# ---------------------------------------------------------------------------
# SetDefaultCaseTypeHandler
# ---------------------------------------------------------------------------

class TestSetDefaultCaseTypeHandler(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.mock_rc = AsyncMock()
        handler = SetDefaultCaseTypeHandler(_LOGGER, _config(), self.mock_rc)
        app = Quart(__name__)

        @app.route("/case_types/<int:type_id>/set_default", methods=["POST"])
        async def route(type_id: int):
            return await handler.set_default_case_type(type_id)

        self.client = app.test_client()

    async def _post(self, type_id=1):
        async with self.client as c:
            return await c.post(f"/case_types/{type_id}/set_default")

    async def test_success_returns_200(self):
        self.mock_rc.post.return_value = _ok({})
        resp = await self._post()
        self.assertEqual(resp.status_code, 200)

    async def test_cms_url_is_correct_and_has_no_body(self):
        self.mock_rc.post.return_value = _ok({})
        await self._post(type_id=4)
        self.mock_rc.post.assert_called_once_with(
            "http://cms/case_types/4/set_default")

    async def test_cms_404_is_propagated(self):
        self.mock_rc.post.return_value = _err(
            {"error": "Case type not found"}, 404)
        resp = await self._post()
        self.assertEqual(resp.status_code, 404)

    async def test_connection_error_returns_500(self):
        self.mock_rc.post.return_value = _conn_err()
        resp = await self._post()
        self.assertEqual(resp.status_code, 500)

    async def test_response_is_json(self):
        self.mock_rc.post.return_value = _ok({})
        resp = await self._post()
        self.assertEqual(resp.content_type, "application/json")


if __name__ == "__main__":
    unittest.main()
