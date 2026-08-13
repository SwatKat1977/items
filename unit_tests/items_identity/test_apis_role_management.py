"""
Handler-level tests for the role management API endpoints:
  GET    /roles           - ListRolesHandler
  GET    /roles/<role_id>  - GetRoleHandler
  POST   /roles           - CreateRoleHandler
  PATCH  /roles/<role_id>  - ModifyRoleHandler
  DELETE /roles/<role_id>  - DeleteRoleHandler
"""
import unittest
import json
import logging
from http import HTTPStatus
from unittest.mock import patch, MagicMock, AsyncMock
from quart import Response
from routes.roles.list_roles_handler import ListRolesHandler
from routes.roles.get_role_handler import GetRoleHandler
from routes.roles.create_role_handler import CreateRoleHandler
from routes.roles.modify_role_handler import ModifyRoleHandler
from routes.roles.delete_role_handler import DeleteRoleHandler
from services.role_management_service import (
    RoleListResult,
    RoleLookupResult,
    RoleCreateResult,
    RoleUpdateResult,
    RoleDeleteResult,
)

_ROLE_DICT = {"id": 1, "name": "Tester"}
_ROLE_WITH_GRID = {
    "id": 1,
    "name": "Tester",
    "permissions": [
        {"area": "test_cases", "can_read": True, "can_add_modify": True,
         "can_delete": False},
    ],
}


def _undecorated(method):
    """Return the original function if it's wrapped by a decorator."""
    return getattr(method, "__wrapped__", method)


def _make_handler_setup(handler_cls):
    """Return an asyncSetUp that wires up a handler with mocked service."""
    async def asyncSetUp(self):
        self.mock_logger = MagicMock(spec=logging.Logger)
        self.mock_logger.getChild.return_value = MagicMock(spec=logging.Logger)
        self.mock_state = MagicMock()
        self.mock_config = MagicMock()

        module_name = handler_cls.__module__.split('.')[-1]
        repo_patch = patch(
            f"routes.roles.{module_name}.RoleRepository", autospec=True)
        svc_patch = patch(
            f"routes.roles.{module_name}.RoleManagementService", autospec=True)
        self.addCleanup(repo_patch.stop)
        self.addCleanup(svc_patch.stop)
        repo_patch.start()
        self.mock_svc_cls = svc_patch.start()

        self.mock_svc = MagicMock()
        self.mock_svc_cls.return_value = self.mock_svc

        self.handler = handler_cls(
            self.mock_logger, self.mock_state, self.mock_config)

    return asyncSetUp


# ---------------------------------------------------------------------------
# ListRolesHandler
# ---------------------------------------------------------------------------

class TestListRolesHandler(unittest.IsolatedAsyncioTestCase):

    asyncSetUp = _make_handler_setup(ListRolesHandler)

    async def _call(self, result: RoleListResult) -> Response:
        self.mock_svc.get_all_roles = AsyncMock(return_value=result)
        return await self.handler.list_roles()

    async def test_success_returns_200_with_roles(self):
        resp = await self._call(RoleListResult(roles=[_ROLE_DICT]))
        self.assertEqual(resp.status_code, HTTPStatus.OK)
        body = json.loads(await resp.get_data())
        self.assertEqual(body["roles"], [_ROLE_DICT])

    async def test_empty_list_returns_200(self):
        resp = await self._call(RoleListResult(roles=[]))
        self.assertEqual(resp.status_code, HTTPStatus.OK)
        body = json.loads(await resp.get_data())
        self.assertEqual(body["roles"], [])

    async def test_unavailable_returns_503(self):
        resp = await self._call(RoleListResult(available=False))
        self.assertEqual(resp.status_code, HTTPStatus.SERVICE_UNAVAILABLE)
        body = json.loads(await resp.get_data())
        self.assertIn("error", body)

    async def test_response_is_json(self):
        resp = await self._call(RoleListResult(roles=[]))
        self.assertEqual(resp.content_type, "application/json")


# ---------------------------------------------------------------------------
# GetRoleHandler
# ---------------------------------------------------------------------------

