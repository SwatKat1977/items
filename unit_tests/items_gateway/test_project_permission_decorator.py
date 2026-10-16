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
from http import HTTPStatus
from unittest.mock import AsyncMock, MagicMock
from quart import Quart
from weaver_framework.microservice.api_response import ApiResponse
from items.services.items_gateway.auth_decorators import (
    require_project_permission, HEADER_TOKEN, HEADER_USER)
from items.services.items_gateway.route_injections import RouteInjections
from items.services.items_gateway.sessions import Sessions
from items.shared.account_logon_type import AccountLogonType
from items.shared.permission_action import PermissionAction
from items.shared.permission_area import PermissionArea

_TOKEN = "a" * 32
_HEADERS = {HEADER_USER: "alice@x.com", HEADER_TOKEN: _TOKEN}
_USER_ID = "alice-uuid"
_IDENTITY = "http://identity/"


def _permissions_url(project_id: int) -> str:
    return f"{_IDENTITY}users/{_USER_ID}/projects/{project_id}/permissions"


def _body(test_cases=(False, False, False), milestones=(False, False, False)):
    """An Identity effective-permissions body, (read, add_modify, delete)."""
    def grant(flags):
        # Real booleans, as Identity sends them: the decorator rejects 1/0.
        return {"read": bool(flags[0]), "add_modify": bool(flags[1]),
                "delete": bool(flags[2])}
    return {"project_id": 5, "areas": {
        "test_cases": grant(test_cases), "milestones": grant(milestones)}}


def _ok(body) -> ApiResponse:
    return ApiResponse(status_code=HTTPStatus.OK, body=body)


class _Harness(unittest.IsolatedAsyncioTestCase):
    """A tiny app with routes gated by the decorator, and a fake Identity.

    The fake is keyed by URL and only ever answers what it was told to, but
    a handler's own broad ``except`` would swallow an "unexpected request"
    error and turn it into an ordinary 500. So tests assert the exact URL
    that was requested rather than relying on the fake to complain.
    """

    is_administrator = False
    user_id = _USER_ID

    async def asyncSetUp(self):
        self.sessions = Sessions()
        await self.sessions.add_session(
            "alice@x.com", _TOKEN, AccountLogonType.BASIC,
            is_administrator=self.is_administrator, user_id=self.user_id)

        self.responses: dict = {}
        self.rest_client = MagicMock()
        self.rest_client.get = AsyncMock(side_effect=self._get)

        config = MagicMock()
        config.apis_identity_svc = _IDENTITY
        self.logger = MagicMock()
        injections = RouteInjections(
            logger=self.logger, sessions=self.sessions,
            configuration=config, rest_client=self.rest_client)

        self.handler_calls = 0
        app = Quart(__name__)

        def gated(area, action):
            return require_project_permission(injections, area, action)

        @app.route('/p/<int:project_id>/read')
        @gated(PermissionArea.TEST_CASES, PermissionAction.READ)
        async def read_by_path(project_id: int):
            self.handler_calls += 1
            return "ok"

        @app.route('/p/<int:project_id>/delete', methods=['DELETE'])
        @gated(PermissionArea.TEST_CASES, PermissionAction.DELETE)
        async def delete_by_path(project_id: int):
            self.handler_calls += 1
            return "ok"

        @app.route('/p/<int:project_id>/milestones')
        @gated(PermissionArea.MILESTONES, PermissionAction.ADD_MODIFY)
        async def milestones_by_path(project_id: int):
            self.handler_calls += 1
            return "ok"

        @app.route('/items')
        @gated(PermissionArea.TEST_CASES, PermissionAction.READ)
        async def read_by_query():
            self.handler_calls += 1
            return "ok"

        self.client = app.test_client()

    async def _get(self, url, *_args, **_kwargs):
        if url not in self.responses:
            raise AssertionError(f"unexpected request: {url}")
        result = self.responses[url]
        if isinstance(result, Exception):
            raise result
        return result

    async def _call(self, path, method="GET", headers=None):
        async with self.client as client:
            return await client.open(
                path, method=method,
                headers=_HEADERS if headers is None else headers)


