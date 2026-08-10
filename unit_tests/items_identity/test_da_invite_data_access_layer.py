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
from unittest.mock import MagicMock, AsyncMock, patch
import logging
from data_access.invite_repository import InviteRepository

_TOKEN = "550e8400-e29b-41d4-a716-446655440000"
_TOKEN2 = "660e8400-e29b-41d4-a716-446655440000"
_EMAIL = "alice@localhost"
_NOW = 1700000000
_EXPIRES = _NOW + (48 * 60 * 60)

# (id, token, email_address, created_at, expires_at, is_expired, expired_at)
_PENDING_ROW = (1, _TOKEN, _EMAIL, _NOW, _EXPIRES, 0, None)
_EXPIRED_ROW = (1, _TOKEN, _EMAIL, _NOW, _EXPIRES, 1, _NOW + 100)


class TestInviteRepository(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.logger = logging.getLogger("test")
        self.mock_config = MagicMock()
        self.mock_config.backend_db_filename = "test.db"

        self.mock_db = MagicMock()
        self.mock_db.run_query = AsyncMock()
        self.mock_db.insert_query = AsyncMock()

        patcher = patch("data_access.invite_repository.SqliteInterface",
                        return_value=self.mock_db)
        self.addCleanup(patcher.stop)
        patcher.start()

        self.repo = InviteRepository(self.logger, self.mock_config)

    # -------------------------------------------------------
    # get_invite_by_token
    # -------------------------------------------------------

    async def test_get_invite_by_token_returns_none_when_not_found(self):
        self.mock_db.run_query.return_value = None
        result = await self.repo.get_invite_by_token(_TOKEN)
        self.assertIsNone(result)

    async def test_get_invite_by_token_returns_row(self):
        self.mock_db.run_query.return_value = _PENDING_ROW
        result = await self.repo.get_invite_by_token(_TOKEN)
        self.assertEqual(result, _PENDING_ROW)

    async def test_get_invite_by_token_passes_correct_query(self):
        self.mock_db.run_query.return_value = None
        await self.repo.get_invite_by_token(_TOKEN)
        self.mock_db.run_query.assert_called_once_with(
            InviteRepository.GET_INVITE_BY_TOKEN_QUERY,
            (_TOKEN,),
            fetch_one=True)

    async def test_get_invite_by_token_query_includes_all_columns(self):
        for col in ("token", "email_address", "created_at", "expires_at",
                    "is_expired", "expired_at"):
            self.assertIn(col, InviteRepository.GET_INVITE_BY_TOKEN_QUERY)

    # -------------------------------------------------------
    # get_invite_by_email
    # -------------------------------------------------------

    async def test_get_invite_by_email_returns_none_when_not_found(self):
        self.mock_db.run_query.return_value = None
        result = await self.repo.get_invite_by_email(_EMAIL)
        self.assertIsNone(result)

    async def test_get_invite_by_email_returns_row(self):
        self.mock_db.run_query.return_value = _PENDING_ROW
        result = await self.repo.get_invite_by_email(_EMAIL)
        self.assertEqual(result, _PENDING_ROW)

    async def test_get_invite_by_email_passes_correct_query(self):
        self.mock_db.run_query.return_value = None
        await self.repo.get_invite_by_email(_EMAIL)
        self.mock_db.run_query.assert_called_once_with(
            InviteRepository.GET_INVITE_BY_EMAIL_QUERY,
            (_EMAIL,),
            fetch_one=True)

    async def test_get_invite_by_email_query_filters_pending_only(self):
        self.assertIn("is_expired = 0",
                      InviteRepository.GET_INVITE_BY_EMAIL_QUERY)

    # -------------------------------------------------------
    # get_pending_invites
    # -------------------------------------------------------

    async def test_get_pending_invites_returns_empty_list_when_none(self):
        self.mock_db.run_query.return_value = None
        result = await self.repo.get_pending_invites()
        self.assertEqual(result, [])

    async def test_get_pending_invites_returns_rows(self):
        self.mock_db.run_query.return_value = [_PENDING_ROW]
        result = await self.repo.get_pending_invites()
        self.assertEqual(result, [_PENDING_ROW])

    async def test_get_pending_invites_passes_correct_query(self):
        self.mock_db.run_query.return_value = None
        await self.repo.get_pending_invites()
        self.mock_db.run_query.assert_called_once_with(
            InviteRepository.GET_PENDING_INVITES_QUERY, ())

    async def test_get_pending_invites_query_filters_pending_only(self):
        self.assertIn("is_expired = 0",
                      InviteRepository.GET_PENDING_INVITES_QUERY)

    async def test_get_pending_invites_query_orders_by_created_at(self):
        self.assertIn("ORDER BY created_at",
                      InviteRepository.GET_PENDING_INVITES_QUERY)

    # -------------------------------------------------------
    # create_invite
    # -------------------------------------------------------

    async def test_create_invite_returns_row_id(self):
        self.mock_db.insert_query.return_value = 42
        result = await self.repo.create_invite(_TOKEN, _EMAIL, _NOW, _EXPIRES)
        self.assertEqual(result, 42)

    async def test_create_invite_passes_correct_query(self):
        self.mock_db.insert_query.return_value = 1
        await self.repo.create_invite(_TOKEN, _EMAIL, _NOW, _EXPIRES)
        self.mock_db.insert_query.assert_called_once_with(
            InviteRepository.INSERT_INVITE_QUERY,
            (_TOKEN, _EMAIL, _NOW, _EXPIRES))

    async def test_insert_query_includes_token_and_email(self):
        for col in ("token", "email_address", "created_at", "expires_at"):
            self.assertIn(col, InviteRepository.INSERT_INVITE_QUERY)

    # -------------------------------------------------------
    # resend_invite
    # -------------------------------------------------------

    async def test_resend_invite_calls_run_query(self):
        await self.repo.resend_invite(_EMAIL, _TOKEN2, _EXPIRES)
        self.mock_db.run_query.assert_called_once_with(
            InviteRepository.RESEND_INVITE_QUERY,
            (_TOKEN2, _EXPIRES, _EMAIL),
            commit=True)

    async def test_resend_invite_query_updates_token_and_expires(self):
        self.assertIn("token", InviteRepository.RESEND_INVITE_QUERY)
        self.assertIn("expires_at", InviteRepository.RESEND_INVITE_QUERY)

    async def test_resend_invite_query_filters_pending_only(self):
        self.assertIn("is_expired = 0", InviteRepository.RESEND_INVITE_QUERY)

    # -------------------------------------------------------
    # uninvite
    # -------------------------------------------------------

    async def test_uninvite_calls_run_query(self):
        await self.repo.uninvite(_EMAIL, _NOW)
        self.mock_db.run_query.assert_called_once_with(
            InviteRepository.SOFT_EXPIRE_BY_EMAIL_QUERY,
            (_NOW, _EMAIL),
            commit=True)

    async def test_uninvite_query_sets_is_expired(self):
        self.assertIn("is_expired = 1",
                      InviteRepository.SOFT_EXPIRE_BY_EMAIL_QUERY)

    async def test_uninvite_query_sets_expired_at(self):
        self.assertIn("expired_at",
                      InviteRepository.SOFT_EXPIRE_BY_EMAIL_QUERY)

    async def test_uninvite_query_filters_pending_only(self):
        self.assertIn("is_expired = 0",
                      InviteRepository.SOFT_EXPIRE_BY_EMAIL_QUERY)

    # -------------------------------------------------------
    # expire_pending_invites
    # -------------------------------------------------------

    async def test_expire_pending_invites_calls_run_query(self):
        await self.repo.expire_pending_invites(_NOW)
        self.mock_db.run_query.assert_called_once_with(
            InviteRepository.SOFT_EXPIRE_PENDING_QUERY,
            (_NOW, _NOW),
            commit=True)

    async def test_expire_pending_query_sets_is_expired(self):
        self.assertIn("is_expired = 1",
                      InviteRepository.SOFT_EXPIRE_PENDING_QUERY)

    async def test_expire_pending_query_filters_pending_only(self):
        self.assertIn("is_expired = 0",
                      InviteRepository.SOFT_EXPIRE_PENDING_QUERY)

    async def test_expire_pending_query_checks_expires_at(self):
        self.assertIn("expires_at", InviteRepository.SOFT_EXPIRE_PENDING_QUERY)


if __name__ == "__main__":
    unittest.main()
