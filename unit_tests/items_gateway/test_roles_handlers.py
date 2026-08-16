"""
Unit tests for gateway role management route handlers:
  GET    /roles              - ListRolesHandler
  GET    /roles/<id>         - GetRoleHandler
  POST   /roles              - CreateRoleHandler
  PATCH  /roles/<id>         - ModifyRoleHandler
  DELETE /roles/<id>         - DeleteRoleHandler
"""
import json
import unittest
from unittest.mock import AsyncMock, MagicMock
from quart import Quart
from weaver_framework.microservice.api_response import ApiResponse
from items.services.items_gateway.routes.web.roles.list_roles_handler import (
    ListRolesHandler)
from items.services.items_gateway.routes.web.roles.get_role_handler import (
    GetRoleHandler)
from items.services.items_gateway.routes.web.roles.create_role_handler import (
    CreateRoleHandler)
from items.services.items_gateway.routes.web.roles.modify_role_handler import (
    ModifyRoleHandler)
from items.services.items_gateway.routes.web.roles.delete_role_handler import (
    DeleteRoleHandler)

_LOGGER = MagicMock()
_ROLE = {
    "id": 1,
    "name": "Tester",
    "permissions": [
        {"area": "test_cases", "can_read": True, "can_add_modify": True,
         "can_delete": False},
    ],
}


def _config():
    cfg = MagicMock()
    cfg.apis_identity_svc = "http://identity/"
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
# ListRolesHandler
# ---------------------------------------------------------------------------

