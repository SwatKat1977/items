import http
import unittest
from unittest.mock import MagicMock, patch
import quart
from threadsafe_configuration import ThreadSafeConfiguration
from base_view import BaseView
from metadata_handler import MetadataHandler
from apis.web.webhook_api_view import WebhookApiView


class TestWebhookApiProjectApiView(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.mock_logger = MagicMock()
        self.mock_metadata_handler = MagicMock(spec=MetadataHandler)
        self.mock_metadata_handler.build_metadata_dictionary.return_value = {"key": "value"}

        self.app = quart.Quart(__name__)
        self.client = self.app.test_client()

        self.view = WebhookApiView(self.mock_logger, self.mock_metadata_handler)

        # Register route for testing
        self.app.add_url_rule('/webhook/get_metadata', view_func=self.view.get_metadata,
                              methods=['GET'])

    async def test_get_metadata_missing_nonce(self):
        async with self.client as client:
            response = await client.get('/webhook/get_metadata')

            self.assertEqual(response.status_code, http.HTTPStatus.UNAUTHORIZED)
            self.assertEqual(await response.get_json(), {"error": "Nonce value required"})

    async def test_get_metadata_missing_signature(self):
        async with self.client as client:
            response = await client.get("/webhook/get_metadata?nonce=test")
            self.assertEqual(response.status_code, http.HTTPStatus.UNAUTHORIZED)
            self.assertEqual(await response.get_json(), {"error": "Unsigned"})

    @patch.object(ThreadSafeConfiguration, "general_api_signing_secret", new_callable=MagicMock,
                  return_value="test_secret")
    @patch.object(BaseView, "verify_api_signature", return_value=False)
    async def test_get_metadata_invalid_signature(self, mock_verify, mock_config):
        async with self.client as client:
            headers = {"X-Signature": "invalid_sig"}
            response = await client.get("/webhook/get_metadata?nonce=test", headers=headers)
            self.assertEqual(response.status_code, http.HTTPStatus.UNAUTHORIZED)
            self.assertEqual(await response.get_json(), {"error": "Invalid signature"})

    @patch.object(ThreadSafeConfiguration, "general_api_signing_secret", new_callable=MagicMock,
                  return_value="test_secret")
    @patch.object(BaseView, "verify_api_signature", return_value=True)
    @patch.object(BaseView, "generate_api_signature", return_value="mock_signature")
    async def test_get_metadata_success(self, mock_generate, mock_verify, mock_config):
        async with self.client as client:
            headers = {"X-Signature": "valid_sig"}
            response = await client.get("/webhook/get_metadata?nonce=test", headers=headers)
            self.assertEqual(response.status_code, http.HTTPStatus.OK)
            self.assertEqual(response.headers["X-Signature"], "mock_signature")
            self.assertEqual(await response.get_json(), {"key": "value"})
