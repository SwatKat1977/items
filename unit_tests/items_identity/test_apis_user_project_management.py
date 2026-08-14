"""
Handler-level tests for the project membership API endpoints:
  GET    /users/<uuid>/projects              - ListUserProjectsHandler
  POST   /users/<uuid>/projects              - AddUserProjectHandler
  PATCH  /users/<uuid>/projects/<project_id> - ModifyUserProjectHandler
  DELETE /users/<uuid>/projects/<project_id> - RemoveUserProjectHandler
"""
import unittest
import json
import logging
from http import HTTPStatus
from unittest.mock import patch, MagicMock, AsyncMock
from quart import Response
from routes.users.list_user_projects_handler import ListUserProjectsHandler
from routes.users.add_user_project_handler import AddUserProjectHandler
from routes.users.modify_user_project_handler import ModifyUserProjectHandler
from routes.users.remove_user_project_handler import RemoveUserProjectHandler
from services.project_membership_service import (
    MembershipListResult,
    MembershipCreateResult,
    MembershipUpdateResult,
    MembershipDeleteResult,
)

_UUID = "550e8400-e29b-41d4-a716-446655440000"

_MEMBERSHIP_DICT = {"project_id": 5, "role_id": 2, "role_name": "Tester"}


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
        member_repo_patch = patch(
            f"routes.users.{module_name}.ProjectMemberRepository",
            autospec=True)
        user_repo_patch = patch(
            f"routes.users.{module_name}.UserRepository", autospec=True)
        role_repo_patch = patch(
            f"routes.users.{module_name}.RoleRepository", autospec=True)
        svc_patch = patch(
            f"routes.users.{module_name}.ProjectMembershipService",
            autospec=True)
        for p in (member_repo_patch, user_repo_patch, role_repo_patch,
                  svc_patch):
            self.addCleanup(p.stop)
        member_repo_patch.start()
        user_repo_patch.start()
        role_repo_patch.start()
        self.mock_svc_cls = svc_patch.start()

        self.mock_svc = MagicMock()
        self.mock_svc_cls.return_value = self.mock_svc

        self.handler = handler_cls(
            self.mock_logger, self.mock_state, self.mock_config)

    return asyncSetUp


# ---------------------------------------------------------------------------
# ListUserProjectsHandler
# ---------------------------------------------------------------------------

class TestListUserProjectsHandler(unittest.IsolatedAsyncioTestCase):

    asyncSetUp = _make_handler_setup(ListUserProjectsHandler)

    async def _call(self, result: MembershipListResult,
                    user_id: str = _UUID) -> Response:
        self.mock_svc.get_memberships = AsyncMock(return_value=result)
        return await self.handler.list_user_projects(user_id)

    async def test_success_returns_200_with_memberships(self):
        resp = await self._call(
            MembershipListResult(memberships=[_MEMBERSHIP_DICT]))
        self.assertEqual(resp.status_code, HTTPStatus.OK)
        body = json.loads(await resp.get_data())
        self.assertEqual(body["memberships"], [_MEMBERSHIP_DICT])

    async def test_empty_list_returns_200(self):
        resp = await self._call(MembershipListResult(memberships=[]))
        self.assertEqual(resp.status_code, HTTPStatus.OK)
        body = json.loads(await resp.get_data())
        self.assertEqual(body["memberships"], [])

    async def test_not_found_returns_404(self):
        resp = await self._call(MembershipListResult(found=False))
        self.assertEqual(resp.status_code, HTTPStatus.NOT_FOUND)
        body = json.loads(await resp.get_data())
        self.assertIn("error", body)

    async def test_unavailable_returns_503(self):
        resp = await self._call(MembershipListResult(available=False))
        self.assertEqual(resp.status_code, HTTPStatus.SERVICE_UNAVAILABLE)

    async def test_user_id_passed_to_service(self):
        self.mock_svc.get_memberships = AsyncMock(
            return_value=MembershipListResult(memberships=[]))
        await self.handler.list_user_projects(_UUID)
        self.mock_svc.get_memberships.assert_awaited_once_with(_UUID)

    async def test_response_is_json(self):
        resp = await self._call(MembershipListResult(memberships=[]))
        self.assertEqual(resp.content_type, "application/json")


