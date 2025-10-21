import asyncio
import unittest
from unittest.mock import AsyncMock, patch
import hashlib
import hmac
from http import HTTPStatus
import json
from types import SimpleNamespace
import jsonschema
import quart
import requests
from aiohttp import ClientConnectionError, ClientError
from base_view import ApiResponse, BaseView, validate_json


class TestApiResponse(unittest.TestCase):
    def test_api_response_initialization(self):
        # Test default initialization
        response = ApiResponse()
        self.assertEqual(response.status_code, 0)
        self.assertIsNone(response.body)
        self.assertIsNone(response.content_type)
        self.assertIsNone(response.exception_msg)

        # Test parameterized initialization
        response = ApiResponse(
            status_code=200,
            body={"key": "value"},
            content_type="application/json",
            exception_msg="Test exception"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.body, {"key": "value"})
        self.assertEqual(response.content_type, "application/json")
        self.assertEqual(response.exception_msg, "Test exception")

app = quart.Quart(__name__)


class TestBaseView(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.view = BaseView()

        self.secret_key = b"supersecretkey"
        self.data = b"testdata"
        self.valid_signature = hmac.new(self.secret_key, self.data, hashlib.sha256).hexdigest()
        self.invalid_signature = "invalidsignature"

    async def asyncSetUp(self):
        """Ensure Quart test request context is available."""
        self.test_client = app.test_client()
        self.context = app.test_request_context('/')
        await self.context.__aenter__()

    async def asyncTearDown(self):
        """Clean up Quart request context."""
        await self.context.__aexit__(None, None, None)

    def test_validate_json_body_none(self):
        response = self.view._validate_json_body(None)
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)
        self.assertEqual(response.content_type, self.view.CONTENT_TYPE_TEXT)
        self.assertEqual(response.exception_msg, self.view.ERR_MSG_MISSING_INVALID_JSON_BODY)

    def test_validate_json_body_invalid_json(self):
        response = self.view._validate_json_body("invalid json")
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)
        self.assertEqual(response.content_type, self.view.CONTENT_TYPE_TEXT)
        self.assertEqual(response.exception_msg, self.view.ERR_MSG_INVALID_BODY_TYPE)

    def test_validate_json_body_schema_validation(self):
        valid_json = json.dumps({"key": "value"})
        schema = {"type": "object", "properties": {"key": {"type": "string"}}, "required": ["key"]}

        # Valid schema
        response = self.view._validate_json_body(valid_json, json_schema=schema)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.content_type, self.view.CONTENT_TYPE_JSON)
        self.assertIsInstance(response.body, SimpleNamespace)
        self.assertEqual(response.body.key, "value")

        # Invalid schema
        invalid_json = json.dumps({"wrong_key": "value"})
        response = self.view._validate_json_body(invalid_json, json_schema=schema)
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)
        self.assertEqual(response.content_type, self.view.CONTENT_TYPE_TEXT)
        self.assertEqual(response.exception_msg, self.view.ERR_MSG_BODY_SCHEMA_MISMATCH)

    @patch("aiohttp.ClientSession.post")
    async def test_call_api_post_success(self, mock_post):
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.content_type = self.view.CONTENT_TYPE_JSON
        mock_response.json.return_value = {"key": "value"}

        # Configure the mock to return the response when used in 'async with'
        mock_post.return_value.__aenter__.return_value = mock_response

        # Call the method under test
        response = await self.view._call_api_post("http://example.com", {"data": "test"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.body, {"key": "value"})
        self.assertEqual(response.content_type, self.view.CONTENT_TYPE_JSON)

    @patch("aiohttp.ClientSession.post")
    async def test_call_api_post_client_error(self, mock_post):
        mock_post.side_effect = ClientError("Connection error")

        response = await self.view._call_api_post("http://example.com", {"data": "test"})
        self.assertIsNone(response.body)
        self.assertEqual(response.exception_msg, "Connection error")

    @patch("aiohttp.ClientSession.post")
    async def test_call_api_post_timeout_error(self, mock_post):
        mock_post.side_effect = asyncio.TimeoutError("Timeout error")

        response = await self.view._call_api_post("http://example.com", {"data": "test"})
        self.assertIsNone(response.body)
        self.assertEqual(response.exception_msg, "Timeout error")

    @patch("aiohttp.ClientSession.get")
    async def test_call_api_get_success(self, mock_get):
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.content_type = self.view.CONTENT_TYPE_JSON
        mock_response.json.return_value = {"key": "value"}
        mock_get.return_value.__aenter__.return_value = mock_response

        response = await self.view._call_api_get("http://example.com")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.body, {"key": "value"})
        self.assertEqual(response.content_type, self.view.CONTENT_TYPE_JSON)

    @patch("aiohttp.ClientSession.get")
    async def test_call_api_get_client_error(self, mock_get):
        mock_get.side_effect = ClientConnectionError("Connection error")

        response = await self.view._call_api_get("http://example.com")
        self.assertIsNone(response.body)
        self.assertIsInstance(response.exception_msg, ClientConnectionError)

    @patch("aiohttp.ClientSession.get")
    async def test_call_api_get_timeout_error(self, mock_get):
        mock_get.side_effect = asyncio.TimeoutError("Timeout error")

        response = await self.view._call_api_get("http://example.com")
        self.assertIsNone(response.body)
        self.assertEqual(response.exception_msg, "Timeout error")

    @patch("aiohttp.ClientSession.patch")
    async def test_call_api_patch_success(self, mock_patch):
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.content_type = self.view.CONTENT_TYPE_JSON
        mock_response.json.return_value = {"key": "value"}
        mock_patch.return_value.__aenter__.return_value = mock_response

        response = await self.view._call_api_patch("http://example.com")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.body, {"key": "value"})
        self.assertEqual(response.content_type, self.view.CONTENT_TYPE_JSON)

    @patch("aiohttp.ClientSession.patch")
    async def test_call_api_patch_client_error(self, mock_patch):
        mock_patch.side_effect = ClientConnectionError("Connection error")

        response = await self.view._call_api_patch("http://example.com", {"data": "test"})
        self.assertIsNone(response.body)
        self.assertEqual(response.exception_msg, "Connection error")

    @patch("aiohttp.ClientSession.patch")
    async def test_call_api_patch_timeout_error(self, mock_patch):
        mock_patch.side_effect = asyncio.TimeoutError("Timeout error")

        response = await self.view._call_api_patch("http://example.com")
        self.assertIsNone(response.body)
        self.assertEqual(response.exception_msg, "Timeout error")

    @patch("quart.request.get_data", new_callable=AsyncMock)
    @patch.object(BaseView, "_validate_json_body")
    async def test_decorator_success(self, mock_validate, mock_get_data):
        """Test decorator when JSON validation succeeds."""

        schema = {"type": "object", "properties": {"project_id": {"type": "integer"}}}
        mock_request_data = json.dumps({"project_id": 100}).encode()

        # Mock request.get_data() to return our JSON payload
        mock_get_data.return_value = mock_request_data

        # Mock successful validation response
        mock_validate.return_value = ApiResponse(status_code=HTTPStatus.OK, exception_msg="")

        @validate_json(schema)
        async def mock_handler(self, request_msg: ApiResponse) -> quart.Response:
            return quart.Response(json.dumps({"status": 1, "message": "Success"}),
                            status=HTTPStatus.OK,
                            content_type="application/json")

        # Call the decorated function
        response = await mock_handler(self.view)

        # Assertions
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(await response.get_data(), b'{"status": 1, "message": "Success"}')
        mock_validate.assert_called_once()  # Ensure validation was called

    @patch("quart.request.get_data", new_callable=AsyncMock)
    @patch.object(BaseView, "_validate_json_body")
    async def test_decorator_validation_failure(self, mock_validate, mock_get_data):
        """Test decorator when JSON validation fails."""
        schema = {"type": "object", "properties": {"project_id": {"type": "integer"}}}
        mock_request_data = json.dumps({"project_id": 100}).encode()

        mock_get_data.return_value = mock_request_data
        mock_validate.return_value = ApiResponse(status_code=HTTPStatus.BAD_REQUEST, exception_msg="Invalid JSON")

        @validate_json(schema)
        async def mock_handler(self, request_msg: ApiResponse) -> quart.Response:
            return quart.Response(json.dumps({"status": 1, "message": "Should not reach here"}),
                            status=HTTPStatus.OK,
                            content_type="application/json")

        response = await mock_handler(self.view)

        # Assertions
        self.assertEqual(response.status_code, HTTPStatus.INTERNAL_SERVER_ERROR)
        self.assertEqual(await response.get_data(), b'{"status": 0, "error": "Invalid JSON"}')
        mock_validate.assert_called_once()

    @patch("quart.request.get_data", new_callable=AsyncMock)
    @patch.object(BaseView, "_validate_json_body",
                  side_effect=jsonschema.exceptions.ValidationError("Unexpected error"))
    async def test_decorator_jsonschema_exception_handling(self, mock_validate, mock_get_data):
        """Test decorator when an exception occurs during validation."""
        schema = {"type": "object", "properties": {"project_id": {"type": "integer"}}}
        mock_request_data = json.dumps({"project_id": 100}).encode()
        assert_value = b'{"status": 0, "error": "Schema validation error: Unexpected error"}'

        mock_get_data.return_value = mock_request_data

        @validate_json(schema)
        async def mock_handler(self, request_msg: ApiResponse) -> quart.Response:
            return quart.Response(json.dumps({"status": 1, "message": "Should not reach here"}),
                                  status=HTTPStatus.OK,
                                  content_type="application/json")

        response = await mock_handler(self.view)

        # Assertions
        self.assertEqual(response.status_code, HTTPStatus.INTERNAL_SERVER_ERROR)
        self.assertIn(assert_value, await response.get_data())
        mock_validate.assert_called_once()

    @patch("quart.request.get_data", new_callable=AsyncMock)
    @patch.object(BaseView, "_validate_json_body",
                  side_effect=json.JSONDecodeError("Unexpected error", "None", 12))
    async def test_decorator_jsons_exception_handling(self, mock_validate, mock_get_data):
        """Test decorator when an exception occurs during validation."""
        schema = {"type": "object", "properties": {"project_id": {"type": "integer"}}}
        mock_request_data = json.dumps({"project_id": 100}).encode()
        assert_value = b'{"status": 0, "error": "JSON decoding error: Unexpected error: line 1 column 13 (char 12)"}'

        mock_get_data.return_value = mock_request_data

        @validate_json(schema)
        async def mock_handler(self, request_msg: ApiResponse) -> quart.Response:
            return quart.Response(json.dumps({"status": 1, "message": "Should not reach here"}),
                                  status=HTTPStatus.OK,
                                  content_type="application/json")

        response = await mock_handler(self.view)

        # Assertions
        self.assertEqual(response.status_code, HTTPStatus.INTERNAL_SERVER_ERROR)
        self.assertIn(assert_value, await response.get_data())
        mock_validate.assert_called_once()

    @patch("quart.request.get_data", new_callable=AsyncMock)
    @patch.object(BaseView, "_validate_json_body",
                  side_effect=requests.exceptions.ConnectionError("Unexpected issue in request"))
    async def test_decorator_requests_exception_handling(self, mock_validate, mock_get_data):
        """Test decorator when an exception occurs during validation."""
        schema = {"type": "object", "properties": {"project_id": {"type": "integer"}}}
        mock_request_data = json.dumps({"project_id": 100}).encode()
        assert_value = b'{"status": 0, "error": "Connection error: Unexpected issue in request"}'

        mock_get_data.return_value = mock_request_data

        @validate_json(schema)
        async def mock_handler(self, request_msg: ApiResponse) -> quart.Response:
            return quart.Response(json.dumps({"status": 1, "message": "Should not reach here"}),
                                  status=HTTPStatus.OK,
                                  content_type="application/json")

        response = await mock_handler(self.view)

        # Assertions
        self.assertEqual(response.status_code, HTTPStatus.INTERNAL_SERVER_ERROR)
        self.assertIn(assert_value, await response.get_data())
        mock_validate.assert_called_once()

    @patch("quart.request.get_data", new_callable=AsyncMock)
    @patch.object(BaseView, "_validate_json_body",
                  side_effect=TypeError("Unknown type"))
    async def test_decorator_type_error_exception_handling(self, mock_validate, mock_get_data):
        """Test decorator when an exception occurs during validation."""
        schema = {"type": "object", "properties": {"project_id": {"type": "integer"}}}
        mock_request_data = json.dumps({"project_id": 100}).encode()
        assert_value = b'{"status": 0, "error": "Type error: Unknown type"}'

        mock_get_data.return_value = mock_request_data

        @validate_json(schema)
        async def mock_handler(self, request_msg: ApiResponse) -> quart.Response:
            return quart.Response(json.dumps({"status": 1, "message": "Should not reach here"}),
                                  status=HTTPStatus.OK,
                                  content_type="application/json")

        response = await mock_handler(self.view)

        # Assertions
        self.assertEqual(response.status_code, HTTPStatus.INTERNAL_SERVER_ERROR)
        self.assertIn(assert_value, await response.get_data())
        mock_validate.assert_called_once()

    def test_verify_api_signature_valid_signature(self):
        """Test with a valid signature."""
        self.assertTrue(self.view.verify_api_signature(self.secret_key,
                                                       self.data,
                                                       self.valid_signature))

    def test_verify_api_signature_invalid_signature(self):
        """Test with an invalid signature."""
        self.assertFalse(self.view.verify_api_signature(self.secret_key,
                                                        self.data,
                                                        self.invalid_signature))

    def test_verify_api_signature_different_data(self):
        """Test with different data but valid secret key."""
        different_data = b"differentdata"
        computed_signature = hmac.new(self.secret_key, different_data, hashlib.sha256).hexdigest()
        self.assertFalse(self.view.verify_api_signature(self.secret_key,
                                                        self.data,
                                                        computed_signature))

    def test_verify_api_signature_different_secret_key(self):
        """Test with a different secret key but same data."""
        different_secret = b"differentsecretkey"
        computed_signature = hmac.new(different_secret, self.data, hashlib.sha256).hexdigest()
        self.assertFalse(self.view.verify_api_signature(self.secret_key,
                                                        self.data,
                                                        computed_signature))

    def test_verify_api_signature_empty_data(self):
        """Test with empty data."""
        empty_data = b""
        computed_signature = hmac.new(self.secret_key, empty_data, hashlib.sha256).hexdigest()
        self.assertFalse(self.view.verify_api_signature(self.secret_key,
                                                        self.data,
                                                        computed_signature))

    def test_verify_api_signature_empty_secret_key(self):
        """Test with an empty secret key."""
        empty_secret = b""
        computed_signature = hmac.new(empty_secret, self.data, hashlib.sha256).hexdigest()
        self.assertFalse(self.view.verify_api_signature(self.secret_key,
                                                        self.data,
                                                        computed_signature))

    def test_generate_signature_consistency(self):
        """Test if the generated signature is consistent for the same inputs."""
        expected_signature = hmac.new(self.secret_key, self.data, hashlib.sha256).hexdigest()
        self.assertEqual(self.view.generate_api_signature(self.secret_key,
                                                          self.data),
                         expected_signature)

    def test_generate_signature_with_different_data(self):
        """Test if different data produces different signatures."""
        different_data = b"differentdata"
        signature_1 = self.view.generate_api_signature(self.secret_key, self.data)
        signature_2 = self.view.generate_api_signature(self.secret_key, different_data)
        self.assertNotEqual(signature_1, signature_2)

    def test_generate_signature_with_different_secret_key(self):
        """Test if different secret keys produce different signatures."""
        different_secret = b"differentsecretkey"
        signature_1 = self.view.generate_api_signature(self.secret_key, self.data)
        signature_2 = self.view.generate_api_signature(different_secret, self.data)
        self.assertNotEqual(signature_1, signature_2)

    def test_generate_signature_with_empty_data(self):
        """Test signature generation with empty data."""
        empty_data = b""
        expected_signature = hmac.new(self.secret_key, empty_data, hashlib.sha256).hexdigest()
        self.assertEqual(self.view.generate_api_signature(self.secret_key, empty_data), expected_signature)

    def test_generate_signature_with_empty_secret_key(self):
        """Test signature generation with an empty secret key."""
        empty_secret = b""
        expected_signature = hmac.new(empty_secret, self.data, hashlib.sha256).hexdigest()
        self.assertEqual(self.view.generate_api_signature(empty_secret,
                                                          self.data),
                         expected_signature)

    def test_generate_signature_with_dict(self):
        """Test signing with a dictionary input"""
        data = {"user": "alice", "action": "login"}
        expected_data = json.dumps(data, separators=(',', ':'), sort_keys=True).encode('utf-8')
        expected_signature = hmac.new(self.secret_key, expected_data, hashlib.sha256).hexdigest()

        result = BaseView.generate_api_signature(self.secret_key, data)
        self.assertEqual(result, expected_signature)

    def test_generate_signature_with_str(self):
        """Test signing with a string input"""
        data = "test_string"
        expected_signature = hmac.new(self.secret_key, data.encode('utf-8'), hashlib.sha256).hexdigest()

        result = BaseView.generate_api_signature(self.secret_key, data)
        self.assertEqual(result, expected_signature)

    def test_generate_signature_with_bytes(self):
        """Test signing with a bytes input"""
        data = b"test_bytes"
        expected_signature = hmac.new(self.secret_key, data, hashlib.sha256).hexdigest()

        result = BaseView.generate_api_signature(self.secret_key, data)
        self.assertEqual(result, expected_signature)

    def test_generate_signature_with_invalid_type(self):
        """Test invalid input type raises TypeError"""
        with self.assertRaises(TypeError):
            BaseView.generate_api_signature(self.secret_key, 1234)  # Invalid type (int)

    @patch("aiohttp.ClientSession.delete")
    async def test_call_api_delete_success(self, mock_delete):
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.content_type = self.view.CONTENT_TYPE_JSON
        mock_response.json.return_value = {"key": "value"}

        # Configure the mock to return the response when used in 'async with'
        mock_delete.return_value.__aenter__.return_value = mock_response

        # Call the method under test
        response = await self.view._call_api_delete("http://example.com", {"data": "test"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.body, {"key": "value"})
        self.assertEqual(response.content_type, self.view.CONTENT_TYPE_JSON)

    @patch("aiohttp.ClientSession.delete")
    async def test_call_api_delete_client_error(self, mock_delete):
        mock_delete.side_effect = ClientError("Connection error")

        response = await self.view._call_api_delete("http://example.com", {"data": "test"})
        self.assertIsNone(response.body)
        self.assertEqual(response.exception_msg, "Connection error")

    @patch("aiohttp.ClientSession.delete")
    async def test_call_api_delete_timeout_error(self, mock_delete):
        mock_delete.side_effect = asyncio.TimeoutError("Timeout error")

        response = await self.view._call_api_delete("http://example.com", {"data": "test"})
        self.assertIsNone(response.body)
        self.assertEqual(response.exception_msg, "Timeout error")
