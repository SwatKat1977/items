import unittest
from unittest.mock import MagicMock
import json
import logging
import time
from quart import Response
from http import HTTPStatus
from apis.web.health_api_view import HealthApiView
from state_object import StateObject
import service_health_enums as health_enums


class TestApiHealthApiView(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.mock_logger = MagicMock(spec=logging.Logger)
        self.mock_state = MagicMock(spec=StateObject)
        self.mock_state.startup_time = int(time.time()) - 5000  # 5000s uptime
        self.mock_state.version = "1.2.3"

        # Default to healthy state
        self.mock_state.database_health = health_enums.ComponentDegradationLevel.NONE
        self.mock_state.database_health_state_str = "OK"
        self.view = HealthApiView(self.mock_logger, self.mock_state)

    async def test_health_healthy(self):
        response = await self.view.health()
        self.assertIsInstance(response, Response)
        self.assertEqual(response.status_code, HTTPStatus.OK)

        data = json.loads(await response.get_data(as_text=True))
        self.assertEqual(data["status"], health_enums.STATUS_HEALTHY)
        self.assertEqual(data["issues"], None)
        self.assertEqual(data["uptime_seconds"], 5000)
        self.assertEqual(data["version"], "1.2.3")
        self.assertEqual(data["dependencies"], {
            "database": health_enums.ComponentDegradationLevelStr[health_enums.ComponentDegradationLevel.NONE],
        })

    async def test_health_degraded(self):
        self.mock_state.database_health = health_enums.ComponentDegradationLevel.PART_DEGRADED
        self.mock_state.database_health_state_str = "Slow queries detected"

        response = await self.view.health()
        self.assertEqual(response.status_code, HTTPStatus.OK)

        data = json.loads(await response.get_data(as_text=True))
        self.assertEqual(data["status"], health_enums.STATUS_DEGRADED)
        self.assertEqual(len(data["issues"]), 1)
        self.assertEqual(data["issues"][0]["component"], "database")
        self.assertEqual(data["issues"][0]["status"],
                         health_enums.ComponentDegradationLevelStr[health_enums.ComponentDegradationLevel.PART_DEGRADED])
        self.assertEqual(data["issues"][0]["details"], "Slow queries detected")

    async def test_health_critical(self):
        self.mock_state.database_health = health_enums.ComponentDegradationLevel.FULLY_DEGRADED
        self.mock_state.database_health_state_str = "Database down"

        response = await self.view.health()
        self.assertEqual(response.status_code, HTTPStatus.OK)

        data = json.loads(await response.get_data(as_text=True))
        self.assertEqual(data["status"], health_enums.STATUS_CRITICAL)
        self.assertEqual(len(data["issues"]), 1)
        self.assertEqual(data["issues"][0]["component"], "database")
        self.assertEqual(data["issues"][0]["status"],
                         health_enums.ComponentDegradationLevelStr[health_enums.ComponentDegradationLevel.FULLY_DEGRADED])
        self.assertEqual(data["issues"][0]["details"], "Database down")