class TestRequireProjectPermissionAccess(_Harness):
    """Who is let through, and who is not."""

    async def test_granted_calls_the_route(self):
        self.responses[_permissions_url(5)] = _ok(_body(test_cases=(1, 0, 0)))
        response = await self._call('/p/5/read')
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(await response.get_data(as_text=True), "ok")
        self.assertEqual(self.handler_calls, 1)

    async def test_asks_identity_for_this_user_and_project(self):
        self.responses[_permissions_url(5)] = _ok(_body(test_cases=(1, 0, 0)))
        await self._call('/p/5/read')
        self.rest_client.get.assert_awaited_once_with(_permissions_url(5))

    async def test_not_granted_is_403_and_the_route_is_not_called(self):
        self.responses[_permissions_url(5)] = _ok(_body())
        response = await self._call('/p/5/read')
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        self.assertEqual(self.handler_calls, 0)

    async def test_the_action_decides_not_just_the_area(self):
        """Read but not Delete: the read route opens, the delete route does
        not, for the same user in the same project."""
        self.responses[_permissions_url(5)] = _ok(_body(test_cases=(1, 1, 0)))
        read = await self._call('/p/5/read')
        delete = await self._call('/p/5/delete', method="DELETE")
        self.assertEqual(read.status_code, HTTPStatus.OK)
        self.assertEqual(delete.status_code, HTTPStatus.FORBIDDEN)
        self.assertEqual(self.handler_calls, 1)

    async def test_delete_is_allowed_when_it_is_granted(self):
        self.responses[_permissions_url(5)] = _ok(_body(test_cases=(1, 0, 1)))
        response = await self._call('/p/5/delete', method="DELETE")
        self.assertEqual(response.status_code, HTTPStatus.OK)

    async def test_the_area_decides_not_just_the_action(self):
        """Test Cases Add/Modify does not open a Milestones route."""
        self.responses[_permissions_url(5)] = _ok(
            _body(test_cases=(1, 1, 1), milestones=(0, 0, 0)))
        response = await self._call('/p/5/milestones')
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    async def test_a_grant_in_another_area_opens_that_area(self):
        self.responses[_permissions_url(5)] = _ok(
            _body(milestones=(1, 1, 0)))
        response = await self._call('/p/5/milestones')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    async def test_no_session_is_401_and_identity_is_not_asked(self):
        response = await self._call('/p/5/read', headers={})
        self.assertEqual(response.status_code, HTTPStatus.UNAUTHORIZED)
        self.rest_client.get.assert_not_called()
        self.assertEqual(self.handler_calls, 0)

    async def test_wrong_token_is_401(self):
        response = await self._call('/p/5/read', headers={
            HEADER_USER: "alice@x.com", HEADER_TOKEN: "b" * 32})
        self.assertEqual(response.status_code, HTTPStatus.UNAUTHORIZED)
        self.rest_client.get.assert_not_called()

    async def test_identity_not_finding_the_user_is_403(self):
        self.responses[_permissions_url(5)] = ApiResponse(
            status_code=HTTPStatus.NOT_FOUND, body={"error": "User not found"})
        response = await self._call('/p/5/read')
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        self.assertEqual(self.handler_calls, 0)


class TestRequireProjectPermissionProjectId(_Harness):
    """Where the project comes from, and what happens when it is missing."""

    async def test_project_from_the_path(self):
        self.responses[_permissions_url(7)] = _ok(_body(test_cases=(1, 0, 0)))
        await self._call('/p/7/read')
        self.rest_client.get.assert_awaited_once_with(_permissions_url(7))

    async def test_project_from_the_query_string(self):
        self.responses[_permissions_url(9)] = _ok(_body(test_cases=(1, 0, 0)))
        response = await self._call('/items?project_id=9')
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.rest_client.get.assert_awaited_once_with(_permissions_url(9))

    async def test_the_path_wins_over_the_query_string(self):
        """The handler acts on the path's project, so that is the one that
        must be authorised."""
        self.responses[_permissions_url(5)] = _ok(_body(test_cases=(1, 0, 0)))
        await self._call('/p/5/read?project_id=9')
        self.rest_client.get.assert_awaited_once_with(_permissions_url(5))

    async def test_missing_project_is_400_not_a_skipped_check(self):
        """Unlike require_project_member, the check is never skipped."""
        response = await self._call('/items')
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)
        self.rest_client.get.assert_not_called()
        self.assertEqual(self.handler_calls, 0)

    async def test_non_integer_project_is_400(self):
        response = await self._call('/items?project_id=abc')
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)
        self.rest_client.get.assert_not_called()
        self.assertEqual(self.handler_calls, 0)

    async def test_the_session_is_checked_before_the_project(self):
        """Someone with no session learns nothing about the request shape."""
        response = await self._call('/items', headers={})
        self.assertEqual(response.status_code, HTTPStatus.UNAUTHORIZED)


