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
from unittest.mock import MagicMock
from quart import Quart
from items.shared.api_signature import generate_api_signature
from items.services.items_gateway.routes.web.webhook.get_metadata_handler \
    import GetMetadataHandler

_SECRET = "test-signing-secret"


class TestGetMetadataHandler(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.config = MagicMock()
        self.config.general_api_signing_secret = _SECRET
        self.metadata_handler = MagicMock()
        self.metadata_handler.build_metadata_dictionary.return_value = {
            "instance_name": "INSTANCE"}
        handler = GetMetadataHandler(MagicMock(), self.config,
                                     self.metadata_handler)

        app = Quart(__name__)

        @app.route("/webhook/metadata", methods=["GET"])
        async def get_metadata():
            return await handler.get_metadata()

        self.client = app.test_client()

    async def _get(self, qs="", headers=None):
        async with self.client as c:
            return await c.get(f"/webhook/metadata{qs}", headers=headers or {})

    async def test_missing_nonce_returns_401(self):
        response = await self._get()
        self.assertEqual(response.status_code, 401)
        data = await response.get_json()
        self.assertEqual(data["error"], "Nonce value required")

    async def test_missing_signature_returns_401(self):
        response = await self._get("?nonce=abc")
        self.assertEqual(response.status_code, 401)
        data = await response.get_json()
        self.assertEqual(data["error"], "Unsigned")

    async def test_invalid_signature_returns_401(self):
        response = await self._get(
            "?nonce=abc", headers={"X-Signature": "not-a-real-signature"})
        self.assertEqual(response.status_code, 401)
        data = await response.get_json()
        self.assertEqual(data["error"], "Invalid signature")

    async def test_valid_signature_returns_metadata(self):
        nonce = "abc"
        string_to_sign = f"/webhook/metadata:{nonce}".encode()
        signature = generate_api_signature(_SECRET.encode(), string_to_sign)

        response = await self._get(
            f"?nonce={nonce}", headers={"X-Signature": signature})

        self.assertEqual(response.status_code, 200)
        data = await response.get_json()
        self.assertEqual(data["instance_name"], "INSTANCE")
        self.assertIn("X-Signature", response.headers)


if __name__ == "__main__":
    unittest.main()
