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

_IDENTITY = "http://identity/"
_TOKEN = "a" * 32

_TESTER = {"project_id": 4, "areas": {
    "test_cases": {"read": True, "add_modify": True, "delete": False},
    "milestones": {"read": False, "add_modify": False, "delete": False}}}
_NOTHING = {"project_id": 4, "areas": {
    "test_cases": {"read": False, "add_modify": False, "delete": False}}}


def _url(user_id: str, project_id: int = 4) -> str:
    return f"{_IDENTITY}users/{user_id}/projects/{project_id}/permissions"


class TestProjectPermissionsRoute(unittest.IsolatedAsyncioTestCase):
    """``GET /web/projects/<project_id>/permissions``: what the caller may do.

    Uses the real blueprint and a fake Identity keyed by URL, and asserts the
    exact URL asked for, because a handler's own broad ``except`` would hide
    an "unexpected request" error from the fake.
    """

    async def asyncSetUp(self):
        self.sessions = Sessions()
        await self.sessions.add_session(
            "alice@x.com", _TOKEN, AccountLogonType.BASIC,
            user_id="alice-uuid")
        await self.sessions.add_session(
            "admin@x.com", _TOKEN, AccountLogonType.BASIC,
            is_administrator=True, user_id="admin-uuid")
        await self.sessions.add_session(
            "noid@x.com", _TOKEN, AccountLogonType.BASIC, user_id="")

        self.identity: dict = {}
        self.rest_client = AsyncMock()
        self.rest_client.get.side_effect = self._get

        configuration = MagicMock()
        configuration.apis_identity_svc = _IDENTITY
        configuration.apis_cms_svc = "http://cms/"
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
        if url not in self.identity:
            raise AssertionError(f"unexpected request: {url}")
        result = self.identity[url]
        if isinstance(result, Exception):
            raise result
        return result

    def _answers(self, body, user_id="alice-uuid", project_id=4):
        self.identity[_url(user_id, project_id)] = ApiResponse(
            status_code=HTTPStatus.OK, body=body)

    async def _call(self, path="/web/projects/4/permissions",
                    user="alice@x.com"):
        headers = {} if user is None else {
            HEADER_USER: user, HEADER_TOKEN: _TOKEN}
        async with self.client as client:
            return await client.get(path, headers=headers)

    # ------------------------------------------------------------------

    async def test_returns_what_identity_says(self):
        self._answers(_TESTER)
        response = await self._call()
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(await response.get_json(), _TESTER)
        self.assertEqual(response.content_type, "application/json")

    async def test_asks_identity_about_the_session_user_and_the_project(self):
        self._answers(_TESTER)
        await self._call()
        self.rest_client.get.assert_awaited_once_with(_url("alice-uuid", 4))

    async def test_the_project_in_the_path_is_the_one_asked_about(self):
        self._answers(_TESTER, project_id=9)
        response = await self._call("/web/projects/9/permissions")
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.rest_client.get.assert_awaited_once_with(_url("alice-uuid", 9))

    async def test_having_no_access_is_a_200_not_an_error(self):
        """A non-member, a member with no role and a disabled account all
        come back from Identity as an empty grid; the Portal needs that
        answer to hide the controls, so it must not be a 403."""
        self._answers(_NOTHING)
        response = await self._call()
        self.assertEqual(response.status_code, HTTPStatus.OK)
        body = await response.get_json()
        self.assertFalse(any(body["areas"]["test_cases"].values()))

    async def test_it_only_ever_answers_about_the_caller(self):
        """Nothing in the request can name another user: a user id in the
        query string is ignored and the session's user is asked about."""
        self._answers(_TESTER)
        response = await self._call(
            "/web/projects/4/permissions?user_id=admin-uuid"
            "&email_address=admin@x.com")
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.rest_client.get.assert_awaited_once_with(_url("alice-uuid", 4))

    async def test_an_administrator_is_asked_about_like_anyone_else(self):
        self._answers({"project_id": 4, "areas": {"test_cases": {
            "read": True, "add_modify": True, "delete": True}}},
            user_id="admin-uuid")
        response = await self._call(user="admin@x.com")
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.rest_client.get.assert_awaited_once_with(_url("admin-uuid", 4))

    async def test_changes_show_on_the_very_next_request(self):
        self._answers(_TESTER)
        before = await (await self._call()).get_json()
        self._answers(_NOTHING)
        after = await (await self._call()).get_json()
        self.assertTrue(before["areas"]["test_cases"]["add_modify"])
        self.assertFalse(after["areas"]["test_cases"]["add_modify"])

    # --- who may ask, and what goes wrong ------------------------------

    async def test_no_session_is_401_and_identity_is_not_asked(self):
        response = await self._call(user=None)
        self.assertEqual(response.status_code, HTTPStatus.UNAUTHORIZED)
        self.rest_client.get.assert_not_called()

    async def test_wrong_token_is_401(self):
        async with self.client as client:
            response = await client.get(
                "/web/projects/4/permissions",
                headers={HEADER_USER: "alice@x.com", HEADER_TOKEN: "b" * 32})
        self.assertEqual(response.status_code, HTTPStatus.UNAUTHORIZED)
        self.rest_client.get.assert_not_called()

    async def test_a_session_with_no_user_id_is_403_and_nothing_is_asked(self):
        response = await self._call(user="noid@x.com")
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        self.rest_client.get.assert_not_called()

    async def test_a_non_integer_project_is_not_found(self):
        response = await self._call("/web/projects/abc/permissions")
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.rest_client.get.assert_not_called()

    async def test_identity_not_knowing_the_user_is_403(self):
        self.identity[_url("alice-uuid")] = ApiResponse(
            status_code=HTTPStatus.NOT_FOUND, body={"error": "User not found"})
        response = await self._call()
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    async def test_identity_unreachable_is_500(self):
        self.identity[_url("alice-uuid")] = ApiResponse(
            exception_msg="connection refused")
        response = await self._call()
        self.assertEqual(response.status_code,
                         HTTPStatus.INTERNAL_SERVER_ERROR)
        self.assertEqual(await response.get_json(),
                         {"error": "Identity service unavailable"})

    async def test_the_rest_client_raising_is_500(self):
        self.identity[_url("alice-uuid")] = RuntimeError("boom")
        response = await self._call()
        self.assertEqual(response.status_code,
                         HTTPStatus.INTERNAL_SERVER_ERROR)

    async def test_identity_error_statuses_are_500(self):
        for status in (HTTPStatus.INTERNAL_SERVER_ERROR,
                       HTTPStatus.SERVICE_UNAVAILABLE,
                       HTTPStatus.BAD_REQUEST):
            with self.subTest(status=status):
                self.identity[_url("alice-uuid")] = ApiResponse(
                    status_code=status, body=_TESTER)
                response = await self._call()
                self.assertEqual(response.status_code,
                                 HTTPStatus.INTERNAL_SERVER_ERROR)


if __name__ == "__main__":
    unittest.main()
