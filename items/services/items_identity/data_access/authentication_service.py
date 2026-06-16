import logging
import bcrypt
from weaver_framework.database.sqlite_interface import SqliteInterfaceException
from items.shared.service_state import ServiceState
from items.services.items_identity.repositories.user_repository import \
    UserRepository
from items.services.items_identity.account_status import AccountStatus
from items.services.items_identity.logon_type import LogonType


class AuthenticationService:
    """
    Handles user authentication workflows and operational policy.
    """

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
        Authenticate a user using email/password credentials.

        Args:
            email: User email address.
            password: Plain-text password supplied by the user.

        Returns:
            tuple:
                (
                    authentication_successful,
                    status_message
                )
        """

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

        if not bcrypt.checkpw(
                password.encode("utf-8"),
                stored_password):
            return False, "Username/password don't match"

        return True, "Authentication successful"