class TestListRolesHandler(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.mock_rc = AsyncMock()
        handler = ListRolesHandler(_LOGGER, _config(), self.mock_rc)
        app = Quart(__name__)

        @app.route("/roles", methods=["GET"])
        async def route():
            return await handler.list_roles()

        self.client = app.test_client()

    async def _get(self):
        async with self.client as c:
            return await c.get("/roles")

    async def test_success_returns_200_with_body(self):
        self.mock_rc.get.return_value = _ok({"roles": [_ROLE]})
        resp = await self._get()
        self.assertEqual(resp.status_code, 200)
        body = json.loads(await resp.get_data())
        self.assertEqual(body["roles"], [_ROLE])

    async def test_identity_url_is_correct(self):
        self.mock_rc.get.return_value = _ok({"roles": []})
        await self._get()
        self.mock_rc.get.assert_called_once_with("http://identity/roles")

    async def test_identity_error_is_propagated(self):
        self.mock_rc.get.return_value = _err({"error": "unavailable"}, 503)
        resp = await self._get()
        self.assertEqual(resp.status_code, 503)

    async def test_connection_error_returns_500(self):
        self.mock_rc.get.return_value = _conn_err()
        resp = await self._get()
        self.assertEqual(resp.status_code, 500)

    async def test_response_is_json(self):
        self.mock_rc.get.return_value = _ok({"roles": []})
        resp = await self._get()
        self.assertEqual(resp.content_type, "application/json")


# ---------------------------------------------------------------------------
# GetRoleHandler
# ---------------------------------------------------------------------------

class TestGetRoleHandler(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.mock_rc = AsyncMock()
        handler = GetRoleHandler(_LOGGER, _config(), self.mock_rc)
        app = Quart(__name__)

        @app.route("/roles/<int:role_id>", methods=["GET"])
        async def route(role_id: int):
            return await handler.get_role(role_id)

        self.client = app.test_client()

    async def _get(self, role_id=1):
        async with self.client as c:
            return await c.get(f"/roles/{role_id}")

    async def test_success_returns_200_with_role(self):
        self.mock_rc.get.return_value = _ok(_ROLE)
        resp = await self._get(1)
        self.assertEqual(resp.status_code, 200)
        body = json.loads(await resp.get_data())
        self.assertEqual(body, _ROLE)

    async def test_role_id_included_in_url(self):
        self.mock_rc.get.return_value = _ok(_ROLE)
        await self._get(7)
        self.mock_rc.get.assert_called_once_with("http://identity/roles/7")

    async def test_identity_404_is_propagated(self):
        self.mock_rc.get.return_value = _err({"error": "Role not found"}, 404)
        resp = await self._get()
        self.assertEqual(resp.status_code, 404)

    async def test_connection_error_returns_500(self):
        self.mock_rc.get.return_value = _conn_err()
        resp = await self._get()
        self.assertEqual(resp.status_code, 500)

    async def test_response_is_json(self):
        self.mock_rc.get.return_value = _ok(_ROLE)
        resp = await self._get()
        self.assertEqual(resp.content_type, "application/json")


# ---------------------------------------------------------------------------
# CreateRoleHandler
# ---------------------------------------------------------------------------

class TestCreateRoleHandler(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.mock_rc = AsyncMock()
        handler = CreateRoleHandler(_LOGGER, _config(), self.mock_rc)
        app = Quart(__name__)

        @app.route("/roles", methods=["POST"])
        async def route():
            return await handler.create_role()

        self.client = app.test_client()

    async def _post(self, body):
        async with self.client as c:
            return await c.post("/roles", json=body)

    async def test_success_returns_201_with_id(self):
        self.mock_rc.post.return_value = ApiResponse(
            status_code=201, body={"id": 1})
        resp = await self._post({"name": "Tester"})
        self.assertEqual(resp.status_code, 201)
        body = json.loads(await resp.get_data())
        self.assertEqual(body["id"], 1)

    async def test_body_forwarded_to_identity(self):
        self.mock_rc.post.return_value = ApiResponse(
            status_code=201, body={"id": 1})
        role_body = {"name": "Tester", "permissions": [
            {"area": "test_cases", "can_read": True,
             "can_add_modify": False, "can_delete": False}]}
        await self._post(role_body)
        self.mock_rc.post.assert_called_once_with(
            "http://identity/roles", json_data=role_body)

    async def test_identity_conflict_is_propagated(self):
        self.mock_rc.post.return_value = ApiResponse(
            status_code=409, body={"error": "Role name already in use"})
        resp = await self._post({"name": "Tester"})
        self.assertEqual(resp.status_code, 409)

    async def test_identity_invalid_grid_is_propagated(self):
        self.mock_rc.post.return_value = ApiResponse(
            status_code=400, body={"error": "Invalid permission grid"})
        resp = await self._post({"name": "Tester"})
        self.assertEqual(resp.status_code, 400)

    async def test_connection_error_returns_500(self):
        self.mock_rc.post.return_value = _conn_err()
        resp = await self._post({"name": "Tester"})
        self.assertEqual(resp.status_code, 500)

    async def test_invalid_json_body_returns_400_without_calling_identity(self):
        async with self.client as c:
            resp = await c.post("/roles", data="not json",
                                headers={"Content-Type": "application/json"})
        self.assertEqual(resp.status_code, 400)
        self.mock_rc.post.assert_not_called()

    async def test_response_is_json(self):
        self.mock_rc.post.return_value = ApiResponse(
            status_code=201, body={"id": 1})
        resp = await self._post({"name": "Tester"})
        self.assertEqual(resp.content_type, "application/json")


# ---------------------------------------------------------------------------
# ModifyRoleHandler
# ---------------------------------------------------------------------------

class TestModifyRoleHandler(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.mock_rc = AsyncMock()
        handler = ModifyRoleHandler(_LOGGER, _config(), self.mock_rc)
        app = Quart(__name__)

        @app.route("/roles/<int:role_id>", methods=["PATCH"])
        async def route(role_id: int):
            return await handler.modify_role(role_id)

        self.client = app.test_client()

    async def _patch(self, body, role_id=1):
        async with self.client as c:
            return await c.patch(f"/roles/{role_id}", json=body)

    async def test_success_returns_200(self):
        self.mock_rc.patch.return_value = _ok({"status": "ok"})
        resp = await self._patch({"name": "New Name"})
        self.assertEqual(resp.status_code, 200)

    async def test_role_id_included_in_url(self):
        self.mock_rc.patch.return_value = _ok({"status": "ok"})
        await self._patch({"name": "New Name"}, role_id=9)
        self.mock_rc.patch.assert_called_once_with(
            "http://identity/roles/9", json_data={"name": "New Name"})

    async def test_identity_404_is_propagated(self):
        self.mock_rc.patch.return_value = _err({"error": "Role not found"}, 404)
        resp = await self._patch({"name": "New Name"})
        self.assertEqual(resp.status_code, 404)

    async def test_identity_conflict_is_propagated(self):
        self.mock_rc.patch.return_value = _err(
            {"error": "Role name already in use"}, 409)
        resp = await self._patch({"name": "Taken"})
        self.assertEqual(resp.status_code, 409)

    async def test_connection_error_returns_500(self):
        self.mock_rc.patch.return_value = _conn_err()
        resp = await self._patch({"name": "New Name"})
        self.assertEqual(resp.status_code, 500)

    async def test_invalid_json_body_returns_400_without_calling_identity(self):
        async with self.client as c:
            resp = await c.patch("/roles/1", data="not json",
                                 headers={"Content-Type": "application/json"})
        self.assertEqual(resp.status_code, 400)
        self.mock_rc.patch.assert_not_called()

    async def test_response_is_json(self):
        self.mock_rc.patch.return_value = _ok({"status": "ok"})
        resp = await self._patch({"name": "New Name"})
        self.assertEqual(resp.content_type, "application/json")


# ---------------------------------------------------------------------------
# DeleteRoleHandler
# ---------------------------------------------------------------------------

class TestDeleteRoleHandler(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.mock_rc = AsyncMock()
        handler = DeleteRoleHandler(_LOGGER, _config(), self.mock_rc)
        app = Quart(__name__)

        @app.route("/roles/<int:role_id>", methods=["DELETE"])
        async def route(role_id: int):
            return await handler.delete_role(role_id)

        self.client = app.test_client()

    async def _delete(self, role_id=1):
        async with self.client as c:
            return await c.delete(f"/roles/{role_id}")

    async def test_success_returns_200(self):
        self.mock_rc.delete.return_value = _ok({"status": "ok"})
        resp = await self._delete()
        self.assertEqual(resp.status_code, 200)

    async def test_role_id_included_in_url(self):
        self.mock_rc.delete.return_value = _ok({"status": "ok"})
        await self._delete(role_id=13)
        self.mock_rc.delete.assert_called_once_with(
            "http://identity/roles/13")

    async def test_identity_404_is_propagated(self):
        self.mock_rc.delete.return_value = _err({"error": "Role not found"}, 404)
        resp = await self._delete()
        self.assertEqual(resp.status_code, 404)

    async def test_connection_error_returns_500(self):
        self.mock_rc.delete.return_value = _conn_err()
        resp = await self._delete()
        self.assertEqual(resp.status_code, 500)

    async def test_response_is_json(self):
        self.mock_rc.delete.return_value = _ok({"status": "ok"})
        resp = await self._delete()
        self.assertEqual(resp.content_type, "application/json")


if __name__ == "__main__":
    unittest.main()
