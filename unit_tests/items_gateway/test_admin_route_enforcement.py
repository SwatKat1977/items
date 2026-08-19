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
    HEADER_TOKEN, HEADER_USER)
from items.services.items_gateway.route_injections import RouteInjections
from items.services.items_gateway.routes import create_routes
from items.services.items_gateway.sessions import Sessions
from items.shared.account_logon_type import AccountLogonType

_VALID_PROJECT_BODY = {
    "name": "EnforcementTest",
    "announcement": "",
    "announcement_on_overview": False,
}

_VALID_FIELD_BODY = {
    "field_name": "Enforcement Field",
    "description": "",
    "system_name": "enforcement_field",
    "field_type": "String",
    "enabled": True,
    "is_required": False,
    "default_value": "",
    "applies_to_all_projects": True,
}

_USER_TOKEN = "a" * 32
_ADMIN_TOKEN = "b" * 32
_OUTSIDER_TOKEN = "c" * 32
_USER_HEADERS = {HEADER_USER: "user@x.com", HEADER_TOKEN: _USER_TOKEN}
_ADMIN_HEADERS = {HEADER_USER: "admin@x.com", HEADER_TOKEN: _ADMIN_TOKEN}
# A valid, non-administrator session with no project memberships at all -
# used to confirm membership is actually enforced, not just "any session
# passes". _USER_HEADERS above is a member of project 1, matching every
# project-scoped path in _SESSION_ONLY_ROUTES, so it can't tell the two
# apart on its own.
_OUTSIDER_HEADERS = {HEADER_USER: "outsider@x.com", HEADER_TOKEN: _OUTSIDER_TOKEN}

# (method, path, json_body) - every admin-only /web/* route.
_ADMIN_ONLY_ROUTES = [
    ("GET", "/web/users", None),
    ("POST", "/web/users",
     {"email_address": "a@b.com", "full_name": "A", "display_name": "A"}),
    ("GET", "/web/users/1", None),
    ("PATCH", "/web/users/1", {"display_name": "New"}),
    ("POST", "/web/users/1/password", {"new_password": "newpass123"}),
    ("GET", "/web/invites", None),
    ("POST", "/web/invites", {"email_address": "a@b.com"}),
    ("POST", "/web/invites/resend", {"email_address": "a@b.com"}),
    ("POST", "/web/invites/uninvite", {"email_address": "a@b.com"}),
    ("POST", "/web/projects", _VALID_PROJECT_BODY),
    ("PATCH", "/web/projects/1", _VALID_PROJECT_BODY),
    ("DELETE", "/web/projects/1", None),
    ("GET", "/web/testcase_custom_fields/", None),
    ("GET", "/web/testcase_custom_fields/1", None),
    ("PUT", "/web/testcase_custom_fields/1", _VALID_FIELD_BODY),
    ("PATCH", "/web/testcase_custom_fields/1", {"direction": "up"}),
    ("POST", "/web/testcase_custom_fields/", _VALID_FIELD_BODY),
    ("DELETE", "/web/testcase_custom_fields/1", None),
    ("GET", "/web/roles", None),
    ("POST", "/web/roles", {"name": "Tester"}),
    ("GET", "/web/roles/1", None),
    ("PATCH", "/web/roles/1", {"name": "New Name"}),
    ("DELETE", "/web/roles/1", None),
    ("GET", "/web/users/1/projects", None),
    ("POST", "/web/users/1/projects", {"project_id": 5}),
    ("PATCH", "/web/users/1/projects/5", {"role_id": 2}),
    ("DELETE", "/web/users/1/projects/5", None),
]

# (method, path, json_body) - routes that need a valid session but not
# administrator rights. All four also require project membership except
# the list, which filters rather than gates - _USER_HEADERS' session is a
# member of project 1, matching every project-scoped path here, so these
# tables alone exercise "a member reaches their own project", not
# "membership is actually checked" - see test_member_only_routes_reject_
# non_member below for the negative case.
_SESSION_ONLY_ROUTES = [
    ("GET", "/web/projects", None),
    ("GET", "/web/projects/1", None),
    ("GET", "/web/1/testcases", None),
    ("GET", "/web/testcases/1?project_id=1", None),
]

