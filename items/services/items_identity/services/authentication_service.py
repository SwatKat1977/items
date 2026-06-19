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
import logging
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError
from weaver_framework.database.sqlite_interface import SqliteInterfaceException
from items.shared.service_state import ServiceState
from items.services.items_identity.data_access.user_repository import \
    UserRepository
from items.shared.account_status import AccountStatus
from items.services.items_identity.logon_type import LogonType


class AuthenticationService:
    """
    Provides user authentication services for password-based accounts.

    This service validates user credentials, enforces account status
    restrictions, and coordinates authentication-related operational
    state management. Database failures are logged and may cause the
    service to transition into a degraded state.
    """
    # pylint: disable=too-few-public-methods

    def __init__(self,
                 logger: logging.Logger,
                 state: ServiceState,
                 user_repository: UserRepository) -> None:
        """
        Initialize the authentication service.

        Args:
            logger:
                Parent logger instance.

            state:
                Shared service operational state.

            user_repository:
                Repository used for user persistence operations.
        """
        self._logger = logger.getChild(__name__)
        self._state = state
        self._user_repository = user_repository

    async def authenticate_password(self,
                                    email: str,
                                    password: str) -> tuple[bool, str]:
        """
        Authenticate a user using an email address and password.

        The authentication process performs the following checks:

        1. Verifies that the authentication service is available.
        2. Retrieves the user account associated with the email address.
        3. Ensures the account uses password-based authentication.
        4. Verifies that the account is active.
        5. Retrieves the stored password hash.
        6. Compares the supplied password against the stored hash.

        Database failures are logged and may cause the service state to be
        marked as degraded.

        Args:
            email:
                Email address supplied by the user.

            password:
                Plain-text password supplied by the user.

        Returns:
            A tuple containing:

            * ``True`` and a success message when authentication succeeds.
            * ``False`` and a descriptive failure message when
              authentication fails.

            The returned tuple has the form::

                (
                    authentication_successful,
                    status_message
                )

        Notes:
            Authentication failures intentionally return a generic
            username/password mismatch message where appropriate to avoid
            disclosing account existence information.
        """
        # pylint: disable=too-many-return-statements

        # Check service availability
        if not self._state.is_available():
            return False, "Authentication service unavailable"

        # Retrieve user
        try:
            row = await self._user_repository.get_user_by_email(email)

        except SqliteInterfaceException as ex:

            self._logger.exception(
                "Database failure during authentication: %s",
                str(ex))

            self._state.set_service_degraded(
                "Authentication database unavailable")

            return False, "Internal authentication error"

        # Check user existence
        if row is None:
            return False, "Username/password don't match"

        user_id, account_logon_type, account_status = row

        # Account validation - incorrect login type
        if account_logon_type != LogonType.PASSWORD.value:
            return False, "Username/password don't match"

        # Account validation - Is account active
        if account_status != AccountStatus.ACTIVE.value:
            self._logger.warning("Login attempt for inactive account %s",
                                 user_id)
            return False, "Account is not active"

        # Retrieve password hash
        try:
            stored_password = (
                await self._user_repository.get_password_hash(user_id))

        except SqliteInterfaceException as ex:

            self._logger.exception(
                "Password lookup failure: %s",
                str(ex))

            self._state.set_service_degraded(
                "Authentication storage degraded")

            return False, "Internal authentication error"

        # Validate password
        if stored_password is None:
            self._logger.error("User %s has no password record", user_id)
            return False, "Internal authentication error"

        try:
            PasswordHasher().verify(stored_password, password)
        except VerifyMismatchError:
            return False, "Username/password don't match"
        except (VerificationError, InvalidHashError) as ex:
            self._logger.error("Password verification error for user %s: %s",
                               user_id, str(ex))
            return False, "Internal authentication error"

        return True, "Authentication successful"
