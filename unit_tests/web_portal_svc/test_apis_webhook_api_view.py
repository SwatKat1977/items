import http
import unittest
from unittest.mock import AsyncMock, MagicMock, patch
import quart
from apis.webhook_api_view import WebhookApiView
from base_view import ApiResponse
from metadata_settings import MetadataSettings

class TestApisWebhookApiView(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.app = quart.Quart(__name__)
        self.mock_logger = MagicMock()
        self.mock_metadata_settings = MagicMock()
        self.view = WebhookApiView(self.mock_logger, self.mock_metadata_settings)

        # Set up Quart test client and mock dependencies.
        self.client = self.app.test_client()

        # Register route for testing
        self.app.add_url_rule('/webhook/update_metadata',
                              view_func=self.view.update_metadata,
                              methods=['POST'])

    @patch.object(WebhookApiView, "_validate_json_body")
    async def test_update_metadata_success(self, mock_validate):
        response_body: MetadataSettings = MetadataSettings()
        response_body.default_time_zone = "UTC"
        response_body.using_server_default_time_zone = True
        response_body.instance_name = "Test Instance"

        # Mock successful validation response
        mock_validate.return_value = ApiResponse(
            status_code=http.HTTPStatus.OK,
            body=response_body)

        async with self.client as client:
            response = await client.post('/webhook/update_metadata')

        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        self.assertEqual(response.content_type, "text/plain")
        self.assertEqual(await response.get_data(as_text=True), "OK")

        self.assertEqual(self.mock_metadata_settings.default_time_zone, "UTC")
        self.assertEqual(self.mock_metadata_settings.using_server_default_time_zone, True)
        self.assertEqual(self.mock_metadata_settings.instance_name, "Test Instance")

    async def test_update_metadata_invalid_json(self):
        request_msg = MagicMock()
        request_msg.body = None  # Simulating invalid JSON

        mock_call_api_post = AsyncMock()
        mock_call_api_post.return_value = MagicMock(status_code=http.HTTPStatus.INTERNAL_SERVER_ERROR,
                                                    body={"status": True})
        self.view._call_api_post = mock_call_api_post

        async with self.client as client:
            response = await client.post('/webhook/update_metadata')

            # Assert response status
            self.assertEqual(response.status_code, http.HTTPStatus.INTERNAL_SERVER_ERROR)
