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
from dataclasses import dataclass
import logging
import secrets
import string
from typing import Optional
from argon2 import PasswordHasher
from weaver_framework.database.sqlite_interface import SqliteInterfaceException
from items.services.items_identity.data_access.user_repository import (
    UserRepository)
from items.shared.account_logon_type import AccountLogonType
from items.shared.account_status import AccountStatus
from items.shared.service_state import ServiceState

# Length of a generated password. Only used when the caller does not supply
# one; the generated value is returned to the caller exactly once and is never
# logged or stored in plaintext.
GENERATED_PASSWORD_LENGTH: int = 16


def generate_password(length: int = GENERATED_PASSWORD_LENGTH) -> str:
    """Generate a cryptographically secure random password.

    Args:
        length: Desired password length.

    Returns:
        A randomly generated password string.
    """
    alphabet = string.ascii_letters + string.digits + string.punctuation
    return ''.join(secrets.choice(alphabet) for _ in range(length))


@dataclass
class UserManagementResult:
    """Outcome of a user management operation.

    Exactly one of the failure flags is set when the operation did not
    succeed. They are kept distinct so callers can map each to the correct
    HTTP status, and - importantly - so a validation failure is never
    mistaken for a service outage.

    Attributes:
        available:  False when the service cannot serve the request at all.
        found:      False when the requested account does not exist.
        conflict:   Set to a message when the request is valid but conflicts
            with current state (duplicate email, or demoting the last
            administrator).
        user:       The affected or requested account.
        users:      All accounts, for list operations.
        generated_password: A password generated on the caller's behalf,
            returned exactly once. None when the caller supplied one.
    """
    available: bool = True
    found: bool = True
    conflict: Optional[str] = None
    user: Optional[dict] = None
    users: Optional[list] = None
    generated_password: Optional[str] = None

    @property
    def success(self) -> bool:
        """True when the operation completed without any failure condition."""
        return self.available and self.found and self.conflict is None


