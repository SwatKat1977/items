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
import logging
from http import HTTPStatus
from account_logon_type import AccountLogonType
from data_access.user_data_access_layer import UserDataAccessLayer


class AuthenticationService:
    """
    Encapsulates authentication business logic.
    Responsible for orchestrating user validation and authentication.
    """

    def __init__(self, logger: logging.Logger, user_dal: UserDataAccessLayer):
        self._logger = logger.getChild(self.__class__.__name__)
        self._user_dal = user_dal

    def authenticate_basic(self, email: str, password: str) -> tuple[int, dict]:
        """
        Handles the business logic for basic authentication.

        Returns:
            tuple[int, dict]: (HTTP status code, response JSON)
        """
        user_id, err_str = self._user_dal.get_user_for_logon(
            email, AccountLogonType.BASIC.value)

        if user_id is None:
            self._logger.critical("Failed to verify user logon: %s", err_str)
            return HTTPStatus.INTERNAL_SERVER_ERROR, {
                "status": 0,
                "error": "Internal server error"
            }

        if not user_id:
            return HTTPStatus.OK, {"status": 0, "error": err_str}

        status, err_str = self._user_dal.authenticate_basic_user(user_id,
                                                                 password)
        return HTTPStatus.OK, {
            "status": 1 if status else 0,
            "error": "" if status else err_str
        }
