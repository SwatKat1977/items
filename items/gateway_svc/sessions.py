"""
Copyright 2025 Integrated Test Management Suite Development Team

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
from dataclasses import dataclass
import threading
import typing
from account_logon_type import AccountLogonType

@dataclass
class SessionEntry:
    """
    Represents an authentication session entry.

    Attributes:
        email_address (str): The email address associated with the session.
        authentication_type (AccountLogonType): The type of authentication used.
        session_expiry (int): The session expiration timestamp (Unix time).
        token (str): The unique token identifying the session.
    """
    email_address: str = ""
    authentication_type: AccountLogonType = AccountLogonType.BASIC
    session_expiry: int = 0
    token: str = ""


class Sessions:
    """
    Manages user authentication sessions with thread safety.

    This class maintains a dictionary of active sessions and ensures
    thread-safe access using a mutex lock. Sessions are stored with unique
    tokens and are associated with email addresses and authentication types.
    """

    def __init__(self):
        # Shared resource (dictionary of sessions)
        self._sessions: typing.Dict[str, SessionEntry] = {}

        # Mutex to ensure thread safety
        self._thread_lock = threading.Lock()

    def add_session(self,
                    email_address: str,
                    token: str,
                    auth_type: AccountLogonType) -> None:
        """
        Add an authentication session to the REDIS database. It will attempt to
        lock the record before adding it to ensure concurrency consistency.

        parameters :
            email_address - Email address of the user
            token - Unique token specific for the session
            auth_type - Type of authentication that occurred
        """

        # Ensure only one thread modifies sessions at a time
        with self._thread_lock:

            # Session timeouts haven't been implemented yet, so the expiry will
            # always be set to a value of 0 (no expiry).
            entry: SessionEntry = SessionEntry()
            entry.email_address = email_address
            entry.token = token
            entry.authentication_type = auth_type

            # If you logon a second time it will invalid any previous session.
            self._sessions.pop(email_address, None)
            self._sessions[email_address] = entry

    def delete_session(self, email_address: str) -> None:
        """
        Remove an authentication session.It will attempt to lock the record
        before deleting it to ensure concurrency consistency.

        parameters :
            email_address - Email address of the user
        """

        # Ensure only one thread modifies sessions at a time
        with self._thread_lock:
            self._sessions.pop(email_address, None)

    def is_valid_session(self, email_address: str, token: str) -> bool:
        """
        Verify if a session token for a given email address is valid.

        parameters :
            emailAddress - Email address of the user\n
            token - Token value

        returns :
            bool - Validity boolean.
        """

        # Ensure only one thread modifies sessions at a time
        with self._thread_lock:
            if email_address in self._sessions:
                entry = self._sessions[email_address]
                return entry.token == token

            return False

    def has_session(self, email_address: str) -> bool:
        """
        Verify if a session exits for a given email address.

        parameters :
            email_address - Email address of the user\n

        returns :
            bool - Validity boolean.
        """
        # Ensure only one thread modifies sessions at a time
        with self._thread_lock:
            return email_address in self._sessions
