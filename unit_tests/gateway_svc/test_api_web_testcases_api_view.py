import unittest
from unittest.mock import AsyncMock, MagicMock, patch
import json
import logging
import http
import requests
from apis.web.testcases_api_view import TestCasesApiView
from threadsafe_configuration import ThreadSafeConfiguration

class TestApiTestcaseApiView(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.logger = MagicMock()
        self.sessions = MagicMock()  # Mocking Sessions
        self.view = TestCasesApiView(self.logger, self.sessions)
        self.view._logger = self.logger
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

    @patch.object(ThreadSafeConfiguration, 'apis_cms_svc', new_callable=lambda: "http://cms-service/")
    async def test_successful_get_testcase(self, mock_config):
        """Test successful API call (200 OK response)"""

        project_id = 123
        case_id = 456
        cms_service_url = "http://cms-service/"
        expected_url = f"{cms_service_url}testcases/get_case/{case_id}"
        expected_request_body = {"project_id": self.project_id}

        # Mock `_call_api_post`
        mock_call_api_post = AsyncMock()
        mock_call_api_post.return_value = MagicMock(
            status_code=http.HTTPStatus.OK, body={"testcase": "data"}
        )
        self.view._call_api_post = mock_call_api_post  # Inject mock

        response = await self.view.get_testcase(project_id, case_id)

        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        self.assertEqual(response.content_type, "application/json")
        self.assertEqual(await response.get_data(as_text=True), json.dumps({"testcase": "data"}))

        mock_call_api_post.assert_called_once_with(expected_url, expected_request_body)

    @patch.object(ThreadSafeConfiguration, 'apis_cms_svc', new_callable=lambda: "http://cms-service/")
    async def test_api_error_get_testcase(self, mock_config):
        """Test API call returning an error status"""

        project_id = 123
        case_id = 456
        cms_service_url = "http://cms-service/"
        expected_url = f"{cms_service_url}testcases/get_case/{case_id}"
        expected_request_body = {"project_id": self.project_id}

        # Mock `_call_api_post` to simulate a failed request
        mock_call_api_post = AsyncMock()
        mock_call_api_post.return_value = MagicMock(
            status_code=http.HTTPStatus.BAD_REQUEST, exception_msg="Some API error"
        )
        self.view._call_api_post = mock_call_api_post  # Inject mock

        response = await self.view.get_testcase(project_id, case_id)

        self.assertEqual(response.status_code, http.HTTPStatus.INTERNAL_SERVER_ERROR)
        self.assertEqual(response.content_type, "application/json")
        self.assertEqual(
            await response.get_data(as_text=True),
            json.dumps({"status": 0, "error": "Internal error!"})
        )

        mock_call_api_post.assert_called_once_with(expected_url, expected_request_body)
        self.logger.critical.assert_called_once()

    @patch.object(ThreadSafeConfiguration, 'apis_cms_svc', new_callable=lambda: "http://cms-service/")
    async def test_connection_error_get_testcase(self, mock_config):
        """Test handling of a connection error"""

        project_id = 123
        case_id = 456
        cms_service_url = "http://cms-service/"
        expected_url = f"{cms_service_url}testcases/get_case/{case_id}"
        expected_request_body = {"project_id": self.project_id}

        # Mock `_call_api_post` to raise a connection error
        mock_call_api_post = AsyncMock()
        mock_call_api_post.side_effect = requests.exceptions.ConnectionError("Connection failed")
        self.view._call_api_post = mock_call_api_post  # Inject mock

        response = await self.view.get_testcase(project_id, case_id)

        self.assertEqual(response.status_code, http.HTTPStatus.INTERNAL_SERVER_ERROR)
        self.assertEqual(response.content_type, "application/json")
        self.assertIn("Connection failed", await response.get_data(as_text=True))

        mock_call_api_post.assert_called_once_with(expected_url, expected_request_body)
        self.logger.error.assert_called_once()
