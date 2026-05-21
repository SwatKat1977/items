import logging
from typing import Optional
from weaver_framework.database.sqlite_interface import SqliteInterface
from items.services.items_identity.identity_configuration import \
    IdentityConfiguration


class UserRepository:
    """
    Repository responsible for user-related persistence operations.
    """

    def __init__(self,
                 logger: logging.Logger,
                 config: IdentityConfiguration) -> None:
        self._logger: logging.Logger = logger.getChild(__name__)
        self._config: IdentityConfiguration = config

        self._db = SqliteInterface(logger,
                                   self._config.backend_db_filename)

    def get_user_for_logon(self, email: str) -> Optional[tuple]:
        """
        Retrieve user logon information by email address.

        Returns:
            tuple:
                (
                    user_id,
                    logon_type,
                    account_status
                )

            or None if the user does not exist.
        """

        query = (
            "SELECT id, logon_type, account_status "
            "FROM user_profile "
            "WHERE email_address = ?")

        return self._db.run_query(
            query,
            (email,),
            fetch_one=True)

    def get_password_hash(
            self,
            user_id: int) -> Optional[bytes]:
        """
        Retrieve password hash for a user.

        Returns:
            Password hash bytes or None if not found.
        """

        query = (
            "SELECT password "
            "FROM user_auth_details "
            "WHERE user_id = ?")

        row = self._db.run_query(
            query,
            (user_id,),
            fetch_one=True)

        if not row:
            return None

        return row[0]