class UserManagementService:
    """Create, read and update user accounts.

    Accounts are never deleted. Deactivation is performed by setting
    ``account_status`` to ``AccountStatus.DISABLED`` - see section 10.6 of
    ``design_docs/user_roles_design.md`` for why hard deletion is not offered.

    Two invariants are enforced here rather than at a higher layer, because
    they are properties of the data and must hold regardless of which client
    is calling:

    * Email addresses are unique. Checked before writing so a duplicate is
      reported as a conflict instead of raising a ``UNIQUE`` violation, which
      would be indistinguishable from a database outage and would wrongly mark
      the service degraded.
    * At least one active administrator must remain. Without this an
      administrator could demote or deactivate themselves and leave nobody
      able to reach the administration pages.
    """

    def __init__(self,
                 logger: logging.Logger,
                 state: ServiceState,
                 user_repository: UserRepository) -> None:
        """Initialise the user management service.

        Args:
            logger:          Parent logger used to create a service logger.
            state:           Shared service state used to determine
                availability and to record database degradation.
            user_repository: Repository providing user data access.
        """
        self._logger = logger.getChild(__name__)
        self._state: ServiceState = state
        self._user_repository: UserRepository = user_repository

    # ------------------------------------------------------------------
    # Reads
    # ------------------------------------------------------------------

    async def list_users(self) -> UserManagementResult:
        """Retrieve all user accounts.

        Returns:
            A result whose ``users`` holds one dict per account.
        """
        if not self._state.is_available():
            return UserManagementResult(available=False)

        try:
            rows = await self._user_repository.list_users()
        except SqliteInterfaceException as ex:
            return self._database_failure("listing users", ex)

        return UserManagementResult(
            users=[self._row_to_user(row) for row in rows])

    async def get_user(self, user_id: int) -> UserManagementResult:
        """Retrieve a single account by identifier.

        Args:
            user_id: Identifier of the account.

        Returns:
            A result whose ``user`` holds the account, or ``found=False``.
        """
        if not self._state.is_available():
            return UserManagementResult(available=False)

        try:
            row = await self._user_repository.get_user_by_id(user_id)
        except SqliteInterfaceException as ex:
            return self._database_failure("retrieving user", ex)

        if row is None:
            return UserManagementResult(found=False)

        return UserManagementResult(user=self._row_to_user(row))

    # ------------------------------------------------------------------
    # Writes
    # ------------------------------------------------------------------

    async def create_user(self,
                          email: str,
                          full_name: str,
                          display_name: str,
                          is_administrator: bool = False,
                          enabled: bool = True,
                          password: Optional[str] = None
                          ) -> UserManagementResult:
        """Create a user account.

        Args:
            email:            Email address; must not already be in use.
            full_name:        The user's full name.
            display_name:     Name shown in the interface.
            is_administrator: Whether the account may administer the instance.
            enabled:          Whether the account starts active.
            password:         Password to set. When omitted, one is generated
                and returned in the result exactly once.

        Returns:
            A result whose ``user`` holds the created account, and whose
            ``generated_password`` is set when no password was supplied.
        """
        # pylint: disable=too-many-arguments, too-many-positional-arguments

        if not self._state.is_available():
            return UserManagementResult(available=False)

        try:
            if await self._user_repository.email_address_exists(email):
                return UserManagementResult(
                    conflict=f"Email address '{email}' is already in use")
        except SqliteInterfaceException as ex:
            return self._database_failure("checking email address", ex)

        generated: Optional[str] = None
        if password is None:
            password = generate_password()
            generated = password

        password_hash: str = PasswordHasher().hash(password)

        status: int = (AccountStatus.ACTIVE.value if enabled
                       else AccountStatus.DISABLED.value)

        try:
            user_id = await self._user_repository.create_user(
                email=email,
                full_name=full_name,
                display_name=display_name,
                account_status=status,
                logon_type=AccountLogonType.BASIC.value,
                is_administrator=is_administrator,
                password_hash=password_hash)
            row = await self._user_repository.get_user_by_id(user_id)
        except SqliteInterfaceException as ex:
            return self._database_failure("creating user", ex)

        self._logger.info("Created user account '%s' (id %s, administrator=%s)",
                          email, user_id, is_administrator)

        return UserManagementResult(user=self._row_to_user(row),
                                    generated_password=generated)

    async def update_user(self,
                          user_id: int,
                          email: Optional[str] = None,
                          full_name: Optional[str] = None,
                          display_name: Optional[str] = None,
                          is_administrator: Optional[bool] = None,
                          enabled: Optional[bool] = None
                          ) -> UserManagementResult:
        """Update a user account.

        Only the supplied fields are changed; omitted fields keep their
        current values.

        Refuses to clear ``is_administrator`` or to deactivate the account if
        doing so would leave no active administrator.

        Args:
            user_id:          Identifier of the account to update.
            email:            New email address, if changing.
            full_name:        New full name, if changing.
            display_name:     New display name, if changing.
            is_administrator: New administrator flag, if changing.
            enabled:          New active state, if changing.

        Returns:
            A result whose ``user`` holds the updated account.
        """
        # pylint: disable=too-many-arguments, too-many-positional-arguments
        # pylint: disable=too-many-return-statements

        if not self._state.is_available():
            return UserManagementResult(available=False)

        try:
            row = await self._user_repository.get_user_by_id(user_id)
        except SqliteInterfaceException as ex:
            return self._database_failure("retrieving user", ex)

        if row is None:
            return UserManagementResult(found=False)

        current = self._row_to_user(row)

        new_email = current["email_address"] if email is None else email
        new_admin = (current["is_administrator"] if is_administrator is None
                     else is_administrator)
        new_enabled = (current["account_status"] == AccountStatus.ACTIVE.value
                       if enabled is None else enabled)

        try:
            if email is not None and await \
                    self._user_repository.email_address_exists(new_email,
                                                               user_id):
                return UserManagementResult(
                    conflict=f"Email address '{new_email}' is already in use")

            guard = await self._check_last_administrator(current, new_admin,
                                                         new_enabled)
            if guard is not None:
                return guard

            await self._user_repository.update_user(
                user_id=user_id,
                email=new_email,
                full_name=(current["full_name"] if full_name is None
                           else full_name),
                display_name=(current["display_name"] if display_name is None
                              else display_name),
                account_status=(AccountStatus.ACTIVE.value if new_enabled
                                else AccountStatus.DISABLED.value),
                is_administrator=new_admin)

            updated = await self._user_repository.get_user_by_id(user_id)

        except SqliteInterfaceException as ex:
            return self._database_failure("updating user", ex)

        return UserManagementResult(user=self._row_to_user(updated))

    async def set_password(self,
                           user_id: int,
                           password: Optional[str] = None
                           ) -> UserManagementResult:
        """Set or reset a user's password.

        Args:
            user_id:  Identifier of the account.
            password: Password to set. When omitted, one is generated and
                returned in the result exactly once.

        Returns:
            A result whose ``generated_password`` is set when no password was
            supplied.
        """
        if not self._state.is_available():
            return UserManagementResult(available=False)

        try:
            row = await self._user_repository.get_user_by_id(user_id)
        except SqliteInterfaceException as ex:
            return self._database_failure("retrieving user", ex)

        if row is None:
            return UserManagementResult(found=False)

        generated: Optional[str] = None
        if password is None:
            password = generate_password()
            generated = password

        try:
            await self._user_repository.update_password_hash(
                user_id, PasswordHasher().hash(password))
        except SqliteInterfaceException as ex:
            return self._database_failure("setting password", ex)

        self._logger.info("Password changed for user id %s", user_id)

        return UserManagementResult(user=self._row_to_user(row),
                                    generated_password=generated)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    async def _check_last_administrator(
            self,
            current: dict,
            new_admin: bool,
            new_enabled: bool) -> Optional[UserManagementResult]:
        """Reject changes that would remove the final active administrator.

        Args:
            current:     The account's current values.
            new_admin:   The administrator flag after the change.
            new_enabled: The active state after the change.

        Returns:
            A conflict result if the change is not permitted, otherwise None.
        """
        was_active_admin = (
            current["is_administrator"]
            and current["account_status"] == AccountStatus.ACTIVE.value)

        if not was_active_admin:
            return None

        # Still an active administrator afterwards - nothing to protect.
        if new_admin and new_enabled:
            return None

        active_admins = await self._user_repository \
            .count_active_administrators(AccountStatus.ACTIVE.value)

        if active_admins > 1:
            return None

        action = ("Removing administrator rights from" if not new_admin
                  else "Deactivating")
        return UserManagementResult(
            conflict=f"{action} this account would leave no active "
                     "administrator")

    def _database_failure(self,
                          activity: str,
                          ex: Exception) -> UserManagementResult:
        """Log a database failure, mark the service degraded, and report it.

        Reported as unavailable rather than not-found so an outage is never
        presented to the caller as a missing account.
        """
        self._logger.exception("Database failure %s: %s", activity, str(ex))
        self._state.set_service_degraded("User management database unavailable")
        return UserManagementResult(available=False)

    @staticmethod
    def _row_to_user(row: tuple) -> dict:
        """Map a user row from the repository to a named dict."""
        (user_id, email_address, full_name, display_name, insertion_date,
         account_status, logon_type, is_administrator) = row

        return {
            "id": user_id,
            "email_address": email_address,
            "full_name": full_name,
            "display_name": display_name,
            "insertion_date": insertion_date,
            "account_status": account_status,
            "logon_type": logon_type,
            # Exposed as a JSON boolean rather than the stored 0/1 so callers
            # do not have to know the storage representation.
            "is_administrator": bool(is_administrator),
        }
