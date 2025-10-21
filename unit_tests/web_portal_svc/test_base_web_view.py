import unittest
from unittest.mock import patch, MagicMock
import jsonschema
import json
import requests
from quart import Quart
from base_items_exception import BaseItemsException
from base_web_view import BaseWebView
from threadsafe_configuration import ThreadSafeConfiguration as Configuration


class TestBaseWebView(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        """Set up the Quart test app and push a request context."""
        self.app = Quart(__name__)
        self.mock_logger_instance = MagicMock()
        self.view = BaseWebView(self.mock_logger_instance)

        self.client = self.app.test_client()
        self.ctx = self.app.test_request_context("/test")
        await self.ctx.__aenter__()

    async def asyncTearDown(self):
        """Pop the request context after tests complete."""
        await self.ctx.__aexit__(None, None, None)

    async def test_generate_redirect(self):
        """Test _generate_redirect correctly formats a redirect URL."""
        async with self.app.test_request_context("/"):
            result = self.view._generate_redirect("dashboard")

            expected = "<meta http-equiv=\"Refresh\" content=\"0; url='http://localhost/dashboard\"/>"
            self.assertEqual(result, expected)

    async def test_has_auth_cookies_true(self):
        with patch("quart.request.cookies.get", side_effect=lambda key: "dummy_value" if key in [self.view.COOKIE_TOKEN, self.view.COOKIE_USER] else None):
            self.assertTrue(self.view._has_auth_cookies())

    async def test_has_auth_cookies_false(self):
        with patch("quart.request.cookies.get", return_value=None):
            self.assertFalse(self.view._has_auth_cookies())

    @patch("requests.post")
    async def test_validate_cookies_valid_token(self, mock_post):
        """Test when token is valid"""
        with patch("quart.request.cookies.get", side_effect=lambda key: "valid_user" if key == self.view.COOKIE_USER else "valid_token"):
            mock_response = MagicMock()
            mock_response.text = json.dumps({"status": "VALID"})
            mock_post.return_value = mock_response

            with patch.object(Configuration, "apis_gateway_svc", "http://mock-gateway"):
                self.assertTrue(self.view._validate_cookies())

    @patch("requests.post")
    async def test_validate_cookies_invalid_token(self, mock_post):
        """Test when token is invalid"""
        with patch("quart.request.cookies.get", side_effect=lambda key: "valid_user" if key == self.view.COOKIE_USER else "invalid_token"):
            mock_response = MagicMock()
            mock_response.text = json.dumps({"status": "INVALID"})
            mock_post.return_value = mock_response

            with patch.object(Configuration, "apis_gateway_svc", "http://mock-gateway"):
                self.assertFalse(self.view._validate_cookies())

    @patch("requests.post")
    async def test_validate_cookies_connection_error(self, mock_post):
        """Test when connection error occurs"""
        with patch("quart.request.cookies.get", return_value="dummy_value"):
            mock_post.side_effect = requests.exceptions.ConnectionError()

            with patch.object(Configuration, "apis_gateway_svc", "http://mock-gateway"):
                with self.assertRaises(BaseItemsException) as cm:
                    self.view._validate_cookies()
                self.assertEqual(str(cm.exception), "Connection to gateway api timed out")

    @patch("requests.post")
    async def test_validate_cookies_invalid_json_body(self, mock_post):
        """Test when JSON response is missing or None"""
        with patch("quart.request.cookies.get", return_value="dummy_value"):
            mock_post.return_value = None

            with patch.object(Configuration, "apis_gateway_svc", "http://mock-gateway"):
                with self.assertRaises(BaseItemsException) as cm:
                    self.view._validate_cookies()
                self.assertEqual(str(cm.exception), "Missing/invalid JSON body for gateway svc session validate")

    @patch("requests.post")
    async def test_validate_cookies_invalid_json_type(self, mock_post):
        """Test when JSON response cannot be decoded"""
        with patch("quart.request.cookies.get", return_value="dummy_value"):
            mock_response = MagicMock()
            mock_response.text = "invalid_json"
            mock_post.return_value = mock_response

            with patch.object(Configuration, "apis_gateway_svc", "http://mock-gateway"):
                with self.assertRaises(BaseItemsException) as cm:
                    self.view._validate_cookies()
                self.assertEqual(str(cm.exception), "Invalid JSON body type for gateway svc session validate")

    @patch("requests.post")
    async def test_validate_cookies_schema_validation_error(self, mock_post):
        """Test when schema validation fails"""
        with patch("quart.request.cookies.get", return_value="dummy_value"):
            mock_response = MagicMock()
            mock_response.text = json.dumps({"status": "UNKNOWN"})  # Invalid schema
            mock_post.return_value = mock_response

            with patch.object(Configuration, "apis_gateway_svc", "http://mock-gateway"):
                with patch("jsonschema.validate", side_effect=jsonschema.exceptions.ValidationError("Invalid schema")):
                    with self.assertRaises(BaseItemsException) as cm:
                        self.view._validate_cookies()
                    self.assertEqual(str(cm.exception), "Schema for accounts service health check invalid!")
