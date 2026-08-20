"""
Unit tests for gateway project-membership route handlers:
  GET    /users/<uuid>/projects              - ListUserProjectsHandler
  POST   /users/<uuid>/projects              - AddUserProjectHandler
  PATCH  /users/<uuid>/projects/<project_id> - ModifyUserProjectHandler
  DELETE /users/<uuid>/projects/<project_id> - RemoveUserProjectHandler
"""
import json
import unittest
from unittest.mock import AsyncMock, MagicMock
from quart import Quart
from weaver_framework.microservice.api_response import ApiResponse
from items.services.items_gateway.routes.web.users.list_user_projects_handler import (
    ListUserProjectsHandler)
from items.services.items_gateway.routes.web.users.add_user_project_handler import (
    AddUserProjectHandler)
from items.services.items_gateway.routes.web.users.modify_user_project_handler import (
    ModifyUserProjectHandler)
from items.services.items_gateway.routes.web.users.remove_user_project_handler import (
    RemoveUserProjectHandler)

_LOGGER = MagicMock()
_UUID = "550e8400-e29b-41d4-a716-446655440000"
_MEMBERSHIP = {"project_id": 5, "role_id": 2, "role_name": "Tester"}


def _config():
    cfg = MagicMock()
    cfg.apis_identity_svc = "http://identity/"
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
# ListUserProjectsHandler
# ---------------------------------------------------------------------------

