"""
Handler-level tests for the invite management API endpoints:
  POST /invites          - CreateInviteHandler
  POST /invites/resend   - ResendInviteHandler
  POST /invites/uninvite - UninviteHandler
"""
import unittest
import json
import logging
from http import HTTPStatus
from unittest.mock import patch, MagicMock, AsyncMock
from routes.invites.create_invite_handler import CreateInviteHandler
from routes.invites.resend_invite_handler import ResendInviteHandler
from routes.invites.uninvite_handler import UninviteHandler
from items.services.items_identity.services.invite_management_service import (
    InviteCreateResult,
    InviteCreateStatus,
    InviteResendResult,
    InviteResendStatus,
    InviteUninviteResult,
    InviteUninviteStatus,
)

_TOKEN = "550e8400-e29b-41d4-a716-446655440000"
_TOKEN2 = "660e8400-e29b-41d4-a716-446655440000"
_EMAIL = "alice@localhost"


def _undecorated(method):
    return getattr(method, "__wrapped__", method)


def _make_app():
    from quart import Quart
    app = Quart(__name__)
    app.config["TESTING"] = True
    return app


def _make_request(body: dict):
    from weaver_framework.microservice.api_response import ApiResponse
    return ApiResponse(status_code=HTTPStatus.OK, body=body)


def _make_handler_setup(handler_cls, module_name: str):
    """Return asyncSetUp that wires handler with mocked InviteManagementService."""
    async def asyncSetUp(self):
        self.mock_logger = MagicMock(spec=logging.Logger)
        self.mock_logger.getChild.return_value = MagicMock(spec=logging.Logger)
        self.mock_config = MagicMock()

        invite_repo_patch = patch(
            f"routes.invites.{module_name}.InviteRepository", autospec=True)
        user_repo_patch = patch(
            f"routes.invites.{module_name}.UserRepository", autospec=True)
        svc_patch = patch(
            f"routes.invites.{module_name}.InviteManagementService", autospec=True)

        self.addCleanup(invite_repo_patch.stop)
        self.addCleanup(user_repo_patch.stop)
        self.addCleanup(svc_patch.stop)

        invite_repo_patch.start()
        user_repo_patch.start()
        self.mock_svc_cls = svc_patch.start()

        self.mock_svc = MagicMock()
        self.mock_svc_cls.return_value = self.mock_svc

        self.handler = handler_cls(self.mock_logger, self.mock_config)

    return asyncSetUp


# ---------------------------------------------------------------------------
# CreateInviteHandler
# ---------------------------------------------------------------------------

class TestCreateInviteHandler(unittest.IsolatedAsyncioTestCase):

    asyncSetUp = _make_handler_setup(CreateInviteHandler, "create_invite_handler")

    async def _call(self, email: str = _EMAIL):
        app = _make_app()
        async with app.app_context():
            return await _undecorated(self.handler.create_invite)(
                self.handler, _make_request({"email_address": email}))

    async def test_success_returns_201(self):
        self.mock_svc.create_invite = AsyncMock(
            return_value=InviteCreateResult(
                status=InviteCreateStatus.SUCCESS, token=_TOKEN))
        response = await self._call()
        self.assertEqual(response.status_code, HTTPStatus.CREATED)

    async def test_success_returns_token_in_body(self):
        self.mock_svc.create_invite = AsyncMock(
            return_value=InviteCreateResult(
                status=InviteCreateStatus.SUCCESS, token=_TOKEN))
        response = await self._call()
        body = json.loads(await response.get_data())
        self.assertEqual(body["token"], _TOKEN)

    async def test_email_passed_to_service(self):
        self.mock_svc.create_invite = AsyncMock(
            return_value=InviteCreateResult(
                status=InviteCreateStatus.SUCCESS, token=_TOKEN))
        await self._call(email=_EMAIL)
        self.mock_svc.create_invite.assert_awaited_once_with(_EMAIL)

    async def test_already_registered_returns_409(self):
        self.mock_svc.create_invite = AsyncMock(
            return_value=InviteCreateResult(
                status=InviteCreateStatus.ALREADY_REGISTERED))
        response = await self._call()
        self.assertEqual(response.status_code, HTTPStatus.CONFLICT)

    async def test_already_registered_error_message(self):
        self.mock_svc.create_invite = AsyncMock(
            return_value=InviteCreateResult(
                status=InviteCreateStatus.ALREADY_REGISTERED))
        response = await self._call()
        body = json.loads(await response.get_data())
        self.assertIn("already registered", body["error"])

    async def test_already_invited_returns_409(self):
        self.mock_svc.create_invite = AsyncMock(
            return_value=InviteCreateResult(
                status=InviteCreateStatus.ALREADY_INVITED))
        response = await self._call()
        self.assertEqual(response.status_code, HTTPStatus.CONFLICT)

    async def test_already_invited_error_message(self):
        self.mock_svc.create_invite = AsyncMock(
            return_value=InviteCreateResult(
                status=InviteCreateStatus.ALREADY_INVITED))
        response = await self._call()
        body = json.loads(await response.get_data())
        self.assertIn("pending invite", body["error"])