# ---------------------------------------------------------------------------
# AddUserProjectHandler
# ---------------------------------------------------------------------------

class TestAddUserProjectHandler(unittest.IsolatedAsyncioTestCase):

    asyncSetUp = _make_handler_setup(AddUserProjectHandler)

    def _request(self, **overrides):
        body = {"project_id": 5}
        body.update(overrides)
        mock_req = MagicMock()
        mock_req.body = body
        return mock_req

    async def _call(self, result: MembershipCreateResult,
                    user_id: str = _UUID, **body_overrides) -> Response:
        self.mock_svc.add_membership = AsyncMock(return_value=result)
        target = _undecorated(self.handler.add_user_project)
        return await target(self.handler, self._request(**body_overrides),
                            user_id)

    async def test_success_returns_201(self):
        resp = await self._call(MembershipCreateResult(success=True))
        self.assertEqual(resp.status_code, HTTPStatus.CREATED)

    async def test_not_found_returns_404(self):
        resp = await self._call(MembershipCreateResult(found=False))
        self.assertEqual(resp.status_code, HTTPStatus.NOT_FOUND)
        body = json.loads(await resp.get_data())
        self.assertIn("error", body)

    async def test_role_not_found_returns_400(self):
        resp = await self._call(MembershipCreateResult(role_not_found=True))
        self.assertEqual(resp.status_code, HTTPStatus.BAD_REQUEST)
        body = json.loads(await resp.get_data())
        self.assertIn("error", body)

    async def test_conflict_returns_409(self):
        resp = await self._call(MembershipCreateResult(conflict=True))
        self.assertEqual(resp.status_code, HTTPStatus.CONFLICT)
        body = json.loads(await resp.get_data())
        self.assertIn("error", body)

    async def test_unavailable_returns_503(self):
        resp = await self._call(MembershipCreateResult(available=False))
        self.assertEqual(resp.status_code, HTTPStatus.SERVICE_UNAVAILABLE)

    async def test_role_id_defaults_to_none_when_absent(self):
        await self._call(MembershipCreateResult(success=True))
        kwargs = self.mock_svc.add_membership.call_args[1]
        self.assertIsNone(kwargs["role_id"])

    async def test_role_id_passed_when_provided(self):
        await self._call(MembershipCreateResult(success=True), role_id=3)
        kwargs = self.mock_svc.add_membership.call_args[1]
        self.assertEqual(kwargs["role_id"], 3)

    async def test_project_id_passed_to_service(self):
        await self._call(MembershipCreateResult(success=True))
        kwargs = self.mock_svc.add_membership.call_args[1]
        self.assertEqual(kwargs["project_id"], 5)

    async def test_user_id_passed_to_service(self):
        await self._call(MembershipCreateResult(success=True), user_id=_UUID)
        kwargs = self.mock_svc.add_membership.call_args[1]
        self.assertEqual(kwargs["user_uuid"], _UUID)

    async def test_response_is_json(self):
        resp = await self._call(MembershipCreateResult(success=True))
        self.assertEqual(resp.content_type, "application/json")


# ---------------------------------------------------------------------------
# ModifyUserProjectHandler
# ---------------------------------------------------------------------------

