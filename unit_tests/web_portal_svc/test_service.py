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
import asyncio
import unittest
from http import HTTPStatus
from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch
from weaver_framework.configuration_system.configuration_manager import (
    ConfigurationError)
from weaver_framework.microservice.base_microservice import BaseMicroservice
from weaver_framework.microservice.api_response import ApiResponse
from items.services.items_web_portal.service import Service
from items.services.items_web_portal.configuration import Configuration


def _make_service():
    """Create a Service instance with only Configuration.__init__ patched.

    BaseMicroservice.__init__ runs for real (it already executes at import
    time via items/services/items_web_portal/__init__.py), so shutdown_event,
    _logger and the logger property are all properly initialised without any
    manual setup.
    """
    with patch.object(Configuration, "__init__", return_value=None):
        svc = Service(MagicMock())
    svc._config = MagicMock()
    svc._config.logging_log_level = "DEBUG"
    svc._config.general_api_signing_secret = "secret"
    svc._config.apis_gateway_svc = "http://gateway/"
    return svc


class TestServiceManageConfiguration(unittest.TestCase):
    """Tests for Service._manage_configuration (synchronous method)."""

    def setUp(self):
        self.service = _make_service()
        self.service._logger = MagicMock()

    def test_returns_false_when_check_for_configuration_reports_error(self):
        with patch.object(self.service, '_check_for_configuration',
                          return_value=("Config file not found", None, None)):
            result = self.service._manage_configuration()
        self.assertFalse(result)
        self.service._logger.critical.assert_called_once()

    def test_returns_false_on_configuration_error(self):
        self.service._config.process_config.side_effect = \
            ConfigurationError("bad section")
        with patch.object(self.service, '_check_for_configuration',
                          return_value=(None, True, "/path/config.ini")):
            result = self.service._manage_configuration()
        self.assertFalse(result)

    def test_returns_false_on_value_error(self):
        self.service._config.process_config.side_effect = \
            ValueError("invalid value")
        with patch.object(self.service, '_check_for_configuration',
                          return_value=(None, True, "/path/config.ini")):
            result = self.service._manage_configuration()
        self.assertFalse(result)

    def test_returns_true_on_success(self):
        with patch.object(self.service, '_check_for_configuration',
                          return_value=(None, True, "/path/config.ini")):
            result = self.service._manage_configuration()
        self.assertTrue(result)
        self.service._config.configure.assert_called_once()
        self.service._config.process_config.assert_called_once()


class TestServiceInitialise(unittest.IsolatedAsyncioTestCase):
    """Tests for Service._initialise (async method)."""

    async def asyncSetUp(self):
        self.service = _make_service()
        self.mock_bm_logger = MagicMock()
        self._logger_patcher = patch.object(
            BaseMicroservice, 'logger',
            new_callable=PropertyMock,
            return_value=self.mock_bm_logger)
        self._logger_patcher.start()

        self._session_patcher = patch(
            "items.services.items_web_portal.service.aiohttp.ClientSession",
            return_value=AsyncMock())
        self._session_patcher.start()

        self._rest_client_patcher = patch(
            "items.services.items_web_portal.service.RestClient")
        self._rest_client_patcher.start()

        self._create_page_handlers_patcher = patch(
            "items.services.items_web_portal.service.create_page_handlers",
            return_value=MagicMock())
        self._create_page_handlers_patcher.start()

    async def asyncTearDown(self):
        patch.stopall()

    async def test_initialise_returns_false_when_manage_configuration_fails(self):
        with patch.object(self.service, '_manage_configuration',
                          return_value=False):
            result = await self.service._initialise()
        self.assertFalse(result)

    async def test_initialise_reraises_and_closes_session_on_cancelled_error(self):
        with patch.object(self.service, '_manage_configuration',
                          return_value=True), \
             patch.object(self.service, '_get_metadata',
                          new=AsyncMock(side_effect=asyncio.CancelledError)):
            with self.assertRaises(asyncio.CancelledError):
                await self.service._initialise()
        self.assertIsNone(self.service._http_session)

    async def test_initialise_reraises_and_closes_session_on_keyboard_interrupt(self):
        with patch.object(self.service, '_manage_configuration',
                          return_value=True), \
             patch.object(self.service, '_get_metadata',
                          new=AsyncMock(side_effect=KeyboardInterrupt)):
            with self.assertRaises(KeyboardInterrupt):
                await self.service._initialise()
        self.assertIsNone(self.service._http_session)

    async def test_initialise_returns_false_when_metadata_retrieval_fails(self):
        with patch.object(self.service, '_manage_configuration',
                          return_value=True), \
             patch.object(self.service, '_get_metadata',
                          new=AsyncMock(return_value=False)):
            result = await self.service._initialise()
        self.assertFalse(result)
        self.assertIsNone(self.service._http_session)

    async def test_initialise_returns_true_on_success(self):
        with patch.object(self.service, '_manage_configuration',
                          return_value=True), \
             patch.object(self.service, '_get_metadata',
                          new=AsyncMock(return_value=True)):
            result = await self.service._initialise()
        self.assertTrue(result)
        self.service._quart_instance.register_blueprint.assert_called_once()


