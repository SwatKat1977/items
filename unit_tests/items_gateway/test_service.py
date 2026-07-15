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
from items.services.items_gateway.service import Service
from items.services.items_gateway.gateway_configuration import (
    GatewayConfiguration)
from items.shared import __version__


def _make_service():
    """Create a Service instance with only GatewayConfiguration.__init__ patched.

    BaseMicroservice.__init__ runs for real (it already executes at import time
    via items/services/items_gateway/__init__.py), so shutdown_event, _logger
    and the logger property are all properly initialised without any manual
    setup.
    """
    with patch.object(GatewayConfiguration, "__init__", return_value=None):
        svc = Service(MagicMock())
    svc._config = MagicMock()
    svc._config.logging_log_level = "DEBUG"
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
            "items.services.items_gateway.service.aiohttp.ClientSession",
            return_value=MagicMock())
        self._session_patcher.start()

        self._metadata_handler_cls_patcher = patch(
            "items.services.items_gateway.service.MetadataHandler")
        self.mock_metadata_handler_cls = self._metadata_handler_cls_patcher.start()
        self.mock_metadata_handler_cls.return_value.read_metadata_file.\
            return_value = True

        self._web_portal_client_patcher = patch(
            "items.services.items_gateway.service.WebPortalClient")
        self._web_portal_client_patcher.start()

        self._rest_client_patcher = patch(
            "items.services.items_gateway.service.RestClient")
        self._rest_client_patcher.start()

        self._create_routes_patcher = patch(
            "items.services.items_gateway.service.create_routes",
            return_value=MagicMock())
        self._create_routes_patcher.start()

    async def asyncTearDown(self):
        patch.stopall()

    async def test_initialise_returns_false_when_manage_configuration_fails(self):
        with patch.object(self.service, '_manage_configuration',
                          return_value=False):
            result = await self.service._initialise()
        self.assertFalse(result)

    async def test_initialise_returns_false_when_metadata_read_fails(self):
        self.mock_metadata_handler_cls.return_value.read_metadata_file.\
            return_value = False
        with patch.object(self.service, '_manage_configuration',
                          return_value=True):
            result = await self.service._initialise()
        self.assertFalse(result)

    async def test_initialise_returns_false_when_identity_check_fails(self):
        with patch.object(self.service, '_manage_configuration',
                          return_value=True), \
             patch.object(self.service, '_check_identity_svc_status',
                          new=AsyncMock(return_value=False)):
            result = await self.service._initialise()
        self.assertFalse(result)

    async def test_initialise_returns_false_when_cms_check_fails(self):
        with patch.object(self.service, '_manage_configuration',
                          return_value=True), \
             patch.object(self.service, '_check_identity_svc_status',
                          new=AsyncMock(return_value=True)), \
             patch.object(self.service, '_check_cms_svc_status',
                          new=AsyncMock(return_value=False)):
            result = await self.service._initialise()
        self.assertFalse(result)

    async def test_initialise_returns_true_on_success(self):
        with patch.object(self.service, '_manage_configuration',
                          return_value=True), \
             patch.object(self.service, '_check_identity_svc_status',
                          new=AsyncMock(return_value=True)), \
             patch.object(self.service, '_check_cms_svc_status',
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
        self.service._http_session = AsyncMock()
        await self.service._shutdown()
        self.service._http_session.close.assert_called_once()

    async def test_shutdown_noop_when_no_http_session(self):
        self.service._http_session = None
        await self.service._shutdown()


class TestIdentitySvcHealthCheck(unittest.IsolatedAsyncioTestCase):
    """Tests for Service._identity_svc_health_check and
    Service._check_identity_svc_status."""

    async def asyncSetUp(self):
        self.service = _make_service()
        self.service._logger = MagicMock()
        self.service._rest_client = AsyncMock()

    async def _health_body(self, status="healthy", version=None):
        return {
            "status": status,
            "dependencies": {"database": "none", "service": "none"},
            "issues": None if status == "healthy" else [
                {"component": "db", "status": "partial", "details": "slow"}],
            "uptime_seconds": 10,
            "version": version or __version__
        }

    async def test_health_check_non_ok_status_returns_none(self):
        self.service._rest_client.get.return_value = ApiResponse(
            status_code=HTTPStatus.SERVICE_UNAVAILABLE)
        result = await self.service._identity_svc_health_check()
        self.assertIsNone(result)

    async def test_health_check_schema_invalid_raises_runtime_error(self):
        self.service._rest_client.get.return_value = ApiResponse(
            status_code=HTTPStatus.OK, body={"not": "matching schema"})
        with self.assertRaises(RuntimeError):
            await self.service._identity_svc_health_check()

    async def test_health_check_version_mismatch_logs_warning(self):
        body = await self._health_body(version="V9.9.9")
        self.service._rest_client.get.return_value = ApiResponse(
            status_code=HTTPStatus.OK, body=body)
        result = await self.service._identity_svc_health_check()
        self.assertEqual(result, body)
        self.service._logger.warning.assert_called()

    async def test_health_check_critical_returns_none(self):
        body = await self._health_body(status="critical")
        self.service._rest_client.get.return_value = ApiResponse(
            status_code=HTTPStatus.OK, body=body)
        result = await self.service._identity_svc_health_check()
        self.assertIsNone(result)

    async def test_health_check_degraded_returns_body(self):
        body = await self._health_body(status="degraded")
        self.service._rest_client.get.return_value = ApiResponse(
            status_code=HTTPStatus.OK, body=body)
        result = await self.service._identity_svc_health_check()
        self.assertEqual(result, body)

    async def test_health_check_healthy_returns_body(self):
        body = await self._health_body(status="healthy")
        self.service._rest_client.get.return_value = ApiResponse(
            status_code=HTTPStatus.OK, body=body)
        result = await self.service._identity_svc_health_check()
        self.assertEqual(result, body)

    async def test_check_identity_svc_status_succeeds_immediately(self):
        with patch.object(self.service, '_identity_svc_health_check',
                          new=AsyncMock(return_value={
                              "status": "healthy", "version": __version__})):
            result = await self.service._check_identity_svc_status()
        self.assertTrue(result)

    async def test_check_identity_svc_status_retries_then_succeeds(self):
        with patch.object(self.service, '_identity_svc_health_check',
                          new=AsyncMock(side_effect=[
                              None, {"status": "healthy",
                                     "version": __version__}])), \
             patch("items.services.items_gateway.service.asyncio.sleep",
                   new=AsyncMock()):
            result = await self.service._check_identity_svc_status()
        self.assertTrue(result)

    async def test_check_identity_svc_status_runtime_error_returns_false(self):
        with patch.object(self.service, '_identity_svc_health_check',
                          new=AsyncMock(side_effect=RuntimeError("bad schema"))):
            result = await self.service._check_identity_svc_status()
        self.assertFalse(result)


class TestCmsSvcHealthCheck(unittest.IsolatedAsyncioTestCase):
    """Tests for Service._cms_svc_health_check and
    Service._check_cms_svc_status."""

    async def asyncSetUp(self):
        self.service = _make_service()
        self.service._logger = MagicMock()
        self.service._rest_client = AsyncMock()

    async def _health_body(self, status="healthy", version=None):
        return {
            "status": status,
            "dependencies": {"database": "none"},
            "issues": None if status == "healthy" else [
                {"component": "db", "status": "partial", "details": "slow"}],
            "uptime_seconds": 10,
            "version": version or __version__
        }

    async def test_health_check_non_ok_status_returns_none(self):
        self.service._rest_client.get.return_value = ApiResponse(
            status_code=HTTPStatus.SERVICE_UNAVAILABLE)
        result = await self.service._cms_svc_health_check()
        self.assertIsNone(result)

    async def test_health_check_schema_invalid_raises_runtime_error(self):
        self.service._rest_client.get.return_value = ApiResponse(
            status_code=HTTPStatus.OK, body={"not": "matching schema"})
        with self.assertRaises(RuntimeError):
            await self.service._cms_svc_health_check()

    async def test_health_check_version_mismatch_logs_warning(self):
        body = await self._health_body(version="V9.9.9")
        self.service._rest_client.get.return_value = ApiResponse(
            status_code=HTTPStatus.OK, body=body)
        result = await self.service._cms_svc_health_check()
        self.assertEqual(result, body)
        self.service._logger.warning.assert_called()

    async def test_health_check_critical_returns_none(self):
        body = await self._health_body(status="critical")
        self.service._rest_client.get.return_value = ApiResponse(
            status_code=HTTPStatus.OK, body=body)
        result = await self.service._cms_svc_health_check()
        self.assertIsNone(result)

    async def test_health_check_degraded_returns_body(self):
        body = await self._health_body(status="degraded")
        self.service._rest_client.get.return_value = ApiResponse(
            status_code=HTTPStatus.OK, body=body)
        result = await self.service._cms_svc_health_check()
        self.assertEqual(result, body)

    async def test_health_check_healthy_returns_body(self):
        body = await self._health_body(status="healthy")
        self.service._rest_client.get.return_value = ApiResponse(
            status_code=HTTPStatus.OK, body=body)
        result = await self.service._cms_svc_health_check()
        self.assertEqual(result, body)

    async def test_check_cms_svc_status_succeeds_immediately(self):
        with patch.object(self.service, '_cms_svc_health_check',
                          new=AsyncMock(return_value={
                              "status": "healthy", "version": __version__})):
            result = await self.service._check_cms_svc_status()
        self.assertTrue(result)

    async def test_check_cms_svc_status_retries_then_succeeds(self):
        with patch.object(self.service, '_cms_svc_health_check',
                          new=AsyncMock(side_effect=[
                              None, {"status": "healthy",
                                     "version": __version__}])), \
             patch("items.services.items_gateway.service.asyncio.sleep",
                   new=AsyncMock()):
            result = await self.service._check_cms_svc_status()
        self.assertTrue(result)

    async def test_check_cms_svc_status_runtime_error_returns_false(self):
        with patch.object(self.service, '_cms_svc_health_check',
                          new=AsyncMock(side_effect=RuntimeError("bad schema"))):
            result = await self.service._check_cms_svc_status()
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