class TestGetRoleHandler(unittest.IsolatedAsyncioTestCase):

    asyncSetUp = _make_handler_setup(GetRoleHandler)

    async def _call(self, result: RoleLookupResult, role_id: int = 1) -> Response:
        self.mock_svc.get_role = AsyncMock(return_value=result)
        return await self.handler.get_role(role_id)

    async def test_success_returns_200_with_role(self):
        resp = await self._call(RoleLookupResult(role=_ROLE_WITH_GRID))
        self.assertEqual(resp.status_code, HTTPStatus.OK)
        body = json.loads(await resp.get_data())
        self.assertEqual(body, _ROLE_WITH_GRID)

    async def test_not_found_returns_404(self):
        resp = await self._call(RoleLookupResult(found=False))
        self.assertEqual(resp.status_code, HTTPStatus.NOT_FOUND)
        body = json.loads(await resp.get_data())
        self.assertIn("error", body)

    async def test_unavailable_returns_503(self):
        resp = await self._call(RoleLookupResult(available=False))
        self.assertEqual(resp.status_code, HTTPStatus.SERVICE_UNAVAILABLE)

    async def test_unavailable_takes_precedence_over_not_found(self):
        resp = await self._call(RoleLookupResult(available=False, found=False))
        self.assertEqual(resp.status_code, HTTPStatus.SERVICE_UNAVAILABLE)

    async def test_role_id_passed_to_service(self):
        self.mock_svc.get_role = AsyncMock(
            return_value=RoleLookupResult(role=_ROLE_WITH_GRID))
        await self.handler.get_role(42)
        self.mock_svc.get_role.assert_awaited_once_with(42)

    async def test_response_is_json(self):
        resp = await self._call(RoleLookupResult(role=_ROLE_WITH_GRID))
        self.assertEqual(resp.content_type, "application/json")


# ---------------------------------------------------------------------------
# CreateRoleHandler
# ---------------------------------------------------------------------------

class TestCreateRoleHandler(unittest.IsolatedAsyncioTestCase):

    asyncSetUp = _make_handler_setup(CreateRoleHandler)

    def _request(self, **overrides):
        body = {"name": "Tester"}
        body.update(overrides)
        mock_req = MagicMock()
        mock_req.body = body
        return mock_req

    async def _call(self, result: RoleCreateResult, **body_overrides) -> Response:
        self.mock_svc.create_role = AsyncMock(return_value=result)
        target = _undecorated(self.handler.create_role)
        return await target(self.handler, self._request(**body_overrides))

    async def test_success_returns_201_with_id(self):
        resp = await self._call(RoleCreateResult(role_id=7))
        self.assertEqual(resp.status_code, HTTPStatus.CREATED)
        body = json.loads(await resp.get_data())
        self.assertEqual(body["id"], 7)

    async def test_conflict_returns_409(self):
        resp = await self._call(RoleCreateResult(conflict=True))
        self.assertEqual(resp.status_code, HTTPStatus.CONFLICT)
        body = json.loads(await resp.get_data())
        self.assertIn("error", body)

    async def test_invalid_returns_400(self):
        resp = await self._call(RoleCreateResult(invalid=True))
        self.assertEqual(resp.status_code, HTTPStatus.BAD_REQUEST)
        body = json.loads(await resp.get_data())
        self.assertIn("error", body)

    async def test_unavailable_returns_503(self):
        resp = await self._call(RoleCreateResult(available=False))
        self.assertEqual(resp.status_code, HTTPStatus.SERVICE_UNAVAILABLE)

    async def test_permissions_defaults_to_empty_list_when_absent(self):
        await self._call(RoleCreateResult(role_id=1))
        kwargs = self.mock_svc.create_role.call_args[1]
        self.assertEqual(kwargs["permissions"], [])

    async def test_permissions_passed_when_provided(self):
        perms = [{"area": "test_cases", "can_read": True,
                  "can_add_modify": False, "can_delete": False}]
        await self._call(RoleCreateResult(role_id=1), permissions=perms)
        kwargs = self.mock_svc.create_role.call_args[1]
        self.assertEqual(kwargs["permissions"], perms)

    async def test_response_is_json(self):
        resp = await self._call(RoleCreateResult(role_id=1))
        self.assertEqual(resp.content_type, "application/json")


# ---------------------------------------------------------------------------
# ModifyRoleHandler
# ---------------------------------------------------------------------------

