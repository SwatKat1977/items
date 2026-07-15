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
from weaver_framework.microservice.api_response import ApiResponse
from items.services.items_gateway.web_portal_client import WebPortalClient


def _make_client():
    logger = MagicMock()
    metadata_handler = MagicMock()
    metadata_handler.build_metadata_dictionary.return_value = {"instance_name": "x"}
    config = MagicMock()
    config.general_api_signing_secret = "secret"
    config.apis_web_portal_svc = "http://localhost:8080/"
    with patch("items.services.items_gateway.web_portal_client.RestClient"):
        client = WebPortalClient(logger, metadata_handler, config, MagicMock())
    client._rest_client = AsyncMock()
    return client


class TestWebPortalClient(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.client = _make_client()
        self._sleep_patcher = patch(
            "items.services.items_gateway.web_portal_client.asyncio.sleep",
            new=AsyncMock())
        self._sleep_patcher.start()

    async def asyncTearDown(self):
        self._sleep_patcher.stop()

    async def test_success_on_first_attempt(self):
        self.client._rest_client.post.return_value = ApiResponse(status_code=200)
        result = await self.client.update_web_portal_webhook()
        self.assertTrue(result)
        self.client._rest_client.post.assert_called_once()

    async def test_single_attempt_failure_via_exception_returns_false(self):
        self.client._rest_client.post.return_value = ApiResponse(
            status_code=None, exception_msg="connection refused")
        result = await self.client.update_web_portal_webhook(retries=0)
        self.assertFalse(result)
        self.client._rest_client.post.assert_called_once()

    async def test_single_attempt_failure_via_bad_status_returns_false(self):
        self.client._rest_client.post.return_value = ApiResponse(status_code=500)
        result = await self.client.update_web_portal_webhook(retries=0)
        self.assertFalse(result)
        self.client._rest_client.post.assert_called_once()

    async def test_finite_retries_gives_up_after_count(self):
        self.client._rest_client.post.return_value = ApiResponse(status_code=500)
        result = await self.client.update_web_portal_webhook(retries=3)
        self.assertFalse(result)
        self.assertEqual(self.client._rest_client.post.call_count, 3)

    async def test_infinite_retries_succeeds_eventually(self):
        self.client._rest_client.post.side_effect = [
            ApiResponse(status_code=500),
            ApiResponse(status_code=500),
            ApiResponse(status_code=200),
        ]
        result = await self.client.update_web_portal_webhook(
            retries=WebPortalClient.INFINITE_UPDATE_RETRIES)
        self.assertTrue(result)
        self.assertEqual(self.client._rest_client.post.call_count, 3)


if __name__ == "__main__":
    unittest.main()
