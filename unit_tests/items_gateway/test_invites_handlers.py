"""
Unit tests for gateway invite management route handlers:
  POST /invites            - CreateInviteHandler
  POST /invites/resend     - ResendInviteHandler
  POST /invites/uninvite   - UninviteHandler
"""
import json
import unittest
from unittest.mock import AsyncMock, MagicMock
from quart import Quart
from weaver_framework.microservice.api_response import ApiResponse
from items.services.items_gateway.routes.web.invites.create_invite_handler import (
    CreateInviteHandler)
from items.services.items_gateway.routes.web.invites.resend_invite_handler import (
    ResendInviteHandler)
from items.services.items_gateway.routes.web.invites.uninvite_handler import (
    UninviteHandler)

_LOGGER = MagicMock()
_EMAIL_BODY = {"email_address": "newuser@example.com"}


def _config():
    cfg = MagicMock()
    cfg.apis_identity_svc = "http://identity/"
    return cfg


def _err(body, status=500):
    return ApiResponse(status_code=status, body=body)


def _conn_err():
    return ApiResponse(status_code=None, exception_msg="connection refused")


# ---------------------------------------------------------------------------
# CreateInviteHandler
# ---------------------------------------------------------------------------

class TestCreateInviteHandler(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.mock_rc = AsyncMock()
        handler = CreateInviteHandler(_LOGGER, _config(), self.mock_rc)
        app = Quart(__name__)

        @app.route("/invites", methods=["POST"])
        async def route():
            return await handler.create_invite()

        self.client = app.test_client()

    async def _post(self, body):
        async with self.client as c:
            return await c.post("/invites", json=body)

    async def test_success_returns_201_with_token(self):
        self.mock_rc.post.return_value = ApiResponse(
            status_code=201, body={"token": "abc123"})
        resp = await self._post(_EMAIL_BODY)
        self.assertEqual(resp.status_code, 201)
        body = json.loads(await resp.get_data())
        self.assertEqual(body["token"], "abc123")

    async def test_body_forwarded_to_identity(self):
        self.mock_rc.post.return_value = ApiResponse(
            status_code=201, body={"token": "abc123"})
        await self._post(_EMAIL_BODY)
        args, kwargs = self.mock_rc.post.call_args
        self.assertEqual(args[0], "http://identity/invites")
        self.assertEqual(kwargs["json_data"], _EMAIL_BODY)

    async def test_already_registered_409_is_propagated(self):
        self.mock_rc.post.return_value = _err(
            {"error": "Email address is already registered"}, 409)
        resp = await self._post(_EMAIL_BODY)
        self.assertEqual(resp.status_code, 409)

    async def test_already_invited_409_is_propagated(self):
        self.mock_rc.post.return_value = _err(
            {"error": "A pending invite already exists for this email"}, 409)
        resp = await self._post(_EMAIL_BODY)
        self.assertEqual(resp.status_code, 409)

    async def test_missing_body_returns_400(self):
        async with self.client as c:
            resp = await c.post("/invites", data="not json",
                                headers={"Content-Type": "text/plain"})
        self.assertEqual(resp.status_code, 400)
        self.mock_rc.post.assert_not_called()

    async def test_connection_error_returns_500(self):
        self.mock_rc.post.return_value = _conn_err()
        resp = await self._post(_EMAIL_BODY)
        self.assertEqual(resp.status_code, 500)

    async def test_non_json_downstream_response_returns_500(self):
        # e.g. a stale identity deployment serving its own generic HTML
        # error page for a route it doesn't have.
        self.mock_rc.post.return_value = ApiResponse(
            status_code=404, body="<!doctype html><h1>Not Found</h1>",
            content_type="text/html")
        resp = await self._post(_EMAIL_BODY)
        self.assertEqual(resp.status_code, 500)
        body = json.loads(await resp.get_data())
        self.assertIn("unexpected response", body["error"])

    async def test_response_is_json(self):
        self.mock_rc.post.return_value = ApiResponse(
            status_code=201, body={"token": "abc123"})
        resp = await self._post(_EMAIL_BODY)
        self.assertEqual(resp.content_type, "application/json")


# ---------------------------------------------------------------------------
# ResendInviteHandler
# ---------------------------------------------------------------------------

class TestResendInviteHandler(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.mock_rc = AsyncMock()
        handler = ResendInviteHandler(_LOGGER, _config(), self.mock_rc)
        app = Quart(__name__)

        @app.route("/invites/resend", methods=["POST"])
        async def route():
            return await handler.resend_invite()

        self.client = app.test_client()

    async def _post(self, body):
        async with self.client as c:
            return await c.post("/invites/resend", json=body)

    async def test_success_returns_200_with_new_token(self):
        self.mock_rc.post.return_value = ApiResponse(
            status_code=200, body={"token": "new-token"})
        resp = await self._post(_EMAIL_BODY)
        self.assertEqual(resp.status_code, 200)
        body = json.loads(await resp.get_data())
        self.assertEqual(body["token"], "new-token")

    async def test_body_forwarded_to_identity(self):
        self.mock_rc.post.return_value = ApiResponse(
            status_code=200, body={"token": "new-token"})
        await self._post(_EMAIL_BODY)
        args, kwargs = self.mock_rc.post.call_args
        self.assertEqual(args[0], "http://identity/invites/resend")
        self.assertEqual(kwargs["json_data"], _EMAIL_BODY)

    async def test_no_pending_invite_404_is_propagated(self):
        self.mock_rc.post.return_value = _err(
            {"error": "No pending invite found for this email address"}, 404)
        resp = await self._post(_EMAIL_BODY)
        self.assertEqual(resp.status_code, 404)

    async def test_missing_body_returns_400(self):
        async with self.client as c:
            resp = await c.post("/invites/resend", data="not json",
                                headers={"Content-Type": "text/plain"})
        self.assertEqual(resp.status_code, 400)
        self.mock_rc.post.assert_not_called()

    async def test_connection_error_returns_500(self):
        self.mock_rc.post.return_value = _conn_err()
        resp = await self._post(_EMAIL_BODY)
        self.assertEqual(resp.status_code, 500)

    async def test_non_json_downstream_response_returns_500(self):
        self.mock_rc.post.return_value = ApiResponse(
            status_code=404, body="<!doctype html><h1>Not Found</h1>",
            content_type="text/html")
        resp = await self._post(_EMAIL_BODY)
        self.assertEqual(resp.status_code, 500)
        body = json.loads(await resp.get_data())
        self.assertIn("unexpected response", body["error"])


# ---------------------------------------------------------------------------
# UninviteHandler
# ---------------------------------------------------------------------------

class TestUninviteHandler(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.mock_rc = AsyncMock()
        handler = UninviteHandler(_LOGGER, _config(), self.mock_rc)
        app = Quart(__name__)

        @app.route("/invites/uninvite", methods=["POST"])
        async def route():
            return await handler.uninvite()

        self.client = app.test_client()

    async def _post(self, body):
        async with self.client as c:
            return await c.post("/invites/uninvite", json=body)

    async def test_success_returns_200(self):
        self.mock_rc.post.return_value = ApiResponse(status_code=200, body={})
        resp = await self._post(_EMAIL_BODY)
        self.assertEqual(resp.status_code, 200)

    async def test_body_forwarded_to_identity(self):
        self.mock_rc.post.return_value = ApiResponse(status_code=200, body={})
        await self._post(_EMAIL_BODY)
        args, kwargs = self.mock_rc.post.call_args
        self.assertEqual(args[0], "http://identity/invites/uninvite")
        self.assertEqual(kwargs["json_data"], _EMAIL_BODY)

    async def test_no_pending_invite_404_is_propagated(self):
        self.mock_rc.post.return_value = _err(
            {"error": "No pending invite found for this email address"}, 404)
        resp = await self._post(_EMAIL_BODY)
        self.assertEqual(resp.status_code, 404)

    async def test_missing_body_returns_400(self):
        async with self.client as c:
            resp = await c.post("/invites/uninvite", data="not json",
                                headers={"Content-Type": "text/plain"})
        self.assertEqual(resp.status_code, 400)
        self.mock_rc.post.assert_not_called()

    async def test_connection_error_returns_500(self):
        self.mock_rc.post.return_value = _conn_err()
        resp = await self._post(_EMAIL_BODY)
        self.assertEqual(resp.status_code, 500)

    async def test_non_json_downstream_response_returns_500(self):
        self.mock_rc.post.return_value = ApiResponse(
            status_code=404, body="<!doctype html><h1>Not Found</h1>",
            content_type="text/html")
        resp = await self._post(_EMAIL_BODY)
        self.assertEqual(resp.status_code, 500)
        body = json.loads(await resp.get_data())
        self.assertIn("unexpected response", body["error"])


if __name__ == "__main__":
    unittest.main()
