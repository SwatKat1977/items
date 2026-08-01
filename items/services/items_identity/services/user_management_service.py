"""
Copyright 2025-2026 Integrated Test Management Suite Development Team

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
from dataclasses import dataclass, field
import logging
import secrets
import string
from typing import Optional
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError
from weaver_framework.database.sqlite_interface import SqliteInterfaceException
from items.services.items_identity.data_access.user_repository import (
    UserRepository)
from items.shared.account_status import AccountStatus
from items.services.items_identity.logon_type import LogonType
from items.shared.service_state import ServiceState

_PASSWORD_ALPHABET = string.ascii_letters + string.digits + string.punctuation
_GENERATED_PASSWORD_LENGTH = 16


def _generate_password() -> str:
    """Generate a cryptographically secure random password."""
    return ''.join(
        secrets.choice(_PASSWORD_ALPHABET)
        for _ in range(_GENERATED_PASSWORD_LENGTH)
    )


def _row_to_dict(row: tuple) -> dict:
    """Convert a ``user_profile`` row tuple to a profile dict.

    Args:
        row: ``(id, email_address, full_name, display_name, account_status,
              logon_type, is_administrator)``

    Returns:
        A dict with the same fields, ``is_administrator`` converted to bool.
    """
    user_id, email_address, full_name, display_name, account_status, \
        logon_type, is_administrator = row
    return {
        "id": user_id,
        "email_address": email_address,
        "full_name": full_name,
        "display_name": display_name,
        "account_status": account_status,
        "logon_type": logon_type,
        "is_administrator": bool(is_administrator),
    }


@dataclass
class UserListResult:
    """Outcome of a list-all-users request.

    Attributes:
        available: False when the service is unavailable.
        users:     List of user profile dicts when the request succeeded.
    """
    available: bool = True
    users: list = field(default_factory=list)


@dataclass
class UserLookupResult:
    """Outcome of a single-user lookup.

    Attributes:
        available: False when the service is unavailable.
        found:     False when no user exists with the requested ID.
        user:      The user's profile dict when the lookup succeeded.
    """
    available: bool = True
    found: bool = True
    user: Optional[dict] = field(default=None)


@dataclass
class UserCreateResult:
    """Outcome of a create-user request.

    Attributes:
        available:          False when the service is unavailable.
        conflict:           True when the email address is already registered.
        user_id:            The newly created user's ID on success.
        generated_password: Set when no password was supplied by the caller;
                            returned exactly once and never stored in plaintext.
    """
    available: bool = True
    conflict: bool = False
    user_id: Optional[int] = field(default=None)
    generated_password: Optional[str] = field(default=None)


@dataclass
class UserUpdateResult:
    """Outcome of an update-user request.

    Attributes:
        available:  False when the service is unavailable.
        found:      False when no user exists with the requested ID.
        forbidden:  True when the update would leave no active administrator.
        success:    True when the update was applied.
    """
    available: bool = True
    found: bool = True
    forbidden: bool = False
    success: bool = False


@dataclass
class PasswordResult:
    """Outcome of a password change or reset request.

    Attributes:
        available:      False when the service is unavailable.
        found:          False when no user exists with the requested ID.
        wrong_password: True when the supplied current password did not match
                        (self-change flow only).
        success:        True when the password was updated.
    """
    available: bool = True
    found: bool = True
    wrong_password: bool = False
    success: bool = False


class UserManagementService:
    """Create and modify user accounts.

    Covers listing users, creating accounts, updating profile fields,
    deactivating accounts, and changing passwords. Authentication is
    handled by :class:`AuthenticationService`; this service handles
    everything that happens *after* an account exists.
    """

    def __init__(self,
                 logger: logging.Logger,
                 state: ServiceState,
                 user_repository: UserRepository) -> None:
        """Initialise the user management service.

        Args:
            logger:          Parent logger.
            state:           Shared service state.
            user_repository: Repository providing user data access.
        """
        self._logger = logger.getChild(__name__)
        self._state: ServiceState = state
        self._repo: UserRepository = user_repository
        self._ph: PasswordHasher = PasswordHasher()

    async def get_all_users(self) -> UserListResult:
        """Return all user profiles.

        Returns:
            A :class:`UserListResult`. Database failures are reported as
            unavailable.
        """
        if not self._state.is_available():
            return UserListResult(available=False)

        try:
            rows = await self._repo.get_all_users()
        except SqliteInterfaceException as ex:
            self._logger.exception("Database failure listing users: %s", ex)
            self._state.set_service_degraded("User list database unavailable")
            return UserListResult(available=False)

        return UserListResult(users=[_row_to_dict(r) for r in rows])

    async def get_user_by_id(self, user_id: int) -> UserLookupResult:
        """Return a single user's profile by ID.

        Args:
            user_id: The user's primary key.

        Returns:
            A :class:`UserLookupResult`.
        """
        if not self._state.is_available():
            return UserLookupResult(available=False)

        try:
            row = await self._repo.get_user_by_id(user_id)
        except SqliteInterfaceException as ex:
            self._logger.exception(
                "Database failure fetching user %s: %s", user_id, ex)
            self._state.set_service_degraded("User lookup database unavailable")
            return UserLookupResult(available=False)

        if row is None:
            return UserLookupResult(found=False)

        return UserLookupResult(user=_row_to_dict(row))

    async def create_user(self,
                          email: str,
                          full_name: str,
                          display_name: str,
                          password: Optional[str],
                          is_administrator: bool) -> UserCreateResult:
        """Create a new user account.

        Hashes the supplied password with Argon2 before storing it. If
        ``password`` is ``None`` a cryptographically secure random password
        is generated and returned in :attr:`UserCreateResult.generated_password`
        — it is never logged or stored in plaintext and cannot be retrieved
        again.

        ``account_status`` is set to ``ACTIVE`` and ``logon_type`` to
        ``PASSWORD`` for all v1 accounts.

        Args:
            email:            Email address (login identifier; must be unique).
            full_name:        User's full name.
            display_name:     Name shown in the UI.
            password:         Plain-text initial password, or ``None`` to
                              generate one automatically.
            is_administrator: Whether the account has administrator access.

        Returns:
            A :class:`UserCreateResult`. ``conflict`` is True if the email is
            already registered. ``generated_password`` is set when the caller
            did not supply a password.
        """
        if not self._state.is_available():
            return UserCreateResult(available=False)

        generated: Optional[str] = None
        if password is None:
            password = _generate_password()
            generated = password

        try:
            if await self._repo.email_exists(email):
                return UserCreateResult(conflict=True)

            password_hash = self._ph.hash(password)

            user_id = await self._repo.create_user(
                email=email,
                full_name=full_name,
                display_name=display_name,
                account_status=AccountStatus.ACTIVE.value,
                logon_type=LogonType.PASSWORD.value,
                is_administrator=is_administrator)

            await self._repo.create_user_auth(user_id, password_hash)

        except SqliteInterfaceException as ex:
            self._logger.exception(
                "Database failure creating user %s: %s", email, ex)
            self._state.set_service_degraded(
                "User creation database unavailable")
            return UserCreateResult(available=False)

        return UserCreateResult(user_id=user_id, generated_password=generated)

    async def update_user(self,
                          user_id: int,
                          full_name: Optional[str] = None,
                          display_name: Optional[str] = None,
                          account_status: Optional[int] = None,
                          is_administrator: Optional[bool] = None
                          ) -> UserUpdateResult:
        """Update a user's profile fields (patch-style).

        Only the fields that are not ``None`` are changed; omitted fields
        retain their current values.  Before writing, the method checks that
        the change would not leave zero active administrators (last-admin
        guard).

        Args:
            user_id:          The user to update.
            full_name:        New full name, or ``None`` to leave unchanged.
            display_name:     New display name, or ``None`` to leave unchanged.
            account_status:   New account status, or ``None`` to leave
                              unchanged.
            is_administrator: New administrator flag, or ``None`` to leave
                              unchanged.

        Returns:
            A :class:`UserUpdateResult`. ``forbidden`` is True when the
            update would leave no active administrator.
        """
        if not self._state.is_available():
            return UserUpdateResult(available=False)

        try:
            row = await self._repo.get_user_by_id(user_id)
            if row is None:
                return UserUpdateResult(found=False)

            # Merge supplied values over current values.
            _, _, cur_full_name, cur_display_name, cur_status, _, cur_is_admin = row
            new_full_name = full_name if full_name is not None else cur_full_name
            new_display_name = (display_name if display_name is not None
                                else cur_display_name)
            new_status = (account_status if account_status is not None
                          else cur_status)
            new_is_admin = (is_administrator if is_administrator is not None
                            else bool(cur_is_admin))

            # Last-admin guard: reject if this change would leave zero active admins.
            if bool(cur_is_admin) and (not new_is_admin
                                       or new_status != AccountStatus.ACTIVE.value):
                admin_count = await self._repo.count_active_administrators(
                    AccountStatus.ACTIVE.value)
                if admin_count <= 1:
                    return UserUpdateResult(forbidden=True)

            await self._repo.update_user(user_id, new_full_name, new_display_name,
                                         new_status, new_is_admin)

        except SqliteInterfaceException as ex:
            self._logger.exception(
                "Database failure updating user %s: %s", user_id, ex)
            self._state.set_service_degraded(
                "User update database unavailable")
            return UserUpdateResult(available=False)

        return UserUpdateResult(success=True)

    async def reset_password(self,
                             user_id: int,
                             new_password: str) -> PasswordResult:
        """Reset a user's password without verifying the current one.

        Intended for administrator use. No knowledge of the existing password
        is required.

        Args:
            user_id:      The user whose password is being reset.
            new_password: New plain-text password.

        Returns:
            A :class:`PasswordResult`.
        """
        if not self._state.is_available():
            return PasswordResult(available=False)

        try:
            row = await self._repo.get_user_by_id(user_id)
            if row is None:
                return PasswordResult(found=False)

            password_hash = self._ph.hash(new_password)
            await self._repo.update_password(user_id, password_hash)

        except SqliteInterfaceException as ex:
            self._logger.exception(
                "Database failure resetting password for user %s: %s",
                user_id, ex)
            self._state.set_service_degraded(
                "Password reset database unavailable")
            return PasswordResult(available=False)

        return PasswordResult(success=True)

    async def change_own_password(self,
                                  user_id: int,
                                  current_password: str,
                                  new_password: str) -> PasswordResult:
        """Change a user's password after verifying their current one.

        Intended for self-service use. The current password must be supplied
        and must match before the new one is stored.

        Args:
            user_id:          The user changing their own password.
            current_password: Plain-text current password for verification.
            new_password:     New plain-text password.

        Returns:
            A :class:`PasswordResult`. ``wrong_password`` is True when the
            current password did not match.
        """
        if not self._state.is_available():
            return PasswordResult(available=False)

        try:
            row = await self._repo.get_user_by_id(user_id)
            if row is None:
                return PasswordResult(found=False)

            stored_hash = await self._repo.get_password_hash(user_id)
            if stored_hash is None:
                self._logger.error("User %s has no password record", user_id)
                return PasswordResult(available=False)

            try:
                self._ph.verify(stored_hash, current_password)
            except VerifyMismatchError:
                return PasswordResult(wrong_password=True)
            except (VerificationError, InvalidHashError) as ex:
                self._logger.error(
                    "Password verification error for user %s: %s", user_id, ex)
                return PasswordResult(available=False)

            new_hash = self._ph.hash(new_password)
            await self._repo.update_password(user_id, new_hash)

        except SqliteInterfaceException as ex:
            self._logger.exception(
                "Database failure changing password for user %s: %s",
                user_id, ex)
            self._state.set_service_degraded(
                "Password change database unavailable")
            return PasswordResult(available=False)

        return PasswordResult(success=True)
