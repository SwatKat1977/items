import logging
import bcrypt
from weaver_framework.database.sqlite_interface import SqliteInterfaceException
from items.shared.service_state import ServiceState
from items.services.items_identity.repositories.user_repository import \
    UserRepository
from items.services.items_identity.account_status import AccountStatus


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

    def authenticate_basic_user(
            self,
            email: str,
            password: str,
            logon_type: int) -> tuple[bool, str]:
        """
        Authenticate a user using email/password credentials.

        Args:
            email:
                User email address.

            password:
                Plain-text password supplied by the user.

            logon_type:
                Expected logon type.

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
            row = self._user_repository.get_user_for_logon(email)

        except SqliteInterfaceException as ex:

            self._logger.exception(
                "Database failure during authentication: %s",
                str(ex))

            self._state.set_service_degraded(
                "Authentication database unavailable")

            return False, "Internal authentication error"

        # Check is the user existence
        if row is None:
            return False, "Username/password don't match"

        user_id, account_logon_type, account_status = row

        # Account validation
        if account_logon_type != logon_type:
            return False, "Incorrect logon type"

        if account_status != AccountStatus.ACTIVE.value:
            return False, "Account is not active"

        # Retrieve password hash
        try:
            stored_password = (
                self._user_repository.get_password_hash(user_id))

        except SqliteInterfaceException as ex:

            self._logger.exception(
                "Password lookup failure: %s",
                str(ex))

            self._state.set_service_degraded(
                "Authentication storage degraded")

            return False, "Internal authentication error"

        # Validate password
        if stored_password is None:
            return False, "Invalid user id"

        if not bcrypt.checkpw(
                password.encode("utf-8"),
                stored_password):
            return False, "Username/password don't match"

        return True, ""
