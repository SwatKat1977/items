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
from items.services.items_gateway.sessions import Sessions, SessionEntry
from items.shared.account_logon_type import AccountLogonType


class TestSessions(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.sessions = Sessions()
        self.email = "test@example.com"
        self.token = "test_token"
        self.auth_type = AccountLogonType.BASIC

    async def test_add_session(self):
        await self.sessions.add_session(self.email, self.token, self.auth_type)
        self.assertTrue(await self.sessions.has_session(self.email))
        self.assertTrue(
            await self.sessions.is_valid_session(self.email, self.token))

    async def test_add_session_overwrites_existing(self):
        await self.sessions.add_session(self.email, "old_token", self.auth_type)
        await self.sessions.add_session(self.email, self.token, self.auth_type)
        self.assertTrue(
            await self.sessions.is_valid_session(self.email, self.token))
        self.assertFalse(
            await self.sessions.is_valid_session(self.email, "old_token"))

    async def test_delete_session(self):
        await self.sessions.add_session(self.email, self.token, self.auth_type)
        await self.sessions.delete_session(self.email)
        self.assertFalse(await self.sessions.has_session(self.email))

    async def test_delete_session_nonexistent(self):
        await self.sessions.delete_session(self.email)
        self.assertFalse(await self.sessions.has_session(self.email))

    async def test_is_valid_session_true(self):
        await self.sessions.add_session(self.email, self.token, self.auth_type)
        self.assertTrue(
            await self.sessions.is_valid_session(self.email, self.token))

    async def test_is_valid_session_false_wrong_token(self):
        await self.sessions.add_session(self.email, self.token, self.auth_type)
        self.assertFalse(
            await self.sessions.is_valid_session(self.email, "wrong_token"))

    async def test_is_valid_session_false_no_session(self):
        self.assertFalse(
            await self.sessions.is_valid_session(self.email, self.token))

    async def test_has_session_true(self):
        await self.sessions.add_session(self.email, self.token, self.auth_type)
        self.assertTrue(await self.sessions.has_session(self.email))

    async def test_has_session_false(self):
        self.assertFalse(await self.sessions.has_session(self.email))

    def test_session_entry_defaults(self):
        entry = SessionEntry()
        self.assertEqual(entry.email_address, "")
        self.assertEqual(entry.authentication_type, AccountLogonType.BASIC)
        self.assertEqual(entry.session_expiry, 0)
        self.assertEqual(entry.token, "")
        self.assertFalse(entry.is_administrator)

    async def test_add_session_stores_is_administrator(self):
        await self.sessions.add_session(
            self.email, self.token, self.auth_type, is_administrator=True)
        entry = await self.sessions.get_session_entry(self.email, self.token)
        self.assertIsNotNone(entry)
        self.assertTrue(entry.is_administrator)

    async def test_add_session_is_administrator_defaults_false(self):
        await self.sessions.add_session(self.email, self.token, self.auth_type)
        entry = await self.sessions.get_session_entry(self.email, self.token)
        self.assertFalse(entry.is_administrator)

    async def test_get_session_entry_valid_token_returns_entry(self):
        await self.sessions.add_session(self.email, self.token, self.auth_type)
        entry = await self.sessions.get_session_entry(self.email, self.token)
        self.assertIsNotNone(entry)
        self.assertEqual(entry.token, self.token)

    async def test_get_session_entry_wrong_token_returns_none(self):
        await self.sessions.add_session(self.email, self.token, self.auth_type)
        entry = await self.sessions.get_session_entry(self.email, "wrong_token")
        self.assertIsNone(entry)

    async def test_get_session_entry_no_session_returns_none(self):
        entry = await self.sessions.get_session_entry(self.email, self.token)
        self.assertIsNone(entry)


if __name__ == "__main__":
    unittest.main()
