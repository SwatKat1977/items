import unittest
from unittest.mock import AsyncMock, MagicMock, patch
import json
import logging
import http
import requests
from apis.testcase_api_view import TestCaseApiView
from threadsafe_configuration import ThreadSafeConfiguration

class TestApiTestcaseApiView(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.logger = logging.getLogger("test_logger")
        self.sessions = MagicMock()  # Mocking Sessions
        self.view = TestCaseApiView(self.logger, self.sessions)
        self.project_id = 123

    @patch.object(ThreadSafeConfiguration, 'apis_cms_svc', new="http://cms-service/")
    async def test_successful_testcases_details(self):
        """Test successful API call (200 OK response)"""

        # Mock `_call_api_post`
        mock_call_api_post = AsyncMock()
        mock_call_api_post.return_value = MagicMock(status_code=http.HTTPStatus.OK, body=[])
        self.view._call_api_post = mock_call_api_post  # Inject mock

        response = await self.view.testcases_details(self.project_id)

        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        self.assertEqual(response.content_type, "application/json")
        self.assertEqual(await response.get_data(as_text=True), json.dumps([]))

        mock_call_api_post.assert_called_once_with("http://cms-service/testcases/details", {"project_id": self.project_id})

    @patch.object(ThreadSafeConfiguration, 'apis_cms_svc', new="http://cms-service/")
    async def test_api_error_response(self):
        """Test API call returning an error (non-200 status)"""

        # Mock `_call_api_post` with an error status
        mock_call_api_post = AsyncMock()
        mock_call_api_post.return_value.status_code = http.HTTPStatus.BAD_REQUEST
        mock_call_api_post.return_value.exception_msg = "Bad request error"
        self.view._call_api_post = mock_call_api_post  # Inject mock

        response = await self.view.testcases_details(self.project_id)

        self.assertEqual(response.status_code, http.HTTPStatus.INTERNAL_SERVER_ERROR)
        self.assertEqual(response.content_type, "application/json")
        self.assertEqual(await response.get_data(as_text=True), json.dumps({"status": 0, "error": "Internal error!"}))

    @patch.object(ThreadSafeConfiguration, 'apis_cms_svc', new="http://cms-service/")
    async def test_connection_error_handling(self):
        """Test handling of a connection error"""

        # Mock `_call_api_post` with a connection error
        mock_call_api_post = AsyncMock()
        mock_call_api_post.side_effect = requests.exceptions.ConnectionError("Connection error")
        self.view._call_api_post = mock_call_api_post  # Inject mock

        response = await self.view.testcases_details(self.project_id)

        self.assertEqual(response.status_code, http.HTTPStatus.INTERNAL_SERVER_ERROR)
        self.assertEqual(response.content_type, "application/json")
        self.assertIn("Connection error", await response.get_data(as_text=True))