class TestModifyUserProjectHandler(unittest.IsolatedAsyncioTestCase):

    asyncSetUp = _make_handler_setup(ModifyUserProjectHandler)

    def _request(self, role_id):
        mock_req = MagicMock()
        mock_req.body = {"role_id": role_id}
        return mock_req

    async def _call(self, result: MembershipUpdateResult, role_id=2,
                    user_id: str = _UUID, project_id: int = 5) -> Response:
        self.mock_svc.update_membership_role = AsyncMock(return_value=result)
        target = _undecorated(self.handler.modify_user_project)
        return await target(self.handler, self._request(role_id),
                            user_id, project_id)

    async def test_success_returns_200(self):
        resp = await self._call(MembershipUpdateResult(success=True))
        self.assertEqual(resp.status_code, HTTPStatus.OK)

    async def test_not_found_returns_404(self):
        resp = await self._call(MembershipUpdateResult(found=False))
        self.assertEqual(resp.status_code, HTTPStatus.NOT_FOUND)

    async def test_role_not_found_returns_400(self):
        resp = await self._call(MembershipUpdateResult(role_not_found=True))
        self.assertEqual(resp.status_code, HTTPStatus.BAD_REQUEST)

    async def test_membership_not_found_returns_404(self):
        resp = await self._call(
            MembershipUpdateResult(membership_not_found=True))
        self.assertEqual(resp.status_code, HTTPStatus.NOT_FOUND)
        body = json.loads(await resp.get_data())
        self.assertIn("error", body)

    async def test_unavailable_returns_503(self):
        resp = await self._call(MembershipUpdateResult(available=False))
        self.assertEqual(resp.status_code, HTTPStatus.SERVICE_UNAVAILABLE)

    async def test_role_not_found_takes_precedence_over_membership_not_found(self):
        resp = await self._call(MembershipUpdateResult(
            role_not_found=True, membership_not_found=True))
        self.assertEqual(resp.status_code, HTTPStatus.BAD_REQUEST)

    async def test_role_id_none_is_passed_through_to_clear_role(self):
        await self._call(MembershipUpdateResult(success=True), role_id=None)
        kwargs = self.mock_svc.update_membership_role.call_args[1]
        self.assertIsNone(kwargs["role_id"])

    async def test_user_id_and_project_id_passed_to_service(self):
        await self._call(MembershipUpdateResult(success=True),
                         user_id=_UUID, project_id=9)
        kwargs = self.mock_svc.update_membership_role.call_args[1]
        self.assertEqual(kwargs["user_uuid"], _UUID)
        self.assertEqual(kwargs["project_id"], 9)

    async def test_response_is_json(self):
        resp = await self._call(MembershipUpdateResult(success=True))
        self.assertEqual(resp.content_type, "application/json")


# ---------------------------------------------------------------------------
# RemoveUserProjectHandler
# ---------------------------------------------------------------------------

class TestRemoveUserProjectHandler(unittest.IsolatedAsyncioTestCase):

    asyncSetUp = _make_handler_setup(RemoveUserProjectHandler)

    async def _call(self, result: MembershipDeleteResult,
                    user_id: str = _UUID, project_id: int = 5) -> Response:
        self.mock_svc.remove_membership = AsyncMock(return_value=result)
        return await self.handler.remove_user_project(user_id, project_id)

    async def test_success_returns_200(self):
        resp = await self._call(MembershipDeleteResult(success=True))
        self.assertEqual(resp.status_code, HTTPStatus.OK)

    async def test_not_found_returns_404(self):
        resp = await self._call(MembershipDeleteResult(found=False))
        self.assertEqual(resp.status_code, HTTPStatus.NOT_FOUND)
        body = json.loads(await resp.get_data())
        self.assertIn("error", body)

    async def test_membership_not_found_returns_404(self):
        resp = await self._call(
            MembershipDeleteResult(membership_not_found=True))
        self.assertEqual(resp.status_code, HTTPStatus.NOT_FOUND)
        body = json.loads(await resp.get_data())
        self.assertIn("error", body)

    async def test_unavailable_returns_503(self):
        resp = await self._call(MembershipDeleteResult(available=False))
        self.assertEqual(resp.status_code, HTTPStatus.SERVICE_UNAVAILABLE)

    async def test_unavailable_takes_precedence_over_not_found(self):
        resp = await self._call(
            MembershipDeleteResult(available=False, found=False))
        self.assertEqual(resp.status_code, HTTPStatus.SERVICE_UNAVAILABLE)

    async def test_user_id_and_project_id_passed_to_service(self):
        self.mock_svc.remove_membership = AsyncMock(
            return_value=MembershipDeleteResult(success=True))
        await self.handler.remove_user_project(_UUID, 9)
        self.mock_svc.remove_membership.assert_awaited_once_with(
            user_uuid=_UUID, project_id=9)

    async def test_response_is_json(self):
        resp = await self._call(MembershipDeleteResult(success=True))
        self.assertEqual(resp.content_type, "application/json")


if __name__ == "__main__":
    unittest.main()
