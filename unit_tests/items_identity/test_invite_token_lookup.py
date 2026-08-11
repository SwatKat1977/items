"""
Unit tests for resolving an invitation link to the address it was issued to:
  InviteManagementService.get_invite_by_token
  GET /invites/token/<token>  - GetInviteByTokenHandler

The address an account is created for comes from here, so a token that is
unknown, cancelled or expired must never resolve. All three are reported
identically, so the endpoint cannot be used to probe for valid tokens.
"""
import json
import logging
import time
import unittest
from http import HTTPStatus
from unittest.mock import AsyncMock, MagicMock, patch
from services.invite_management_service import InviteManagementService

_TOKEN = "550e8400-e29b-41d4-a716-446655440000"
_EMAIL = "invitee@example.com"
_NOW = 1_800_000_000

# Row shape: (id, token, email_address, created_at, expires_at,
#             is_expired, expired_at)
def _row(is_expired=0, expires_at=_NOW + 3600):
    return (1, _TOKEN, _EMAIL, _NOW - 3600, expires_at, is_expired, None)


class TestGetInviteByTokenService(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.logger = MagicMock(spec=logging.Logger)
        self.logger.getChild.return_value = MagicMock(spec=logging.Logger)
        self.invite_repo = MagicMock()
        self.invite_repo.get_invite_by_token = AsyncMock()
        self.user_repo = MagicMock()

        self.service = InviteManagementService(
            self.logger, self.invite_repo, self.user_repo)

        patcher = patch("services.invite_management_service.time.time",
                        return_value=_NOW)
        self.addCleanup(patcher.stop)
        patcher.start()

    async def test_valid_token_returns_the_invited_address(self):
        self.invite_repo.get_invite_by_token.return_value = _row()

        result = await self.service.get_invite_by_token(_TOKEN)

        self.assertTrue(result.valid)
        self.assertEqual(result.email_address, _EMAIL)

    async def test_unknown_token_is_not_valid(self):
        self.invite_repo.get_invite_by_token.return_value = None

        result = await self.service.get_invite_by_token("nope")

        self.assertFalse(result.valid)
        self.assertIsNone(result.email_address)

    async def test_cancelled_invite_is_not_valid(self):
        """is_expired is set by an admin uninvite as well as by timeout."""
        self.invite_repo.get_invite_by_token.return_value = _row(is_expired=1)

        result = await self.service.get_invite_by_token(_TOKEN)

        self.assertFalse(result.valid)

    async def test_elapsed_invite_is_not_valid(self):
        self.invite_repo.get_invite_by_token.return_value = _row(
            expires_at=_NOW - 1)

        result = await self.service.get_invite_by_token(_TOKEN)

        self.assertFalse(result.valid)

    async def test_invite_expiring_exactly_now_is_not_valid(self):
        self.invite_repo.get_invite_by_token.return_value = _row(
            expires_at=_NOW)

        result = await self.service.get_invite_by_token(_TOKEN)

        self.assertFalse(result.valid)

    async def test_no_address_leaks_for_any_invalid_case(self):
        """An unusable token must not reveal who was invited."""
        for label, row in (("unknown", None),
                           ("cancelled", _row(is_expired=1)),
                           ("expired", _row(expires_at=_NOW - 1))):
            with self.subTest(case=label):
                self.invite_repo.get_invite_by_token.return_value = row
                result = await self.service.get_invite_by_token(_TOKEN)
                self.assertIsNone(result.email_address)


class TestGetInviteByTokenHandler(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        from routes.invites.get_invite_by_token_handler import (
            GetInviteByTokenHandler)

        self.logger = MagicMock(spec=logging.Logger)
        self.logger.getChild.return_value = MagicMock(spec=logging.Logger)

        with patch("routes.invites.get_invite_by_token_handler."
                   "InviteRepository"), \
             patch("routes.invites.get_invite_by_token_handler."
                   "UserRepository"), \
             patch("routes.invites.get_invite_by_token_handler."
                   "InviteManagementService") as svc_cls:
            self.svc = MagicMock()
            svc_cls.return_value = self.svc
            self.handler = GetInviteByTokenHandler(self.logger, MagicMock())

    @staticmethod
    async def _body(response):
        return json.loads(await response.get_data())

    async def test_valid_token_returns_200_and_address(self):
        result = MagicMock(valid=True, email_address=_EMAIL)
        self.svc.get_invite_by_token = AsyncMock(return_value=result)

        response = await self.handler.get_invite_by_token(_TOKEN)

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual((await self._body(response))["email_address"], _EMAIL)

    async def test_invalid_token_returns_404(self):
        result = MagicMock(valid=False, email_address=None)
        self.svc.get_invite_by_token = AsyncMock(return_value=result)

        response = await self.handler.get_invite_by_token("nope")

        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    async def test_404_body_does_not_reveal_why(self):
        """Expired, cancelled and unknown must be indistinguishable."""
        result = MagicMock(valid=False, email_address=None)
        self.svc.get_invite_by_token = AsyncMock(return_value=result)

        response = await self.handler.get_invite_by_token("nope")

        error = (await self._body(response))["error"].lower()
        for leak in ("expired", "cancelled", "used", "unknown"):
            self.assertNotIn(leak, error)