# (method, path) - the three of the four above that actually gate on
# membership (unlike the list, which filters its response instead of
# rejecting the request).
_MEMBER_ONLY_ROUTES = [
    ("GET", "/web/projects/1"),
    ("GET", "/web/1/testcases"),
    ("GET", "/web/testcases/1?project_id=1"),
]

# (method, path, json_body) - routes that must stay reachable with no
# X-Items-* session at all, each for its own documented reason (see the
# individual blueprint docstrings).
#
# /web/webhook/metadata is deliberately not in this list: it is also
# unauthenticated with respect to sessions, but it enforces its own HMAC
# signature and correctly 401s an unsigned request for that unrelated
# reason - which this table can't distinguish from a session-enforcement
# 401. Its own auth is covered by test_webhook_handler.py; its wiring is
# covered by test_route_factories.py.
_EXEMPT_ROUTES = [
    ("POST", "/web/sessions",
     {"email_address": "a@b.com", "password": "x"}),
    ("POST", "/web/sessions/validate",
     {"email_address": "a@b.com", "token": "a" * 32}),
    ("POST", "/web/sessions/refresh", None),
    ("DELETE", "/web/sessions",
     {"email_address": "a@b.com", "token": "a" * 32}),
    ("GET", "/web/invites/token/abc123", None),
    ("POST", "/web/accept_invite",
     {"token": "abc123", "full_name": "A", "display_name": "A",
      "password": "password1"}),
]


