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

    LIST_USERS_QUERY: str = (
        "SELECT id, email_address, full_name, display_name, insertion_date, "
        "account_status, logon_type, is_administrator "
        "FROM user_profile "
        "ORDER BY email_address")

    GET_USER_BY_ID_QUERY: str = (
        "SELECT id, email_address, full_name, display_name, insertion_date, "
        "account_status, logon_type, is_administrator "
        "FROM user_profile "
        "WHERE id = ?")

    # email_address is declared COLLATE NOCASE, so '=' is already
    # case-insensitive here - no LOWER() wrapping required.
    EMAIL_EXISTS_QUERY: str = (
        "SELECT 1 FROM user_profile WHERE email_address = ? LIMIT 1")

    EMAIL_EXISTS_EXCLUDING_QUERY: str = (
        "SELECT 1 FROM user_profile "
        "WHERE email_address = ? AND id != ? LIMIT 1")

    COUNT_ACTIVE_ADMINISTRATORS_QUERY: str = (
        "SELECT COUNT(*) FROM user_profile "
        "WHERE is_administrator = 1 AND account_status = ?")

    ADD_USER_PROFILE_QUERY: str = (
        "INSERT INTO user_profile (email_address, full_name, display_name, "
        "insertion_date, account_status, logon_type, is_administrator) "
        "VALUES(?, ?, ?, ?, ?, ?, ?)")

    ADD_USER_AUTH_DETAILS_QUERY: str = (
        "INSERT INTO user_auth_details (password, user_id) VALUES(?, ?)")

    UPDATE_USER_PROFILE_QUERY: str = (
        "UPDATE user_profile "
        "SET email_address = ?, full_name = ?, display_name = ?, "
        "account_status = ?, is_administrator = ? "
        "WHERE id = ?")

    # user_auth_details.user_id is UNIQUE, so a user has at most one
    # credential row; this updates it in place rather than inserting a second.
    UPDATE_PASSWORD_QUERY: str = (
        "UPDATE user_auth_details SET password = ? WHERE user_id = ?")

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

    # ------------------------------------------------------------------
    # User management: reads
    # ------------------------------------------------------------------

    async def list_users(self) -> list:
        """
        Retrieve every user account, ordered by email address.

        Returns:
            A list of row tuples, each of the form:

            (
                user_id,
                email_address,
                full_name,
                display_name,
                insertion_date,
                account_status,
                logon_type,
                is_administrator
            )

            An empty list if no accounts exist.

        Raises:
            SqliteInterfaceException:
                If the underlying database operation fails.
        """
        rows = await self._db.run_query(self.LIST_USERS_QUERY, ())
        return rows or []

    async def get_user_by_id(
            self,
            user_id: int) -> Optional[tuple]:
        """
        Retrieve a single user account by its identifier.

        Args:
            user_id:
                Unique identifier of the user.

        Returns:
            A row tuple in the same shape as :meth:`list_users`, or ``None``
            if no user has that identifier.

        Raises:
            SqliteInterfaceException:
                If the underlying database operation fails.
        """
        return await self._db.run_query(self.GET_USER_BY_ID_QUERY,
                                        (user_id,),
                                        fetch_one=True)

    async def email_address_exists(
            self,
            email: str,
            exclude_id: Optional[int] = None) -> bool:
        """
        Determine whether an email address is already in use.

        The comparison is case-insensitive because ``email_address`` is
        declared ``COLLATE NOCASE``.

        Callers should use this before inserting or updating, so that a
        duplicate address is reported as a conflict rather than surfacing as a
        database exception - a ``UNIQUE`` violation would otherwise be
        indistinguishable from a genuine outage and would mark the service
        degraded.

        Args:
            email:
                Email address to check.

            exclude_id:
                Identifier of the user being updated, excluded from the check
                so that keeping its own current address is not a conflict.

        Returns:
            ``True`` if the address is already used by another account.

        Raises:
            SqliteInterfaceException:
                If the underlying database operation fails.
        """
        if exclude_id is not None:
            row = await self._db.run_query(self.EMAIL_EXISTS_EXCLUDING_QUERY,
                                           (email, exclude_id),
                                           fetch_one=True)
        else:
            row = await self._db.run_query(self.EMAIL_EXISTS_QUERY,
                                           (email,),
                                           fetch_one=True)
        return bool(row)

    async def count_active_administrators(self, active_status: int) -> int:
        """
        Count the accounts that are both administrators and active.

        Used to prevent the last active administrator from being demoted or
        deactivated, which would leave the instance with no way to reach the
        administration pages.

        Args:
            active_status:
                The ``account_status`` value that represents an active
                account.

        Returns:
            The number of active administrator accounts.

        Raises:
            SqliteInterfaceException:
                If the underlying database operation fails.
        """
        row = await self._db.run_query(self.COUNT_ACTIVE_ADMINISTRATORS_QUERY,
                                       (active_status,),
                                       fetch_one=True)
        return int(row[0]) if row else 0

    # ------------------------------------------------------------------
    # User management: writes
    # ------------------------------------------------------------------

    async def create_user(self,
                          email: str,
                          full_name: str,
                          display_name: str,
                          account_status: int,
                          logon_type: int,
                          is_administrator: bool,
                          password_hash: str) -> Optional[int]:
        """
        Insert a user account and its credentials.

        ``insertion_date`` is recorded as the current Unix timestamp.

        Callers must check :meth:`email_address_exists` first; this method does
        not validate uniqueness itself.

        Args:
            email:            Email address (must not already be in use).
            full_name:        The user's full name.
            display_name:     Name shown in the interface.
            account_status:   Initial account status.
            logon_type:       Authentication type for the account.
            is_administrator: Whether the account may administer the instance.
            password_hash:    Pre-hashed password; never a plaintext value.

        Returns:
            The identifier of the newly created account.

        Raises:
            SqliteInterfaceException:
                If either insert fails.
        """
        # pylint: disable=too-many-arguments, too-many-positional-arguments

        user_id: int = await self._db.insert_query(
            self.ADD_USER_PROFILE_QUERY,
            (email, full_name, display_name, int(time.time()),
             account_status, logon_type, 1 if is_administrator else 0))

        await self._db.insert_query(self.ADD_USER_AUTH_DETAILS_QUERY,
                                    (password_hash, user_id))

        return user_id

    async def update_user(self,
                          user_id: int,
                          email: str,
                          full_name: str,
                          display_name: str,
                          account_status: int,
                          is_administrator: bool) -> None:
        """
        Update a user account's profile fields.

        ``logon_type`` and ``insertion_date`` are deliberately not updatable.
        Passwords are changed via :meth:`update_password_hash`.

        Callers must check :meth:`email_address_exists` first (passing
        ``exclude_id``); this method does not validate uniqueness itself.

        Args:
            user_id:          Identifier of the account to update.
            email:            New email address.
            full_name:        New full name.
            display_name:     New display name.
            account_status:   New account status.
            is_administrator: Whether the account may administer the instance.

        Raises:
            SqliteInterfaceException:
                If the update fails.
        """
        # pylint: disable=too-many-arguments, too-many-positional-arguments

        await self._db.run_query(
            self.UPDATE_USER_PROFILE_QUERY,
            (email, full_name, display_name, account_status,
             1 if is_administrator else 0, user_id),
            commit=True)

    async def update_password_hash(self,
                                   user_id: int,
                                   password_hash: str) -> None:
        """
        Replace a user's stored password hash.

        Args:
            user_id:       Identifier of the account.
            password_hash: Pre-hashed password; never a plaintext value.

        Raises:
            SqliteInterfaceException:
                If the update fails.
        """
        await self._db.run_query(self.UPDATE_PASSWORD_QUERY,
                                 (password_hash, user_id),
                                 commit=True)
