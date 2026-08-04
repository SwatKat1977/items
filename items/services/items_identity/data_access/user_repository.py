import logging
import time
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

    All queries that return user profile rows now include the ``uuid`` column.
    The integer primary key (``id``) is used internally for joins and foreign
    keys but is never surfaced in API responses; the ``uuid`` is the public
    identifier.
    """

    GET_USER_FOR_LOGON_QUERY: str = (
            "SELECT id, logon_type, account_status "
            "FROM user_profile "
            "WHERE email_address = ?")

    GET_USER_PROFILE_QUERY: str = (
        "SELECT id, uuid, email_address, full_name, display_name, "
        "account_status, logon_type, is_administrator "
        "FROM user_profile "
        "WHERE email_address = ?")

    GET_ALL_USERS_QUERY: str = (
        "SELECT id, uuid, email_address, full_name, display_name, "
        "account_status, logon_type, is_administrator "
        "FROM user_profile "
        "ORDER BY id")

    GET_USER_BY_ID_QUERY: str = (
        "SELECT id, uuid, email_address, full_name, display_name, "
        "account_status, logon_type, is_administrator "
        "FROM user_profile "
        "WHERE id = ?")

    GET_USER_BY_UUID_QUERY: str = (
        "SELECT id, uuid, email_address, full_name, display_name, "
        "account_status, logon_type, is_administrator "
        "FROM user_profile "
        "WHERE uuid = ?")

    EMAIL_EXISTS_QUERY: str = (
        "SELECT COUNT(*) FROM user_profile WHERE email_address = ?")

    INSERT_USER_PROFILE_QUERY: str = (
        "INSERT INTO user_profile "
        "(uuid, email_address, full_name, display_name, insertion_date, "
        "account_status, logon_type, is_administrator) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)")

    INSERT_USER_AUTH_QUERY: str = (
        "INSERT INTO user_auth_details (password, user_id) VALUES (?, ?)")

    UPDATE_USER_QUERY: str = (
        "UPDATE user_profile "
        "SET full_name = ?, display_name = ?, account_status = ?, "
        "is_administrator = ? "
        "WHERE id = ?")

    UPDATE_PASSWORD_QUERY: str = (
        "UPDATE user_auth_details SET password = ? WHERE user_id = ?")

    COUNT_ACTIVE_ADMINS_QUERY: str = (
        "SELECT COUNT(*) FROM user_profile "
        "WHERE is_administrator = 1 AND account_status = ?")

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
            email: str) -> Optional[
                tuple[int, str, str, str, str, int, int, int]]:
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
                id,
                uuid,
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
                Internal integer primary key of the user.

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

    async def get_all_users(self) -> list:
        """Retrieve all user profiles ordered by ID.

        Returns:
            A list of tuples, each containing:
            ``(id, uuid, email_address, full_name, display_name,
            account_status, logon_type, is_administrator)``.
            Returns an empty list if no users exist.

        Raises:
            SqliteInterfaceException: If the database query fails.
        """
        rows = await self._db.run_query(self.GET_ALL_USERS_QUERY, ())
        return rows if rows else []

    async def get_user_by_id(
            self,
            user_id: int) -> Optional[
                tuple[int, str, str, str, str, int, int, int]]:
        """Retrieve a user's profile by their internal integer ID.

        This is an internal lookup used within the identity service. External
        callers should use UUIDs; see :meth:`get_user_by_uuid`.

        Args:
            user_id: The user's primary key.

        Returns:
            A tuple ``(id, uuid, email_address, full_name, display_name,
            account_status, logon_type, is_administrator)`` if found,
            otherwise ``None``.

        Raises:
            SqliteInterfaceException: If the database query fails.
        """
        return await self._db.run_query(self.GET_USER_BY_ID_QUERY,
                                        (user_id,),
                                        fetch_one=True)

    async def get_user_by_uuid(
            self,
            user_uuid: str) -> Optional[
                tuple[int, str, str, str, str, int, int, int]]:
        """Retrieve a user's profile by their public UUID.

        This is the primary external lookup. The UUID is the identifier
        exposed in API responses; the integer ``id`` is kept internal.

        Args:
            user_uuid: The user's UUID string.

        Returns:
            A tuple ``(id, uuid, email_address, full_name, display_name,
            account_status, logon_type, is_administrator)`` if found,
            otherwise ``None``.

        Raises:
            SqliteInterfaceException: If the database query fails.
        """
        return await self._db.run_query(self.GET_USER_BY_UUID_QUERY,
                                        (user_uuid,),
                                        fetch_one=True)

    async def email_exists(self, email: str) -> bool:
        """Return True if the email address is already registered.

        Args:
            email: Email address to check.

        Returns:
            True if at least one row in ``user_profile`` has this address.

        Raises:
            SqliteInterfaceException: If the database query fails.
        """
        row = await self._db.run_query(self.EMAIL_EXISTS_QUERY,
                                       (email,),
                                       fetch_one=True)
        return bool(row and row[0])

    async def create_user(self,
                          user_uuid: str,
                          email: str,
                          full_name: str,
                          display_name: str,
                          account_status: int,
                          logon_type: int,
                          is_administrator: bool) -> int:
        """Insert a new user profile row.

        ``insertion_date`` is set to the current Unix timestamp automatically.

        Args:
            user_uuid:        UUID to assign as the public identifier.
            email:            Email address (login identifier).
            full_name:        User's full name.
            display_name:     Name shown in the UI.
            account_status:   Initial account status value.
            logon_type:       Logon mechanism (e.g. ``LogonType.PASSWORD``).
            is_administrator: Whether the new account has administrator access.

        Returns:
            The internal ``id`` of the newly inserted row.

        Raises:
            SqliteInterfaceException: If the database insert fails.
        """
        insertion_date = int(time.time())
        return await self._db.insert_query(
            self.INSERT_USER_PROFILE_QUERY,
            (user_uuid, email, full_name, display_name, insertion_date,
             account_status, logon_type, int(is_administrator)))

    async def create_user_auth(self, user_id: int, password_hash: str) -> None:
        """Insert a password hash record for a user.

        Args:
            user_id:       The user's internal primary key.
            password_hash: Argon2 hash of the user's initial password.

        Raises:
            SqliteInterfaceException: If the database insert fails.
        """
        await self._db.insert_query(self.INSERT_USER_AUTH_QUERY,
                                    (password_hash, user_id))

    async def update_user(self,
                          user_id: int,
                          full_name: str,
                          display_name: str,
                          account_status: int,
                          is_administrator: bool) -> None:
        """Update a user's profile fields.

        Args:
            user_id:          The user's internal primary key.
            full_name:        New full name.
            display_name:     New display name.
            account_status:   New account status value.
            is_administrator: New administrator flag.

        Raises:
            SqliteInterfaceException: If the database update fails.
        """
        await self._db.run_query(
            self.UPDATE_USER_QUERY,
            (full_name, display_name, account_status,
             int(is_administrator), user_id),
            commit=True)

    async def update_password(self, user_id: int, password_hash: str) -> None:
        """Replace the stored password hash for a user.

        Args:
            user_id:       The user's internal primary key.
            password_hash: New Argon2 hash.

        Raises:
            SqliteInterfaceException: If the database update fails.
        """
        await self._db.run_query(self.UPDATE_PASSWORD_QUERY,
                                 (password_hash, user_id),
                                 commit=True)

    async def count_active_administrators(self, active_status: int) -> int:
        """Return the number of active administrator accounts.

        Args:
            active_status: The ``account_status`` value that means active
                (i.e. ``AccountStatus.ACTIVE.value``).

        Returns:
            Count of rows in ``user_profile`` where ``is_administrator = 1``
            and ``account_status = active_status``.

        Raises:
            SqliteInterfaceException: If the database query fails.
        """
        row = await self._db.run_query(self.COUNT_ACTIVE_ADMINS_QUERY,
                                       (active_status,),
                                       fetch_one=True)
        return row[0] if row else 0
