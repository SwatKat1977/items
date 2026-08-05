import asyncio
import os
import unittest
from unittest.mock import ANY, AsyncMock, MagicMock, patch
from service import Service
from identity_configuration import IdentityConfiguration
from weaver_framework.configuration_system.configuration_manager import (
    ConfigurationError)


class TestService(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.mock_quart_instance = MagicMock()
        self.mock_logger_instance = MagicMock()

        patcher = patch.object(IdentityConfiguration, 'get_entry', return_value=":memory:")
        self.mock_get_entry = patcher.start()
        self.addCleanup(patcher.stop)

    @patch("service.__version__", new="V1.0.0-123-alpha")
    @patch("pathlib.Path.is_file", return_value=True)
    @patch("service.create_routes")
    @patch("service.AuthenticationService")
    @patch("service.UserRepository")
    async def test_initialise_success(self, mock_user_repo, mock_auth_svc,
                                      mock_create_routes, mock_isfile):
        mock_config = MagicMock()
        mock_config.logging_log_level = "DEBUG"
        mock_config.backend_db_filename = "mock_db.sqlite"

        service = Service(self.mock_quart_instance)
        service._logger = self.mock_logger_instance
        service._config = mock_config
        service._manage_configuration = MagicMock(return_value=True)

        result = await service._initialise()

        self.assertTrue(result)
        self.mock_logger_instance.info.assert_any_call(
            'ITEMS Identity Microservice %s', "V1.0.0-123-alpha")
        self.mock_logger_instance.info.assert_any_call(
            "Setting logging level to %s", "DEBUG")
        self.mock_logger_instance.setLevel.assert_called_once_with("DEBUG")
        service._manage_configuration.assert_called_once()

    async def test_initialise_failure_configuration(self):
        service = Service(self.mock_quart_instance)
        service._logger = self.mock_logger_instance
        service._manage_configuration = MagicMock(return_value=False)

        result = await service._initialise()

        self.assertFalse(result)
        service._manage_configuration.assert_called_once()
        self.mock_logger_instance.info.assert_called()

    @patch("pathlib.Path.is_file", return_value=False)
    @patch("service.AuthenticationService")
    @patch("service.UserRepository")
    async def test_initialise_failure_database_missing(self, mock_user_repo,
                                                       mock_auth_svc, mock_isfile):
        mock_config = MagicMock()
        mock_config.logging_log_level = "DEBUG"
        mock_config.backend_db_filename = "mock_db.sqlite"

        service = Service(self.mock_quart_instance)
        service._logger = self.mock_logger_instance
        service._config = mock_config
        service._manage_configuration = MagicMock(return_value=True)

        result = await service._initialise()

        self.assertFalse(result)
        service._manage_configuration.assert_called_once()

    @patch.dict(os.environ, {"ITEMS_IDENTITY_CONFIG_FILE_REQUIRED": "1"})
    def test_manage_configuration_missing_config_file_required(self):
        service = Service(self.mock_quart_instance)
        service._logger = self.mock_logger_instance

        result = service._manage_configuration()

        self.assertFalse(result)
        self.mock_logger_instance.critical.assert_called_with(
            "Configuration file is not defined")

    @patch.dict(os.environ, {
        "ITEMS_IDENTITY_CONFIG_FILE": "config_file_path",
        "ITEMS_IDENTITY_CONFIG_FILE_REQUIRED": "1"
    })
    def test_manage_configuration_success(self):
        service = Service(self.mock_quart_instance)
        service._logger = self.mock_logger_instance

        mock_config = MagicMock()
        mock_config.logging_log_level = "DEBUG"
        mock_config.backend_db_filename = "mock_db.sqlite"
        service._config = mock_config

        result = service._manage_configuration()

        self.assertTrue(result)
        mock_config.configure.assert_called_once_with(
            ANY, "config_file_path", True)
        mock_config.process_config.assert_called_once()
        self.mock_logger_instance.info.assert_any_call("[logging]")
        self.mock_logger_instance.info.assert_any_call(
            "=> Logging log level : %s", "DEBUG")
        self.mock_logger_instance.info.assert_any_call("[Backend]")
        self.mock_logger_instance.info.assert_any_call(
            "=> Database filename : %s", "mock_db.sqlite")

    async def test_create_tasks_returns_single_task(self):
        service = Service(self.mock_quart_instance)
        service._shutdown_event.set()
        tasks = await service._create_tasks()
        self.assertEqual(len(tasks), 1)
        await asyncio.gather(*tasks, return_exceptions=True)

    async def test_invite_expiry_task_completes_on_shutdown(self):
        service = Service(self.mock_quart_instance)
        service._shutdown_event.set()
        await asyncio.wait_for(service._invite_expiry_task(), timeout=1.0)

    async def test_invite_expiry_task_calls_expire_when_not_shutdown(self):
        """Loop body executes once when shutdown is signalled via wait_for."""
        service = Service(self.mock_quart_instance)
        service._invite_service = MagicMock()
        service._invite_service.expire_pending_invites = AsyncMock()

        async def fake_wait_for(coro, **kwargs):
            coro.close()  # prevent "coroutine never awaited" warning
            service._shutdown_event.set()

        with patch("asyncio.wait_for", side_effect=fake_wait_for):
            await service._invite_expiry_task()

        service._invite_service.expire_pending_invites.assert_awaited_once()

    async def test_invite_expiry_task_loops_after_timeout(self):
        """TimeoutError causes the loop to iterate again before shutdown."""
        service = Service(self.mock_quart_instance)
        service._invite_service = MagicMock()
        service._invite_service.expire_pending_invites = AsyncMock()
        call_count = 0

        async def fake_wait_for(coro, **kwargs):
            nonlocal call_count
            coro.close()  # prevent "coroutine never awaited" warning
            call_count += 1
            if call_count == 1:
                raise asyncio.TimeoutError()
            service._shutdown_event.set()

        with patch("asyncio.wait_for", side_effect=fake_wait_for):
            await service._invite_expiry_task()

        self.assertEqual(
            service._invite_service.expire_pending_invites.await_count, 2)

    @patch.dict(os.environ, {
        "ITEMS_IDENTITY_CONFIG_FILE": "config_file_path",
        "ITEMS_IDENTITY_CONFIG_FILE_REQUIRED": "1"
    })

    def test_manage_configuration_process_config_configuration_error(self):
        mock_config = MagicMock()
        mock_config.process_config = MagicMock(
            side_effect=ConfigurationError("bad config"))

        service = Service(self.mock_quart_instance)
        service._logger = self.mock_logger_instance
        service._config = mock_config

        result = service._manage_configuration()

        self.assertFalse(result)
        self.mock_logger_instance.critical.assert_called_with(
            "Configuration error : %s", "bad config")

    @patch.dict(os.environ, {
        "ITEMS_IDENTITY_CONFIG_FILE": "config_file_path",
        "ITEMS_IDENTITY_CONFIG_FILE_REQUIRED": "1"
    })
    def test_manage_configuration_process_config_exception(self):
        mock_config = MagicMock()
        mock_config.process_config = MagicMock(
            side_effect=ValueError("Test config error"))

        service = Service(self.mock_quart_instance)
        service._logger = self.mock_logger_instance
        service._config = mock_config

        result = service._manage_configuration()

        self.assertFalse(result)
        self.mock_logger_instance.critical.assert_called_with(
            "Configuration error : %s", "Test config error")
