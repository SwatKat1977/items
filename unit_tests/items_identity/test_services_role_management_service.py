import unittest
import logging
from unittest.mock import MagicMock, AsyncMock
from weaver_framework.database.sqlite_interface import SqliteInterfaceException
from services.role_management_service import (
    RoleManagementService,
    RoleListResult,
    RoleLookupResult,
    RoleCreateResult,
    RoleUpdateResult,
    RoleDeleteResult,
)

_VALID_PERMISSIONS = [
    {"area": "test_cases", "can_read": True, "can_add_modify": True,
     "can_delete": False},
]
_VALID_PERMISSION_ROWS = [("test_cases", True, True, False)]

_INVALID_PERMISSIONS_NO_READ = [
    {"area": "test_cases", "can_read": False, "can_add_modify": True,
     "can_delete": False},
]

_DUPLICATE_AREA_PERMISSIONS = [
    {"area": "test_cases", "can_read": True, "can_add_modify": False,
     "can_delete": False},
    {"area": "test_cases", "can_read": True, "can_add_modify": False,
     "can_delete": False},
]


class TestRoleManagementService(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.mock_logger = MagicMock(spec=logging.Logger)
        self.mock_logger.getChild.return_value = MagicMock(spec=logging.Logger)

        self.mock_state = MagicMock()
        self.mock_state.is_available.return_value = True

        self.mock_repo = MagicMock()
        self.mock_repo.get_all_roles = AsyncMock()
        self.mock_repo.get_role_by_id = AsyncMock()
        self.mock_repo.get_role_permissions = AsyncMock()
        self.mock_repo.role_name_exists = AsyncMock(return_value=False)
        self.mock_repo.create_role = AsyncMock()
        self.mock_repo.update_role = AsyncMock()
        self.mock_repo.delete_role = AsyncMock()

        self.svc = RoleManagementService(
            self.mock_logger, self.mock_state, self.mock_repo)

    # -------------------------------------------------------
    # get_all_roles
    # -------------------------------------------------------

    async def test_get_all_roles_unavailable_when_state_unavailable(self):
        self.mock_state.is_available.return_value = False
        result = await self.svc.get_all_roles()
        self.assertFalse(result.available)

    async def test_get_all_roles_returns_empty_list(self):
        self.mock_repo.get_all_roles.return_value = []
        result = await self.svc.get_all_roles()
        self.assertEqual(result.roles, [])

    async def test_get_all_roles_returns_id_name_dicts(self):
        self.mock_repo.get_all_roles.return_value = [(1, "Tester"), (2, "Lead")]
        result = await self.svc.get_all_roles()
        self.assertEqual(result.roles,
                         [{"id": 1, "name": "Tester"}, {"id": 2, "name": "Lead"}])

    async def test_get_all_roles_unavailable_on_db_exception(self):
        self.mock_repo.get_all_roles.side_effect = SqliteInterfaceException("err")
        result = await self.svc.get_all_roles()
        self.assertFalse(result.available)
        self.mock_state.set_service_degraded.assert_called_once()

    # -------------------------------------------------------
    # get_role
    # -------------------------------------------------------

    async def test_get_role_unavailable_when_state_unavailable(self):
        self.mock_state.is_available.return_value = False
        result = await self.svc.get_role(1)
        self.assertFalse(result.available)

    async def test_get_role_not_found(self):
        self.mock_repo.get_role_by_id.return_value = None
        result = await self.svc.get_role(999)
        self.assertFalse(result.found)

    async def test_get_role_success_includes_permissions(self):
        self.mock_repo.get_role_by_id.return_value = (1, "Tester")
        self.mock_repo.get_role_permissions.return_value = _VALID_PERMISSION_ROWS
        result = await self.svc.get_role(1)
        self.assertTrue(result.found)
        self.assertEqual(result.role["id"], 1)
        self.assertEqual(result.role["name"], "Tester")
        self.assertEqual(result.role["permissions"], _VALID_PERMISSIONS)

    async def test_get_role_success_with_no_permissions_rows(self):
        self.mock_repo.get_role_by_id.return_value = (1, "Tester")
        self.mock_repo.get_role_permissions.return_value = []
        result = await self.svc.get_role(1)
        self.assertEqual(result.role["permissions"], [])

    async def test_get_role_unavailable_on_db_exception(self):
        self.mock_repo.get_role_by_id.side_effect = SqliteInterfaceException("err")
        result = await self.svc.get_role(1)
        self.assertFalse(result.available)
        self.mock_state.set_service_degraded.assert_called_once()

    # -------------------------------------------------------
    # create_role
    # -------------------------------------------------------

    async def test_create_role_unavailable_when_state_unavailable(self):
        self.mock_state.is_available.return_value = False
        result = await self.svc.create_role("Tester", [])
        self.assertFalse(result.available)

    async def test_create_role_success(self):
        self.mock_repo.create_role.return_value = 5
        result = await self.svc.create_role("Tester", _VALID_PERMISSIONS)
        self.assertTrue(result.available)
        self.assertFalse(result.conflict)
        self.assertFalse(result.invalid)
        self.assertEqual(result.role_id, 5)
        self.mock_repo.create_role.assert_awaited_once_with(
            "Tester", _VALID_PERMISSION_ROWS)

    async def test_create_role_conflict_when_name_exists(self):
        self.mock_repo.role_name_exists.return_value = True
        result = await self.svc.create_role("Tester", [])
        self.assertTrue(result.conflict)
        self.mock_repo.create_role.assert_not_called()

    async def test_create_role_invalid_when_add_modify_without_read(self):
        result = await self.svc.create_role(
            "Tester", _INVALID_PERMISSIONS_NO_READ)
        self.assertTrue(result.invalid)
        self.mock_repo.role_name_exists.assert_not_called()
        self.mock_repo.create_role.assert_not_called()

    async def test_create_role_invalid_when_area_repeated(self):
        result = await self.svc.create_role(
            "Tester", _DUPLICATE_AREA_PERMISSIONS)
        self.assertTrue(result.invalid)
        self.mock_repo.create_role.assert_not_called()

    async def test_create_role_empty_permissions_is_valid(self):
        self.mock_repo.create_role.return_value = 1
        result = await self.svc.create_role("Tester", [])
        self.assertFalse(result.invalid)
        self.assertEqual(result.role_id, 1)

    async def test_create_role_unavailable_on_db_exception(self):
        self.mock_repo.create_role.side_effect = SqliteInterfaceException("err")
        result = await self.svc.create_role("Tester", [])
        self.assertFalse(result.available)
        self.mock_state.set_service_degraded.assert_called_once()

    # -------------------------------------------------------
    # update_role
    # -------------------------------------------------------

    async def test_update_role_unavailable_when_state_unavailable(self):
        self.mock_state.is_available.return_value = False
        result = await self.svc.update_role(1)
        self.assertFalse(result.available)

    async def test_update_role_invalid_permissions_skips_lookup(self):
        result = await self.svc.update_role(
            1, permissions=_INVALID_PERMISSIONS_NO_READ)
        self.assertTrue(result.invalid)
        self.mock_repo.get_role_by_id.assert_not_called()

    async def test_update_role_not_found(self):
        self.mock_repo.get_role_by_id.return_value = None
        result = await self.svc.update_role(999, name="New")
        self.assertFalse(result.found)

    async def test_update_role_success_name_only(self):
        self.mock_repo.get_role_by_id.return_value = (1, "Old Name")
        result = await self.svc.update_role(1, name="New Name")
        self.assertTrue(result.success)
        self.mock_repo.update_role.assert_awaited_once_with(1, "New Name", None)

    async def test_update_role_success_permissions_only(self):
        self.mock_repo.get_role_by_id.return_value = (1, "Tester")
        result = await self.svc.update_role(1, permissions=_VALID_PERMISSIONS)
        self.assertTrue(result.success)
        self.mock_repo.update_role.assert_awaited_once_with(
            1, None, _VALID_PERMISSION_ROWS)

    async def test_update_role_renaming_to_own_current_name_is_not_a_conflict(self):
        self.mock_repo.get_role_by_id.return_value = (1, "Tester")
        self.mock_repo.role_name_exists.return_value = True
        result = await self.svc.update_role(1, name="Tester")
        self.assertFalse(result.conflict)
        self.assertTrue(result.success)

    async def test_update_role_renaming_to_another_roles_name_is_conflict(self):
        self.mock_repo.get_role_by_id.return_value = (1, "Tester")
        self.mock_repo.role_name_exists.return_value = True
        result = await self.svc.update_role(1, name="Lead")
        self.assertTrue(result.conflict)
        self.mock_repo.update_role.assert_not_called()

    async def test_update_role_no_name_change_does_not_check_uniqueness(self):
        self.mock_repo.get_role_by_id.return_value = (1, "Tester")
        result = await self.svc.update_role(1, permissions=[])
        self.assertTrue(result.success)
        self.mock_repo.role_name_exists.assert_not_called()

    async def test_update_role_unavailable_on_db_exception(self):
        self.mock_repo.get_role_by_id.side_effect = SqliteInterfaceException("err")
        result = await self.svc.update_role(1, name="New")
        self.assertFalse(result.available)
        self.mock_state.set_service_degraded.assert_called_once()

    # -------------------------------------------------------
    # delete_role
    # -------------------------------------------------------

    async def test_delete_role_unavailable_when_state_unavailable(self):
        self.mock_state.is_available.return_value = False
        result = await self.svc.delete_role(1)
        self.assertFalse(result.available)

    async def test_delete_role_not_found(self):
        self.mock_repo.get_role_by_id.return_value = None
        result = await self.svc.delete_role(999)
        self.assertFalse(result.found)
        self.mock_repo.delete_role.assert_not_called()

    async def test_delete_role_success(self):
        self.mock_repo.get_role_by_id.return_value = (1, "Tester")
        result = await self.svc.delete_role(1)
        self.assertTrue(result.success)
        self.mock_repo.delete_role.assert_awaited_once_with(1)

    async def test_delete_role_unavailable_on_db_exception(self):
        self.mock_repo.get_role_by_id.side_effect = SqliteInterfaceException("err")
        result = await self.svc.delete_role(1)
        self.assertFalse(result.available)
        self.mock_state.set_service_degraded.assert_called_once()


if __name__ == "__main__":
    unittest.main()
