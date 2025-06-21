import unittest
from unittest.mock import MagicMock, patch
from apis.web import create_web_routes
import quart


class TestCreateWebRoutes(unittest.TestCase):
    @patch("apis.web.admin.create_admin_routes")
    @patch("apis.web.testcases_api.create_blueprint")
    @patch("apis.web.projects_api.create_blueprint")
    @patch("apis.web.health_api.create_blueprint")
    def test_create_web_routes_registers_all_blueprints(
        self,
        mock_health_bp,
        mock_projects_bp,
        mock_testcases_bp,
        mock_admin_bp):
        # Mock return values for blueprints
        mock_health = MagicMock(spec=quart.Blueprint)
        mock_projects = MagicMock(spec=quart.Blueprint)
        mock_testcases = MagicMock(spec=quart.Blueprint)
        mock_admin = MagicMock(spec=quart.Blueprint)

        mock_health_bp.return_value = mock_health
        mock_projects_bp.return_value = mock_projects
        mock_testcases_bp.return_value = mock_testcases
        mock_admin_bp.return_value = mock_admin

        mock_logger = MagicMock()
        mock_state = MagicMock()

        bp = create_web_routes(mock_logger, mock_state)

        self.assertIsInstance(bp, quart.Blueprint)

        # Check that each sub-blueprint was registered
        mock_health_bp.assert_called_once_with(mock_logger, mock_state)
        mock_projects_bp.assert_called_once_with(mock_logger, mock_state)
        mock_testcases_bp.assert_called_once_with(mock_logger, mock_state)
        mock_admin_bp.assert_called_once_with(mock_logger, mock_state)

        bp.register_blueprint.assert_any_call(mock_health, url_prefix="/health")
        bp.register_blueprint.assert_any_call(mock_projects, url_prefix="/projects")
        bp.register_blueprint.assert_any_call(mock_testcases, url_prefix="/testcases")
        bp.register_blueprint.assert_any_call(mock_admin, url_prefix="/admin")
