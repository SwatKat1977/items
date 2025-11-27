import logging
import unittest
from unittest.mock import Mock, patch

from items_common.service_state import ServiceState
from apis import create_api_routes


class TestCreateApiRoutes(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.logger = Mock(spec=logging.Logger)
        self.state = Mock(spec=ServiceState)

        # Patch Blueprint and all route factories in apis.__init__
        self.patcher_bp = patch("apis.quart.Blueprint")
        self.patcher_health = patch("apis.create_heath_bp", new_callable=Mock)
        self.patcher_projects = patch("apis.create_projects_bp", new_callable=Mock)
        self.patcher_testcases = patch("apis.create_testcases_bp", new_callable=Mock)
        self.patcher_admin = patch("apis.create_admin_routes", new_callable=Mock)

        self.mock_blueprint_class = self.patcher_bp.start()
        self.mock_create_health = self.patcher_health.start()
        self.mock_create_projects = self.patcher_projects.start()
        self.mock_create_testcases = self.patcher_testcases.start()
        self.mock_create_admin = self.patcher_admin.start()

        self.addCleanup(self.patcher_bp.stop)
        self.addCleanup(self.patcher_health.stop)
        self.addCleanup(self.patcher_projects.stop)
        self.addCleanup(self.patcher_testcases.stop)
        self.addCleanup(self.patcher_admin.stop)

        # Mock returned blueprints
        self.mock_main_bp = Mock()
        self.mock_blueprint_class.return_value = self.mock_main_bp
        self.mock_create_health.return_value = Mock()
        self.mock_create_projects.return_value = Mock()
        self.mock_create_testcases.return_value = Mock()
        self.mock_create_admin.return_value = Mock()

    async def test_create_api_routes_success(self):
        result = create_api_routes(self.logger, self.state)

        self.assertEqual(result, self.mock_main_bp)

        self.mock_create_health.assert_called_once_with(self.logger, self.state)
        self.mock_create_projects.assert_called_once_with(self.logger, self.state)
        self.mock_create_testcases.assert_called_once_with(self.logger, self.state)
        self.mock_create_admin.assert_called_once_with(self.logger, self.state)

        self.assertEqual(self.mock_main_bp.register_blueprint.call_count, 4)