class TestAdminRouteEnforcement(unittest.IsolatedAsyncioTestCase):
    """Confirms every /web/* route enforces the access level it should.

    Complements test_route_factories.py (which proves every route wires
    through to its handler when authorized) and test_auth_decorators.py
    (which proves the decorators themselves are correct in isolation) with
    the piece neither of those covers: that the *right* decorator, or none,
    was actually attached to each specific route. Getting this wrong in
    either direction is the whole point of the change - too strict locks
    out real users, too loose leaves the gap this work exists to close.
    """

    async def asyncSetUp(self):
        logger = MagicMock()
        self.sessions = Sessions()
        await self.sessions.add_session(
            "user@x.com", _USER_TOKEN, AccountLogonType.BASIC,
            is_administrator=False, project_ids=frozenset({1}))
        await self.sessions.add_session(
            "admin@x.com", _ADMIN_TOKEN, AccountLogonType.BASIC,
            is_administrator=True)
        await self.sessions.add_session(
            "outsider@x.com", _OUTSIDER_TOKEN, AccountLogonType.BASIC,
            is_administrator=False, project_ids=frozenset())
        configuration = MagicMock()
        configuration.apis_cms_svc = "http://cms/"
        configuration.apis_identity_svc = "http://identity/"
        configuration.general_api_signing_secret = "secret"
        rest_client = AsyncMock()
        rest_client.get.return_value = ApiResponse(status_code=200, body={})
        rest_client.post.return_value = ApiResponse(status_code=200, body={})
        rest_client.put.return_value = ApiResponse(status_code=200, body={})
        rest_client.patch.return_value = ApiResponse(status_code=200, body={})
        rest_client.delete.return_value = ApiResponse(status_code=200, body={})
        metadata_handler = MagicMock()
        metadata_handler.build_metadata_dictionary.return_value = {}

        injections = RouteInjections(
            logger=logger,
            sessions=self.sessions,
            configuration=configuration,
            rest_client=rest_client,
            metadata_handler=metadata_handler)

        blueprint = create_routes(injections)

        app = Quart(__name__)
        app.register_blueprint(blueprint)
        self.client = app.test_client()

    async def _call(self, method, path, json_body, headers=None):
        async with self.client as c:
            return await c.open(path, method=method, json=json_body,
                                headers=headers)

    async def test_admin_only_routes_reject_no_session(self):
        for method, path, body in _ADMIN_ONLY_ROUTES:
            with self.subTest(method=method, path=path):
                response = await self._call(method, path, body)
                self.assertEqual(response.status_code,
                                 HTTPStatus.UNAUTHORIZED)

    async def test_admin_only_routes_reject_non_administrator(self):
        for method, path, body in _ADMIN_ONLY_ROUTES:
            with self.subTest(method=method, path=path):
                response = await self._call(
                    method, path, body, headers=_USER_HEADERS)
                self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    async def test_admin_only_routes_accept_administrator(self):
        for method, path, body in _ADMIN_ONLY_ROUTES:
            with self.subTest(method=method, path=path):
                response = await self._call(
                    method, path, body, headers=_ADMIN_HEADERS)
                self.assertNotIn(
                    response.status_code,
                    (HTTPStatus.UNAUTHORIZED, HTTPStatus.FORBIDDEN))

    async def test_session_only_routes_reject_no_session(self):
        for method, path, body in _SESSION_ONLY_ROUTES:
            with self.subTest(method=method, path=path):
                response = await self._call(method, path, body)
                self.assertEqual(response.status_code,
                                 HTTPStatus.UNAUTHORIZED)

    async def test_session_only_routes_accept_non_administrator(self):
        for method, path, body in _SESSION_ONLY_ROUTES:
            with self.subTest(method=method, path=path):
                response = await self._call(
                    method, path, body, headers=_USER_HEADERS)
                self.assertNotIn(
                    response.status_code,
                    (HTTPStatus.UNAUTHORIZED, HTTPStatus.FORBIDDEN))

    async def test_session_only_routes_accept_administrator(self):
        for method, path, body in _SESSION_ONLY_ROUTES:
            with self.subTest(method=method, path=path):
                response = await self._call(
                    method, path, body, headers=_ADMIN_HEADERS)
                self.assertNotIn(
                    response.status_code,
                    (HTTPStatus.UNAUTHORIZED, HTTPStatus.FORBIDDEN))

    async def test_exempt_routes_accept_no_session(self):
        for method, path, body in _EXEMPT_ROUTES:
            with self.subTest(method=method, path=path):
                response = await self._call(method, path, body)
                self.assertNotIn(
                    response.status_code,
                    (HTTPStatus.UNAUTHORIZED, HTTPStatus.FORBIDDEN))

    async def test_member_only_routes_reject_non_member(self):
        """A valid session with no membership of project 1 must be
        rejected by these three - proves membership is actually being
        checked, not just "any session passes" (which _USER_HEADERS, a
        member of project 1, can't distinguish on its own)."""
        for method, path in _MEMBER_ONLY_ROUTES:
            with self.subTest(method=method, path=path):
                response = await self._call(
                    method, path, None, headers=_OUTSIDER_HEADERS)
                self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    async def test_member_only_routes_accept_administrator(self):
        """Administrators bypass membership entirely, same as every other
        admin-gated view - not covered by _SESSION_ONLY_ROUTES' admin
        check alone, since that uses _ADMIN_HEADERS which never proves
        the bypass is membership-specific rather than coincidental."""
        for method, path in _MEMBER_ONLY_ROUTES:
            with self.subTest(method=method, path=path):
                response = await self._call(
                    method, path, None, headers=_ADMIN_HEADERS)
                self.assertNotIn(
                    response.status_code,
                    (HTTPStatus.UNAUTHORIZED, HTTPStatus.FORBIDDEN))

    async def test_project_list_never_rejects_a_non_member_just_filters(self):
        """Unlike the three above, the list route has nothing to 403 - a
        member of nothing still gets a 200 with an empty list, not a
        rejection."""
        response = await self._call(
            "GET", "/web/projects", None, headers=_OUTSIDER_HEADERS)
        self.assertEqual(response.status_code, HTTPStatus.OK)


if __name__ == "__main__":
    unittest.main()
