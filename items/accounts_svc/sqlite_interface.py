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
from hashlib import sha256
import logging
from typing import Optional, Tuple
from account_status import AccountStatus
from base_sqlite_interface import BaseSqliteInterface, SqliteInterfaceException
from state_object import StateObject
from service_health_enums import ComponentDegradationLevel


class SqliteInterface(BaseSqliteInterface):
    """
    Interface for interacting with a SQLite database, extending the
    functionality of the `BaseSqliteInterface`. Provides methods for verifying
    user logon eligibility and other database-related operations.

    Args:
        logger (logging.Logger): A logger instance for logging database-related events.
        db_file (str): Path to the SQLite database file.
    """

    def __init__(self, logger: logging.Logger, db_file: str,
                 state_object: StateObject) -> None:
        super().__init__(db_file)
        self._logger = logger.getChild(__name__)
        self._state_object: StateObject = state_object

    def valid_user_to_logon(self, email_address: str, logon_type: int) \
            -> Optional[Tuple[Optional[int], str]]:
        """
        Check to see if a user is able to logon based on email address and the
        logon type.

        parameters:
            email_address - User's email address\n
            logon_type - Logon type
        """

        user_id: Optional[int] = None
        error_str: str = ""

        query: str = ("SELECT id, logon_type, account_status "
                      "FROM user_profile "
                      "WHERE email_address = ?")

        try:
            rows: Optional[dict] = self.query_with_values(
                query, (email_address,))

        except SqliteInterfaceException as ex:
            self._logger.critical("Query failed, reason: %s", str(ex))
            self._state_object.database_health = ComponentDegradationLevel.SEVERE
            self._state_object.database_health_state_str = "Fatal SQL failure"
            return None

        if rows:
            user_id: int = rows[0][0]
            account_logon_type: int = rows[0][1]
            account_status: int = rows[0][2]

            if account_logon_type != logon_type:
                return 0, "Incorrect logon type"

            if account_status != AccountStatus.ACTIVE.value:
                return 0, "Account not active"

        else:
            error_str = 'Unknown e-mail address'

        return user_id, error_str

    def basic_user_authenticate(self, user_id: int, password: str) -> \
            Optional[Tuple[bool, str]]:
        """
        Authenticate a user using basic authentication (email address and a
        password.

        parameters:
            user_id - User's unique id\n
            password - Password to authenticate

        returns:
            tuple : (status, error string)
        """

        return_status: bool = False
        return_status_str: str = ""

        query: str = ("SELECT password, password_salt FROM user_auth_details "
                      "WHERE user_id = ?")

        try:
            rows: dict = self.query_with_values(query, (user_id,))

        except SqliteInterfaceException as ex:
            self._logger.critical("Query failed, reason: %s", str(ex))
            self._state_object.database_health = ComponentDegradationLevel.SEVERE
            self._state_object.database_health_state_str = "Fatal SQL failure"
            return None

        if not rows:
            raise SqliteInterfaceException('Invalid user id')

        recv_password = rows[0][0]
        recv_password_salt = rows[0][1]

        password_hash = f"{password}{recv_password_salt}".encode('UTF-8')
        password_hash = sha256(password_hash).hexdigest()

        if password_hash != recv_password:
            return_status_str = "Username/password don't match"

        else:
            return_status = True

        return return_status, return_status_str
