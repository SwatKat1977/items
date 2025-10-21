import unittest
from unittest.mock import Mock, patch
import logging

from state_object import StateObject
from apis.admin import create_admin_routes


class TestCreateAdminRoutes(unittest.TestCase):
    @patch("apis.admin.create_cf_bp")
    @patch("apis.admin.quart.Blueprint")
    def test_create_admin_routes(self, mock_blueprint_class, mock_create_cf_bp):
        logger = Mock(spec=logging.Logger)
        state = Mock(spec=StateObject)

        mock_admin_bp = Mock()
        mock_blueprint_class.return_value = mock_admin_bp

        mock_cf_bp = Mock()
        mock_create_cf_bp.return_value = mock_cf_bp

        result = create_admin_routes(logger, state)

        # Asserts
        mock_blueprint_class.assert_called_once_with("admin_routes", "apis.admin")
        mock_create_cf_bp.assert_called_once_with(logger, state)
        mock_admin_bp.register_blueprint.assert_called_once_with(
            mock_cf_bp, url_prefix="/testcase_custom_fields"
        )
        self.assertEqual(result, mock_admin_bp)
