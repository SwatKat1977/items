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

    def test_system_name_exists_none(self):
        self.iface.safe_query = MagicMock(return_value=None)
        self.assertIsNone(self.iface.system_name_exists("x"))

    def test_system_name_exists_true(self):
        self.iface.safe_query = MagicMock(return_value=(1,))
        self.assertTrue(self.iface.system_name_exists("x"))

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
        # Patch the iface._logger to a real logger for assertLogs to work
        with patch.object(self.iface, '_logger', logging.getLogger('test_logger')):
            with self.assertLogs('test_logger', level='WARNING'):
                result = self.iface._SqlTCCustomFields__get_custom_field_type_info("str")
                self.assertIsNone(result)

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
            self.iface._logger.warning.assert_called_once_with(
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

    def test_get_fields_for_project_returns_none_on_query_failure(self):
        self.iface.safe_query = MagicMock(return_value=None)

        result = self.iface.get_fields_for_project(project_id=1)

        self.assertIsNone(result)
        self.iface.safe_query.assert_called_once()

    def test_get_fields_for_project_returns_empty_list_if_no_results(self):
        self.iface.safe_query = MagicMock(return_value=[])

        result = self.iface.get_fields_for_project(project_id=1)

        self.assertEqual(result, [])
        self.iface.safe_query.assert_called_once()

    def test_get_fields_for_project_returns_fields(self):
        expected_rows = [
            (1, 'Priority', 'Desc', 'priority', 'Text', 'system', 1, 0, 0, '', 1)
        ]
        self.iface.safe_query = MagicMock(return_value=expected_rows)

        result = self.iface.get_fields_for_project(project_id=1)

        self.assertEqual(result, expected_rows)
        self.iface.safe_query.assert_called_once()

    def test_get_all_fields_success(self):
        # Simulate safe_query returning a list of rows (dict-like or sqlite3.Row)
        self.iface.safe_query = MagicMock()

        mock_rows = [
            {
                "id": 1,
                "field_name": "Field1",
                "description": "Desc1",
                "system_name": "sys1",
                "field_type_name": "type1",
                "entry_type": "system",
                "enabled": True,
                "position": 1,
                "is_required": False,
                "default_value": "default1",
                "applies_to_all_projects": True,
                "linked_projects": None,
            },
            {
                "id": 2,
                "field_name": "Field2",
                "description": "Desc2",
                "system_name": "sys2",
                "field_type_name": "type2",
                "entry_type": "user",
                "enabled": False,
                "position": 2,
                "is_required": True,
                "default_value": "default2",
                "applies_to_all_projects": False,
                "linked_projects": "1:ProjectA,2:ProjectB",
            },
        ]
        self.iface.safe_query.return_value = mock_rows

        result = self.iface.get_all_fields()
        self.iface.safe_query.assert_called_once()
        self.assertEqual(result, mock_rows)

    def test_get_all_fields_empty(self):
        # safe_query returns empty list
        self.iface.safe_query = MagicMock()

        self.iface.safe_query.return_value = []

        result = self.iface.get_all_fields()
        self.iface.safe_query.assert_called_once()
        self.assertEqual(result, [])

    def test_get_all_fields_failure(self):
        # safe_query returns None, simulating a failure
        self.iface.safe_query = MagicMock()

        self.iface.safe_query.return_value = None

        result = self.iface.get_all_fields()
        self.iface.safe_query.assert_called_once()
        self.assertIsNone(result)
