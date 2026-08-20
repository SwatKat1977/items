"""
Copyright 2025-2026 Integrated Test Management Suite Development Team
Copyright 2017-2025 INTMAC Development Team [Defunct]

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
import asyncio
from dataclasses import dataclass
from items.shared.account_logon_type import AccountLogonType


@dataclass
class SessionEntry:
    """
    Represents an authentication session entry.

    Attributes:
        email_address (str): The email address associated with the session.
        authentication_type (AccountLogonType): The type of authentication used.
        session_expiry (int): The session expiration timestamp (Unix time).
        token (str): The unique token identifying the session.
        is_administrator (bool): Whether the user has administrator privileges.
        user_id (str): The user's identity-service UUID. Empty if it could
            not be resolved at login (treated the same as no memberships).
        project_ids (frozenset[int]): The project ids this user was a member
            of at login/refresh time. Snapshotted, not re-checked per
            request - same staleness tradeoff already accepted for
            ``is_administrator`` (see the "deactivating a user does not
            touch their existing session" item in future.md).
    """
    email_address: str = ""
    authentication_type: AccountLogonType = AccountLogonType.BASIC
    session_expiry: int = 0
    token: str = ""
    is_administrator: bool = False
    user_id: str = ""
    project_ids: frozenset[int] = frozenset()


class Sessions:
    """
    Manages user authentication sessions.

    This class maintains an in-memory dictionary of active sessions and ensures
    safe concurrent access using an asyncio lock. Sessions are stored with unique
    tokens and are associated with email addresses and authentication types.
    """

    def __init__(self):
        self._sessions: dict[str, SessionEntry] = {}
        self._lock: asyncio.Lock = asyncio.Lock()

    # pylint: disable=too-many-arguments, too-many-positional-arguments
    async def add_session(self,
                          email_address: str,
                          token: str,
                          auth_type: AccountLogonType,
                          is_administrator: bool = False,
                          user_id: str = "",
                          project_ids: frozenset[int] | None = None) -> None:
        """
        Add an authentication session. Any existing session for the same email
        address is invalidated and replaced.

        Args:
            email_address (str): Email address of the user.
            token (str): Unique token for the session.
            auth_type (AccountLogonType): Type of authentication used.
            is_administrator (bool): Whether the user has administrator
                privileges. Defaults to False.
            user_id (str): The user's identity-service UUID, if resolved.
            project_ids (frozenset[int] | None): The project ids the user
                was a member of at login/refresh time. Defaults to an
                empty set - "no memberships" is the safe default, matching
                the existing "no membership = no access" rule elsewhere.
        """
        async with self._lock:
            entry: SessionEntry = SessionEntry()
            entry.email_address = email_address
            entry.token = token
            entry.authentication_type = auth_type
            entry.is_administrator = is_administrator
            entry.user_id = user_id
            entry.project_ids = project_ids if project_ids is not None \
                else frozenset()

            # If you logon a second time it will invalid any previous session.
            self._sessions.pop(email_address, None)
            self._sessions[email_address] = entry

    async def delete_session(self, email_address: str) -> None:
        """
        Remove an authentication session.

        Args:
            email_address (str): Email address of the user.
        """
        async with self._lock:
            self._sessions.pop(email_address, None)

    async def get_session_entry(self,
                                email_address: str,
                                token: str) -> SessionEntry | None:
        """
        Return the session entry if the token is valid, otherwise None.

        Args:
            email_address (str): Email address of the user.
            token (str): Token value to validate.

        Returns:
            SessionEntry if a session exists and the token matches,
            None otherwise.
        """
        async with self._lock:
            entry = self._sessions.get(email_address)
            if entry and entry.token == token:
                return entry
        return None

    async def is_valid_session(self, email_address: str, token: str) -> bool:
        """
        Verify if a session token for a given email address is valid.

        Args:
            email_address (str): Email address of the user.
            token (str): Token value to validate.

        Returns:
            bool: True if the session exists and the token matches, False otherwise.
        """
        async with self._lock:
            if email_address in self._sessions:
                return self._sessions[email_address].token == token
        return False

    async def has_session(self, email_address: str) -> bool:
        """
        Check whether a session exists for a given email address.

        Args:
            email_address (str): Email address of the user.

        Returns:
            bool: True if a session exists, False otherwise.
        """
        async with self._lock:
            return email_address in self._sessions

    async def add_project_id_for_user(self, user_id: str,
                                      project_id: int) -> None:
        """
        Live-patch a project id into a user's already-open session, if any.

        Called after a membership is successfully created, so a granted
        project shows up immediately rather than only after the user's
        next login - unlike deactivation, granting access has no reason to
        force a re-login. A no-op, not an error, if the user has no active
        session right now (nothing to patch) - the new membership is still
        picked up normally the next time they do log in.

        ``Sessions`` is keyed by email address, not user id, so this scans
        every entry for a matching ``user_id`` rather than doing a direct
        lookup. Cheap in practice - this is an in-memory dict of active
        sessions, not a database table - and avoids needing an email
        address the caller (a membership handler working from a URL-supplied
        UUID) doesn't have.

        Args:
            user_id: The user's identity-service UUID.
            project_id: The project id just added to their membership.
        """
        async with self._lock:
            for entry in self._sessions.values():
                if entry.user_id == user_id:
                    entry.project_ids = entry.project_ids | {project_id}
                    break

    async def remove_project_id_for_user(self, user_id: str,
                                         project_id: int) -> None:
        """
        Live-patch a project id out of a user's already-open session, if any.

        See :meth:`add_project_id_for_user` - same reasoning, same
        no-op-if-no-active-session behaviour, opposite direction: called
        after a membership is successfully removed, so the project stops
        being visible/reachable immediately rather than only after the
        user's next login.

        Args:
            user_id: The user's identity-service UUID.
            project_id: The project id just removed from their membership.
        """
        async with self._lock:
            for entry in self._sessions.values():
                if entry.user_id == user_id:
                    entry.project_ids = entry.project_ids - {project_id}
                    break

    async def set_is_administrator_for_user(self, user_id: str,
                                            is_administrator: bool) -> None:
        """
        Live-patch a user's already-open session to reflect a changed
        ``is_administrator`` flag, if they have one.

        Called after a successful ``PATCH /users/<id>`` that changes this
        flag, so admin rights granted or revoked take effect immediately
        rather than only at the user's next login - same reasoning as
        :meth:`add_project_id_for_user`, and the same "no-op, not an
        error, if there's no active session right now" behaviour.
        Deliberately a patch, not a forced logout, in either direction:
        revoking admin rights takes effect at the next admin-gated
        request regardless (``require_administrator`` reads this same
        field), so there's nothing a forced re-login would add.

        Args:
            user_id: The user's identity-service UUID.
            is_administrator: The new value of the flag.
        """
        async with self._lock:
            for entry in self._sessions.values():
                if entry.user_id == user_id:
                    entry.is_administrator = is_administrator
                    break

    async def delete_session_for_user(self, user_id: str) -> None:
        """
        Delete a user's already-open session, if any, looked up by user id.

        Called after a user is deactivated (``account_status`` set to 0
        via ``PATCH /users/<id>``) - unlike a project-access or
        admin-rights change, deactivation disables the whole account, so
        forcing a re-login (which will then correctly fail) is the right
        outcome here, not a live patch. A no-op if the user has no active
        session right now.

        Supersedes the original design for this fix (predating ``user_id``
        being cached on ``SessionEntry``), which proposed threading
        ``email_address`` through identity's response as a companion
        change there. Looking sessions up by ``user_id`` - the same
        mechanism ``add_project_id_for_user`` already uses - makes that
        unnecessary: this is a pure Gateway-side change.

        Args:
            user_id: The user's identity-service UUID.
        """
        async with self._lock:
            matching_email = next(
                (email for email, entry in self._sessions.items()
                 if entry.user_id == user_id), None)
            if matching_email is not None:
                del self._sessions[matching_email]
