import logging
from typing import Optional
from weaver_framework.database.sqlite_interface import SqliteInterface
from items.services.items_identity.identity_configuration import \
    IdentityConfiguration


class UserRepository:
    """
    Repository responsible for user-related persistence operations.
    """

    GET_USER_FOR_LOGON_QUERY: str = (
            "SELECT id, logon_type, account_status "
            "FROM user_profile "
            "WHERE email_address = ?")

    GET_PASSWORD_HASH_QUERY: str = (
        "SELECT password "
        "FROM user_auth_details "
        "WHERE user_id = ?")

    def __init__(self,
                 logger: logging.Logger,
                 config: IdentityConfiguration) -> None:
        self._logger: logging.Logger = logger.getChild(__name__)
        self._config: IdentityConfiguration = config

        self._db: SqliteInterface = SqliteInterface(
            self._logger,
            self._config.backend_db_filename)

    async def get_user_by_email(self,
                                email: str) -> Optional[tuple[int, int, int]]:
        """
        Retrieve user logon information by email address.

        Returns:
            Tuple containing:
                (
                    user_id,
                    logon_type,
                    account_status
                )

            or None if no matching user exists.
        """

        return await self._db.run_query(self.GET_USER_FOR_LOGON_QUERY,
                                        (email,),
                                        fetch_one=True)

    async def get_password_hash(
            self,
            user_id: int) -> Optional[bytes]:
        """
        Retrieve password hash for a user.

        Returns:
            Password hash bytes or None if not found.
        """

        row = await self._db.run_query(self.GET_PASSWORD_HASH_QUERY,
                                       (user_id,),
                                       fetch_one=True)

        return row[0] if row else None
