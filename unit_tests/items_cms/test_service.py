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
import os
import tempfile
import unittest
from unittest.mock import MagicMock, PropertyMock, patch
from quart import Quart
from weaver_framework.configuration_system.configuration_manager import (
    ConfigurationError)
from weaver_framework.microservice.base_microservice import BaseMicroservice
from items.services.items_cms.service import Service
from items.services.items_cms.cms_configuration import CMSConfiguration


def _make_service():
    """Create a Service instance with only CMSConfiguration.__init__ patched.

    BaseMicroservice.__init__ runs for real (it already executes at import time
    via items/services/items_cms/__init__.py), so shutdown_event, _logger and
    the logger property are all properly initialised without any manual setup.
    """
    with patch.object(CMSConfiguration, "__init__", return_value=None):
        svc = Service(Quart("test_service"))
    # Replace the blank CMSConfiguration instance with a controllable mock.
    svc._config = MagicMock()
    svc._config.logging_log_level = "DEBUG"
    svc._config.backend_db_filename = "/fake/path.db"
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

    async def asyncTearDown(self):
        self._logger_patcher.stop()

    async def test_initialise_returns_false_when_manage_configuration_fails(self):
        with patch.object(self.service, '_manage_configuration',
                          return_value=False):
            result = await self.service._initialise()
        self.assertFalse(result)

    async def test_initialise_returns_false_when_db_file_missing(self):
        self.service._config.backend_db_filename = "/does/not/exist.db"
        with patch.object(self.service, '_manage_configuration',
                          return_value=True):
            result = await self.service._initialise()
        self.assertFalse(result)

    async def test_initialise_returns_true_when_db_file_exists(self):
        fd, db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        try:
            self.service._config.backend_db_filename = db_path
            with patch.object(self.service, '_manage_configuration',
                               return_value=True), \
                 patch("items.services.items_cms.service.create_routes",
                       return_value=MagicMock()):
                result = await self.service._initialise()
            self.assertTrue(result)
        finally:
            os.unlink(db_path)


class TestServiceTasks(unittest.IsolatedAsyncioTestCase):
    """Tests for Service._create_tasks and Service._dummy_task."""

    async def asyncSetUp(self):
        self.service = _make_service()

    async def test_create_tasks_returns_one_task(self):
        # Signal shutdown immediately so _dummy_task exits without waiting.
        self.service.shutdown_event.set()
        tasks = await self.service._create_tasks()
        self.assertEqual(len(tasks), 1)
        # Allow the task to complete cleanly.
        await asyncio.gather(*tasks, return_exceptions=True)

    async def test_dummy_task_exits_when_shutdown_event_is_set(self):
        self.service.shutdown_event.set()
        # Should return immediately without blocking.
        await self.service._dummy_task()


if __name__ == "__main__":
    unittest.main()
