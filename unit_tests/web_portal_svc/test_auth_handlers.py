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
from http import HTTPStatus
from weaver_framework.microservice.api_response import ApiResponse
from items.shared.base_items_exception import BaseItemsException
from _test_utils import make_app
from items.services.items_web_portal.page_handlers.auth.index_page_handler \
    import IndexPageHandler
from items.services.items_web_portal.page_handlers.auth.login_get_page_handler \
    import LoginGetPageHandler
from items.services.items_web_portal.page_handlers.auth.login_post_page_handler \
    import LoginPostPageHandler
from items.services.items_web_portal.page_handlers.auth.logout_page_handler \
    import LogoutPageHandler

_LOGGER = MagicMock()
_VALID_TOKEN_COOKIE = "Cookie: items_token=abc; items_user=bob"


def _config():
    config = MagicMock()
    config.apis_gateway_svc = "http://gateway/"
    return config


# ------------------------------------------------------------------
# IndexPageHandler
# ------------------------------------------------------------------

class TestIndexPageHandler(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.mock_rest_client = AsyncMock()
        handler = IndexPageHandler(_LOGGER, _config(), self.mock_rest_client,
                                   MagicMock(instance_name="INSTANCE"))

        app = make_app()

        @app.route("/", methods=["GET"])
        async def index():
            return await handler.index()

        self.client = app.test_client()

    async def test_no_auth_cookies_redirects_to_login(self):
        async with self.client as c:
            response = await c.get("/")
        self.assertEqual(response.status_code, 200)
        text = await response.get_data(as_text=True)
        self.assertIn("login", text)
        self.mock_rest_client.get.assert_not_called()

    async def test_internal_error_on_validate_exception(self):
        self.mock_rest_client.post.side_effect = BaseItemsException("boom")
        async with self.client as c:
            response = await c.get("/", headers={"Cookie": "items_token=a; items_user=b"})
        self.assertEqual(response.status_code, 200)

    async def test_gateway_failure_renders_internal_error_page(self):
        self.mock_rest_client.post.return_value = ApiResponse(
            status_code=HTTPStatus.OK, body={"status": "VALID"})
        self.mock_rest_client.get.return_value = ApiResponse(
            status_code=HTTPStatus.SERVICE_UNAVAILABLE)
        async with self.client as c:
            response = await c.get("/", headers={"Cookie": "items_token=a; items_user=b"})
        self.assertEqual(response.status_code, 200)

    async def test_success_renders_dashboard(self):
        self.mock_rest_client.post.return_value = ApiResponse(
            status_code=HTTPStatus.OK, body={"status": "VALID"})
        self.mock_rest_client.get.return_value = ApiResponse(
            status_code=HTTPStatus.OK, body={"projects": [{"id": 1}]})
        async with self.client as c:
            response = await c.get("/", headers={"Cookie": "items_token=a; items_user=b"})
        self.assertEqual(response.status_code, 200)


# ------------------------------------------------------------------
# LoginGetPageHandler
# ------------------------------------------------------------------

class TestLoginGetPageHandler(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.mock_rest_client = AsyncMock()
        handler = LoginGetPageHandler(_LOGGER, _config(), self.mock_rest_client)

        app = make_app()

        @app.route("/login", methods=["GET"])
        async def login_get():
            return await handler.login_get()

        self.client = app.test_client()

    async def test_no_cookies_renders_login_page(self):
        async with self.client as c:
            response = await c.get("/login")
        self.assertEqual(response.status_code, 200)
        self.mock_rest_client.post.assert_not_called()

    async def test_valid_session_redirects(self):
        self.mock_rest_client.post.return_value = ApiResponse(
            status_code=HTTPStatus.OK, body={"status": "VALID"})
        async with self.client as c:
            response = await c.get(
                "/login", headers={"Cookie": "items_token=a; items_user=b"})
        self.assertEqual(response.status_code, 200)
        text = await response.get_data(as_text=True)
        self.assertIn("Refresh", text)

    async def test_invalid_session_renders_login_page(self):
        self.mock_rest_client.post.return_value = ApiResponse(
            status_code=HTTPStatus.OK, body={"status": "INVALID"})
        async with self.client as c:
            response = await c.get(
                "/login", headers={"Cookie": "items_token=a; items_user=b"})
        self.assertEqual(response.status_code, 200)

        # A redirect is also served as a 200 (it is a meta-refresh document),
        # so the status code alone cannot distinguish the login page from a
        # bounce to '/'. Assert the absence of the refresh explicitly:
        # stale cookies must land on the login page, not be redirected to a
        # page that sends them straight back here.
        text = await response.get_data(as_text=True)
        self.assertNotIn("Refresh", text)

    async def test_validation_exception_renders_internal_error_page(self):
        self.mock_rest_client.post.side_effect = BaseItemsException("boom")
        async with self.client as c:
            response = await c.get(
                "/login", headers={"Cookie": "items_token=a; items_user=b"})
        self.assertEqual(response.status_code, 200)


# ------------------------------------------------------------------
# LoginPostPageHandler
# ------------------------------------------------------------------

class TestLoginPostPageHandler(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.mock_rest_client = AsyncMock()
        handler = LoginPostPageHandler(_LOGGER, _config(), self.mock_rest_client)

        app = make_app()

        @app.route("/login", methods=["POST"])
        async def login_post():
            return await handler.login_post()

        self.client = app.test_client()

    async def _post(self, form=None, cookies=None):
        async with self.client as c:
            return await c.post("/login", form=form or {},
                               headers={"Cookie": cookies} if cookies else None)

    async def test_already_valid_session_redirects(self):
        self.mock_rest_client.post.return_value = ApiResponse(
            status_code=HTTPStatus.OK, body={"status": "VALID"})
        response = await self._post(cookies="items_token=a; items_user=b")
        self.assertEqual(response.status_code, 200)
        text = await response.get_data(as_text=True)
        self.assertIn("Refresh", text)

    async def test_stale_cookies_do_not_redirect_and_login_proceeds(self):
        """Submitting the form with stale cookies must not bounce to '/'.

        _validate_cookies returns a (is_valid, is_administrator) tuple. If it
        is tested directly rather than unpacked it is always truthy - even
        (False, False) - which redirects the user to '/', where the session
        guard sends them back to /login, looping indefinitely.
        """
        self.mock_rest_client.post.return_value = ApiResponse(
            status_code=HTTPStatus.OK, body={"status": "INVALID"})

        response = await self._post(cookies="items_token=a; items_user=b")

        self.assertEqual(response.status_code, 200)
        text = await response.get_data(as_text=True)
        self.assertNotIn("Refresh", text)
        # Fell through to processing the (empty) form rather than redirecting.
        self.assertIn("Invalid username/password", text)

    async def test_validate_exception_renders_internal_error_page(self):
        self.mock_rest_client.post.side_effect = BaseItemsException("boom")
        response = await self._post(cookies="items_token=a; items_user=b")
        self.assertEqual(response.status_code, 200)

    async def test_missing_email_or_password_renders_error(self):
        response = await self._post(form={"user_email": "a@b.com"})
        self.assertEqual(response.status_code, 200)
        text = await response.get_data(as_text=True)
        self.assertIn("Invalid username/password", text)

    async def test_unauthorized_renders_invalid_credentials(self):
        self.mock_rest_client.post.return_value = ApiResponse(
            status_code=HTTPStatus.UNAUTHORIZED)
        response = await self._post(
            form={"user_email": "a@b.com", "password": "password1"})
        self.assertEqual(response.status_code, 200)
        text = await response.get_data(as_text=True)
        self.assertIn("Invalid username/password", text)

    async def test_other_error_status_renders_internal_error(self):
        self.mock_rest_client.post.return_value = ApiResponse(status_code=503)
        response = await self._post(
            form={"user_email": "a@b.com", "password": "password1"})
        self.assertEqual(response.status_code, 200)
        text = await response.get_data(as_text=True)
        self.assertIn("Internal Error", text)

    async def test_success_sets_cookies_and_redirects(self):
        self.mock_rest_client.post.return_value = ApiResponse(
            status_code=HTTPStatus.OK,
            body={"status": 1, "token": "abc123"})
        response = await self._post(
            form={"user_email": "a@b.com", "password": "password1"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("items_user", response.headers.get("Set-Cookie", ""))

    async def test_status_not_one_renders_invalid_credentials(self):
        self.mock_rest_client.post.return_value = ApiResponse(
            status_code=HTTPStatus.OK, body={"status": 0})
        response = await self._post(
            form={"user_email": "a@b.com", "password": "password1"})
        self.assertEqual(response.status_code, 200)
        text = await response.get_data(as_text=True)
        self.assertIn("Invalid username/password", text)


# ------------------------------------------------------------------
# LogoutPageHandler
# ------------------------------------------------------------------

class TestLogoutPageHandler(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        handler = LogoutPageHandler(_LOGGER, _config(), AsyncMock())

        app = make_app()

        @app.route("/logout", methods=["GET"])
        async def logout():
            return await handler.logout()

        self.client = app.test_client()

    async def test_logout_renders_internal_error_page(self):
        async with self.client as c:
            response = await c.get("/logout")
        self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
    unittest.main()
