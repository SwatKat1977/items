import unittest
import logging
from unittest.mock import MagicMock, patch
from http import HTTPStatus
from services.authentication_service import AuthenticationService


class TestAuthenticationService(unittest.TestCase):
    def setUp(self):
        # Mock logger and its getChild() method
        self.mock_logger = MagicMock(spec=logging.Logger)
        self.mock_child_logger = MagicMock(spec=logging.Logger)
        self.mock_logger.getChild.return_value = self.mock_child_logger

        # Mock UserDataAccessLayer
        self.mock_user_dal = MagicMock()

        # Create AuthenticationService instance
        self.auth_service = AuthenticationService(self.mock_logger, self.mock_user_dal)

    def test_authenticate_basic_internal_error(self):
        """
        Case: get_user_for_logon returns (None, "some error")
        Expect: INTERNAL_SERVER_ERROR, log critical called
        """
        self.mock_user_dal.get_user_for_logon.return_value = (None, "DB error")

        status, response = self.auth_service.authenticate_basic("test@example.com", "pass")

        self.assertEqual(status, HTTPStatus.INTERNAL_SERVER_ERROR)
        self.assertEqual(response["status"], 0)
        self.assertIn("error", response)
        self.mock_child_logger.critical.assert_called_once_with(
            "Failed to verify user logon: %s", "DB error"
        )

    def test_authenticate_basic_invalid_user(self):
        """
        Case: get_user_for_logon returns ("", "Invalid user")
        Expect: OK, error message returned
        """
        self.mock_user_dal.get_user_for_logon.return_value = ("", "Invalid user")

        status, response = self.auth_service.authenticate_basic("no@user.com", "pass")

        self.assertEqual(status, HTTPStatus.OK)
        self.assertEqual(response, {"status": 0, "error": "Invalid user"})
        self.mock_child_logger.critical.assert_not_called()

    def test_authenticate_basic_success(self):
        """
        Case: get_user_for_logon returns valid user_id, authenticate_basic_user returns True
        Expect: OK, status 1, empty error
        """
        self.mock_user_dal.get_user_for_logon.return_value = ("user123", "")
        self.mock_user_dal.authenticate_basic_user.return_value = (True, "")

        status, response = self.auth_service.authenticate_basic("test@example.com", "password")

        self.assertEqual(status, HTTPStatus.OK)
        self.assertEqual(response, {"status": 1, "error": ""})
        self.mock_child_logger.critical.assert_not_called()
        self.mock_user_dal.authenticate_basic_user.assert_called_once_with("user123", "password")

    def test_authenticate_basic_wrong_password(self):
        """
        Case: valid user_id, but authentication fails
        Expect: OK, status 0, error message returned
        """
        self.mock_user_dal.get_user_for_logon.return_value = ("user123", "")
        self.mock_user_dal.authenticate_basic_user.return_value = (False, "Wrong password")

        status, response = self.auth_service.authenticate_basic("test@example.com", "badpass")

        self.assertEqual(status, HTTPStatus.OK)
        self.assertEqual(response, {"status": 0, "error": "Wrong password"})
        self.mock_child_logger.critical.assert_not_called()
