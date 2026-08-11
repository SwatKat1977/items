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
    require_administrator, require_session, HEADER_TOKEN, HEADER_USER)
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


if __name__ == "__main__":
    unittest.main()
