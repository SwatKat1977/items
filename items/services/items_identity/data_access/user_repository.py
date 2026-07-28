import logging
from typing import Optional
from weaver_framework.database.sqlite_interface import SqliteInterface
from items.services.items_identity.identity_configuration import \
    IdentityConfiguration


class UserRepository:
    """
    Provides persistence operations for user account and authentication data.

    This repository encapsulates database access for user identity and
    credential information. It serves as the data access layer between
    application services and the underlying SQLite storage.
    """

    GET_USER_FOR_LOGON_QUERY: str = (
            "SELECT id, logon_type, account_status "
            "FROM user_profile "
            "WHERE email_address = ?")

    GET_USER_PROFILE_QUERY: str = (
        "SELECT id, email_address, full_name, display_name, account_status, "
        "logon_type, is_administrator "
        "FROM user_profile "
        "WHERE email_address = ?")

    GET_PASSWORD_HASH_QUERY: str = (
        "SELECT password "
        "FROM user_auth_details "
        "WHERE user_id = ?")

    def __init__(self,
                 logger: logging.Logger,
                 config: IdentityConfiguration) -> None:
        """
        Initialize a UserRepository instance.

        Args:
            logger:
                Parent logger used for repository and database logging.

            config:
                Identity service configuration containing database
                connection settings.
        """
        self._logger: logging.Logger = logger.getChild(__name__)
        self._config: IdentityConfiguration = config

        self._db: SqliteInterface = SqliteInterface(
            self._logger,
            self._config.backend_db_filename)

    async def get_user_by_email(self,
                                email: str) -> Optional[tuple[int, int, int]]:
        """
        Retrieve user authentication information by email address.

        Args:
            email:
                Email address associated with the user account.

        Returns:
            A tuple containing the user's authentication metadata if a
            matching account exists:

            (
                user_id,
                logon_type,
                account_status
            )

            Returns ``None`` if no user exists with the specified email
            address.

        Raises:
            SqliteInterfaceException:
                If the underlying database operation fails.
        """
        return await self._db.run_query(self.GET_USER_FOR_LOGON_QUERY,
                                        (email,),
                                        fetch_one=True)

    async def get_user_profile_by_email(
            self,
            email: str) -> Optional[tuple[int, str, str, str, int, int, int]]:
        """
        Retrieve a user's profile details by email address.

        Unlike :meth:`get_user_by_email`, which returns only the fields needed
        to make a logon decision, this returns the user's profile for callers
        that need to know who the user is and what they are permitted to do.

        Args:
            email:
                Email address associated with the user account.

        Returns:
            A tuple containing the user's profile if a matching account
            exists:

            (
                user_id,
                email_address,
                full_name,
                display_name,
                account_status,
                logon_type,
                is_administrator
            )

            Returns ``None`` if no user exists with the specified email
            address.

        Raises:
            SqliteInterfaceException:
                If the underlying database operation fails.
        """
        return await self._db.run_query(self.GET_USER_PROFILE_QUERY,
                                        (email,),
                                        fetch_one=True)

    async def get_password_hash(
            self,
            user_id: int) -> Optional[str]:
        """
        Retrieve the stored password hash for a user.

        Args:
            user_id:
                Unique identifier of the user.

        Returns:
            The stored Argon2 password hash string if a password record
            exists, otherwise ``None``.

        Raises:
            SqliteInterfaceException:
                If the underlying database operation fails.
        """
        row = await self._db.run_query(self.GET_PASSWORD_HASH_QUERY,
                                       (user_id,),
                                       fetch_one=True)
        return row[0] if row else None
