import unittest
from unittest.mock import MagicMock, patch
import logging
from sql.sql_tc_custom_fields import (
    SqlTCCustomFields,
    CustomFieldMoveDirection)

class TestSqlSqlTCCustomFields(unittest.TestCase):
    def setUp(self):
        self.mock_logger = MagicMock()
        self.mock_state = MagicMock()
        self.mock_parent = MagicMock()
        self.iface = SqlTCCustomFields(self.mock_logger, self.mock_state, self.mock_parent)

    def test_enum_values(self):
        self.assertEqual(CustomFieldMoveDirection.UP.value, 0)
        self.assertEqual(CustomFieldMoveDirection.DOWN.value, 1)

    # move_custom_field paths
    def test_move_none_row(self):
        self.iface.safe_query = MagicMock(return_value=None)
        self.assertIsNone(self.iface.move_custom_field(1, CustomFieldMoveDirection.UP))

    def test_move_empty_row(self):
        self.iface.safe_query = MagicMock(side_effect=[tuple(), 5])
        self.iface._SqlTCCustomFields__count_custom_fields = MagicMock(return_value=5)
        self.assertFalse(self.iface.move_custom_field(1, CustomFieldMoveDirection.DOWN))

    def test_move_out_of_bounds(self):
        self.iface.safe_query = MagicMock(side_effect=[(1,), 1])
        self.iface._SqlTCCustomFields__count_custom_fields = MagicMock(return_value=1)
        self.assertFalse(self.iface.move_custom_field(1, CustomFieldMoveDirection.UP))

    def test_move_target_lookup_error(self):
        self.iface.safe_query = MagicMock(side_effect=[(2,), 5])
        self.iface._SqlTCCustomFields__count_custom_fields = MagicMock(return_value=5)
        self.iface._SqlTCCustomFields__get_id_for_custom_field_in_position = MagicMock(return_value=-1)
        self.assertIsNone(self.iface.move_custom_field(1, CustomFieldMoveDirection.DOWN))

    def test_move_target_not_found(self):
        self.iface.safe_query = MagicMock(side_effect=[(2,), 5])
        self.iface._SqlTCCustomFields__count_custom_fields = MagicMock(return_value=5)
        self.iface._SqlTCCustomFields__get_id_for_custom_field_in_position = MagicMock(return_value=0)
        self.assertFalse(self.iface.move_custom_field(1, CustomFieldMoveDirection.DOWN))

    def test_move_success(self):
        self.iface.safe_query = MagicMock(side_effect=[(2,), 5, True])
        self.iface._SqlTCCustomFields__count_custom_fields = MagicMock(return_value=5)
        self.iface._SqlTCCustomFields__get_id_for_custom_field_in_position = MagicMock(return_value=10)
        self.assertTrue(self.iface.move_custom_field(1, CustomFieldMoveDirection.DOWN))

    # __get_id_for_custom_field_in_position
    def test_get_id_none(self):
        self.iface.safe_query = MagicMock(return_value=None)
        self.assertEqual(self.iface._SqlTCCustomFields__get_id_for_custom_field_in_position(1), -1)

    def test_get_id_empty(self):
        self.iface.safe_query = MagicMock(return_value=[])
        self.assertEqual(self.iface._SqlTCCustomFields__get_id_for_custom_field_in_position(1), 0)

    def test_get_id_valid(self):
        self.iface.safe_query = MagicMock(return_value=(42,))
        self.assertEqual(self.iface._SqlTCCustomFields__get_id_for_custom_field_in_position(1), 42)

    # custom_field_name_exists
    def test_field_name_exists_none(self):
        self.iface.safe_query = MagicMock(return_value=None)
        self.assertIsNone(self.iface.custom_field_name_exists("x"))

    def test_field_name_exists_true(self):
        self.iface.safe_query = MagicMock(return_value=(1,))
        self.assertTrue(self.iface.custom_field_name_exists("x"))

    # __count_custom_fields
    def test_count_none(self):
        self.iface.safe_query = MagicMock(return_value=None)
        self.assertEqual(self.iface._SqlTCCustomFields__count_custom_fields(), -1)

    def test_count_valid(self):
        self.iface.safe_query = MagicMock(return_value=(5,))
        self.assertEqual(self.iface._SqlTCCustomFields__count_custom_fields(), 5)

    # __get_custom_field_max_position
    def test_max_pos_none(self):
        self.iface.safe_query = MagicMock(return_value=None)
        self.assertEqual(self.iface._SqlTCCustomFields__get_custom_field_max_position(), -1)

    def test_max_pos_valid(self):
        self.iface.safe_query = MagicMock(return_value=(7,))
        self.assertEqual(self.iface._SqlTCCustomFields__get_custom_field_max_position(), 7)

    # __get_custom_field_type_info
    def test_type_info_none(self):
        self.iface.safe_query = MagicMock(return_value=None)
        self.assertIsNone(self.iface._SqlTCCustomFields__get_custom_field_type_info("str"))

    def test_type_info_empty(self):
        self.iface.safe_query = MagicMock(return_value=[])
        with self.assertLogs(self.iface._logger, level='WARNING'):
            self.assertIsNone(self.iface._SqlTCCustomFields__get_custom_field_type_info("str"))

    def test_type_info_valid(self):
        self.iface.safe_query = MagicMock(return_value=(2, 0, 1))
        result = self.iface._SqlTCCustomFields__get_custom_field_type_info("str")
        self.assertEqual(result, (2, False, True))

    # add_custom_field
    def test_add_fail_max(self):
        self.iface._SqlTCCustomFields__get_custom_field_max_position = MagicMock(return_value=-1)
        self.assertEqual(self.iface.add_custom_field("", "", "", "str", True, False, "", True), 0)

    def test_add_fail_type(self):
        self.iface._SqlTCCustomFields__get_custom_field_max_position = MagicMock(return_value=1)
        self.iface._SqlTCCustomFields__get_custom_field_type_info = MagicMock(return_value=None)
        self.assertEqual(self.iface.add_custom_field("", "", "", "str", True, False, "", True), 0)

    def test_add_fail_insert(self):
        self.iface._SqlTCCustomFields__get_custom_field_max_position = MagicMock(return_value=1)
        self.iface._SqlTCCustomFields__get_custom_field_type_info = MagicMock(return_value=(1, True, False))
        self.iface.safe_insert_query = MagicMock(return_value=None)
        self.assertEqual(self.iface.add_custom_field("", "", "", "str", True, False, "", True), -1)

    def test_add_success(self):
        self.iface._SqlTCCustomFields__get_custom_field_max_position = MagicMock(return_value=1)
        self.iface._SqlTCCustomFields__get_custom_field_type_info = MagicMock(return_value=(1, True, False))
        self.iface.safe_insert_query = MagicMock(return_value=99)
        self.assertEqual(self.iface.add_custom_field("", "", "", "str", True, False, "", True), 99)

    # assign_custom_field_to_project
    def test_assign_invalid_project(self):
        self.mock_parent.projects.get_project_id_by_name = MagicMock(return_value=0)
        self.assertEqual(self.iface.assign_custom_field_to_project(1, ["x"]), "Project 'x' is not valid")

    def test_assign_success(self):
        self.mock_parent.projects.get_project_id_by_name = MagicMock(return_value=5)
        self.iface.safe_bulk_insert = MagicMock(return_value=True)
        self.assertTrue(self.iface.assign_custom_field_to_project(1, ["p"]))

    def test_get_custom_field_type_info_invalid_type(self):
        with patch.object(self.iface, 'safe_query', return_value=[]):
            result = self.iface._SqlTCCustomFields__get_custom_field_type_info("nonexistent_type")
            self.assertIsNone(result)
            self.logger.warning.assert_called_once_with(
                "Invalid field type name '%s'", "nonexistent_type"
            )

    def test_move_custom_field_count_custom_fields_error(self):
        # Simulate safe_query returning a valid position for the field
        with patch.object(self.iface, 'safe_query', return_value=(2,)), \
             patch.object(self.iface, '_SqlTCCustomFields__count_custom_fields',
                          return_value=-1):

            result = self.iface.move_custom_field(field_id=1,
                                                  direction=CustomFieldMoveDirection.UP)
            self.assertIsNone(result)
