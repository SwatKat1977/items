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
from items.shared.permission_action import PermissionAction

_IDENTITY = "http://identity/"
_CMS = "http://cms/"
_TOKEN = "a" * 32

# (name, method, path, json_body, the permission the route needs)
_ROUTES = [
    ("list test cases", "GET", "/web/1/testcases", None,
     PermissionAction.READ),
    ("get a test case", "GET", "/web/testcases/7?project_id=1", None,
     PermissionAction.READ),
    ("create a test case", "POST", "/web/1/testcases",
     {"folder_id": None, "name": "T", "description": ""},
     PermissionAction.ADD_MODIFY),
    ("modify a test case", "PATCH", "/web/testcases/7?project_id=1",
     {"name": "T", "description": ""}, PermissionAction.ADD_MODIFY),
    # Moving needs Add/Modify, not Delete: nothing is destroyed.
    ("move a test case", "POST", "/web/testcases/7/move?project_id=1",
     {"folder_id": None}, PermissionAction.ADD_MODIFY),
    ("delete a test case", "DELETE", "/web/testcases/7?project_id=1", None,
     PermissionAction.DELETE),
    # Sections (folders) belong to the same Test Cases area.
    ("create a section", "POST", "/web/1/folders",
     {"parent_id": None, "name": "S"}, PermissionAction.ADD_MODIFY),
    ("rename a section", "PATCH", "/web/folders/7?project_id=1",
     {"name": "S"}, PermissionAction.ADD_MODIFY),
    ("delete a section", "DELETE", "/web/folders/7?project_id=1", None,
     PermissionAction.DELETE),
    # A cascading delete destroys the test cases inside, so it needs Delete
    # too - not merely whatever covers sections.
    ("delete a section and its test cases", "DELETE",
     "/web/folders/7?project_id=1&cascade=true", None,
     PermissionAction.DELETE),
]

# The routes that take the project from the query string, and so can be sent
# without one.
_QUERY_STRING_ROUTES = [route for route in _ROUTES if "project_id=" in route[2]]


def _grant(*actions: PermissionAction) -> dict:
    """An Identity effective-permissions body granting exactly ``actions`` on
    Test Cases, everything else false."""
    granted = {action.value for action in actions}
    return {"project_id": 1, "areas": {"test_cases": {
        action.value: action.value in granted for action in PermissionAction}}}


def _identity_url(user_id: str, project_id: int = 1) -> str:
    return f"{_IDENTITY}users/{user_id}/projects/{project_id}/permissions"


