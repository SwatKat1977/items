import unittest
from unittest.mock import MagicMock, patch
import logging

from apis.web.admin import create_admin_routes
from state_object import StateObject


class TestCreateAdminRoutes(unittest.TestCase):
    @patch("apis.web.admin.quart.Blueprint")  # <-- Patch the Blueprint class
    @patch("apis.web.admin.testcase_custom_fields_api.create_blueprint")
    def test_create_admin_routes(self, mock_create_cf_bp, mock_blueprint_cls):
        logger = logging.getLogger("test")
        state = MagicMock(spec=StateObject)

        # Mock blueprint instance returned by quart.Blueprint(...)
        mock_admin_bp = MagicMock(name="AdminBlueprint")
        mock_blueprint_cls.return_value = mock_admin_bp

        # Mock sub-blueprint from create_blueprint
        mock_sub_bp = MagicMock(name="TestcaseCustomFieldsBlueprint")
        mock_create_cf_bp.return_value = mock_sub_bp

        # Run function under test
        result = create_admin_routes(logger, state)

        # Assertions
        mock_blueprint_cls.assert_called_once_with("admin_routes", "apis.web.admin")
        mock_create_cf_bp.assert_called_once_with(logger, state)
        mock_admin_bp.register_blueprint.assert_called_once_with(
            mock_sub_bp, url_prefix="/testcase_custom_fields"
        )
        self.assertEqual(result, mock_admin_bp)
