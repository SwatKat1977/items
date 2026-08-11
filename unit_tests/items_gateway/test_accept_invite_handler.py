"""
Unit tests for redeeming an invitation:
  GET  /invites/token/<token>  - GetInviteByTokenHandler
  POST /accept_invite          - AcceptInviteHandler

Two behaviours here are security properties rather than conveniences, and
have dedicated tests:

  * The account's email address comes from the invite record, never from the
    submitted body - otherwise an invitation issued to one address could be
    redeemed to create an account for another.
  * The invite is consumed before the account is created, so a failure cannot
    leave a live invite that is redeemable more than once.
"""
import json
import unittest
from http import HTTPStatus
from unittest.mock import AsyncMock, MagicMock
from quart import Quart
from weaver_framework.microservice.api_response import ApiResponse
from items.services.items_gateway.routes.web.invites.accept_invite_handler import (
    AcceptInviteHandler)
from items.services.items_gateway.routes.web.invites.get_invite_by_token_handler import (
    GetInviteByTokenHandler)
from items.services.items_gateway.services.email_service import (
    EmailServiceError)

_LOGGER = MagicMock()
_TOKEN = "550e8400-e29b-41d4-a716-446655440000"
_INVITED = "invitee@example.com"
_PORTAL = "http://portal.example/"

_FORM = {
    "token": _TOKEN,
    "full_name": "Gemma Tester",
    "display_name": "Gemma",
    "password": "a-strong-password",
}


def _config():
    cfg = MagicMock()
    cfg.apis_identity_svc = "http://identity/"
    cfg.apis_web_portal_svc = _PORTAL
    return cfg


