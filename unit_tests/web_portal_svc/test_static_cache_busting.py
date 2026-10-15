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
import os
import re
import unittest
from unittest.mock import AsyncMock, MagicMock
from quart import Quart, url_for
import items.services.items_web_portal as portal_pkg
from items.services.items_web_portal.page_handler_injections import (
    PageHandlerInjections)
from items.services.items_web_portal.page_handlers import create_page_handlers
from items.shared import __version__

_PORTAL_FOLDER = os.path.dirname(portal_pkg.__file__)


class TestStaticCacheBusting(unittest.IsolatedAsyncioTestCase):
    """The version is added to static asset URLs so upgrades are re-fetched.

    Uses the portal's real ``templates`` and ``static`` folders, so a
    rendered page proves the hook reaches the existing ``url_for`` calls
    without any template needing to change.
    """

    async def asyncSetUp(self):
        metadata = MagicMock()
        metadata.instance_name = "INSTANCE"
        injections = PageHandlerInjections(
            config=MagicMock(),
            logger=MagicMock(),
            metadata=metadata,
            rest_client=AsyncMock())

        self.app = Quart(
            __name__,
            template_folder=os.path.join(_PORTAL_FOLDER, "templates"),
            static_folder=os.path.join(_PORTAL_FOLDER, "static"))
        self.app.register_blueprint(create_page_handlers(injections))

        # An unrelated endpoint, to prove only static URLs are touched.
        @self.app.route("/unrelated")
        async def unrelated():
            return "ok"

    async def test_static_url_includes_the_version(self):
        async with self.app.test_request_context("/"):
            url = url_for("static", filename="css/login.css")

        self.assertEqual(f"/static/css/login.css?v={__version__}", url)

    async def test_explicit_version_is_not_overridden(self):
        async with self.app.test_request_context("/"):
            url = url_for("static", filename="css/login.css", v="custom")

        self.assertEqual("/static/css/login.css?v=custom", url)

    async def test_other_endpoints_are_unchanged(self):
        async with self.app.test_request_context("/"):
            url = url_for("unrelated")

        self.assertEqual("/unrelated", url)

    async def test_rendered_page_links_are_versioned(self):
        async with self.app.test_client() as client:
            response = await client.get("/login")
        body = (await response.get_data()).decode()

        static_urls = re.findall(r'(?:href|src)="(/static/[^"]+)"', body)
        self.assertTrue(static_urls)
        for static_url in static_urls:
            self.assertTrue(static_url.endswith(f"?v={__version__}"),
                            static_url)


if __name__ == "__main__":
    unittest.main()
