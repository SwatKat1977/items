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
from unittest.mock import AsyncMock, MagicMock
from quart import Quart
from weaver_framework.microservice.api_response import ApiResponse
from items.services.items_gateway.routes.web.sessions.new_session_password_handler \
    import NewSessionPasswordHandler
from items.services.items_gateway.routes.web.sessions.delete_session_handler \
    import DeleteSessionHandler
from items.services.items_gateway.routes.web.sessions.refresh_session_handler \
    import RefreshSessionHandler
from items.services.items_gateway.routes.web.sessions.validate_session_handler \
    import ValidateSessionHandler
from items.services.items_gateway.sessions import SessionEntry

_LOGGER = MagicMock()
_VALID_TOKEN = "a" * 32


# ------------------------------------------------------------------
# NewSessionPasswordHandler
# ------------------------------------------------------------------

class TestNewSessionPasswordHandler(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.mock_sessions = AsyncMock()
        self.mock_config = MagicMock()
        self.mock_config.apis_identity_svc = "http://identity/"
        self.mock_rest_client = AsyncMock()
        handler = NewSessionPasswordHandler(
            _LOGGER, self.mock_sessions, self.mock_config, self.mock_rest_client)

        app = Quart(__name__)

        @app.route("/sessions", methods=["POST"])
        async def create_session():
            return await handler.create_new_session()

        self.client = app.test_client()

    async def _post(self, body):
        async with self.client as c:
            return await c.post("/sessions", json=body)

    async def test_missing_fields_returns_400(self):
        response = await self._post({"email_address": "a@b.com"})
        self.assertEqual(response.status_code, 400)
        self.mock_rest_client.post.assert_not_called()

    async def test_identity_connection_failure_returns_500(self):
        self.mock_rest_client.post.return_value = ApiResponse(
            status_code=None, exception_msg="connection refused")
        response = await self._post(
            {"email_address": "a@b.com", "password": "password1"})
        self.assertEqual(response.status_code, 500)

    async def test_identity_unauthorized_returns_401(self):
        self.mock_rest_client.post.return_value = ApiResponse(status_code=401)
        response = await self._post(
            {"email_address": "a@b.com", "password": "password1"})
        self.assertEqual(response.status_code, 401)

    async def test_identity_other_error_returns_500(self):
        self.mock_rest_client.post.return_value = ApiResponse(status_code=503)
        response = await self._post(
            {"email_address": "a@b.com", "password": "password1"})
        self.assertEqual(response.status_code, 500)

    async def test_success_new_login(self):
        self.mock_sessions.has_session.return_value = False
        self.mock_rest_client.post.side_effect = [
            ApiResponse(status_code=200),
            ApiResponse(status_code=200, body={"is_administrator": False})
        ]
        response = await self._post(
            {"email_address": "a@b.com", "password": "password1"})
        self.assertEqual(response.status_code, 200)
        data = await response.get_json()
        self.assertEqual(data["status"], 1)
        self.mock_sessions.add_session.assert_called_once()

    async def test_success_relogin(self):
        self.mock_sessions.has_session.return_value = True
        self.mock_rest_client.post.side_effect = [
            ApiResponse(status_code=200),
            ApiResponse(status_code=200, body={"is_administrator": False})
        ]
        response = await self._post(
            {"email_address": "a@b.com", "password": "password1"})
        self.assertEqual(response.status_code, 200)
        self.mock_sessions.add_session.assert_called_once()

    async def test_success_stores_is_administrator_true(self):
        self.mock_sessions.has_session.return_value = False
        self.mock_rest_client.post.side_effect = [
            ApiResponse(status_code=200),
            ApiResponse(status_code=200, body={"is_administrator": True})
        ]
        await self._post({"email_address": "a@b.com", "password": "password1"})
        args, kwargs = self.mock_sessions.add_session.call_args
        # is_administrator may be passed positionally (index 3) or as a kwarg
        is_admin = kwargs.get("is_administrator", args[3] if len(args) > 3 else False)
        self.assertTrue(is_admin)

    async def test_profile_fetch_failure_defaults_is_administrator_false(self):
        self.mock_sessions.has_session.return_value = False
        self.mock_rest_client.post.side_effect = [
            ApiResponse(status_code=200),
            ApiResponse(status_code=503)
        ]
        response = await self._post(
            {"email_address": "a@b.com", "password": "password1"})
        self.assertEqual(response.status_code, 200)
        args, kwargs = self.mock_sessions.add_session.call_args
        is_admin = kwargs.get("is_administrator", args[3] if len(args) > 3 else False)
        self.assertFalse(is_admin)

    async def test_success_stores_user_id_from_profile(self):
        self.mock_sessions.has_session.return_value = False
        self.mock_rest_client.post.side_effect = [
            ApiResponse(status_code=200),
            ApiResponse(status_code=200,
                       body={"is_administrator": False, "id": "uuid-123"})
        ]
        self.mock_rest_client.get.return_value = ApiResponse(
            status_code=200, body={"memberships": []})
        await self._post({"email_address": "a@b.com", "password": "password1"})
        _, kwargs = self.mock_sessions.add_session.call_args
        self.assertEqual(kwargs["user_id"], "uuid-123")

    async def test_success_stores_project_ids_from_memberships(self):
        self.mock_sessions.has_session.return_value = False
        self.mock_rest_client.post.side_effect = [
            ApiResponse(status_code=200),
            ApiResponse(status_code=200,
                       body={"is_administrator": False, "id": "uuid-123"})
        ]
        self.mock_rest_client.get.return_value = ApiResponse(
            status_code=200, body={"memberships": [
                {"project_id": 5, "role_id": 1},
                {"project_id": 7, "role_id": None}]})
        await self._post({"email_address": "a@b.com", "password": "password1"})
        _, kwargs = self.mock_sessions.add_session.call_args
        self.assertEqual(kwargs["project_ids"], frozenset({5, 7}))

    async def test_membership_fetch_uses_the_resolved_user_id(self):
        self.mock_sessions.has_session.return_value = False
        self.mock_rest_client.post.side_effect = [
            ApiResponse(status_code=200),
            ApiResponse(status_code=200,
                       body={"is_administrator": False, "id": "uuid-123"})
        ]
        self.mock_rest_client.get.return_value = ApiResponse(
            status_code=200, body={"memberships": []})
        await self._post({"email_address": "a@b.com", "password": "password1"})
        self.mock_rest_client.get.assert_called_once_with(
            "http://identity/users/uuid-123/projects")

    async def test_no_user_id_skips_membership_fetch(self):
        """A failed/empty profile fetch leaves user_id empty - nothing to
        look memberships up by, so don't bother calling identity again."""
        self.mock_sessions.has_session.return_value = False
        self.mock_rest_client.post.side_effect = [
            ApiResponse(status_code=200),
            ApiResponse(status_code=503)
        ]
        await self._post({"email_address": "a@b.com", "password": "password1"})
        self.mock_rest_client.get.assert_not_called()
        _, kwargs = self.mock_sessions.add_session.call_args
        self.assertEqual(kwargs["project_ids"], frozenset())

    async def test_membership_fetch_failure_defaults_to_no_projects(self):
        self.mock_sessions.has_session.return_value = False
        self.mock_rest_client.post.side_effect = [
            ApiResponse(status_code=200),
            ApiResponse(status_code=200,
                       body={"is_administrator": False, "id": "uuid-123"})
        ]
        self.mock_rest_client.get.return_value = ApiResponse(
            status_code=503, body={})
        response = await self._post(
            {"email_address": "a@b.com", "password": "password1"})
        self.assertEqual(response.status_code, 200)
        _, kwargs = self.mock_sessions.add_session.call_args
        self.assertEqual(kwargs["project_ids"], frozenset())

    async def test_membership_fetch_exception_defaults_to_no_projects(self):
        self.mock_sessions.has_session.return_value = False
        self.mock_rest_client.post.side_effect = [
            ApiResponse(status_code=200),
            ApiResponse(status_code=200,
                       body={"is_administrator": False, "id": "uuid-123"})
        ]
        self.mock_rest_client.get.side_effect = RuntimeError("boom")
        response = await self._post(
            {"email_address": "a@b.com", "password": "password1"})
        self.assertEqual(response.status_code, 200)
        _, kwargs = self.mock_sessions.add_session.call_args
        self.assertEqual(kwargs["project_ids"], frozenset())


# ------------------------------------------------------------------
# DeleteSessionHandler
# ------------------------------------------------------------------

class TestDeleteSessionHandler(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.mock_sessions = AsyncMock()
        handler = DeleteSessionHandler(_LOGGER, self.mock_sessions)

        app = Quart(__name__)

        @app.route("/sessions", methods=["DELETE"])
        async def delete_session():
            return await handler.delete_session()

        self.client = app.test_client()

    async def _delete(self, body):
        async with self.client as c:
            return await c.delete("/sessions", json=body)

    async def test_missing_fields_returns_400(self):
        response = await self._delete({"email_address": "a@b.com"})
        self.assertEqual(response.status_code, 400)

    async def test_valid_session_deletes_and_returns_200(self):
        self.mock_sessions.is_valid_session.return_value = True
        response = await self._delete(
            {"email_address": "a@b.com", "token": _VALID_TOKEN})
        self.assertEqual(response.status_code, 200)
        self.mock_sessions.delete_session.assert_called_once_with("a@b.com")

    async def test_invalid_session_still_returns_200(self):
        self.mock_sessions.is_valid_session.return_value = False
        response = await self._delete(
            {"email_address": "a@b.com", "token": _VALID_TOKEN})
        self.assertEqual(response.status_code, 200)
        self.mock_sessions.delete_session.assert_not_called()


# ------------------------------------------------------------------
# RefreshSessionHandler
# ------------------------------------------------------------------

class TestRefreshSessionHandler(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.mock_sessions = AsyncMock()
        handler = RefreshSessionHandler(_LOGGER, self.mock_sessions)

        app = Quart(__name__)

        @app.route("/sessions/refresh", methods=["POST"])
        async def refresh_session():
            return await handler.refresh_session()

        self.client = app.test_client()

    async def test_returns_not_implemented(self):
        async with self.client as c:
            response = await c.post("/sessions/refresh")
        self.assertEqual(response.status_code, 501)
        data = await response.get_json()
        self.assertEqual(data["status"], 0)


# ------------------------------------------------------------------
# ValidateSessionHandler
# ------------------------------------------------------------------

class TestValidateSessionHandler(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.mock_sessions = AsyncMock()
        handler = ValidateSessionHandler(_LOGGER, self.mock_sessions)

        app = Quart(__name__)

        @app.route("/sessions/validate", methods=["POST"])
        async def validate_session():
            return await handler.validate_session()

        self.client = app.test_client()

    async def _post(self, body):
        async with self.client as c:
            return await c.post("/sessions/validate", json=body)

    async def test_missing_fields_returns_400(self):
        response = await self._post({"email_address": "a@b.com"})
        self.assertEqual(response.status_code, 400)

    async def test_valid_session_returns_valid_with_is_administrator_false(self):
        entry = SessionEntry(email_address="a@b.com", token=_VALID_TOKEN,
                             is_administrator=False)
        self.mock_sessions.get_session_entry.return_value = entry
        response = await self._post(
            {"email_address": "a@b.com", "token": _VALID_TOKEN})
        self.assertEqual(response.status_code, 200)
        data = await response.get_json()
        self.assertEqual(data["status"], "VALID")
        self.assertFalse(data["is_administrator"])

    async def test_valid_session_returns_is_administrator_true(self):
        entry = SessionEntry(email_address="a@b.com", token=_VALID_TOKEN,
                             is_administrator=True)
        self.mock_sessions.get_session_entry.return_value = entry
        response = await self._post(
            {"email_address": "a@b.com", "token": _VALID_TOKEN})
        self.assertEqual(response.status_code, 200)
        data = await response.get_json()
        self.assertEqual(data["status"], "VALID")
        self.assertTrue(data["is_administrator"])

    async def test_invalid_session_returns_invalid(self):
        self.mock_sessions.get_session_entry.return_value = None
        response = await self._post(
            {"email_address": "a@b.com", "token": _VALID_TOKEN})
        self.assertEqual(response.status_code, 200)
        data = await response.get_json()
        self.assertEqual(data["status"], "INVALID")
        self.assertNotIn("is_administrator", data)


if __name__ == "__main__":
    unittest.main()
