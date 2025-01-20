import unittest
from unittest.mock import AsyncMock, patch
from http import HTTPStatus
import json
import jsonschema
from types import SimpleNamespace
from aiohttp import ClientConnectionError, ClientError
from base_view import BaseView

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


class TestBaseView(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.view = BaseView()

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
        self.assertIsInstance(response.exception_msg, ClientError)

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
