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
    """
    email_address: str = ""
    authentication_type: AccountLogonType = AccountLogonType.BASIC
    session_expiry: int = 0
    token: str = ""
    is_administrator: bool = False


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

    async def add_session(self,
                          email_address: str,
                          token: str,
                          auth_type: AccountLogonType,
                          is_administrator: bool = False) -> None:
        """
        Add an authentication session. Any existing session for the same email
        address is invalidated and replaced.

        Args:
            email_address (str): Email address of the user.
            token (str): Unique token for the session.
            auth_type (AccountLogonType): Type of authentication used.
            is_administrator (bool): Whether the user has administrator
                privileges. Defaults to False.
        """
        async with self._lock:
            entry: SessionEntry = SessionEntry()
            entry.email_address = email_address
            entry.token = token
            entry.authentication_type = auth_type
            entry.is_administrator = is_administrator

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