class TestListUserProjectsHandler(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.mock_rc = AsyncMock()
        handler = ListUserProjectsHandler(_LOGGER, _config(), self.mock_rc)
        app = Quart(__name__)

        @app.route("/users/<string:user_id>/projects", methods=["GET"])
        async def route(user_id: str):
            return await handler.list_user_projects(user_id)

        self.client = app.test_client()

    async def _get(self, user_id=_UUID):
        async with self.client as c:
            return await c.get(f"/users/{user_id}/projects")

    async def test_success_returns_200_with_memberships(self):
        self.mock_rc.get.return_value = _ok({"memberships": [_MEMBERSHIP]})
        resp = await self._get()
        self.assertEqual(resp.status_code, 200)
        body = json.loads(await resp.get_data())
        self.assertEqual(body["memberships"], [_MEMBERSHIP])

    async def test_identity_url_is_correct(self):
        self.mock_rc.get.return_value = _ok({"memberships": []})
        await self._get()
        self.mock_rc.get.assert_called_once_with(
            f"http://identity/users/{_UUID}/projects")

    async def test_identity_404_is_propagated(self):
        self.mock_rc.get.return_value = _err({"error": "User not found"}, 404)
        resp = await self._get()
        self.assertEqual(resp.status_code, 404)

    async def test_connection_error_returns_500(self):
        self.mock_rc.get.return_value = _conn_err()
        resp = await self._get()
        self.assertEqual(resp.status_code, 500)

    async def test_response_is_json(self):
        self.mock_rc.get.return_value = _ok({"memberships": []})
        resp = await self._get()
        self.assertEqual(resp.content_type, "application/json")


# ---------------------------------------------------------------------------
# AddUserProjectHandler
# ---------------------------------------------------------------------------

class TestAddUserProjectHandler(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.mock_rc = AsyncMock()
        self.mock_sessions = AsyncMock()
        handler = AddUserProjectHandler(
            _LOGGER, _config(), self.mock_rc, self.mock_sessions)
        app = Quart(__name__)

        @app.route("/users/<string:user_id>/projects", methods=["POST"])
        async def route(user_id: str):
            return await handler.add_user_project(user_id)

        self.client = app.test_client()

    async def _post(self, body, user_id=_UUID):
        async with self.client as c:
            return await c.post(f"/users/{user_id}/projects", json=body)

    async def test_success_returns_201(self):
        self.mock_rc.get.return_value = _ok({"id": 5, "name": "Alpha"})
        self.mock_rc.post.return_value = ApiResponse(
            status_code=201, body={"status": "ok"})
        resp = await self._post({"project_id": 5, "role_id": 2})
        self.assertEqual(resp.status_code, 201)

    async def test_cms_checked_before_identity_when_project_id_present(self):
        self.mock_rc.get.return_value = _ok({"id": 5, "name": "Alpha"})
        self.mock_rc.post.return_value = ApiResponse(
            status_code=201, body={"status": "ok"})
        await self._post({"project_id": 5})
        self.mock_rc.get.assert_called_once_with("http://cms/projects/5")
        self.mock_rc.post.assert_called_once()

    async def test_cms_project_not_found_returns_404_without_calling_identity(self):
        self.mock_rc.get.return_value = _err({"error": "not found"}, 404)
        resp = await self._post({"project_id": 999999})
        self.assertEqual(resp.status_code, 404)
        self.mock_rc.post.assert_not_called()

    async def test_cms_connection_error_returns_500_without_calling_identity(self):
        self.mock_rc.get.return_value = _conn_err()
        resp = await self._post({"project_id": 5})
        self.assertEqual(resp.status_code, 500)
        self.mock_rc.post.assert_not_called()

    async def test_cms_unexpected_status_returns_500_without_calling_identity(self):
        self.mock_rc.get.return_value = _err({"error": "boom"}, 503)
        resp = await self._post({"project_id": 5})
        self.assertEqual(resp.status_code, 500)
        self.mock_rc.post.assert_not_called()

    async def test_missing_project_id_skips_cms_check(self):
        """Identity's own schema validation rejects a missing project_id -
        the gateway has nothing to check against CMS without one."""
        self.mock_rc.post.return_value = ApiResponse(
            status_code=400, body={"error": "project_id required"})
        resp = await self._post({"role_id": 2})
        self.assertEqual(resp.status_code, 400)
        self.mock_rc.get.assert_not_called()

    async def test_non_integer_project_id_skips_cms_check(self):
        """Malformed project_id is identity's schema validation's job, not
        the gateway's - the gateway just can't check it against CMS."""
        self.mock_rc.post.return_value = ApiResponse(
            status_code=400, body={"error": "project_id must be an integer"})
        resp = await self._post({"project_id": "not-a-number"})
        self.assertEqual(resp.status_code, 400)
        self.mock_rc.get.assert_not_called()

    async def test_identity_user_not_found_is_propagated(self):
        self.mock_rc.get.return_value = _ok({"id": 5, "name": "Alpha"})
        self.mock_rc.post.return_value = _err({"error": "User not found"}, 404)
        resp = await self._post({"project_id": 5})
        self.assertEqual(resp.status_code, 404)

    async def test_identity_conflict_is_propagated(self):
        self.mock_rc.get.return_value = _ok({"id": 5, "name": "Alpha"})
        self.mock_rc.post.return_value = _err(
            {"error": "User is already a member of this project"}, 409)
        resp = await self._post({"project_id": 5})
        self.assertEqual(resp.status_code, 409)

    async def test_identity_connection_error_returns_500(self):
        self.mock_rc.get.return_value = _ok({"id": 5, "name": "Alpha"})
        self.mock_rc.post.return_value = _conn_err()
        resp = await self._post({"project_id": 5})
        self.assertEqual(resp.status_code, 500)

    async def test_invalid_json_body_returns_400_without_calling_anything(self):
        async with self.client as c:
            resp = await c.post(f"/users/{_UUID}/projects", data="not json",
                                headers={"Content-Type": "application/json"})
        self.assertEqual(resp.status_code, 400)
        self.mock_rc.get.assert_not_called()
        self.mock_rc.post.assert_not_called()

    async def test_body_forwarded_to_identity_unchanged(self):
        self.mock_rc.get.return_value = _ok({"id": 5, "name": "Alpha"})
        self.mock_rc.post.return_value = ApiResponse(
            status_code=201, body={"status": "ok"})
        body = {"project_id": 5, "role_id": 2}
        await self._post(body)
        self.mock_rc.post.assert_called_once_with(
            f"http://identity/users/{_UUID}/projects", json_data=body)

    async def test_response_is_json(self):
        self.mock_rc.get.return_value = _ok({"id": 5, "name": "Alpha"})
        self.mock_rc.post.return_value = ApiResponse(
            status_code=201, body={"status": "ok"})
        resp = await self._post({"project_id": 5})
        self.assertEqual(resp.content_type, "application/json")

    async def test_success_live_patches_the_session(self):
        self.mock_rc.get.return_value = _ok({"id": 5, "name": "Alpha"})
        self.mock_rc.post.return_value = ApiResponse(
            status_code=201, body={"status": "ok"})
        await self._post({"project_id": 5, "role_id": 2})
        self.mock_sessions.add_project_id_for_user.assert_called_once_with(
            _UUID, 5)

    async def test_failure_does_not_patch_the_session(self):
        self.mock_rc.get.return_value = _ok({"id": 5, "name": "Alpha"})
        self.mock_rc.post.return_value = _err(
            {"error": "User is already a member of this project"}, 409)
        await self._post({"project_id": 5})
        self.mock_sessions.add_project_id_for_user.assert_not_called()


# ---------------------------------------------------------------------------
# ModifyUserProjectHandler
# ---------------------------------------------------------------------------

class TestModifyUserProjectHandler(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.mock_rc = AsyncMock()
        handler = ModifyUserProjectHandler(_LOGGER, _config(), self.mock_rc)
        app = Quart(__name__)

        @app.route("/users/<string:user_id>/projects/<int:project_id>",
                  methods=["PATCH"])
        async def route(user_id: str, project_id: int):
            return await handler.modify_user_project(user_id, project_id)

        self.client = app.test_client()

    async def _patch(self, body, user_id=_UUID, project_id=5):
        async with self.client as c:
            return await c.patch(
                f"/users/{user_id}/projects/{project_id}", json=body)

    async def test_success_returns_200(self):
        self.mock_rc.patch.return_value = _ok({"status": "ok"})
        resp = await self._patch({"role_id": 3})
        self.assertEqual(resp.status_code, 200)

    async def test_does_not_call_cms(self):
        """No project-existence check here - only AddUserProjectHandler
        does that, on creation."""
        self.mock_rc.patch.return_value = _ok({"status": "ok"})
        await self._patch({"role_id": 3})
        self.mock_rc.get.assert_not_called()

    async def test_url_includes_user_and_project_id(self):
        self.mock_rc.patch.return_value = _ok({"status": "ok"})
        await self._patch({"role_id": 3}, user_id=_UUID, project_id=9)
        self.mock_rc.patch.assert_called_once_with(
            f"http://identity/users/{_UUID}/projects/9",
            json_data={"role_id": 3})

    async def test_role_id_null_is_forwarded_to_clear_role(self):
        self.mock_rc.patch.return_value = _ok({"status": "ok"})
        await self._patch({"role_id": None})
        self.mock_rc.patch.assert_called_once_with(
            f"http://identity/users/{_UUID}/projects/5",
            json_data={"role_id": None})

    async def test_identity_role_not_found_is_propagated(self):
        self.mock_rc.patch.return_value = _err(
            {"error": "No role exists with that id"}, 400)
        resp = await self._patch({"role_id": 999})
        self.assertEqual(resp.status_code, 400)

    async def test_identity_membership_not_found_is_propagated(self):
        self.mock_rc.patch.return_value = _err(
            {"error": "User is not a member of this project"}, 404)
        resp = await self._patch({"role_id": 3})
        self.assertEqual(resp.status_code, 404)

    async def test_connection_error_returns_500(self):
        self.mock_rc.patch.return_value = _conn_err()
        resp = await self._patch({"role_id": 3})
        self.assertEqual(resp.status_code, 500)

    async def test_invalid_json_body_returns_400_without_calling_identity(self):
        async with self.client as c:
            resp = await c.patch(f"/users/{_UUID}/projects/5", data="not json",
                                 headers={"Content-Type": "application/json"})
        self.assertEqual(resp.status_code, 400)
        self.mock_rc.patch.assert_not_called()

    async def test_response_is_json(self):
        self.mock_rc.patch.return_value = _ok({"status": "ok"})
        resp = await self._patch({"role_id": 3})
        self.assertEqual(resp.content_type, "application/json")


# ---------------------------------------------------------------------------
# RemoveUserProjectHandler
# ---------------------------------------------------------------------------

class TestRemoveUserProjectHandler(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.mock_rc = AsyncMock()
        self.mock_sessions = AsyncMock()
        handler = RemoveUserProjectHandler(
            _LOGGER, _config(), self.mock_rc, self.mock_sessions)
        app = Quart(__name__)

        @app.route("/users/<string:user_id>/projects/<int:project_id>",
                  methods=["DELETE"])
        async def route(user_id: str, project_id: int):
            return await handler.remove_user_project(user_id, project_id)

        self.client = app.test_client()

    async def _delete(self, user_id=_UUID, project_id=5):
        async with self.client as c:
            return await c.delete(f"/users/{user_id}/projects/{project_id}")

    async def test_success_returns_200(self):
        self.mock_rc.delete.return_value = _ok({"status": "ok"})
        resp = await self._delete()
        self.assertEqual(resp.status_code, 200)

    async def test_url_includes_user_and_project_id(self):
        self.mock_rc.delete.return_value = _ok({"status": "ok"})
        await self._delete(user_id=_UUID, project_id=9)
        self.mock_rc.delete.assert_called_once_with(
            f"http://identity/users/{_UUID}/projects/9")

    async def test_identity_404_is_propagated(self):
        self.mock_rc.delete.return_value = _err(
            {"error": "User is not a member of this project"}, 404)
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

    async def test_success_live_patches_the_session(self):
        self.mock_rc.delete.return_value = _ok({"status": "ok"})
        await self._delete(user_id=_UUID, project_id=9)
        self.mock_sessions.remove_project_id_for_user.assert_called_once_with(
            _UUID, 9)

    async def test_failure_does_not_patch_the_session(self):
        self.mock_rc.delete.return_value = _err(
            {"error": "User is not a member of this project"}, 404)
        await self._delete()
        self.mock_sessions.remove_project_id_for_user.assert_not_called()


if __name__ == "__main__":
    unittest.main()
