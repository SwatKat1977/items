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
from typing import Optional
from weaver_framework.database.sqlite_interface import SqliteInterface
from items.services.items_identity.identity_configuration import (
    IdentityConfiguration)


class InviteRepository:
    """Provides persistence operations for user invites.

    Encapsulates all database access for the ``user_invite`` table. The
    integer primary key is internal only; the ``token`` UUID is the public
    identifier embedded in invite email links.

    Soft-expiry (``is_expired = 1``) is the standard lifecycle end-state.
    Hard-deletes (purges) are handled separately by a scheduled task and are
    not part of this repository's responsibility.
    """

    GET_INVITE_BY_TOKEN_QUERY: str = (
        "SELECT id, token, email_address, created_at, expires_at, "
        "is_expired, expired_at "
        "FROM user_invite "
        "WHERE token = ?")

    GET_INVITE_BY_EMAIL_QUERY: str = (
        "SELECT id, token, email_address, created_at, expires_at, "
        "is_expired, expired_at "
        "FROM user_invite "
        "WHERE email_address = ? AND is_expired = 0")

    GET_PENDING_INVITES_QUERY: str = (
        "SELECT id, token, email_address, created_at, expires_at, "
        "is_expired, expired_at "
        "FROM user_invite "
        "WHERE is_expired = 0 "
        "ORDER BY created_at")

    INSERT_INVITE_QUERY: str = (
        "INSERT INTO user_invite (token, email_address, created_at, expires_at) "
        "VALUES(?, ?, ?, ?)")

    RESEND_INVITE_QUERY: str = (
        "UPDATE user_invite SET token = ?, expires_at = ? "
        "WHERE email_address = ? AND is_expired = 0")

    SOFT_EXPIRE_BY_EMAIL_QUERY: str = (
        "UPDATE user_invite "
        "SET is_expired = 1, expired_at = ? "
        "WHERE email_address = ? AND is_expired = 0")

    SOFT_EXPIRE_PENDING_QUERY: str = (
        "UPDATE user_invite "
        "SET is_expired = 1, expired_at = ? "
        "WHERE is_expired = 0 AND expires_at < ?")

    def __init__(self,
                 logger: logging.Logger,
                 config: IdentityConfiguration) -> None:
        """Initialise the repository with a database connection.

        Args:
            logger: Parent logger used for repository and database logging.
            config: Identity service configuration providing the database path.
        """
        self._logger = logger.getChild(__name__)
        self._db = SqliteInterface(self._logger, config.backend_db_filename)

    async def get_invite_by_token(self, token: str) -> Optional[tuple]:
        """Fetch an invite row by its token UUID.

        Args:
            token: The invite token to look up.

        Returns:
            A 7-field row tuple, or None if not found.
        """
        return await self._db.run_query(
            self.GET_INVITE_BY_TOKEN_QUERY, (token,), fetch_one=True)

    async def get_invite_by_email(self, email_address: str) -> Optional[tuple]:
        """Fetch the pending invite for an email address.

        Only returns rows where ``is_expired = 0``.

        Args:
            email_address: Email address to look up.

        Returns:
            A 7-field row tuple, or None if no pending invite exists.
        """
        return await self._db.run_query(
            self.GET_INVITE_BY_EMAIL_QUERY, (email_address,), fetch_one=True)

    async def get_pending_invites(self) -> list[tuple]:
        """Fetch every pending (not yet expired or cancelled) invite.

        Returns:
            A list of 7-field row tuples, ordered by creation time, oldest
            first. Empty if there are no pending invites.
        """
        rows = await self._db.run_query(self.GET_PENDING_INVITES_QUERY, ())
        return rows or []

    async def create_invite(self,
                            token: str,
                            email_address: str,
                            created_at: int,
                            expires_at: int) -> int:
        """Insert a new invite record.

        Args:
            token:         UUID token to embed in the invite link.
            email_address: Recipient email address.
            created_at:    Creation timestamp (epoch seconds).
            expires_at:    Expiry timestamp (epoch seconds).

        Returns:
            The integer primary key of the inserted row.
        """
        return await self._db.insert_query(
            self.INSERT_INVITE_QUERY,
            (token, email_address, created_at, expires_at))

    async def resend_invite(self,
                            email_address: str,
                            new_token: str,
                            new_expires_at: int) -> None:
        """Refresh the token and expiry on an existing pending invite.

        Args:
            email_address: Email address of the pending invite to update.
            new_token:     Freshly generated UUID token.
            new_expires_at: New expiry timestamp (epoch seconds).
        """
        await self._db.run_query(
            self.RESEND_INVITE_QUERY,
            (new_token, new_expires_at, email_address),
            commit=True)

    async def uninvite(self, email_address: str, now: int) -> None:
        """Soft-expire the pending invite for an email address.

        Sets ``is_expired = 1`` and ``expired_at = now`` for the pending row.
        Has no effect if there is no pending invite for the address.

        Args:
            email_address: Email address whose invite should be cancelled.
            now:           Current timestamp (epoch seconds).
        """
        await self._db.run_query(
            self.SOFT_EXPIRE_BY_EMAIL_QUERY, (now, email_address),
            commit=True)

    async def expire_pending_invites(self, now: int) -> None:
        """Soft-expire all pending invites whose expiry time has passed.

        Called by the background task every 5 minutes. Sets ``is_expired = 1``
        and ``expired_at = now`` for every pending row where
        ``expires_at < now``.

        Args:
            now: Current timestamp (epoch seconds).
        """
        await self._db.run_query(
            self.SOFT_EXPIRE_PENDING_QUERY, (now, now),
            commit=True)
