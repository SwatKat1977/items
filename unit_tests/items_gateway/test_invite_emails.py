"""
Unit tests for invitation email delivery.

Creating an invite must email the invitation, and resending must email the
regenerated link. The identity service has no mail capability, so the gateway
is solely responsible for delivery - if these handlers do not send, the invite
is issued and nobody is ever told about it.
"""
import json
import unittest
from http import HTTPStatus
from unittest.mock import AsyncMock, MagicMock, patch
from quart import Quart
from items.services.items_gateway.routes.web.invites import (
    create_invite_routes)
from weaver_framework.microservice.api_response import ApiResponse
from items.services.items_gateway.routes.web.invites.create_invite_handler import (
    CreateInviteHandler)
from items.services.items_gateway.routes.web.invites.resend_invite_handler import (
    ResendInviteHandler)
from items.services.items_gateway.services.email_service import (
    EmailServiceError)
from items.services.items_gateway.services.invite_email import (
    INVITE_SUBJECT, build_invite_url)

_LOGGER = MagicMock()
_RECIPIENT = "newuser@example.com"
_BODY = {"email_address": _RECIPIENT}
_TOKEN = "550e8400-e29b-41d4-a716-446655440000"
_PORTAL = "http://portal.example/"


def _config():
    cfg = MagicMock()
    cfg.apis_identity_svc = "http://identity/"
    cfg.apis_web_portal_svc = _PORTAL
    return cfg


class _InviteEmailCase(unittest.IsolatedAsyncioTestCase):
    """Shared harness; subclasses set HANDLER, PATH, METHOD and OK_STATUS."""

    HANDLER = None
    PATH = None
    METHOD = None
    OK_STATUS = None

    async def asyncSetUp(self):
        if self.HANDLER is None:
            self.skipTest("base class")

        self.mock_rc = AsyncMock()
        self.mock_email = AsyncMock()

        self.handler = self.HANDLER(_LOGGER, _config(), self.mock_rc,
                                    self.mock_email)
        app = Quart(__name__)
        method_name = self.METHOD

        @app.route(self.PATH, methods=["POST"], endpoint="route")
        async def route():
            return await getattr(self.handler, method_name)()

        self.client = app.test_client()

    def _identity_returns(self, status, body):
        self.mock_rc.post.return_value = ApiResponse(status_code=status,
                                                     body=body)

    async def _post(self, body=None):
        async with self.client as c:
            return await c.post(self.PATH, json=body or _BODY)

    # ------------------------------------------------------------------

    async def test_invitation_is_emailed_on_success(self):
        self._identity_returns(self.OK_STATUS, {"token": _TOKEN})

        await self._post()

        self.mock_email.send.assert_awaited_once()
        kwargs = self.mock_email.send.await_args.kwargs
        self.assertEqual(kwargs["to"], _RECIPIENT)
        self.assertEqual(kwargs["subject"], INVITE_SUBJECT)

    async def test_email_contains_the_token_link(self):
        self._identity_returns(self.OK_STATUS, {"token": _TOKEN})

        await self._post()

        body = self.mock_email.send.await_args.kwargs["body"]
        self.assertIn(build_invite_url(_PORTAL, _TOKEN), body)
        self.assertIn(_TOKEN, body)

    async def test_no_email_when_identity_rejects_the_request(self):
        self._identity_returns(HTTPStatus.CONFLICT,
                               {"error": "already invited"})

        await self._post()

        self.mock_email.send.assert_not_awaited()

    async def test_no_email_when_identity_is_unreachable(self):
        self.mock_rc.post.return_value = ApiResponse(
            status_code=None, exception_msg="connection refused")

        await self._post()

        self.mock_email.send.assert_not_awaited()

    async def test_no_email_when_response_has_no_token(self):
        self._identity_returns(self.OK_STATUS, {})

        await self._post()

        self.mock_email.send.assert_not_awaited()

    async def test_delivery_failure_does_not_fail_the_request(self):
        """The invite exists; reporting failure would be misleading."""
        self._identity_returns(self.OK_STATUS, {"token": _TOKEN})
        self.mock_email.send.side_effect = EmailServiceError("smtp down")

        response = await self._post()

        self.assertEqual(response.status_code, self.OK_STATUS)
        body = json.loads(await response.get_data())
        self.assertEqual(body["token"], _TOKEN)

    async def test_works_when_no_email_service_is_configured(self):
        """Mail being unconfigured must not break invite creation."""
        handler = self.HANDLER(_LOGGER, _config(), self.mock_rc, None)
        app = Quart(__name__)
        method_name = self.METHOD

        @app.route(self.PATH, methods=["POST"], endpoint="route_no_mail")
        async def route():
            return await getattr(handler, method_name)()

        self._identity_returns(self.OK_STATUS, {"token": _TOKEN})

        async with app.test_client() as client:
            response = await client.post(self.PATH, json=_BODY)

        self.assertEqual(response.status_code, self.OK_STATUS)


class TestCreateInviteSendsEmail(_InviteEmailCase):
    HANDLER = CreateInviteHandler
    PATH = "/invites"
    METHOD = "create_invite"
    OK_STATUS = HTTPStatus.CREATED


class TestResendInviteSendsEmail(_InviteEmailCase):
    HANDLER = ResendInviteHandler
    PATH = "/invites/resend"
    METHOD = "resend_invite"
    OK_STATUS = HTTPStatus.OK


class TestInviteBlueprintWiring(unittest.IsolatedAsyncioTestCase):
    """The original defect was here: the handlers were constructed without the
    email service, so no invitation was ever sent."""

    async def test_create_and_resend_receive_the_email_service(self):
        injections = MagicMock()
        injections.email_service = MagicMock(name="email_service")

        with patch("items.services.items_gateway.routes.web.invites"
                   ".CreateInviteHandler") as create_cls, \
             patch("items.services.items_gateway.routes.web.invites"
                   ".ResendInviteHandler") as resend_cls:
            create_invite_routes(injections)

        for name, cls in (("CreateInviteHandler", create_cls),
                          ("ResendInviteHandler", resend_cls)):
            self.assertIn(injections.email_service, cls.call_args.args,
                          f"{name} was not given the email service")