class TestRoutePermissions(unittest.IsolatedAsyncioTestCase):
    """The Test Cases permission each test case and section route needs, end
    to end through the real blueprint, with a fake Identity.

    test_project_permission_decorator.py proves the decorator is right in
    isolation; this proves the *right* permission was attached to *each*
    route - Read to browse, Add/Modify to create, edit or rename, Delete to
    delete.
    """

    async def asyncSetUp(self):
        self.sessions = Sessions()
        # alice's session says she is a member of project 1. That snapshot
        # must no longer decide anything for these routes.
        await self.sessions.add_session(
            "alice@x.com", _TOKEN, AccountLogonType.BASIC,
            user_id="alice-uuid", project_ids=frozenset({1}))
        # newbie's session has no memberships at all.
        await self.sessions.add_session(
            "newbie@x.com", _TOKEN, AccountLogonType.BASIC,
            user_id="newbie-uuid", project_ids=frozenset())
        await self.sessions.add_session(
            "admin@x.com", _TOKEN, AccountLogonType.BASIC,
            is_administrator=True, user_id="admin-uuid")

        self.identity: dict = {}
        self.rest_client = AsyncMock()
        self.rest_client.get.side_effect = self._get
        for method in ("post", "put", "patch", "delete"):
            getattr(self.rest_client, method).return_value = ApiResponse(
                status_code=200, body={})

        configuration = MagicMock()
        configuration.apis_cms_svc = _CMS
        configuration.apis_identity_svc = _IDENTITY
        configuration.general_api_signing_secret = "secret"
        metadata_handler = MagicMock()
        metadata_handler.build_metadata_dictionary.return_value = {}

        injections = RouteInjections(
            logger=MagicMock(), sessions=self.sessions,
            configuration=configuration, rest_client=self.rest_client,
            metadata_handler=metadata_handler)

        app = Quart(__name__)
        app.register_blueprint(create_routes(injections))
        self.client = app.test_client()

    async def _get(self, url, *_args, **_kwargs):
        if url.startswith(_IDENTITY):
            if url not in self.identity:
                raise AssertionError(f"unexpected Identity request: {url}")
            result = self.identity[url]
            if isinstance(result, Exception):
                raise result
            return result
        return ApiResponse(status_code=200, body={})

    def _grants(self, body, user_id="alice-uuid", project_id=1):
        self.identity[_identity_url(user_id, project_id)] = ApiResponse(
            status_code=200, body=body)

    def _identity_requests(self) -> list:
        return [call.args[0] for call in self.rest_client.get.await_args_list
                if call.args[0].startswith(_IDENTITY)]

    def _cms_requests(self) -> list:
        """Every call that reached CMS, of any method."""
        urls = [call.args[0] for call in self.rest_client.get.await_args_list
                if call.args[0].startswith(_CMS)]
        for method in ("post", "put", "patch", "delete"):
            urls += [call.args[0] for call in
                     getattr(self.rest_client, method).await_args_list]
        return urls

    async def _call(self, method, path, body, user="alice@x.com"):
        headers = {} if user is None else {
            HEADER_USER: user, HEADER_TOKEN: _TOKEN}
        async with self.client as client:
            return await client.open(
                path, method=method, json=body, headers=headers)

    # ------------------------------------------------------------------

    async def test_each_route_needs_exactly_its_own_permission(self):
        """Grant one permission at a time: a route opens only for the one it
        needs, and CMS is reached only when it opens. This pins the whole
        route-to-permission map."""
        for name, method, path, body, needed in _ROUTES:
            for granted in PermissionAction:
                with self.subTest(route=name, granted=granted.value):
                    self.rest_client.reset_mock()
                    self._grants(_grant(granted))

                    response = await self._call(method, path, body)

                    if granted is needed:
                        self.assertNotIn(
                            response.status_code,
                            (HTTPStatus.UNAUTHORIZED, HTTPStatus.FORBIDDEN,
                             HTTPStatus.INTERNAL_SERVER_ERROR))
                        self.assertTrue(self._cms_requests())
                    else:
                        self.assertEqual(response.status_code,
                                         HTTPStatus.FORBIDDEN)
                        self.assertEqual(self._cms_requests(), [])

    async def test_a_role_with_everything_opens_every_route(self):
        self._grants(_grant(*PermissionAction))
        for name, method, path, body, _ in _ROUTES:
            with self.subTest(route=name):
                self.rest_client.reset_mock()
                response = await self._call(method, path, body)
                self.assertNotIn(
                    response.status_code,
                    (HTTPStatus.UNAUTHORIZED, HTTPStatus.FORBIDDEN,
                     HTTPStatus.INTERNAL_SERVER_ERROR))
                self.assertTrue(self._cms_requests())

    async def test_a_member_with_no_permissions_is_refused_everywhere(self):
        """A non-member, a member with no role and a disabled account all
        come back from Identity as an empty grid."""
        self._grants(_grant())
        for name, method, path, body, _ in _ROUTES:
            with self.subTest(route=name):
                self.rest_client.reset_mock()
                response = await self._call(method, path, body)
                self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
                self.assertEqual(self._cms_requests(), [])

    async def test_a_read_only_role_can_browse_but_not_change_anything(self):
        """The scenario this whole change exists for."""
        self._grants(_grant(PermissionAction.READ))
        outcomes = {}
        for name, method, path, body, _ in _ROUTES:
            outcomes[name] = (await self._call(method, path, body)
                              ).status_code
        self.assertNotEqual(outcomes["list test cases"], HTTPStatus.FORBIDDEN)
        self.assertNotEqual(outcomes["get a test case"], HTTPStatus.FORBIDDEN)
        self.assertEqual(outcomes["create a test case"], HTTPStatus.FORBIDDEN)
        self.assertEqual(outcomes["modify a test case"], HTTPStatus.FORBIDDEN)
        self.assertEqual(outcomes["move a test case"], HTTPStatus.FORBIDDEN)
        self.assertEqual(outcomes["delete a test case"], HTTPStatus.FORBIDDEN)
        self.assertEqual(outcomes["create a section"], HTTPStatus.FORBIDDEN)
        self.assertEqual(outcomes["rename a section"], HTTPStatus.FORBIDDEN)
        self.assertEqual(outcomes["delete a section"], HTTPStatus.FORBIDDEN)
        self.assertEqual(outcomes["delete a section and its test cases"],
                         HTTPStatus.FORBIDDEN)

    async def test_deleting_a_section_needs_delete_not_just_add_modify(self):
        """The cascading delete can destroy every test case in the section,
        so Add/Modify (which lets you create and rename sections) is not
        enough - with or without cascade."""
        self._grants(_grant(PermissionAction.READ,
                            PermissionAction.ADD_MODIFY))
        for path in ("/web/folders/7?project_id=1",
                     "/web/folders/7?project_id=1&cascade=true"):
            with self.subTest(path=path):
                self.rest_client.reset_mock()
                response = await self._call("DELETE", path, None)
                self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
                self.assertEqual(self._cms_requests(), [])

    async def test_add_modify_lets_you_create_and_rename_sections(self):
        self._grants(_grant(PermissionAction.ADD_MODIFY))
        create = await self._call("POST", "/web/1/folders",
                                  {"parent_id": None, "name": "S"})
        rename = await self._call("PATCH", "/web/folders/7?project_id=1",
                                  {"name": "S"})
        self.assertNotEqual(create.status_code, HTTPStatus.FORBIDDEN)
        self.assertNotEqual(rename.status_code, HTTPStatus.FORBIDDEN)

    async def test_identity_decides_not_the_sessions_membership_snapshot(self):
        """alice's session says she is a member of project 1, but Identity
        says she can do nothing there: Identity wins."""
        self._grants(_grant())
        response = await self._call("GET", "/web/1/testcases", None)
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    async def test_a_session_with_no_memberships_is_still_let_in_if_granted(
            self):
        """The reverse: newbie's session has no project ids at all, but
        Identity grants Read, so the request goes through."""
        self._grants(_grant(PermissionAction.READ), user_id="newbie-uuid")
        response = await self._call(
            "GET", "/web/1/testcases", None, user="newbie@x.com")
        self.assertNotIn(response.status_code,
                         (HTTPStatus.FORBIDDEN, HTTPStatus.UNAUTHORIZED))
        self.assertTrue(self._cms_requests())

    async def test_the_project_asked_about_is_the_one_in_the_request(self):
        self._grants(_grant(PermissionAction.READ), project_id=1)
        self._grants(_grant(), project_id=2)
        allowed = await self._call("GET", "/web/1/testcases", None)
        refused = await self._call("GET", "/web/2/testcases", None)
        self.assertNotEqual(allowed.status_code, HTTPStatus.FORBIDDEN)
        self.assertEqual(refused.status_code, HTTPStatus.FORBIDDEN)

    async def test_query_string_project_is_the_one_asked_about(self):
        self._grants(_grant(PermissionAction.READ), project_id=1)
        self._grants(_grant(), project_id=2)
        allowed = await self._call(
            "GET", "/web/testcases/7?project_id=1", None)
        refused = await self._call(
            "GET", "/web/testcases/7?project_id=2", None)
        self.assertNotEqual(allowed.status_code, HTTPStatus.FORBIDDEN)
        self.assertEqual(refused.status_code, HTTPStatus.FORBIDDEN)

    async def test_an_administrator_is_asked_about_like_anyone_else(self):
        self._grants(_grant(*PermissionAction), user_id="admin-uuid")
        response = await self._call(
            "DELETE", "/web/testcases/7?project_id=1", None,
            user="admin@x.com")
        self.assertNotIn(response.status_code,
                         (HTTPStatus.FORBIDDEN, HTTPStatus.UNAUTHORIZED))
        self.assertEqual(self._identity_requests(),
                         [_identity_url("admin-uuid")])

    async def test_no_session_is_401_and_nothing_is_asked(self):
        for name, method, path, body, _ in _ROUTES:
            with self.subTest(route=name):
                self.rest_client.reset_mock()
                response = await self._call(method, path, body, user=None)
                self.assertEqual(response.status_code,
                                 HTTPStatus.UNAUTHORIZED)
                self.assertEqual(self._identity_requests(), [])
                self.assertEqual(self._cms_requests(), [])

    async def test_no_project_is_400_and_nothing_is_asked(self):
        """Never a skipped check: a request that names no project is refused
        before Identity or CMS is touched."""
        for name, method, path, body, _ in _QUERY_STRING_ROUTES:
            bare_path = path.split("?")[0]
            for label, bad_path in (("missing", bare_path),
                                    ("not a number",
                                     bare_path + "?project_id=abc")):
                with self.subTest(route=name, project_id=label):
                    self.rest_client.reset_mock()
                    response = await self._call(method, bad_path, body)
                    self.assertEqual(response.status_code,
                                     HTTPStatus.BAD_REQUEST)
                    self.assertEqual(self._identity_requests(), [])
                    self.assertEqual(self._cms_requests(), [])

    async def test_identity_down_is_500_and_cms_is_not_reached(self):
        """Fail closed: not being able to ask is never a yes."""
        self.identity[_identity_url("alice-uuid")] = ApiResponse(
            exception_msg="connection refused")
        for name, method, path, body, _ in _ROUTES:
            with self.subTest(route=name):
                self.rest_client.reset_mock()
                response = await self._call(method, path, body)
                self.assertEqual(response.status_code,
                                 HTTPStatus.INTERNAL_SERVER_ERROR)
                self.assertEqual(self._cms_requests(), [])

    async def test_revoking_applies_on_the_very_next_request(self):
        """Same session, no re-login: the point of asking Identity each
        time."""
        self._grants(_grant(PermissionAction.READ))
        before = await self._call("GET", "/web/1/testcases", None)

        self._grants(_grant())
        after = await self._call("GET", "/web/1/testcases", None)

        self.assertNotEqual(before.status_code, HTTPStatus.FORBIDDEN)
        self.assertEqual(after.status_code, HTTPStatus.FORBIDDEN)


if __name__ == "__main__":
    unittest.main()
