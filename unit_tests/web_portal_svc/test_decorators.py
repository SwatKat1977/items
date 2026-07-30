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
from quart import Quart, g
from items.shared.base_items_exception import BaseItemsException
from items.services.items_web_portal.decorators import (
    require_session, require_administrator)


class _FakeHandler:
    """Minimal stand-in for a SessionAuthMixin/PortalPageHandler subclass."""

    def __init__(self, is_valid=True, is_administrator=False):
        self._has_auth_cookies = AsyncMock(return_value=True)
        self._validate_cookies = AsyncMock(
            return_value=(is_valid, is_administrator))
        self._generate_redirect = MagicMock(return_value="<redirect/>")
        self._logger = MagicMock()
        self._render_page = AsyncMock(return_value="internal-error-page")

    @require_session
    async def protected_method(self, *args, **kwargs):
        return ("handler-result", args, kwargs)

    @require_administrator
    async def admin_method(self, *args, **kwargs):
        return ("admin-result", args, kwargs)


class TestRequireSession(unittest.IsolatedAsyncioTestCase):

    async def test_calls_wrapped_handler_when_session_valid(self):
        handler = _FakeHandler()
        app = Quart(__name__)
        async with app.app_context():
            result = await handler.protected_method()
        self.assertEqual(result, ("handler-result", (), {}))

    async def test_passes_through_args_and_kwargs(self):
        handler = _FakeHandler()
        app = Quart(__name__)
        async with app.app_context():
            result = await handler.protected_method(1, b=2)
        self.assertEqual(result, ("handler-result", (1,), {"b": 2}))

    async def test_sets_g_is_administrator_true_when_valid_admin(self):
        handler = _FakeHandler(is_valid=True, is_administrator=True)
        app = Quart(__name__)
        async with app.app_context():
            await handler.protected_method()
            self.assertTrue(g.is_administrator)

    async def test_sets_g_is_administrator_false_when_not_admin(self):
        handler = _FakeHandler(is_valid=True, is_administrator=False)
        app = Quart(__name__)
        async with app.app_context():
            await handler.protected_method()
            self.assertFalse(g.is_administrator)

    async def test_sets_g_is_administrator_false_when_no_cookies(self):
        handler = _FakeHandler()
        handler._has_auth_cookies.return_value = False
        app = Quart(__name__)
        async with app.app_context():
            await handler.protected_method()
            self.assertFalse(g.is_administrator)

    async def test_redirects_when_no_auth_cookies(self):
        handler = _FakeHandler()
        handler._has_auth_cookies.return_value = False
        app = Quart(__name__)
        async with app.app_context():
            result = await handler.protected_method()
        self.assertEqual(result.status_code, 200)
        handler._generate_redirect.assert_called_once_with('login')

    async def test_redirects_when_cookies_invalid(self):
        handler = _FakeHandler(is_valid=False)
        app = Quart(__name__)
        async with app.app_context():
            await handler.protected_method()
        handler._generate_redirect.assert_called_once_with('login')

    async def test_internal_error_page_on_exception(self):
        handler = _FakeHandler()
        handler._validate_cookies.side_effect = BaseItemsException("boom")
        app = Quart(__name__)
        async with app.app_context():
            result = await handler.protected_method()
        self.assertEqual(result, "internal-error-page")
        handler._logger.error.assert_called_once()


class TestRequireAdministrator(unittest.IsolatedAsyncioTestCase):

    async def test_calls_wrapped_handler_when_administrator(self):
        handler = _FakeHandler(is_valid=True, is_administrator=True)
        app = Quart(__name__)
        async with app.app_context():
            result = await handler.admin_method()
        self.assertEqual(result, ("admin-result", (), {}))

    async def test_passes_through_args_and_kwargs(self):
        handler = _FakeHandler(is_valid=True, is_administrator=True)
        app = Quart(__name__)
        async with app.app_context():
            result = await handler.admin_method(1, b=2)
        self.assertEqual(result, ("admin-result", (1,), {"b": 2}))

    async def test_sets_g_is_administrator_true_for_admin(self):
        handler = _FakeHandler(is_valid=True, is_administrator=True)
        app = Quart(__name__)
        async with app.app_context():
            await handler.admin_method()
            self.assertTrue(g.is_administrator)

    async def test_redirects_to_login_when_no_auth_cookies(self):
        handler = _FakeHandler(is_valid=True, is_administrator=True)
        handler._has_auth_cookies.return_value = False
        app = Quart(__name__)
        async with app.app_context():
            await handler.admin_method()
        handler._generate_redirect.assert_called_once_with('login')

    async def test_redirects_to_login_when_session_invalid(self):
        handler = _FakeHandler(is_valid=False, is_administrator=False)
        app = Quart(__name__)
        async with app.app_context():
            await handler.admin_method()
        handler._generate_redirect.assert_called_once_with('login')

    async def test_redirects_to_dashboard_when_not_administrator(self):
        handler = _FakeHandler(is_valid=True, is_administrator=False)
        app = Quart(__name__)
        async with app.app_context():
            await handler.admin_method()
        handler._generate_redirect.assert_called_once_with('')

    async def test_sets_g_is_administrator_false_for_non_admin(self):
        handler = _FakeHandler(is_valid=True, is_administrator=False)
        app = Quart(__name__)
        async with app.app_context():
            await handler.admin_method()
            self.assertFalse(g.is_administrator)

    async def test_internal_error_page_on_exception(self):
        handler = _FakeHandler(is_valid=True, is_administrator=True)
        handler._validate_cookies.side_effect = BaseItemsException("boom")
        app = Quart(__name__)
        async with app.app_context():
            result = await handler.admin_method()
        self.assertEqual(result, "internal-error-page")
        handler._logger.error.assert_called_once()


if __name__ == "__main__":
    unittest.main()
