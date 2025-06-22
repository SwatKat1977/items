import unittest
from unittest.mock import MagicMock, patch
import quart
from apis.web import create_web_routes

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

        # Patch the register_blueprint method on the real Blueprint to a mock so we can assert calls
        bp.register_blueprint = MagicMock()

        # Call again if needed, or if create_web_routes calls it internally, adjust accordingly

        # If create_web_routes already called register_blueprint internally,
        # you'll need to patch before calling create_web_routes or redesign the test

        # For demonstration, let's assume you patch before calling create_web_routes
        # You can move the patch earlier like so:
        # with patch.object(quart.Blueprint, 'register_blueprint', new=MagicMock()) as mock_reg_bp:
        #     bp = create_web_routes(mock_logger, mock_state)
        #     mock_reg_bp.assert_any_call(mock_health, url_prefix="/health")
        #     ...

        # But since patching after call won't catch calls inside create_web_routes,
        # better to patch before calling create_web_routes:

    @patch("apis.web.admin.create_admin_routes")
    @patch("apis.web.testcases_api.create_blueprint")
    @patch("apis.web.projects_api.create_blueprint")
    @patch("apis.web.health_api.create_blueprint")
    def test_create_web_routes_registers_all_blueprints_with_patch_register(
            self,
            mock_health_bp,
            mock_projects_bp,
            mock_testcases_bp,
            mock_admin_bp):
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

        with patch.object(quart.Blueprint, 'register_blueprint', new=MagicMock()) as mock_reg_bp:
            bp = create_web_routes(mock_logger, mock_state)

            self.assertIsInstance(bp, quart.Blueprint)

            mock_health_bp.assert_called_once_with(mock_logger, mock_state)
            mock_projects_bp.assert_called_once_with(mock_logger, mock_state)
            mock_testcases_bp.assert_called_once_with(mock_logger, mock_state)
            mock_admin_bp.assert_called_once_with(mock_logger, mock_state)

            # Now assert register_blueprint calls
            mock_reg_bp.assert_any_call(mock_health, url_prefix="/health")
            mock_reg_bp.assert_any_call(mock_projects, url_prefix="/projects")
            mock_reg_bp.assert_any_call(mock_testcases, url_prefix="/testcases")
            mock_reg_bp.assert_any_call(mock_admin, url_prefix="/admin")
