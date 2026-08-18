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
from quart import Quart
from items.services.items_gateway.auth_decorators import (
    require_administrator, require_project_member, require_session,
    require_session_with_entry, HEADER_TOKEN, HEADER_USER)
from items.services.items_gateway.sessions import Sessions
from items.shared.account_logon_type import AccountLogonType

_USER_TOKEN = "a" * 32
_ADMIN_TOKEN = "b" * 32


def _make_app(sessions: Sessions) -> Quart:
    app = Quart(__name__)

    @app.route('/session-only')
    @require_session(sessions)
    async def session_only():
        return "ok"

    @app.route('/admin-only')
    @require_administrator(sessions)
    async def admin_only():
        return "ok"

    @app.route('/projects/<int:project_id>')
    @require_project_member(sessions)
    async def project_member_route_param(project_id: int):
        return "ok"

    @app.route('/testcases')
    @require_project_member(sessions)
    async def project_member_query_param():
        return "ok"

    @app.route('/list-for-caller')
    @require_session_with_entry(sessions)
    async def list_for_caller(session_entry):
        return "member" if session_entry.is_administrator else "non-admin"

    return app


class TestRequireSession(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.sessions = Sessions()
        await self.sessions.add_session(
            "user@x.com", _USER_TOKEN, AccountLogonType.BASIC)
        self.client = _make_app(self.sessions).test_client()

    async def test_no_headers_returns_401(self):
        async with self.client as c:
            response = await c.get('/session-only')
        self.assertEqual(response.status_code, HTTPStatus.UNAUTHORIZED)

    async def test_only_user_header_returns_401(self):
        async with self.client as c:
            response = await c.get(
                '/session-only', headers={HEADER_USER: "user@x.com"})
        self.assertEqual(response.status_code, HTTPStatus.UNAUTHORIZED)

    async def test_only_token_header_returns_401(self):
        async with self.client as c:
            response = await c.get(
                '/session-only', headers={HEADER_TOKEN: _USER_TOKEN})
        self.assertEqual(response.status_code, HTTPStatus.UNAUTHORIZED)

    async def test_unknown_email_returns_401(self):
        async with self.client as c:
            response = await c.get('/session-only', headers={
                HEADER_USER: "nobody@x.com", HEADER_TOKEN: _USER_TOKEN})
        self.assertEqual(response.status_code, HTTPStatus.UNAUTHORIZED)

    async def test_wrong_token_returns_401(self):
        async with self.client as c:
            response = await c.get('/session-only', headers={
                HEADER_USER: "user@x.com", HEADER_TOKEN: "c" * 32})
        self.assertEqual(response.status_code, HTTPStatus.UNAUTHORIZED)

    async def test_valid_session_calls_through(self):
        async with self.client as c:
            response = await c.get('/session-only', headers={
                HEADER_USER: "user@x.com", HEADER_TOKEN: _USER_TOKEN})
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(await response.get_data(as_text=True), "ok")


class TestRequireAdministrator(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.sessions = Sessions()
        await self.sessions.add_session(
            "user@x.com", _USER_TOKEN, AccountLogonType.BASIC,
            is_administrator=False)
        await self.sessions.add_session(
            "admin@x.com", _ADMIN_TOKEN, AccountLogonType.BASIC,
            is_administrator=True)
        self.client = _make_app(self.sessions).test_client()

    async def test_no_headers_returns_401(self):
        async with self.client as c:
            response = await c.get('/admin-only')
        self.assertEqual(response.status_code, HTTPStatus.UNAUTHORIZED)

    async def test_invalid_session_returns_401(self):
        async with self.client as c:
            response = await c.get('/admin-only', headers={
                HEADER_USER: "user@x.com", HEADER_TOKEN: "wrong"})
        self.assertEqual(response.status_code, HTTPStatus.UNAUTHORIZED)

    async def test_valid_non_administrator_session_returns_403(self):
        async with self.client as c:
            response = await c.get('/admin-only', headers={
                HEADER_USER: "user@x.com", HEADER_TOKEN: _USER_TOKEN})
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    async def test_valid_administrator_session_calls_through(self):
        async with self.client as c:
            response = await c.get('/admin-only', headers={
                HEADER_USER: "admin@x.com", HEADER_TOKEN: _ADMIN_TOKEN})
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(await response.get_data(as_text=True), "ok")


class TestRequireProjectMember(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.sessions = Sessions()
        await self.sessions.add_session(
            "member@x.com", _USER_TOKEN, AccountLogonType.BASIC,
            is_administrator=False, project_ids=frozenset({1}))
        await self.sessions.add_session(
            "admin@x.com", _ADMIN_TOKEN, AccountLogonType.BASIC,
            is_administrator=True)
        self.client = _make_app(self.sessions).test_client()

    async def test_no_headers_returns_401(self):
        async with self.client as c:
            response = await c.get('/projects/1')
        self.assertEqual(response.status_code, HTTPStatus.UNAUTHORIZED)

    async def test_member_of_the_route_project_calls_through(self):
        async with self.client as c:
            response = await c.get('/projects/1', headers={
                HEADER_USER: "member@x.com", HEADER_TOKEN: _USER_TOKEN})
        self.assertEqual(response.status_code, HTTPStatus.OK)

    async def test_not_a_member_of_the_route_project_returns_403(self):
        async with self.client as c:
            response = await c.get('/projects/2', headers={
                HEADER_USER: "member@x.com", HEADER_TOKEN: _USER_TOKEN})
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    async def test_administrator_bypasses_membership(self):
        async with self.client as c:
            response = await c.get('/projects/2', headers={
                HEADER_USER: "admin@x.com", HEADER_TOKEN: _ADMIN_TOKEN})
        self.assertEqual(response.status_code, HTTPStatus.OK)

    async def test_member_of_the_query_param_project_calls_through(self):
        async with self.client as c:
            response = await c.get('/testcases?project_id=1', headers={
                HEADER_USER: "member@x.com", HEADER_TOKEN: _USER_TOKEN})
        self.assertEqual(response.status_code, HTTPStatus.OK)

    async def test_not_a_member_of_the_query_param_project_returns_403(self):
        async with self.client as c:
            response = await c.get('/testcases?project_id=2', headers={
                HEADER_USER: "member@x.com", HEADER_TOKEN: _USER_TOKEN})
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    async def test_missing_project_id_falls_through_to_the_handler(self):
        """No project_id anywhere in the request - nothing to check
        membership against, so this decorator gets out of the way and lets
        the handler's own validation respond (here, just "ok", since the
        stub route doesn't validate anything itself)."""
        async with self.client as c:
            response = await c.get('/testcases', headers={
                HEADER_USER: "member@x.com", HEADER_TOKEN: _USER_TOKEN})
        self.assertEqual(response.status_code, HTTPStatus.OK)

    async def test_non_integer_project_id_query_param_falls_through(self):
        async with self.client as c:
            response = await c.get('/testcases?project_id=abc', headers={
                HEADER_USER: "member@x.com", HEADER_TOKEN: _USER_TOKEN})
        self.assertEqual(response.status_code, HTTPStatus.OK)

    async def test_invalid_session_returns_401(self):
        async with self.client as c:
            response = await c.get('/projects/1', headers={
                HEADER_USER: "member@x.com", HEADER_TOKEN: "wrong"})
        self.assertEqual(response.status_code, HTTPStatus.UNAUTHORIZED)


class TestRequireSessionWithEntry(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.sessions = Sessions()
        await self.sessions.add_session(
            "user@x.com", _USER_TOKEN, AccountLogonType.BASIC,
            is_administrator=False)
        await self.sessions.add_session(
            "admin@x.com", _ADMIN_TOKEN, AccountLogonType.BASIC,
            is_administrator=True)
        self.client = _make_app(self.sessions).test_client()

    async def test_no_headers_returns_401(self):
        async with self.client as c:
            response = await c.get('/list-for-caller')
        self.assertEqual(response.status_code, HTTPStatus.UNAUTHORIZED)

    async def test_invalid_session_returns_401(self):
        async with self.client as c:
            response = await c.get('/list-for-caller', headers={
                HEADER_USER: "user@x.com", HEADER_TOKEN: "wrong"})
        self.assertEqual(response.status_code, HTTPStatus.UNAUTHORIZED)

    async def test_passes_the_resolved_entry_through_to_the_handler(self):
        async with self.client as c:
            admin_response = await c.get('/list-for-caller', headers={
                HEADER_USER: "admin@x.com", HEADER_TOKEN: _ADMIN_TOKEN})
            user_response = await c.get('/list-for-caller', headers={
                HEADER_USER: "user@x.com", HEADER_TOKEN: _USER_TOKEN})
        self.assertEqual(
            await admin_response.get_data(as_text=True), "member")
        self.assertEqual(
            await user_response.get_data(as_text=True), "non-admin")


if __name__ == "__main__":
    unittest.main()