class TestModifyRoleHandler(unittest.IsolatedAsyncioTestCase):

    asyncSetUp = _make_handler_setup(ModifyRoleHandler)

    def _request(self, **overrides):
        mock_req = MagicMock()
        mock_req.body = dict(overrides)
        return mock_req

    async def _call(self, result: RoleUpdateResult, role_id: int = 1,
                    **body_overrides) -> Response:
        self.mock_svc.update_role = AsyncMock(return_value=result)
        target = _undecorated(self.handler.modify_role)
        return await target(self.handler, self._request(**body_overrides),
                            role_id=role_id)

    async def test_success_returns_200(self):
        resp = await self._call(RoleUpdateResult(success=True), name="New")
        self.assertEqual(resp.status_code, HTTPStatus.OK)

    async def test_not_found_returns_404(self):
        resp = await self._call(RoleUpdateResult(found=False), name="New")
        self.assertEqual(resp.status_code, HTTPStatus.NOT_FOUND)
        body = json.loads(await resp.get_data())
        self.assertIn("error", body)

    async def test_conflict_returns_409(self):
        resp = await self._call(RoleUpdateResult(conflict=True), name="Taken")
        self.assertEqual(resp.status_code, HTTPStatus.CONFLICT)

    async def test_invalid_returns_400(self):
        resp = await self._call(RoleUpdateResult(invalid=True), permissions=[])
        self.assertEqual(resp.status_code, HTTPStatus.BAD_REQUEST)

    async def test_unavailable_returns_503(self):
        resp = await self._call(RoleUpdateResult(available=False), name="New")
        self.assertEqual(resp.status_code, HTTPStatus.SERVICE_UNAVAILABLE)

    async def test_invalid_takes_precedence_over_not_found(self):
        resp = await self._call(
            RoleUpdateResult(invalid=True, found=False), permissions=[])
        self.assertEqual(resp.status_code, HTTPStatus.BAD_REQUEST)

    async def test_not_found_takes_precedence_over_conflict(self):
        resp = await self._call(
            RoleUpdateResult(found=False, conflict=True), name="New")
        self.assertEqual(resp.status_code, HTTPStatus.NOT_FOUND)

    async def test_role_id_and_name_passed_to_service(self):
        self.mock_svc.update_role = AsyncMock(
            return_value=RoleUpdateResult(success=True))
        target = _undecorated(self.handler.modify_role)
        await target(self.handler, self._request(name="New"), role_id=9)
        self.mock_svc.update_role.assert_awaited_once_with(
            role_id=9, name="New", permissions=None)

    async def test_name_defaults_to_none_when_absent(self):
        await self._call(RoleUpdateResult(success=True), permissions=[])
        kwargs = self.mock_svc.update_role.call_args[1]
        self.assertIsNone(kwargs["name"])

    async def test_permissions_defaults_to_none_when_absent(self):
        await self._call(RoleUpdateResult(success=True), name="New")
        kwargs = self.mock_svc.update_role.call_args[1]
        self.assertIsNone(kwargs["permissions"])

    async def test_response_is_json(self):
        resp = await self._call(RoleUpdateResult(success=True), name="New")
        self.assertEqual(resp.content_type, "application/json")


# ---------------------------------------------------------------------------
# DeleteRoleHandler
# ---------------------------------------------------------------------------

class TestDeleteRoleHandler(unittest.IsolatedAsyncioTestCase):

    asyncSetUp = _make_handler_setup(DeleteRoleHandler)

    async def _call(self, result: RoleDeleteResult, role_id: int = 1) -> Response:
        self.mock_svc.delete_role = AsyncMock(return_value=result)
        return await self.handler.delete_role(role_id)

    async def test_success_returns_200(self):
        resp = await self._call(RoleDeleteResult(success=True))
        self.assertEqual(resp.status_code, HTTPStatus.OK)

    async def test_not_found_returns_404(self):
        resp = await self._call(RoleDeleteResult(found=False))
        self.assertEqual(resp.status_code, HTTPStatus.NOT_FOUND)
        body = json.loads(await resp.get_data())
        self.assertIn("error", body)

    async def test_unavailable_returns_503(self):
        resp = await self._call(RoleDeleteResult(available=False))
        self.assertEqual(resp.status_code, HTTPStatus.SERVICE_UNAVAILABLE)

    async def test_unavailable_takes_precedence_over_not_found(self):
        resp = await self._call(RoleDeleteResult(available=False, found=False))
        self.assertEqual(resp.status_code, HTTPStatus.SERVICE_UNAVAILABLE)

    async def test_role_id_passed_to_service(self):
        self.mock_svc.delete_role = AsyncMock(
            return_value=RoleDeleteResult(success=True))
        await self.handler.delete_role(13)
        self.mock_svc.delete_role.assert_awaited_once_with(13)

    async def test_response_is_json(self):
        resp = await self._call(RoleDeleteResult(success=True))
        self.assertEqual(resp.content_type, "application/json")


if __name__ == "__main__":
    unittest.main()