# ---------------------------------------------------------------------------
# ResendInviteHandler
# ---------------------------------------------------------------------------

class TestResendInviteHandler(unittest.IsolatedAsyncioTestCase):

    asyncSetUp = _make_handler_setup(ResendInviteHandler, "resend_invite_handler")

    async def _call(self, email: str = _EMAIL):
        app = _make_app()
        async with app.app_context():
            return await _undecorated(self.handler.resend_invite)(
                self.handler, _make_request({"email_address": email}))

    async def test_success_returns_200(self):
        self.mock_svc.resend_invite = AsyncMock(
            return_value=InviteResendResult(
                status=InviteResendStatus.SUCCESS, token=_TOKEN2))
        response = await self._call()
        self.assertEqual(response.status_code, HTTPStatus.OK)

    async def test_success_returns_new_token(self):
        self.mock_svc.resend_invite = AsyncMock(
            return_value=InviteResendResult(
                status=InviteResendStatus.SUCCESS, token=_TOKEN2))
        response = await self._call()
        body = json.loads(await response.get_data())
        self.assertEqual(body["token"], _TOKEN2)

    async def test_email_passed_to_service(self):
        self.mock_svc.resend_invite = AsyncMock(
            return_value=InviteResendResult(
                status=InviteResendStatus.SUCCESS, token=_TOKEN2))
        await self._call(email=_EMAIL)
        self.mock_svc.resend_invite.assert_awaited_once_with(_EMAIL)

    async def test_no_pending_invite_returns_404(self):
        self.mock_svc.resend_invite = AsyncMock(
            return_value=InviteResendResult(
                status=InviteResendStatus.NO_PENDING_INVITE))
        response = await self._call()
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    async def test_no_pending_invite_error_message(self):
        self.mock_svc.resend_invite = AsyncMock(
            return_value=InviteResendResult(
                status=InviteResendStatus.NO_PENDING_INVITE))
        response = await self._call()
        body = json.loads(await response.get_data())
        self.assertIn("No pending invite", body["error"])


# ---------------------------------------------------------------------------
# UninviteHandler
# ---------------------------------------------------------------------------

class TestUninviteHandler(unittest.IsolatedAsyncioTestCase):

    asyncSetUp = _make_handler_setup(UninviteHandler, "uninvite_handler")

    async def _call(self, email: str = _EMAIL):
        app = _make_app()
        async with app.app_context():
            return await _undecorated(self.handler.uninvite)(
                self.handler, _make_request({"email_address": email}))

    async def test_success_returns_200(self):
        self.mock_svc.uninvite = AsyncMock(
            return_value=InviteUninviteResult(
                status=InviteUninviteStatus.SUCCESS))
        response = await self._call()
        self.assertEqual(response.status_code, HTTPStatus.OK)

    async def test_email_passed_to_service(self):
        self.mock_svc.uninvite = AsyncMock(
            return_value=InviteUninviteResult(
                status=InviteUninviteStatus.SUCCESS))
        await self._call(email=_EMAIL)
        self.mock_svc.uninvite.assert_awaited_once_with(_EMAIL)

    async def test_no_pending_invite_returns_404(self):
        self.mock_svc.uninvite = AsyncMock(
            return_value=InviteUninviteResult(
                status=InviteUninviteStatus.NO_PENDING_INVITE))
        response = await self._call()
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    async def test_no_pending_invite_error_message(self):
        self.mock_svc.uninvite = AsyncMock(
            return_value=InviteUninviteResult(
                status=InviteUninviteStatus.NO_PENDING_INVITE))
        response = await self._call()
        body = json.loads(await response.get_data())
        self.assertIn("No pending invite", body["error"])


if __name__ == "__main__":
    unittest.main()
