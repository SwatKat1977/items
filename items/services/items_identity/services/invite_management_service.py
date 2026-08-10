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
import uuid as uuid_mod
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional

from items.services.items_identity.data_access.invite_repository import (
    InviteRepository)
from items.services.items_identity.data_access.user_repository import (
    UserRepository)

_INVITE_EXPIRY_SECONDS: int = 48 * 60 * 60  # 48 hours


class InviteCreateStatus(Enum):
    """Outcome codes for an invite creation attempt."""

    SUCCESS = auto()
    ALREADY_REGISTERED = auto()   # email exists in user_profile
    ALREADY_INVITED = auto()      # pending invite already exists


class InviteResendStatus(Enum):
    """Outcome codes for an invite resend attempt."""

    SUCCESS = auto()
    NO_PENDING_INVITE = auto()    # no pending invite found for email


class InviteUninviteStatus(Enum):
    """Outcome codes for an uninvite attempt."""

    SUCCESS = auto()
    NO_PENDING_INVITE = auto()    # no pending invite found for email


@dataclass
class InviteCreateResult:
    """Result returned by :meth:`InviteManagementService.create_invite`."""

    status: InviteCreateStatus
    token: Optional[str] = field(default=None)


@dataclass
class InviteResendResult:
    """Result returned by :meth:`InviteManagementService.resend_invite`."""

    status: InviteResendStatus
    token: Optional[str] = field(default=None)


@dataclass
class InviteUninviteResult:
    """Result returned by :meth:`InviteManagementService.uninvite`."""

    status: InviteUninviteStatus


@dataclass
class PendingInvite:
    """A single pending invite, as exposed to API callers.

    Deliberately excludes the invite ``token`` - it's a secret embedded in
    the invite email link, not needed by anything a list view does
    (resend/uninvite act on ``email_address``), so there's no reason to
    expose it over a general listing endpoint.
    """

    email_address: str
    created_at: int
    expires_at: int


class InviteManagementService:
    """Business logic for user invite lifecycle management.

    Coordinates between ``InviteRepository`` (invite table) and
    ``UserRepository`` (user_profile table) to enforce the rules:

    - An email already present in ``user_profile`` cannot be invited.
    - Only one pending invite per email address is permitted at any time.
    - Resend refreshes the token and expiry on the existing pending row.
    - Uninvite soft-expires the pending row.
    - The background expiry task soft-expires all overdue pending invites.
    """

    def __init__(self,
                 logger: logging.Logger,
                 invite_repo: InviteRepository,
                 user_repo: UserRepository) -> None:
        """Initialise the invite management service.

        Args:
            logger:      Logger used to record diagnostic messages.
            invite_repo: Repository for ``user_invite`` table operations.
            user_repo:   Repository for ``user_profile`` lookups (to check
                         whether an email is already registered).
        """
        self._logger = logger.getChild(type(self).__name__)
        self._invite_repo = invite_repo
        self._user_repo = user_repo

    async def get_pending_invites(self) -> list[PendingInvite]:
        """Return every pending (not yet expired or cancelled) invite.

        Returns:
            A list of :class:`PendingInvite`, ordered by creation time,
            oldest first. Empty if there are no pending invites.
        """
        rows = await self._invite_repo.get_pending_invites()
        return [
            PendingInvite(email_address=row[2], created_at=row[3],
                         expires_at=row[4])
            for row in rows
        ]

    async def create_invite(self, email_address: str) -> InviteCreateResult:
        """Create a new pending invite for an email address.

        Checks, in order:
        1. Email must not already exist in ``user_profile``.
        2. No pending invite must already exist for this email.

        On success, generates a UUID token and inserts the invite row with a
        48-hour expiry window.

        Args:
            email_address: Email address to invite.

        Returns:
            ``InviteCreateResult`` with status and token on success.
        """
        existing_user = await self._user_repo.get_user_by_email(email_address)
        if existing_user is not None:
            self._logger.warning(
                "Invite rejected: %s is already a registered user", email_address)
            return InviteCreateResult(status=InviteCreateStatus.ALREADY_REGISTERED)

        existing_invite = await self._invite_repo.get_invite_by_email(email_address)
        if existing_invite is not None:
            self._logger.warning(
                "Invite rejected: pending invite already exists for %s",
                email_address)
            return InviteCreateResult(status=InviteCreateStatus.ALREADY_INVITED)

        token: str = str(uuid_mod.uuid4())
        now: int = int(time.time())
        expires_at: int = now + _INVITE_EXPIRY_SECONDS

        await self._invite_repo.create_invite(token, email_address, now, expires_at)
        self._logger.info("Invite created for %s (token=%s)", email_address, token)

        return InviteCreateResult(status=InviteCreateStatus.SUCCESS, token=token)

    async def resend_invite(self, email_address: str) -> InviteResendResult:
        """Refresh the token and expiry for an existing pending invite.

        Generates a new UUID token and resets the 48-hour expiry window from
        now. Has no effect if no pending invite exists.

        Args:
            email_address: Email address whose pending invite should be refreshed.

        Returns:
            ``InviteResendResult`` with new token on success.
        """
        existing_invite = await self._invite_repo.get_invite_by_email(email_address)
        if existing_invite is None:
            self._logger.warning(
                "Resend rejected: no pending invite for %s", email_address)
            return InviteResendResult(status=InviteResendStatus.NO_PENDING_INVITE)

        new_token: str = str(uuid_mod.uuid4())
        new_expires_at: int = int(time.time()) + _INVITE_EXPIRY_SECONDS

        await self._invite_repo.resend_invite(email_address, new_token, new_expires_at)
        self._logger.info("Invite resent for %s (token=%s)", email_address, new_token)

        return InviteResendResult(status=InviteResendStatus.SUCCESS, token=new_token)

    async def uninvite(self, email_address: str) -> InviteUninviteResult:
        """Cancel the pending invite for an email address (soft-expire).

        Args:
            email_address: Email address whose pending invite should be cancelled.

        Returns:
            ``InviteUninviteResult`` with status.
        """
        existing_invite = await self._invite_repo.get_invite_by_email(email_address)
        if existing_invite is None:
            self._logger.warning(
                "Uninvite rejected: no pending invite for %s", email_address)
            return InviteUninviteResult(status=InviteUninviteStatus.NO_PENDING_INVITE)

        now: int = int(time.time())
        await self._invite_repo.uninvite(email_address, now)
        self._logger.info("Invite cancelled for %s", email_address)

        return InviteUninviteResult(status=InviteUninviteStatus.SUCCESS)

    async def expire_pending_invites(self) -> int:
        """Soft-expire all pending invites whose expiry time has passed.

        Intended to be called by the background task every 5 minutes.

        Returns:
            Always returns 0 (row count not surfaced by current DB interface).
            The operation is logged regardless.
        """
        now: int = int(time.time())
        await self._invite_repo.expire_pending_invites(now)
        self._logger.debug("Ran soft-expiry pass for pending invites (now=%d)", now)
        return 0
