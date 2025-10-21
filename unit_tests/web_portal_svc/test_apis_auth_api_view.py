from http import HTTPStatus
import unittest
from unittest.mock import AsyncMock, patch, MagicMock
from quart import Quart, request
from apis.auth_api_view import AuthApiView
from base_web_view import BaseWebView
from base_items_exception import BaseItemsException
from threadsafe_configuration import ThreadSafeConfiguration
from configuration.configuration_manager import ConfigurationManager
from metadata_settings import MetadataSettings


class TestApisAuthApiView(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.app = Quart(__name__)
        self.logger = MagicMock()
        self.metadata = MetadataSettings()
        self.auth_api_view = AuthApiView(self.logger,
                                         self.metadata)

        # Need to push the context for it to be valid in async tests
        self.app_ctx = self.app.app_context()
        await self.app_ctx.__aenter__()

        self.client = self.app.test_client()  # Client for making requests in tests

    async def asyncTearDown(self):
        await self.app_ctx.__aexit__(None, None, None)

    @patch.object(BaseWebView, '_generate_redirect', return_value="redirect_html")
    @patch.object(BaseWebView, '_has_auth_cookies', return_value=False)
    @patch.object(BaseWebView, '_validate_cookies', return_value=False)
    async def test_index_page_no_auth_cookies(self, mock_validate_cookies,
                                              mock_has_auth_cookies,
                                              mock_redirect):
        async with self.app.test_request_context('/'):
            mock_make_response = AsyncMock(return_value="redirect_response")
            with patch('quart.make_response', mock_make_response):
                result = await self.auth_api_view.index_page()

                mock_redirect.assert_called_once()
                mock_has_auth_cookies.assert_called_once()
                mock_validate_cookies.assert_not_called()
                self.assertEqual(await result.get_data(), b"redirect_html")

    @patch.object(BaseWebView, '_generate_redirect', return_value="redirect_html")
    @patch.object(BaseWebView, '_has_auth_cookies', return_value=True)
    @patch.object(BaseWebView, '_validate_cookies', return_value=False)
    async def test_index_page_has_invalid_auth_cookies(self, mock_validate_cookies,
                                                       mock_has_auth_cookies,
                                                       mock_redirect):
        async with self.app.test_request_context('/'):
            mock_make_response = AsyncMock(return_value="redirect_response")
            with patch('quart.make_response', mock_make_response):
                result = await self.auth_api_view.index_page()

                mock_redirect.assert_called_once()
                mock_has_auth_cookies.assert_called_once()
                mock_validate_cookies.assert_called_once()
                self.assertEqual(await result.get_data(), b"redirect_html")

    @patch.object(ConfigurationManager, 'get_entry')
    @patch.object(BaseWebView, '_has_auth_cookies', return_value=True)
    @patch.object(BaseWebView, '_validate_cookies', return_value=True)
    async def test_index_page_has_valid_auth_cookies(self,
                                                     mock_validate_cookies,
                                                     mock_has_auth_cookies,
                                                     mock_get_entry):
        self.auth_api_view._render_page = AsyncMock(return_value="mocked_template_content")

        response_body: dict = {"projects": [{'id': 0}]}

        # Mock the response of `_call_api_post`
        mock_call_api_get = AsyncMock()
        mock_call_api_get.return_value = MagicMock(
            status_code=HTTPStatus.OK,
            body=response_body)
        self.auth_api_view._call_api_get = mock_call_api_get

        async with self.app.app_context():
            async with self.app.test_request_context('/'):
                result = await self.auth_api_view.index_page()

                self.assertEqual(result, "mocked_template_content")
                mock_has_auth_cookies.assert_called_once()
                mock_validate_cookies.assert_called_once()

    @patch.object(ConfigurationManager, 'get_entry')
    @patch.object(BaseWebView, '_has_auth_cookies', return_value=True)
    @patch.object(BaseWebView, '_validate_cookies', return_value=True)
    async def test_index_page_invalid_gateway_request(self,
                                                      mock_validate_cookies,
                                                      mock_has_auth_cookies,
                                                      mock_get_entry):
        self.auth_api_view._render_page = AsyncMock(return_value="mocked_template_content")

        response_body: dict = {"status": 0}

        # Mock the response of `_call_api_post`
        mock_call_api_get = AsyncMock()
        mock_call_api_get.return_value = MagicMock(
            status_code=HTTPStatus.BAD_REQUEST,
            body=response_body)
        self.auth_api_view._call_api_get = mock_call_api_get

        async with self.app.app_context():
            async with self.app.test_request_context('/'):
                result = await self.auth_api_view.index_page()

                self.assertEqual(result, "mocked_template_content")
                mock_has_auth_cookies.assert_called_once()
                mock_validate_cookies.assert_called_once()

    async def test_index_page_internal_error(self):
        """Test when `BaseItemsException` is raised, returning internal error page."""

        self.auth_api_view._has_auth_cookies = MagicMock(
            side_effect=BaseItemsException("Test error"))
        self.auth_api_view._render_page = AsyncMock(return_value="internal_error_page")

        async with self.app.app_context():
            async with self.app.test_request_context('/'):
                result = await self.auth_api_view.index_page()
                self.assertEqual(result, "internal_error_page")
                self.auth_api_view._render_page.assert_awaited_once_with(
                    "internal_server_error.html")

    async def test_login_page_get_authenticated(self):
        """Test login_page_get redirects when user is already authenticated."""
        async with self.app.app_context():
            self.auth_api_view._has_auth_cookies = MagicMock(return_value=True)
            self.auth_api_view._validate_cookies = MagicMock(return_value=True)
            self.auth_api_view._render_page = AsyncMock(return_value="main_page")

            async with self.app.test_request_context('/login'):
                response = await self.auth_api_view.login_page_get()
                self.assertEqual(response.status_code, 200)
                self.assertEqual(await response.get_data(),
                                 b'<meta http-equiv="Refresh" content="0; url=\'http://localhost/"/>')

    async def test_login_page_get_unauthenticated(self):
        """Test login_page_get redirects when user is not authenticated."""
        async with self.app.test_request_context('/login'):

            self.auth_api_view._has_auth_cookies = MagicMock(return_value=False)
            self.auth_api_view._validate_cookies = MagicMock(return_value=False)
            self.auth_api_view._render_page = AsyncMock(return_value="main_page")

            mock_make_response = AsyncMock(return_value="redirect_response")
            with patch('quart.make_response', mock_make_response):
                result = await self.auth_api_view.login_page_get()

                self.assertEqual(result, "main_page")

    async def test_login_page_get_internal_error(self):
        """Test when `BaseItemsException` is raised, returning internal error page."""

        self.auth_api_view._has_auth_cookies = MagicMock(
            side_effect=BaseItemsException("Test error"))
        self.auth_api_view._render_page = AsyncMock(return_value="internal_error_page")

        async with self.app.app_context():
            async with self.app.test_request_context('/login'):
                result = await self.auth_api_view.login_page_get()
                self.assertEqual(result, "internal_error_page")
                self.auth_api_view._render_page.assert_awaited_once_with(
                    "internal_server_error.html")

    async def test_login_page_post_authenticated(self):
        """Test login_page_post redirects authenticated users."""
        async with self.app.app_context():
            self.auth_api_view._has_auth_cookies = MagicMock(return_value=True)
            self.auth_api_view._validate_cookies = MagicMock(return_value=True)
            self.auth_api_view._render_page = AsyncMock(return_value="login_page")

            async with self.app.test_request_context('/login', method="POST"):
                response = await self.auth_api_view.login_page_post()
                self.assertEqual(response.status_code, 200)
                self.assertEqual(await response.get_data(),
                                 b'<meta http-equiv="Refresh" content="0; url=\'http://localhost/"/>')

    async def test_login_page_post_missing_credentials(self):
        """Test login_page_post handles missing credentials."""
        async with self.app.test_request_context("/login", method="POST", data={}):
            self.auth_api_view._has_auth_cookies = MagicMock(return_value=False)
            self.auth_api_view._render_page = AsyncMock(return_value="main_page")

            async with self.app.test_request_context('/login', method="POST"):
                response = await self.auth_api_view.login_page_post()
                self.auth_api_view._render_page.assert_awaited_once_with(
                    'login.html', generate_error_msg=True, error_msg='Invalid username/password')
                self.assertEqual(response,
                                 'main_page')

    async def test_login_page_post_internal_error(self):
        """Test when `BaseItemsException` is raised, returning internal error page."""

        self.auth_api_view._has_auth_cookies = MagicMock(
            side_effect=BaseItemsException("Test error"))
        self.auth_api_view._render_page = AsyncMock(return_value="internal_error_page")

        async with self.app.app_context():
            async with self.app.test_request_context('/login', method="POST", data={}):
                result = await self.auth_api_view.login_page_post()
                self.assertEqual(result, "internal_error_page")
                self.auth_api_view._render_page.assert_awaited_once_with(
                    "internal_server_error.html")

    @patch.object(ThreadSafeConfiguration,
                  "get_entry",
                  return_value="https://mocked-url.com/")
    @patch.object(BaseWebView, '_process_post_form_data',
                  return_value={"user_email": "test", "password": "pass"})
    async def test_login_page_post_valid_login(self,
                                               mock_process_post_form_data,
                                               mock_config):
        """Test login_page_post handles successful login."""
        mock_response = AsyncMock(
            status_code=HTTPStatus.OK,
            body={"status": 1, "token": "fake-token"})

        # Mock the API call
        with patch.object(self.auth_api_view, "_call_api_post", return_value=mock_response):
            with patch.object(self.auth_api_view, "_render_page", return_value="login_page"):
                async with self.app.test_request_context('/login', method="POST"):
                    result = await self.auth_api_view.login_page_post()

                    # Ensure the mock API call was made correctly
                    self.auth_api_view._call_api_post.assert_awaited_once_with(
                        "https://mocked-url.com/web/session",
                        {"type": "basic", "email_address": "test", "password": "pass"}
                    )

                    self.assertEqual(result.status_code, HTTPStatus.OK)
                    self.assertEqual(await result.get_data(),
                                     b'<meta http-equiv="Refresh" content="0; url=\'http://localhost/"/>')

    @patch.object(ThreadSafeConfiguration,
                  "get_entry",
                  return_value="https://mocked-url.com/")
    @patch.object(BaseWebView, '_process_post_form_data',
                  return_value={"user_email": "test", "password": "pass"})
    async def test_login_page_post_api_failure(self,
                                               mock_process_post_form_data,
                                               mock_config):
        """Test login_page_post handles successful login."""
        mock_response = AsyncMock(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            body={"status": 1, "token": "fake-token"})

        # Mock the API call
        with patch.object(self.auth_api_view, "_call_api_post", return_value=mock_response):
            with patch.object(self.auth_api_view, "_render_page", return_value="login_page"):
                async with self.app.test_request_context('/login', method="POST"):
                    result = await self.auth_api_view.login_page_post()

                    # Ensure the mock API call was made correctly
                    self.auth_api_view._call_api_post.assert_awaited_once_with(
                        "https://mocked-url.com/web/session",
                        {"type": "basic", "email_address": "test", "password": "pass"}
                    )

                    self.auth_api_view._render_page.assert_awaited_once_with(
                        'login.html', generate_error_msg=True,
                        error_msg='Internal Error')

                    self.assertEqual(result, "login_page")

    @patch.object(ThreadSafeConfiguration,
                  "get_entry",
                  return_value="https://mocked-url.com/")
    @patch.object(BaseWebView, '_process_post_form_data',
                  return_value={"type": "basic", "user_email": "test", "password": "pass"})
    async def test_login_page_post_invalid_username_or_password(self,
                                               mock_process_post_form_data,
                                               mock_config):
        """Test login_page_post handles successful login."""
        mock_response = AsyncMock(
            status_code=HTTPStatus.OK,
            body={"status": 0, "error": "fake-token"})

        # Mock the API call
        with patch.object(self.auth_api_view, "_call_api_post", return_value=mock_response):
            with patch.object(self.auth_api_view, "_render_page", return_value="login_page"):
                async with self.app.test_request_context('/login', method="POST"):
                    result = await self.auth_api_view.login_page_post()

                    # Ensure the mock API call was made correctly
                    self.auth_api_view._call_api_post.assert_awaited_once_with(
                        "https://mocked-url.com/web/session",
                        {"type": "basic", "email_address": "test", "password": "pass"}
                    )

                    self.auth_api_view._render_page.assert_awaited_once_with(
                        'login.html', generate_error_msg=True,
                        error_msg='Invalid username/password')

                    self.assertEqual(result, "login_page")
