import unittest
from unittest.mock import MagicMock, patch
from sql.sql_projects import SqlProjects
from threadsafe_configuration import ThreadSafeConfiguration

class TestSqlSqlProjects(unittest.TestCase):
    def setUp(self):
        self.logger = MagicMock()
        self.state_object = MagicMock()
        self.parent = MagicMock()

        # Patch ThreadSafeConfiguration.get_entry just for the test
        self.patcher = patch.object(
            ThreadSafeConfiguration,
            'get_entry',
            return_value=":memory:"
        )
        self.mock_get_entry = self.patcher.start()

        self.sql_projects = SqlProjects(self.logger, self.state_object, self.parent)

    # is_valid_project_id
    def test_is_valid_project_id_none(self):
        self.sql_projects.safe_query = MagicMock(return_value=None)
        self.assertIsNone(self.sql_projects.is_valid_project_id(1))

    def test_is_valid_project_id_true(self):
        self.sql_projects.safe_query = MagicMock(return_value=(1,))
        self.assertTrue(self.sql_projects.is_valid_project_id(42))

    def test_is_valid_project_id_false(self):
        self.sql_projects.safe_query = MagicMock(return_value=())
        self.assertFalse(self.sql_projects.is_valid_project_id(999))

    # get_project_details
    def test_get_project_details_none(self):
        self.sql_projects.safe_query = MagicMock(return_value=None)
        self.assertIsNone(self.sql_projects.get_project_details(1))

    def test_get_project_details_empty_tuple(self):
        self.sql_projects.safe_query = MagicMock(return_value=())
        self.assertEqual(self.sql_projects.get_project_details(2), {})

    def test_get_project_details_awaiting_purge(self):
        self.sql_projects.safe_query = MagicMock(return_value=('Name', 1, 'Ann', False))
        self.assertEqual(self.sql_projects.get_project_details(3), {})

    def test_get_project_details_valid(self):
        val = ('Project X', 0, 'Promo', True)
        expected = {
            'id': 4,
            'name': 'Project X',
            'announcement': 'Promo',
            'show_announcement_on_overview': True
        }
        self.sql_projects.safe_query = MagicMock(return_value=val)
        self.assertEqual(self.sql_projects.get_project_details(4), expected)

    # get_projects_details
    def test_get_projects_details_none(self):
        self.sql_projects.safe_query = MagicMock(return_value=None)
        self.assertIsNone(self.sql_projects.get_projects_details('id,name'))

    def test_get_projects_details_valid(self):
        rows = [('A', 1), ('B', 2)]
        self.sql_projects.safe_query = MagicMock(return_value=rows)
        self.assertEqual(self.sql_projects.get_projects_details('id,name'), rows)

    # unimplemented counters
    def test_get_no_of_milestones_for_project(self):
        self.assertEqual(self.sql_projects.get_no_of_milestones_for_project(5), 0)

    def test_get_no_of_testruns_for_project(self):
        self.assertEqual(self.sql_projects.get_no_of_testruns_for_project(6), 0)

    # project_name_exists
    def test_project_name_exists_none(self):
        self.sql_projects.safe_query = MagicMock(return_value=None)
        self.assertIsNone(self.sql_projects.project_name_exists("Foo"))

    def test_project_name_exists_zero(self):
        self.sql_projects.safe_query = MagicMock(return_value=(0,))
        self.assertFalse(self.sql_projects.project_name_exists("Foo"))

    def test_project_name_exists_nonzero(self):
        self.sql_projects.safe_query = MagicMock(return_value=(5,))
        self.assertTrue(self.sql_projects.project_name_exists("Foo"))

    # add_project
    def test_add_project_none(self):
        self.sql_projects.safe_insert_query = MagicMock(return_value=None)
        details = {"project_name": "Foo", "announcement": "A", "announcement_on_overview": False}
        self.assertIsNone(self.sql_projects.add_project(details))

    def test_add_project_valid(self):
        self.sql_projects.safe_insert_query = MagicMock(return_value=123)
        details = {"project_name": "Foo", "announcement": "A", "announcement_on_overview": True}
        self.assertEqual(self.sql_projects.add_project(details), 123)

    # modify_project
    def test_modify_project_with_name_success(self):
        self.sql_projects.safe_query = MagicMock(return_value=1)
        details = {"project_name": "New", "announcement": "A", "announcement_on_overview": False}
        self.assertTrue(self.sql_projects.modify_project(10, details))

    def test_modify_project_without_name_success(self):
        self.sql_projects.safe_query = MagicMock(return_value=2)
        details = {"announcement": "B", "announcement_on_overview": True}
        self.assertTrue(self.sql_projects.modify_project(11, details))

    def test_modify_project_failure(self):
        self.sql_projects.safe_query = MagicMock(return_value=None)
        details = {"announcement": "C", "announcement_on_overview": True}
        self.assertFalse(self.sql_projects.modify_project(12, details))

    # mark_project_for_awaiting_purge
    def test_mark_project_for_awaiting_purge_success(self):
        self.sql_projects.safe_query = MagicMock(return_value=1)
        self.assertTrue(self.sql_projects.mark_project_for_awaiting_purge(13))

    def test_mark_project_for_awaiting_purge_failure(self):
        self.sql_projects.safe_query = MagicMock(return_value=None)
        self.assertFalse(self.sql_projects.mark_project_for_awaiting_purge(14))

    # hard_delete_project
    def test_hard_delete_project_success(self):
        self.sql_projects.safe_query = MagicMock(return_value=1)
        self.assertTrue(self.sql_projects.hard_delete_project(15))

    def test_hard_delete_project_failure(self):
        self.sql_projects.safe_query = MagicMock(return_value=None)
        self.assertFalse(self.sql_projects.hard_delete_project(16))

    # get_project_id_by_name
    def test_get_project_id_by_name_none(self):
        self.sql_projects.safe_query = MagicMock(return_value=None)
        self.assertIsNone(self.sql_projects.get_project_id_by_name("Z"))

    def test_get_project_id_by_name_zero(self):
        self.sql_projects.safe_query = MagicMock(return_value=())
        self.assertEqual(self.sql_projects.get_project_id_by_name("Z"), 0)

    def test_get_project_id_by_name_valid(self):
        self.sql_projects.safe_query = MagicMock(return_value=(77,))
        self.assertEqual(self.sql_projects.get_project_id_by_name("Z"), 77)
