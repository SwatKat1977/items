import unittest
import logging
from unittest.mock import MagicMock, AsyncMock
from weaver_framework.database.sqlite_interface import SqliteInterfaceException
from items.shared.permission_area import PermissionArea
from services.project_membership_service import (
    ProjectMembershipService,
    EffectivePermissionsResult,
    MembershipListResult,
    MembershipCreateResult,
    MembershipUpdateResult,
    MembershipDeleteResult,
)

_UUID = "550e8400-e29b-41d4-a716-446655440000"

# UserRepository.get_user_by_uuid row shape:
# (id, uuid, email_address, full_name, display_name, account_status,
#  logon_type, is_administrator)
_USER_ROW = (1, _UUID, "a@b.com", "Full Name", "Display", 1, 0, 0)

# ProjectMemberRepository row shapes:
_MEMBERSHIP_ROW_WITH_ROLE = (10, 5, 2, "Tester")   # (id, project_id, role_id, role_name)
_MEMBERSHIP_ROW_NO_ROLE = (11, 7, None, None)


class TestProjectMembershipService(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.mock_logger = MagicMock(spec=logging.Logger)
        self.mock_logger.getChild.return_value = MagicMock(spec=logging.Logger)

        self.mock_state = MagicMock()
        self.mock_state.is_available.return_value = True

        self.mock_member_repo = MagicMock()
        self.mock_member_repo.get_memberships_for_user = AsyncMock()
        self.mock_member_repo.get_membership = AsyncMock()
        self.mock_member_repo.get_effective_permissions = AsyncMock(
            return_value=[])
        self.mock_member_repo.create_membership = AsyncMock()
        self.mock_member_repo.update_membership_role = AsyncMock()
        self.mock_member_repo.delete_membership = AsyncMock()

        self.mock_user_repo = MagicMock()
        self.mock_user_repo.get_user_by_uuid = AsyncMock(
            return_value=_USER_ROW)

        self.mock_role_repo = MagicMock()
        self.mock_role_repo.get_role_by_id = AsyncMock(
            return_value=(2, "Tester"))

        self.svc = ProjectMembershipService(
            self.mock_logger, self.mock_state,
            self.mock_member_repo, self.mock_user_repo, self.mock_role_repo)

    # -------------------------------------------------------
    # get_memberships
    # -------------------------------------------------------

    async def test_get_memberships_unavailable_when_state_unavailable(self):
        self.mock_state.is_available.return_value = False
        result = await self.svc.get_memberships(_UUID)
        self.assertFalse(result.available)

    async def test_get_memberships_not_found_when_user_missing(self):
        self.mock_user_repo.get_user_by_uuid.return_value = None
        result = await self.svc.get_memberships(_UUID)
        self.assertFalse(result.found)
        self.mock_member_repo.get_memberships_for_user.assert_not_called()

    async def test_get_memberships_returns_empty_list(self):
        self.mock_member_repo.get_memberships_for_user.return_value = []
        result = await self.svc.get_memberships(_UUID)
        self.assertEqual(result.memberships, [])

    async def test_get_memberships_returns_dicts_with_role(self):
        self.mock_member_repo.get_memberships_for_user.return_value = [
            _MEMBERSHIP_ROW_WITH_ROLE]
        result = await self.svc.get_memberships(_UUID)
        self.assertEqual(result.memberships,
                         [{"project_id": 5, "role_id": 2, "role_name": "Tester"}])

    async def test_get_memberships_returns_dicts_with_no_role(self):
        self.mock_member_repo.get_memberships_for_user.return_value = [
            _MEMBERSHIP_ROW_NO_ROLE]
        result = await self.svc.get_memberships(_UUID)
        self.assertEqual(result.memberships,
                         [{"project_id": 7, "role_id": None, "role_name": None}])

    async def test_get_memberships_uses_internal_id_not_uuid(self):
        self.mock_member_repo.get_memberships_for_user.return_value = []
        await self.svc.get_memberships(_UUID)
        self.mock_member_repo.get_memberships_for_user.assert_awaited_once_with(
            _USER_ROW[0])

    async def test_get_memberships_unavailable_on_db_exception(self):
        self.mock_member_repo.get_memberships_for_user.side_effect = (
            SqliteInterfaceException("err"))
        result = await self.svc.get_memberships(_UUID)
        self.assertFalse(result.available)
        self.mock_state.set_service_degraded.assert_called_once()

    # -------------------------------------------------------
    # add_membership
    # -------------------------------------------------------

    async def test_add_membership_unavailable_when_state_unavailable(self):
        self.mock_state.is_available.return_value = False
        result = await self.svc.add_membership(_UUID, 5)
        self.assertFalse(result.available)

    async def test_add_membership_not_found_when_user_missing(self):
        self.mock_user_repo.get_user_by_uuid.return_value = None
        result = await self.svc.add_membership(_UUID, 5)
        self.assertFalse(result.found)
        self.mock_member_repo.create_membership.assert_not_called()

    async def test_add_membership_success_with_role(self):
        self.mock_member_repo.get_membership.return_value = None
        result = await self.svc.add_membership(_UUID, 5, role_id=2)
        self.assertTrue(result.success)
        self.mock_member_repo.create_membership.assert_awaited_once_with(
            _USER_ROW[0], 5, 2)

    async def test_add_membership_success_without_role(self):
        self.mock_member_repo.get_membership.return_value = None
        result = await self.svc.add_membership(_UUID, 5)
        self.assertTrue(result.success)
        self.mock_role_repo.get_role_by_id.assert_not_called()
        self.mock_member_repo.create_membership.assert_awaited_once_with(
            _USER_ROW[0], 5, None)

    async def test_add_membership_role_not_found(self):
        self.mock_role_repo.get_role_by_id.return_value = None
        result = await self.svc.add_membership(_UUID, 5, role_id=999)
        self.assertTrue(result.role_not_found)
        self.mock_member_repo.get_membership.assert_not_called()
        self.mock_member_repo.create_membership.assert_not_called()

    async def test_add_membership_conflict_when_already_a_member(self):
        self.mock_member_repo.get_membership.return_value = (
            _MEMBERSHIP_ROW_WITH_ROLE)
        result = await self.svc.add_membership(_UUID, 5)
        self.assertTrue(result.conflict)
        self.mock_member_repo.create_membership.assert_not_called()

    async def test_add_membership_unavailable_on_db_exception(self):
        self.mock_member_repo.get_membership.side_effect = (
            SqliteInterfaceException("err"))
        result = await self.svc.add_membership(_UUID, 5)
        self.assertFalse(result.available)
        self.mock_state.set_service_degraded.assert_called_once()

    # -------------------------------------------------------
    # update_membership_role
    # -------------------------------------------------------

    async def test_update_membership_role_unavailable_when_state_unavailable(self):
        self.mock_state.is_available.return_value = False
        result = await self.svc.update_membership_role(_UUID, 5, 2)
        self.assertFalse(result.available)

    async def test_update_membership_role_not_found_when_user_missing(self):
        self.mock_user_repo.get_user_by_uuid.return_value = None
        result = await self.svc.update_membership_role(_UUID, 5, 2)
        self.assertFalse(result.found)

    async def test_update_membership_role_role_not_found(self):
        self.mock_role_repo.get_role_by_id.return_value = None
        result = await self.svc.update_membership_role(_UUID, 5, 999)
        self.assertTrue(result.role_not_found)
        self.mock_member_repo.get_membership.assert_not_called()

    async def test_update_membership_role_membership_not_found(self):
        self.mock_member_repo.get_membership.return_value = None
        result = await self.svc.update_membership_role(_UUID, 5, 2)
        self.assertTrue(result.membership_not_found)
        self.mock_member_repo.update_membership_role.assert_not_called()

    async def test_update_membership_role_success(self):
        self.mock_member_repo.get_membership.return_value = (
            _MEMBERSHIP_ROW_WITH_ROLE)
        result = await self.svc.update_membership_role(_UUID, 5, 3)
        self.assertTrue(result.success)
        self.mock_member_repo.update_membership_role.assert_awaited_once_with(
            _USER_ROW[0], 5, 3)

    async def test_update_membership_role_can_clear_to_none(self):
        self.mock_member_repo.get_membership.return_value = (
            _MEMBERSHIP_ROW_WITH_ROLE)
        result = await self.svc.update_membership_role(_UUID, 5, None)
        self.assertTrue(result.success)
        self.mock_role_repo.get_role_by_id.assert_not_called()
        self.mock_member_repo.update_membership_role.assert_awaited_once_with(
            _USER_ROW[0], 5, None)

    async def test_update_membership_role_unavailable_on_db_exception(self):
        self.mock_member_repo.get_membership.side_effect = (
            SqliteInterfaceException("err"))
        result = await self.svc.update_membership_role(_UUID, 5, 2)
        self.assertFalse(result.available)
        self.mock_state.set_service_degraded.assert_called_once()

    # -------------------------------------------------------
    # remove_membership
    # -------------------------------------------------------

    async def test_remove_membership_unavailable_when_state_unavailable(self):
        self.mock_state.is_available.return_value = False
        result = await self.svc.remove_membership(_UUID, 5)
        self.assertFalse(result.available)

    async def test_remove_membership_not_found_when_user_missing(self):
        self.mock_user_repo.get_user_by_uuid.return_value = None
        result = await self.svc.remove_membership(_UUID, 5)
        self.assertFalse(result.found)

    async def test_remove_membership_membership_not_found(self):
        self.mock_member_repo.get_membership.return_value = None
        result = await self.svc.remove_membership(_UUID, 5)
        self.assertTrue(result.membership_not_found)
        self.mock_member_repo.delete_membership.assert_not_called()

    async def test_remove_membership_success(self):
        self.mock_member_repo.get_membership.return_value = (
            _MEMBERSHIP_ROW_WITH_ROLE)
        result = await self.svc.remove_membership(_UUID, 5)
        self.assertTrue(result.success)
        self.mock_member_repo.delete_membership.assert_awaited_once_with(
            _USER_ROW[0], 5)

    async def test_remove_membership_unavailable_on_db_exception(self):
        self.mock_member_repo.get_membership.side_effect = (
            SqliteInterfaceException("err"))
        result = await self.svc.remove_membership(_UUID, 5)
        self.assertFalse(result.available)
        self.mock_state.set_service_degraded.assert_called_once()

    # -------------------------------------------------------
    # get_effective_permissions
    # -------------------------------------------------------

    @staticmethod
    def _user(account_status=1, is_administrator=0):
        """A user row with the given account status and administrator flag."""
        return (1, _UUID, "a@b.com", "Full Name", "Display", account_status,
                0, is_administrator)

    @staticmethod
    def _all_flags(areas, value):
        """True if every flag in every area equals ``value``."""
        return all(flag is value
                   for grant in areas.values() for flag in grant.values())

    async def test_permissions_unavailable_when_state_unavailable(self):
        self.mock_state.is_available.return_value = False
        result = await self.svc.get_effective_permissions(_UUID, 5)
        self.assertIsInstance(result, EffectivePermissionsResult)
        self.assertFalse(result.available)

    async def test_permissions_not_found_when_user_missing(self):
        self.mock_user_repo.get_user_by_uuid.return_value = None
        result = await self.svc.get_effective_permissions(_UUID, 5)
        self.assertFalse(result.found)
        self.mock_member_repo.get_effective_permissions.assert_not_called()

    async def test_permissions_cover_every_area(self):
        result = await self.svc.get_effective_permissions(_UUID, 5)
        self.assertEqual(set(result.areas),
                         {area.value for area in PermissionArea})

    async def test_permissions_disabled_account_gets_nothing(self):
        """§8 rule 3: a disabled account short-circuits everything, even an
        administrator who also holds a role."""
        self.mock_user_repo.get_user_by_uuid.return_value = self._user(
            account_status=0, is_administrator=1)
        result = await self.svc.get_effective_permissions(_UUID, 5)
        self.assertTrue(self._all_flags(result.areas, False))
        self.mock_member_repo.get_effective_permissions.assert_not_called()

    async def test_permissions_administrator_gets_everything(self):
        """§8 rule 4, and without needing a membership: the roles are not
        even consulted."""
        self.mock_user_repo.get_user_by_uuid.return_value = self._user(
            is_administrator=1)
        result = await self.svc.get_effective_permissions(_UUID, 5)
        self.assertTrue(self._all_flags(result.areas, True))
        self.mock_member_repo.get_effective_permissions.assert_not_called()

    async def test_permissions_non_member_gets_nothing(self):
        self.mock_member_repo.get_effective_permissions.return_value = []
        result = await self.svc.get_effective_permissions(_UUID, 5)
        self.assertTrue(result.available)
        self.assertTrue(result.found)
        self.assertTrue(self._all_flags(result.areas, False))

    async def test_permissions_member_gets_their_roles_grid(self):
        self.mock_member_repo.get_effective_permissions.return_value = [
            ("milestones", 1, 0, 0), ("test_cases", 1, 1, 0)]
        result = await self.svc.get_effective_permissions(_UUID, 5)
        self.assertEqual(
            result.areas["test_cases"],
            {"read": True, "add_modify": True, "delete": False})
        self.assertEqual(
            result.areas["milestones"],
            {"read": True, "add_modify": False, "delete": False})

    async def test_permissions_areas_not_in_the_roles_grid_are_denied(self):
        self.mock_member_repo.get_effective_permissions.return_value = [
            ("test_cases", 1, 1, 1)]
        result = await self.svc.get_effective_permissions(_UUID, 5)
        self.assertEqual(result.areas["test_runs"],
                         {"read": False, "add_modify": False,
                          "delete": False})

    async def test_permissions_flags_are_real_booleans(self):
        self.mock_member_repo.get_effective_permissions.return_value = [
            ("test_cases", 1, 0, 1)]
        result = await self.svc.get_effective_permissions(_UUID, 5)
        for flag in result.areas["test_cases"].values():
            self.assertIsInstance(flag, bool)

    async def test_permissions_unknown_area_is_ignored(self):
        self.mock_member_repo.get_effective_permissions.return_value = [
            ("not_an_area", 1, 1, 1), ("test_cases", 1, 0, 0)]
        result = await self.svc.get_effective_permissions(_UUID, 5)
        self.assertNotIn("not_an_area", result.areas)
        self.assertTrue(result.areas["test_cases"]["read"])

    async def test_permissions_uses_internal_id_and_project(self):
        await self.svc.get_effective_permissions(_UUID, 5)
        self.mock_member_repo.get_effective_permissions.assert_awaited_once_with(
            _USER_ROW[0], 5)

    async def test_permissions_unavailable_on_db_exception(self):
        self.mock_member_repo.get_effective_permissions.side_effect = (
            SqliteInterfaceException("err"))
        result = await self.svc.get_effective_permissions(_UUID, 5)
        self.assertFalse(result.available)
        self.mock_state.set_service_degraded.assert_called_once()


if __name__ == "__main__":
    unittest.main()