class TestRequireProjectPermissionFailsClosed(_Harness):
    """Every way of not getting a clear 'yes' ends in no."""

    async def _assert_denied_with_500(self):
        response = await self._call('/p/5/read')
        self.assertEqual(response.status_code,
                         HTTPStatus.INTERNAL_SERVER_ERROR)
        self.assertEqual(self.handler_calls, 0)
        return response

    async def test_identity_unreachable_is_500(self):
        self.responses[_permissions_url(5)] = ApiResponse(
            exception_msg="connection refused")
        await self._assert_denied_with_500()
        self.logger.error.assert_called()

    async def test_the_rest_client_raising_is_500(self):
        self.responses[_permissions_url(5)] = RuntimeError("boom")
        response = await self._assert_denied_with_500()
        self.assertIn("error", await response.get_json())
        self.logger.exception.assert_called()

    async def test_identity_error_statuses_are_500(self):
        for status in (HTTPStatus.INTERNAL_SERVER_ERROR,
                       HTTPStatus.SERVICE_UNAVAILABLE,
                       HTTPStatus.BAD_REQUEST,
                       HTTPStatus.UNAUTHORIZED):
            with self.subTest(status=status):
                self.responses[_permissions_url(5)] = ApiResponse(
                    status_code=status, body=_body(test_cases=(1, 1, 1)))
                await self._assert_denied_with_500()

    async def test_a_200_with_a_granting_body_is_still_needed(self):
        """A granting body on a non-200 must not be believed (above); and a
        200 with nothing in it is not a yes."""
        self.responses[_permissions_url(5)] = _ok(None)
        await self._assert_denied_with_500()

    async def test_malformed_bodies_are_500_never_a_yes(self):
        malformed = {
            "empty dict": {},
            "list": [],
            "string": "granted",
            "areas not a dict": {"areas": []},
            "area missing": {"areas": {"milestones": {
                "read": True, "add_modify": True, "delete": True}}},
            "area not a dict": {"areas": {"test_cases": True}},
            "action missing": {"areas": {"test_cases": {
                "add_modify": True, "delete": True}}},
            "string true": {"areas": {"test_cases": {"read": "true"}}},
            "number one": {"areas": {"test_cases": {"read": 1}}},
            "null": {"areas": {"test_cases": {"read": None}}},
        }
        for label, body in malformed.items():
            with self.subTest(label):
                self.responses[_permissions_url(5)] = _ok(body)
                await self._assert_denied_with_500()

    async def test_only_a_real_boolean_true_grants(self):
        self.responses[_permissions_url(5)] = _ok(
            {"areas": {"test_cases": {"read": True}}})
        response = await self._call('/p/5/read')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    async def test_explicit_false_is_403_not_500(self):
        self.responses[_permissions_url(5)] = _ok(
            {"areas": {"test_cases": {"read": False}}})
        response = await self._call('/p/5/read')
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)


class TestRequireProjectPermissionAppliesImmediately(_Harness):
    """The reason for asking Identity each time."""

    async def test_revoking_applies_on_the_very_next_request(self):
        self.responses[_permissions_url(5)] = _ok(_body(test_cases=(1, 0, 0)))
        before = await self._call('/p/5/read')

        # An administrator removes the permission. Same session, no re-login.
        self.responses[_permissions_url(5)] = _ok(_body())
        after = await self._call('/p/5/read')

        self.assertEqual(before.status_code, HTTPStatus.OK)
        self.assertEqual(after.status_code, HTTPStatus.FORBIDDEN)

    async def test_granting_applies_on_the_very_next_request(self):
        self.responses[_permissions_url(5)] = _ok(_body())
        before = await self._call('/p/5/read')

        self.responses[_permissions_url(5)] = _ok(_body(test_cases=(1, 0, 0)))
        after = await self._call('/p/5/read')

        self.assertEqual(before.status_code, HTTPStatus.FORBIDDEN)
        self.assertEqual(after.status_code, HTTPStatus.OK)

    async def test_every_request_asks_identity(self):
        self.responses[_permissions_url(5)] = _ok(_body(test_cases=(1, 0, 0)))
        await self._call('/p/5/read')
        await self._call('/p/5/read')
        await self._call('/p/5/read')
        self.assertEqual(self.rest_client.get.await_count, 3)


class TestRequireProjectPermissionAdministrator(_Harness):
    """Administrators are not special-cased: Identity decides."""

    is_administrator = True

    async def test_an_administrator_is_still_asked_about(self):
        self.responses[_permissions_url(5)] = _ok(
            _body(test_cases=(1, 1, 1)))
        response = await self._call('/p/5/read')
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.rest_client.get.assert_awaited_once_with(_permissions_url(5))

    async def test_the_session_flag_does_not_override_identity(self):
        """If Identity says no, a stale 'administrator' flag on the session
        must not turn that into a yes."""
        self.responses[_permissions_url(5)] = _ok(_body())
        response = await self._call('/p/5/read')
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)


class TestRequireProjectPermissionNoUserId(_Harness):
    """A session whose user id could not be resolved at login."""

    user_id = ""

    async def test_is_403_and_identity_is_not_asked(self):
        response = await self._call('/p/5/read')
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        self.rest_client.get.assert_not_called()
        self.assertEqual(self.handler_calls, 0)


if __name__ == "__main__":
    unittest.main()
