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
from unittest.mock import AsyncMock, MagicMock
from weaver_framework.microservice.api_response import ApiResponse
from _test_utils import make_app
from items.services.items_web_portal.page_handlers.auth\
    .accept_invite_page_handler import AcceptInvitePageHandler

_LOGGER = MagicMock()
_TOKEN = "550e8400-e29b-41d4-a716-446655440000"
_INVITED = "invitee@example.com"

_VALID_FORM = {
    "token": _TOKEN,
    "full_name": "Gemma Tester",
    "display_name": "Gemma",
    "password": "a-strong-password",
    "confirm_password": "a-strong-password",
}


def _config():
    config = MagicMock()
    config.apis_gateway_svc = "http://gateway/"
    return config


class TestAcceptInvitePageHandler(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.mock_rest_client = AsyncMock()
        metadata = MagicMock()
        metadata.instance_name = "ITEMS"

        handler = AcceptInvitePageHandler(
            _LOGGER, _config(), self.mock_rest_client, metadata)

        app = make_app()

        @app.route("/accept_invite", methods=["GET"])
        async def accept_get():
            return await handler.accept_invite_get()

        @app.route("/accept_invite", methods=["POST"])
        async def accept_post():
            return await handler.accept_invite_post()

        self.client = app.test_client()

        # Default: the token resolves to an invited address.
        self.mock_rest_client.get.return_value = ApiResponse(
            status_code=HTTPStatus.OK, body={"email_address": _INVITED})
        self.mock_rest_client.post.return_value = ApiResponse(
            status_code=HTTPStatus.CREATED, body={"id": "new-uuid"})

    def _token_invalid(self):
        self.mock_rest_client.get.return_value = ApiResponse(
            status_code=HTTPStatus.NOT_FOUND, body={"error": "nope"})

    async def _get(self, query=""):
        async with self.client as c:
            response = await c.get(f"/accept_invite{query}")
            return await response.get_data(as_text=True)

    async def _post(self, form=None):
        async with self.client as c:
            response = await c.post("/accept_invite", form=form or _VALID_FORM)
            return await response.get_data(as_text=True)

    # ------------------------------------------------------------------
    # GET
    # ------------------------------------------------------------------

    async def test_valid_token_shows_the_form_with_the_invited_address(self):
        text = await self._get(f"?token={_TOKEN}")

        self.assertIn(_INVITED, text)
        self.assertIn("Create my account", text)

    async def test_invited_address_is_not_editable(self):
        text = await self._get(f"?token={_TOKEN}")

        self.assertIn("disabled", text)

    async def test_form_offers_no_role_or_project_selection(self):
        """An invitee must not be able to grant themselves access."""
        text = (await self._get(f"?token={_TOKEN}")).lower()

        self.assertNotIn("is_administrator", text)
        self.assertNotIn("project", text)

    async def test_missing_token_shows_no_form(self):
        text = await self._get()

        self.assertNotIn("Create my account", text)
        self.mock_rest_client.get.assert_not_awaited()

    async def test_unusable_token_shows_no_form(self):
        self._token_invalid()

        text = await self._get(f"?token={_TOKEN}")

        self.assertNotIn("Create my account", text)
        self.assertIn("no longer valid", text)

    # ------------------------------------------------------------------
    # POST - validation
    # ------------------------------------------------------------------

    async def test_mismatched_passwords_are_rejected_without_calling_gateway(self):
        text = await self._post({**_VALID_FORM,
                                 "confirm_password": "something-else"})

        self.assertIn("do not match", text)
        self.mock_rest_client.post.assert_not_awaited()

    async def test_short_password_is_rejected(self):
        text = await self._post({**_VALID_FORM,
                                 "password": "short",
                                 "confirm_password": "short"})

        self.assertIn("at least 8", text)
        self.mock_rest_client.post.assert_not_awaited()

    async def test_missing_names_are_rejected(self):
        for field in ("full_name", "display_name"):
            with self.subTest(missing=field):
                self.mock_rest_client.post.reset_mock()
                text = await self._post({**_VALID_FORM, field: "   "})
                self.assertIn("full name", text.lower())
                self.mock_rest_client.post.assert_not_awaited()

    async def test_rejected_submission_redisplays_the_form(self):
        text = await self._post({**_VALID_FORM,
                                 "confirm_password": "something-else"})

        self.assertIn("Create my account", text)
        self.assertIn(_INVITED, text)

    # ------------------------------------------------------------------
    # POST - submission
    # ------------------------------------------------------------------

    async def test_successful_submission_confirms_the_account(self):
        text = await self._post()

        self.assertIn("Account created", text)
        self.assertNotIn("Create my account", text)

    async def test_submission_never_sends_an_email_address(self):
        """The address is the gateway's to determine, from the invite."""
        await self._post()

        payload = self.mock_rest_client.post.await_args.kwargs["json_data"]
        self.assertNotIn("email_address", payload)
        self.assertEqual(payload["token"], _TOKEN)

    async def test_token_is_revalidated_on_submission(self):
        """A token valid when the page loaded may not be at submit time."""
        self._token_invalid()

        text = await self._post()

        self.assertIn("no longer valid", text)
        self.mock_rest_client.post.assert_not_awaited()

    async def test_gateway_error_is_shown_to_the_user(self):
        self.mock_rest_client.post.return_value = ApiResponse(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            body={"error": "Please ask an administrator for a new invitation."})

        text = await self._post()

        self.assertIn("new invitation", text)

    async def test_missing_token_on_submission_is_rejected(self):
        text = await self._post({**_VALID_FORM, "token": ""})

        self.assertNotIn("Account created", text)
        self.mock_rest_client.post.assert_not_awaited()
