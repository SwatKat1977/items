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
from unittest.mock import AsyncMock, MagicMock, patch
import logging
from services.invite_management_service import (
    InviteManagementService,
    InviteCreateStatus,
    InviteResendStatus,
    InviteUninviteStatus)

_TOKEN = "550e8400-e29b-41d4-a716-446655440000"
_TOKEN2 = "660e8400-e29b-41d4-a716-446655440000"
_EMAIL = "alice@localhost"
_NOW = 1700000000
_EXPIRES = _NOW + (48 * 60 * 60)

# (id, token, email_address, created_at, expires_at, is_expired, expired_at)
_PENDING_ROW = (1, _TOKEN, _EMAIL, _NOW, _EXPIRES, 0, None)


class TestInviteManagementService(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.logger = logging.getLogger("test")
        self.mock_invite_repo = MagicMock()
        self.mock_invite_repo.get_invite_by_email = AsyncMock()
        self.mock_invite_repo.get_invite_by_token = AsyncMock()
        self.mock_invite_repo.create_invite = AsyncMock()
        self.mock_invite_repo.resend_invite = AsyncMock()
        self.mock_invite_repo.uninvite = AsyncMock()
        self.mock_invite_repo.expire_pending_invites = AsyncMock()

        self.mock_user_repo = MagicMock()
        self.mock_user_repo.get_user_by_email = AsyncMock(return_value=None)

        self.service = InviteManagementService(
            self.logger, self.mock_invite_repo, self.mock_user_repo)

    # -------------------------------------------------------
    # create_invite
    # -------------------------------------------------------

    async def test_create_invite_success(self):
        self.mock_invite_repo.get_invite_by_email.return_value = None
        with patch("services.invite_management_service.uuid_mod.uuid4",
                   return_value=_TOKEN):
            result = await self.service.create_invite(_EMAIL)
        self.assertEqual(result.status, InviteCreateStatus.SUCCESS)
        self.assertEqual(result.token, str(_TOKEN))

    async def test_create_invite_calls_repo_with_token_and_email(self):
        self.mock_invite_repo.get_invite_by_email.return_value = None
        with patch("services.invite_management_service.uuid_mod.uuid4",
                   return_value=_TOKEN):
            await self.service.create_invite(_EMAIL)
        args = self.mock_invite_repo.create_invite.call_args[0]
        self.assertEqual(args[0], str(_TOKEN))
        self.assertEqual(args[1], _EMAIL)

    async def test_create_invite_sets_48h_expiry(self):
        self.mock_invite_repo.get_invite_by_email.return_value = None
        with patch("services.invite_management_service.uuid_mod.uuid4",
                   return_value=_TOKEN), \
             patch("services.invite_management_service.time.time",
                   return_value=_NOW):
            await self.service.create_invite(_EMAIL)
        args = self.mock_invite_repo.create_invite.call_args[0]
        self.assertEqual(args[3], _NOW + 48 * 60 * 60)

    async def test_create_invite_returns_already_registered_if_user_exists(self):
        self.mock_user_repo.get_user_by_email.return_value = (1, "uuid", _EMAIL)
        result = await self.service.create_invite(_EMAIL)
        self.assertEqual(result.status, InviteCreateStatus.ALREADY_REGISTERED)
        self.assertIsNone(result.token)
        self.mock_invite_repo.create_invite.assert_not_called()

    async def test_create_invite_returns_already_invited_if_pending_exists(self):
        self.mock_invite_repo.get_invite_by_email.return_value = _PENDING_ROW
        result = await self.service.create_invite(_EMAIL)
        self.assertEqual(result.status, InviteCreateStatus.ALREADY_INVITED)
        self.assertIsNone(result.token)
        self.mock_invite_repo.create_invite.assert_not_called()

    async def test_create_invite_checks_user_before_invite(self):
        """User check must happen before invite check."""
        self.mock_user_repo.get_user_by_email.return_value = (1, "uuid", _EMAIL)
        await self.service.create_invite(_EMAIL)
        self.mock_invite_repo.get_invite_by_email.assert_not_called()

    # -------------------------------------------------------
    # resend_invite
    # -------------------------------------------------------

    async def test_resend_invite_success(self):
        self.mock_invite_repo.get_invite_by_email.return_value = _PENDING_ROW
        with patch("services.invite_management_service.uuid_mod.uuid4",
                   return_value=_TOKEN2):
            result = await self.service.resend_invite(_EMAIL)
        self.assertEqual(result.status, InviteResendStatus.SUCCESS)
        self.assertEqual(result.token, str(_TOKEN2))

    async def test_resend_invite_calls_repo_with_new_token(self):
        self.mock_invite_repo.get_invite_by_email.return_value = _PENDING_ROW
        with patch("services.invite_management_service.uuid_mod.uuid4",
                   return_value=_TOKEN2):
            await self.service.resend_invite(_EMAIL)
        self.mock_invite_repo.resend_invite.assert_awaited_once()
        args = self.mock_invite_repo.resend_invite.call_args[0]
        self.assertEqual(args[0], _EMAIL)
        self.assertEqual(args[1], str(_TOKEN2))

    async def test_resend_invite_resets_48h_expiry(self):
        self.mock_invite_repo.get_invite_by_email.return_value = _PENDING_ROW
        with patch("services.invite_management_service.uuid_mod.uuid4",
                   return_value=_TOKEN2), \
             patch("services.invite_management_service.time.time",
                   return_value=_NOW):
            await self.service.resend_invite(_EMAIL)
        args = self.mock_invite_repo.resend_invite.call_args[0]
        self.assertEqual(args[2], _NOW + 48 * 60 * 60)

    async def test_resend_invite_returns_no_pending_invite_when_none_found(self):
        self.mock_invite_repo.get_invite_by_email.return_value = None
        result = await self.service.resend_invite(_EMAIL)
        self.assertEqual(result.status, InviteResendStatus.NO_PENDING_INVITE)
        self.assertIsNone(result.token)
        self.mock_invite_repo.resend_invite.assert_not_called()

    # -------------------------------------------------------
    # uninvite
    # -------------------------------------------------------

    async def test_uninvite_success(self):
        self.mock_invite_repo.get_invite_by_email.return_value = _PENDING_ROW
        result = await self.service.uninvite(_EMAIL)
        self.assertEqual(result.status, InviteUninviteStatus.SUCCESS)

    async def test_uninvite_calls_repo_uninvite(self):
        self.mock_invite_repo.get_invite_by_email.return_value = _PENDING_ROW
        with patch("services.invite_management_service.time.time",
                   return_value=_NOW):
            await self.service.uninvite(_EMAIL)
        self.mock_invite_repo.uninvite.assert_awaited_once_with(_EMAIL, _NOW)

    async def test_uninvite_returns_no_pending_invite_when_none_found(self):
        self.mock_invite_repo.get_invite_by_email.return_value = None
        result = await self.service.uninvite(_EMAIL)
        self.assertEqual(result.status, InviteUninviteStatus.NO_PENDING_INVITE)
        self.mock_invite_repo.uninvite.assert_not_called()

    # -------------------------------------------------------
    # expire_pending_invites
    # -------------------------------------------------------

    async def test_expire_pending_invites_calls_repo(self):
        with patch("services.invite_management_service.time.time",
                   return_value=_NOW):
            await self.service.expire_pending_invites()
        self.mock_invite_repo.expire_pending_invites.assert_awaited_once_with(_NOW)

    async def test_expire_pending_invites_returns_zero(self):
        result = await self.service.expire_pending_invites()
        self.assertEqual(result, 0)


if __name__ == "__main__":
    unittest.main()