class TestAcceptInviteHandler(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.mock_rc = AsyncMock()
        self.mock_email = AsyncMock()
        self.handler = AcceptInviteHandler(_LOGGER, _config(), self.mock_rc,
                                           self.mock_email)

        app = Quart(__name__)

        @app.route("/accept_invite", methods=["POST"])
        async def route():
            return await self.handler.accept_invite()

        self.client = app.test_client()

        # Default happy path: token resolves, consume succeeds, user created.
        self.mock_rc.get.return_value = ApiResponse(
            status_code=HTTPStatus.OK, body={"email_address": _INVITED})
        self._set_post_results(consume_ok=True, create_status=HTTPStatus.CREATED)

    def _set_post_results(self, consume_ok, create_status):
        """Route POSTs by URL: uninvite consumes, users creates."""
        async def post(url, json_data=None, **_kwargs):
            if "uninvite" in url:
                return ApiResponse(
                    status_code=HTTPStatus.OK if consume_ok
                    else HTTPStatus.INTERNAL_SERVER_ERROR,
                    body={})
            return ApiResponse(status_code=create_status,
                               body={"id": "new-user-uuid"})

        self.mock_rc.post.side_effect = post

    async def _post(self, body=None):
        async with self.client as c:
            return await c.post("/accept_invite", json=body or _FORM)

    def _posted_urls(self):
        return [call.args[0] for call in self.mock_rc.post.await_args_list]

    def _create_payload(self):
        for call in self.mock_rc.post.await_args_list:
            if "users" in call.args[0]:
                return call.kwargs["json_data"]
        return None

    # ------------------------------------------------------------------
    # Security properties
    # ------------------------------------------------------------------

    async def test_email_comes_from_the_invite_not_the_request_body(self):
        """A tampered body must not create an account for another address."""
        await self._post({**_FORM, "email_address": "attacker@evil.example"})

        payload = self._create_payload()
        self.assertEqual(payload["email_address"], _INVITED)

    async def test_invite_is_consumed_before_the_account_is_created(self):
        await self._post()

        urls = self._posted_urls()
        consume_at = next(i for i, u in enumerate(urls) if "uninvite" in u)
        create_at = next(i for i, u in enumerate(urls) if "users" in u)
        self.assertLess(consume_at, create_at,
                        "the invite must be consumed before the account is "
                        "created, or a failure leaves it redeemable again")

    async def test_account_is_not_created_if_the_invite_cannot_be_consumed(self):
        self._set_post_results(consume_ok=False,
                               create_status=HTTPStatus.CREATED)

        response = await self._post()

        self.assertEqual(response.status_code,
                         HTTPStatus.INTERNAL_SERVER_ERROR)
        self.assertNotIn("users", " ".join(self._posted_urls()))

    # ------------------------------------------------------------------
    # Token validation
    # ------------------------------------------------------------------

    async def test_unusable_token_returns_404_and_creates_nothing(self):
        self.mock_rc.get.return_value = ApiResponse(
            status_code=HTTPStatus.NOT_FOUND, body={"error": "nope"})

        response = await self._post()

        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.mock_rc.post.assert_not_awaited()

    async def test_identity_unreachable_creates_nothing(self):
        self.mock_rc.get.return_value = ApiResponse(
            status_code=None, exception_msg="connection refused")

        response = await self._post()

        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.mock_rc.post.assert_not_awaited()

    # ------------------------------------------------------------------
    # Request validation
    # ------------------------------------------------------------------

    async def test_missing_fields_are_rejected(self):
        for field in ("token", "full_name", "display_name", "password"):
            with self.subTest(missing=field):
                body = {k: v for k, v in _FORM.items() if k != field}
                async with self.client as c:
                    response = await c.post("/accept_invite", json=body)
                self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)

    async def test_empty_field_is_rejected(self):
        response = await self._post({**_FORM, "password": ""})
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)

    async def test_non_json_body_is_rejected(self):
        async with self.client as c:
            response = await c.post("/accept_invite", data="not json at all")

        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)
        self.mock_rc.get.assert_not_awaited()

    # ------------------------------------------------------------------
    # Success and failure reporting
    # ------------------------------------------------------------------

    async def test_success_returns_201(self):
        response = await self._post()

        self.assertEqual(response.status_code, HTTPStatus.CREATED)

    async def test_welcome_email_is_sent_on_success(self):
        await self._post()

        self.mock_email.send.assert_awaited_once()
        kwargs = self.mock_email.send.await_args.kwargs
        self.assertEqual(kwargs["to"], _INVITED)

    async def test_welcome_email_failure_does_not_fail_the_request(self):
        """The account exists; reporting failure would be misleading."""
        self.mock_email.send.side_effect = EmailServiceError("smtp down")

        response = await self._post()

        self.assertEqual(response.status_code, HTTPStatus.CREATED)

    async def test_creation_failure_after_consuming_asks_for_a_new_invite(self):
        """The invite is spent, so the message must say what to do next."""
        self._set_post_results(
            consume_ok=True, create_status=HTTPStatus.INTERNAL_SERVER_ERROR)

        response = await self._post()

        self.assertEqual(response.status_code,
                         HTTPStatus.INTERNAL_SERVER_ERROR)
        body = json.loads(await response.get_data())
        self.assertIn("new invitation", body["error"].lower())

    async def test_no_welcome_email_when_creation_fails(self):
        self._set_post_results(
            consume_ok=True, create_status=HTTPStatus.INTERNAL_SERVER_ERROR)

        await self._post()

        self.mock_email.send.assert_not_awaited()

    async def test_works_without_an_email_service(self):
        handler = AcceptInviteHandler(_LOGGER, _config(), self.mock_rc, None)
        app = Quart(__name__)

        @app.route("/accept_invite", methods=["POST"])
        async def route():
            return await handler.accept_invite()

        async with app.test_client() as client:
            response = await client.post("/accept_invite", json=_FORM)

        self.assertEqual(response.status_code, HTTPStatus.CREATED)


class TestGetInviteByTokenHandler(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.mock_rc = AsyncMock()
        self.handler = GetInviteByTokenHandler(_LOGGER, _config(),
                                                self.mock_rc)

    async def _call(self):
        return await self.handler.get_invite_by_token(_TOKEN)

    @staticmethod
    async def _body(response):
        return json.loads(await response.get_data())

    async def test_valid_token_returns_the_address(self):
        self.mock_rc.get.return_value = ApiResponse(
            status_code=HTTPStatus.OK, body={"email_address": _INVITED})

        response = await self._call()

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual((await self._body(response))["email_address"],
                         _INVITED)

    async def test_unknown_token_returns_404(self):
        self.mock_rc.get.return_value = ApiResponse(
            status_code=HTTPStatus.NOT_FOUND, body={"error": "nope"})

        response = await self._call()

        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    async def test_identity_unreachable_returns_500(self):
        """Distinguished from 404 so an outage is not read as a bad token."""
        self.mock_rc.get.return_value = ApiResponse(
            status_code=None, exception_msg="connection refused")

        response = await self._call()

        self.assertEqual(response.status_code,
                         HTTPStatus.INTERNAL_SERVER_ERROR)
