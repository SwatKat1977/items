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
from http import HTTPStatus
import jinja2
from quart import Quart
from weaver_framework.microservice.api_response import ApiResponse
from items.shared.base_items_exception import BaseItemsException
from items.services.items_web_portal.portal_page_handler import (
    SessionAuthMixin, PortalPageHandler)


def _make_app():
    return Quart(__name__)


class TestSessionAuthMixinGenerateRedirect(unittest.IsolatedAsyncioTestCase):

    async def test_generate_redirect_builds_absolute_url(self):
        mixin = SessionAuthMixin(MagicMock(), MagicMock())
        app = _make_app()
        async with app.test_request_context('/'):
            result = mixin._generate_redirect('login')
        self.assertIn("http://localhost/login", result)
        self.assertIn("Refresh", result)


class TestHasAuthCookies(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.mixin = SessionAuthMixin(MagicMock(), MagicMock())
        self.app = _make_app()

    async def test_true_when_both_cookies_present(self):
        async with self.app.test_request_context(
                '/', headers={"Cookie": "items_token=abc; items_user=bob"}):
            result = await self.mixin._has_auth_cookies()
        self.assertTrue(result)

    async def test_false_when_token_missing(self):
        async with self.app.test_request_context(
                '/', headers={"Cookie": "items_user=bob"}):
            result = await self.mixin._has_auth_cookies()
        self.assertFalse(result)

    async def test_false_when_no_cookies(self):
        async with self.app.test_request_context('/'):
            result = await self.mixin._has_auth_cookies()
        self.assertFalse(result)


class TestValidateCookies(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.mock_config = MagicMock()
        self.mock_config.apis_gateway_svc = "http://gateway/"
        self.mock_rest_client = AsyncMock()
        self.mixin = SessionAuthMixin(self.mock_config, self.mock_rest_client)
        self.app = _make_app()

    async def _validate(self):
        async with self.app.test_request_context(
                '/', headers={"Cookie": "items_token=abc; items_user=bob"}):
            return await self.mixin._validate_cookies()

    async def test_non_ok_status_raises_with_exception_msg(self):
        self.mock_rest_client.post.return_value = ApiResponse(
            status_code=HTTPStatus.SERVICE_UNAVAILABLE,
            exception_msg="connection refused")
        with self.assertRaises(BaseItemsException) as ctx:
            await self._validate()
        self.assertIn("connection refused", str(ctx.exception))

    async def test_non_ok_status_raises_without_exception_msg(self):
        self.mock_rest_client.post.return_value = ApiResponse(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR)
        with self.assertRaises(BaseItemsException):
            await self._validate()

    async def test_schema_validation_failure_raises(self):
        self.mock_rest_client.post.return_value = ApiResponse(
            status_code=HTTPStatus.OK, body={"status": "NOT_A_VALID_ENUM"})
        with self.assertRaises(BaseItemsException):
            await self._validate()

    async def test_valid_status_returns_true_and_is_administrator_false(self):
        self.mock_rest_client.post.return_value = ApiResponse(
            status_code=HTTPStatus.OK, body={"status": "VALID"})
        is_valid, is_administrator = await self._validate()
        self.assertTrue(is_valid)
        self.assertFalse(is_administrator)

    async def test_invalid_status_returns_false_and_is_administrator_false(self):
        self.mock_rest_client.post.return_value = ApiResponse(
            status_code=HTTPStatus.OK, body={"status": "INVALID"})
        is_valid, is_administrator = await self._validate()
        self.assertFalse(is_valid)
        self.assertFalse(is_administrator)

    async def test_valid_status_with_is_administrator_true(self):
        self.mock_rest_client.post.return_value = ApiResponse(
            status_code=HTTPStatus.OK,
            body={"status": "VALID", "is_administrator": True})
        is_valid, is_administrator = await self._validate()
        self.assertTrue(is_valid)
        self.assertTrue(is_administrator)

    async def test_valid_status_with_is_administrator_false(self):
        self.mock_rest_client.post.return_value = ApiResponse(
            status_code=HTTPStatus.OK,
            body={"status": "VALID", "is_administrator": False})
        is_valid, is_administrator = await self._validate()
        self.assertTrue(is_valid)
        self.assertFalse(is_administrator)

    async def test_is_administrator_wrong_type_raises(self):
        self.mock_rest_client.post.return_value = ApiResponse(
            status_code=HTTPStatus.OK,
            body={"status": "VALID", "is_administrator": "yes"})
        with self.assertRaises(BaseItemsException):
            await self._validate()


class TestPortalPageHandlerRenderPage(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.handler = PortalPageHandler(MagicMock(), MagicMock(), MagicMock())
        self.app = _make_app()

    async def test_render_success(self):
        with patch(
            "items.services.items_web_portal.portal_page_handler."
            "render_template", new=AsyncMock(return_value="<html/>")):
            async with self.app.app_context():
                result = await self.handler._render_page("some_page.html")
        self.assertEqual(result, "<html/>")

    async def test_render_failure_falls_back_to_internal_error_page(self):
        mock_render = AsyncMock(
            side_effect=[jinja2.TemplateError("bad template"), "<error/>"])
        with patch(
            "items.services.items_web_portal.portal_page_handler."
            "render_template", new=mock_render):
            async with self.app.app_context():
                result = await self.handler._render_page("some_page.html")
        self.assertEqual(result, "<error/>")
        self.handler._logger.error.assert_called_once()


if __name__ == "__main__":
    unittest.main()
