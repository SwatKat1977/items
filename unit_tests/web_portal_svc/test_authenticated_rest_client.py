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
from unittest.mock import AsyncMock
from quart import Quart
from weaver_framework.microservice.api_response import ApiResponse
from items.services.items_web_portal.authenticated_rest_client import (
    AuthenticatedRestClient, HEADER_TOKEN, HEADER_USER)

_AUTH_COOKIE = "items_token=abc123; items_user=alice@x.com"


def _make_app():
    app = Quart(__name__)

    inner = AsyncMock()
    for method in ("get", "post", "put", "patch", "delete"):
        getattr(inner, method).return_value = ApiResponse(
            status_code=200, body={})
    wrapped = AuthenticatedRestClient(inner)

    @app.route('/probe-get')
    async def probe_get():
        await wrapped.get("http://gateway/web/projects")
        return "ok"

    @app.route('/probe-post-keyword', methods=['POST'])
    async def probe_post_keyword():
        await wrapped.post("http://gateway/web/projects",
                          json_data={"name": "x"})
        return "ok"

    @app.route('/probe-post-positional', methods=['POST'])
    async def probe_post_positional():
        # Matches the real call-site pattern in
        # admin_add_project_page_handlers.py: the JSON body passed as the
        # second positional argument, not as a json_data= keyword. This is
        # exactly the shape that broke when the wrapper's second positional
        # parameter was `headers` instead of `json_data`.
        await wrapped.post("http://gateway/web/projects", {"name": "x"})
        return "ok"

    @app.route('/probe-patch-positional', methods=['POST'])
    async def probe_patch_positional():
        # Matches admin_modify_project_page_handlers.py's call shape.
        await wrapped.patch("http://gateway/web/projects/1", {"name": "x"})
        return "ok"

    @app.route('/probe-put', methods=['POST'])
    async def probe_put():
        # Matches admin_customisations_page_handler.py's call shape.
        await wrapped.put("http://gateway/web/testcase_custom_fields/1",
                          json_data={"field_name": "x"})
        return "ok"

    @app.route('/probe-delete', methods=['POST'])
    async def probe_delete():
        await wrapped.delete("http://gateway/web/projects/1")
        return "ok"

    @app.route('/probe-with-headers')
    async def probe_with_headers():
        await wrapped.get("http://gateway/web/projects",
                          headers={"X-Custom": "1"})
        return "ok"

    return app, inner


class TestAuthenticatedRestClient(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.app, self.inner = _make_app()
        self.client = self.app.test_client()

    async def test_get_attaches_session_headers_from_cookies(self):
        async with self.client as c:
            await c.get("/probe-get", headers={"Cookie": _AUTH_COOKIE})
        call = self.inner.get.await_args
        self.assertEqual(call.kwargs["headers"],
                         {HEADER_USER: "alice@x.com", HEADER_TOKEN: "abc123"})

    async def test_post_with_keyword_json_data_forwards_it_unchanged(self):
        async with self.client as c:
            await c.post("/probe-post-keyword",
                         headers={"Cookie": _AUTH_COOKIE})
        call = self.inner.post.await_args
        self.assertEqual(call.kwargs["json_data"], {"name": "x"})
        self.assertEqual(call.kwargs["headers"],
                         {HEADER_USER: "alice@x.com", HEADER_TOKEN: "abc123"})

    async def test_post_with_positional_json_data_forwards_it_unchanged(self):
        """Regression test: a positional body must land in json_data, not
        be silently swallowed into headers."""
        async with self.client as c:
            await c.post("/probe-post-positional",
                         headers={"Cookie": _AUTH_COOKIE})
        call = self.inner.post.await_args
        self.assertEqual(call.kwargs["json_data"], {"name": "x"})
        self.assertEqual(call.kwargs["headers"],
                         {HEADER_USER: "alice@x.com", HEADER_TOKEN: "abc123"})

    async def test_patch_with_positional_json_data_forwards_it_unchanged(self):
        async with self.client as c:
            await c.post("/probe-patch-positional",
                         headers={"Cookie": _AUTH_COOKIE})
        call = self.inner.patch.await_args
        self.assertEqual(call.kwargs["json_data"], {"name": "x"})
        self.assertEqual(call.kwargs["headers"],
                         {HEADER_USER: "alice@x.com", HEADER_TOKEN: "abc123"})

    async def test_put_attaches_session_headers_and_forwards_json_data(self):
        async with self.client as c:
            await c.post("/probe-put", headers={"Cookie": _AUTH_COOKIE})
        call = self.inner.put.await_args
        self.assertEqual(call.kwargs["json_data"], {"field_name": "x"})
        self.assertEqual(call.kwargs["headers"],
                         {HEADER_USER: "alice@x.com", HEADER_TOKEN: "abc123"})

    async def test_delete_attaches_session_headers(self):
        async with self.client as c:
            await c.post("/probe-delete", headers={"Cookie": _AUTH_COOKIE})
        call = self.inner.delete.await_args
        self.assertEqual(call.kwargs["headers"],
                         {HEADER_USER: "alice@x.com", HEADER_TOKEN: "abc123"})

    async def test_no_cookies_means_no_session_headers(self):
        """An unauthenticated page (e.g. accept-invite) has no session
        cookies to forward - the gateway call still goes out, just without
        the session headers, exactly as it did before this wrapper existed.
        """
        async with self.client as c:
            await c.get("/probe-get")
        call = self.inner.get.await_args
        self.assertEqual(call.kwargs["headers"], {})

    async def test_existing_headers_are_preserved_alongside_session_headers(self):
        async with self.client as c:
            await c.get("/probe-with-headers", headers={"Cookie": _AUTH_COOKIE})
        call = self.inner.get.await_args
        self.assertEqual(call.kwargs["headers"], {
            "X-Custom": "1", HEADER_USER: "alice@x.com",
            HEADER_TOKEN: "abc123"})


if __name__ == "__main__":
    unittest.main()