class TestServiceTasksAndShutdown(unittest.IsolatedAsyncioTestCase):
    """Tests for Service._create_tasks, _shutdown_wait_task and _shutdown."""

    async def asyncSetUp(self):
        self.service = _make_service()

    async def test_create_tasks_returns_one_task(self):
        self.service.shutdown_event.set()
        tasks = await self.service._create_tasks()
        self.assertEqual(len(tasks), 1)
        await asyncio.gather(*tasks, return_exceptions=True)

    async def test_shutdown_wait_task_exits_when_shutdown_event_is_set(self):
        self.service.shutdown_event.set()
        await self.service._shutdown_wait_task()

    async def test_shutdown_closes_http_session_when_present(self):
        mock_session = AsyncMock()
        mock_session.closed = False
        self.service._http_session = mock_session
        await self.service._shutdown()
        mock_session.close.assert_called_once()
        self.assertIsNone(self.service._http_session)

    async def test_shutdown_noop_when_no_http_session(self):
        self.service._http_session = None
        await self.service._shutdown()
        self.assertIsNone(self.service._http_session)

    async def test_close_http_session_idempotent(self):
        mock_session = AsyncMock()
        mock_session.closed = False
        self.service._http_session = mock_session
        await self.service._close_http_session()
        # Second call must not attempt to close again.
        await self.service._close_http_session()
        mock_session.close.assert_called_once()

    async def test_close_http_session_skips_already_closed_session(self):
        mock_session = AsyncMock()
        mock_session.closed = True
        self.service._http_session = mock_session
        await self.service._close_http_session()
        mock_session.close.assert_not_called()
        self.assertIsNone(self.service._http_session)


class TestGetMetadata(unittest.IsolatedAsyncioTestCase):
    """Tests for Service._get_metadata."""

    async def asyncSetUp(self):
        self.service = _make_service()
        self.service._logger = MagicMock()
        self.service._rest_client = AsyncMock()
        self.service.METADATA_RETRY_DELAY = 0.01

    async def test_unauthorized_returns_false_immediately(self):
        self.service._rest_client.get.return_value = ApiResponse(
            status_code=HTTPStatus.UNAUTHORIZED)
        result = await self.service._get_metadata()
        self.assertFalse(result)
        self.service._rest_client.get.assert_called_once()

    async def test_ok_updates_metadata_and_returns_true(self):
        self.service._rest_client.get.return_value = ApiResponse(
            status_code=HTTPStatus.OK,
            body={
                "default_time_zone": "Europe/London",
                "using_server_default_time_zone": True,
                "instance_name": "INSTANCE"
            })
        result = await self.service._get_metadata()
        self.assertTrue(result)
        self.assertEqual(self.service._metadata_settings.default_time_zone,
                         "Europe/London")
        self.assertTrue(
            self.service._metadata_settings.using_server_default_time_zone)
        self.assertEqual(self.service._metadata_settings.instance_name,
                         "INSTANCE")

    async def test_single_attempt_failure_returns_false(self):
        self.service._rest_client.get.return_value = ApiResponse(
            status_code=HTTPStatus.SERVICE_UNAVAILABLE)
        result = await self.service._get_metadata(retries=0)
        self.assertFalse(result)
        self.service._rest_client.get.assert_called_once()

    async def test_finite_retries_gives_up_after_count(self):
        self.service._rest_client.get.return_value = ApiResponse(
            status_code=HTTPStatus.SERVICE_UNAVAILABLE)
        result = await self.service._get_metadata(retries=3)
        self.assertFalse(result)
        self.assertEqual(self.service._rest_client.get.call_count, 3)

    async def test_infinite_retries_succeeds_eventually(self):
        self.service._rest_client.get.side_effect = [
            ApiResponse(status_code=HTTPStatus.SERVICE_UNAVAILABLE),
            ApiResponse(status_code=HTTPStatus.SERVICE_UNAVAILABLE),
            ApiResponse(status_code=HTTPStatus.OK,
                       body={"default_time_zone": "UTC",
                             "using_server_default_time_zone": False,
                             "instance_name": "X"}),
        ]
        result = await self.service._get_metadata(
            retries=self.service.GET_METADATA_INFINITE_RETRIES)
        self.assertTrue(result)
        self.assertEqual(self.service._rest_client.get.call_count, 3)

    async def test_shutdown_requested_during_wait_aborts(self):
        self.service._rest_client.get.return_value = ApiResponse(
            status_code=HTTPStatus.SERVICE_UNAVAILABLE)
        self.service.shutdown_event.set()
        result = await self.service._get_metadata(
            retries=self.service.GET_METADATA_INFINITE_RETRIES)
        self.assertFalse(result)
        self.service._rest_client.get.assert_called_once()


if __name__ == "__main__":
    unittest.main()
